import copy
import inspect
from functools import partial
from pathlib import Path

import networkx as nx

from dag_gettsim.functions_loader import load_functions


def compute_taxes_and_transfers(
    data, functions=None, params=None, targets="all", return_dag=False
):
    """Simulate a tax and transfers system specified in model_spec.

    Args:
        data (dict): User provided dataset as dictionary of Series.
        functions (dict): Dictionary with user provided functions. The keys are the
            names of the function. The values are either callables or strings with
            absolute or relative import paths to a function. If functions have the
            same name as an existing gettsim function they override that function.
        params (dict): A pandas Series or dictionary with user provided parameters.
            Currently just mapping a parameter name to a parameter value, in the
            future we will need more metadata. If parameters have the same name as
            an existing parameter from the gettsim parameters database at the
            specified date they override that parameter.
        targets (list): List of strings with names of functions whose output is actually
            needed by the user. By default, all results are returned.

    Returns:
        dict: Dictionary of Series containing the target quantities.

    """
    data = copy.deepcopy(data)

    if isinstance(targets, str) and targets != "all":
        targets = [targets]

    user_functions = [] if functions is None else functions
    user_functions = load_functions(user_functions)

    internal_functions = {}
    internal_function_files = [
        "arbeitsl_v_rentenv.py",
        "krankv_pflegev.py",
        "eink_grenzen.py",
    ]
    for file in internal_function_files:
        new_funcs = load_functions(Path(__file__).parent / "soz_vers_funcs" / file)
        internal_functions.update(new_funcs)

    func_dict = create_function_dict(user_functions, internal_functions, params)

    dag = create_dag(func_dict)

    if targets != "all":
        dag = prune_dag(dag, targets)

        # Remove columns in data which are not used in the DAG.
        relevant_columns = set(data) & set(dag.nodes)
        data = _dict_subset(data, relevant_columns)

    results = execute_dag(func_dict, dag, data, targets)

    if len(results) == 1:
        results = list(results.values())[0]

    if return_dag:
        results = (results, dag)

    return results


def create_function_dict(user_functions, internal_functions, params):
    """Create a dictionary of all functions that will appear in the DAG.

    Args:
        user_functions (dict): Dictionary with user provided functions. The keys are the
            names of the function. The values are either callables or strings with
            absolute or relative import paths to a function.

    Returns:
        dict: Dictionary mapping function names to callables.

    """
    functions = {**internal_functions, **user_functions}

    partialed = {
        name: partial(func, params=params)
        if "params" in inspect.getfullargspec(func).args
        else func
        for name, func in functions.items()
    }

    return partialed


def create_dag(func_dict):
    """Create a directed acyclic graph (DAG) capturing dependencies between functions.

    Args:
        func_dict (dict): Maps function names to functions.

    Returns:
        dict: The DAG, represented as a dictionary of lists that maps function names
            to a list of its data dependencies.

    """
    dag_dict = {
        name: inspect.getfullargspec(func).args for name, func in func_dict.items()
    }
    return nx.DiGraph(dag_dict).reverse()


def prune_dag(dag, targets):
    """Prune the dag.

    Args:
        dag (nx.DiGraph): The unpruned DAG.
        targets (list): Variables of interest.

    Returns:
        dag (nx.DiGraph): Pruned DAG.

    """
    # Go through the DAG from the targets to the bottom and collect all visited nodes.
    visited_nodes = set(targets)
    visited_nodes_changed = True
    while visited_nodes_changed:
        n_visited_nodes = len(visited_nodes)
        for node in visited_nodes:
            visited_nodes = visited_nodes.union(nx.ancestors(dag, node))

        visited_nodes_changed = n_visited_nodes != len(visited_nodes)

    # Redundant nodes are nodes not visited going from the targets through the graph.
    all_nodes = set(dag.nodes)
    redundant_nodes = all_nodes - visited_nodes

    dag.remove_nodes_from(redundant_nodes)

    return dag


def execute_dag(func_dict, dag, data, targets):
    """Naive serial scheduler for our tasks.

    We will probably use some existing scheduler instead. Interesting sources are:
    - https://ipython.org/ipython-doc/3/parallel/dag_dependencies.html
    - https://docs.dask.org/en/latest/graphs.html

    The main reason for writing an own implementation is to explore how difficult it
    would to avoid dask as a dependency.

    Args:
        func_dict (dict): Maps function names to functions.
        dag (nx.DiGraph)
        data (dict):
        targets (list):

    Returns:
        dict: Dictionary of pd.Series with the results.

    """
    # Needed for garbage collection.
    visited_nodes = set(data)
    results = data.copy()

    for task in nx.topological_sort(dag):
        if task not in results:
            if task in func_dict:
                kwargs = _dict_subset(results, dag.predecessors(task))
                results[task] = func_dict[task](**kwargs)
            else:
                raise KeyError(f"Missing variable or function: {task}")

            visited_nodes.add(task)

            if targets != "all":
                results = collect_garbage(results, task, visited_nodes, targets, dag)

    return results


def _dict_subset(dictionary, keys):
    return {k: dictionary[k] for k in keys}


def collect_garbage(results, task, visited_nodes, targets, dag):
    """Remove data which is no longer necessary.

    If all descendants of a node have been evaluated, the information in the node
    becomes redundant and can be removed to save memory.

    Args:
        results (dict)
        task (str)
        visited_nodes (set)
        dag (nx.DiGraph)

    Returns:
        results (dict)

    """
    for ancestor in dag.predecessors(task):
        is_obsolete = all(
            successor in visited_nodes for successor in dag.successors(ancestor)
        )

        if is_obsolete and ancestor not in targets:
            del results[ancestor]

    return results

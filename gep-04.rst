=========================================
GEP 4 — A DAG-based Computational Backend
=========================================

+------------+---------------------------------------------------------------+
|   Author   |          `Max Blesch <https://github.com/MaxBlesch>`_         |
|            |          `Janos Gabler <https://github.com/janosg>`_          |
|            | `Hans-Martin von Gaudecker <https://github.com/hmgaudecker>`_ |
|            |        `Tobias Raabe <https://github.com/tobiasraabe>`_       |
+------------+---------------------------------------------------------------+
| Status     | Draft                                                         |
+------------+---------------------------------------------------------------+
| Type       | Standards Track                                               |
+------------+---------------------------------------------------------------+
| Created    | 2020-05-05                                                    |
+------------+---------------------------------------------------------------+
| Resolution | <url> (required for Accepted or Rejected or Withdrawn)        |
+------------+---------------------------------------------------------------+


Abstract
--------

This GEP lays out the plan to build a DAG-based computational backend for gettsim. A
directed acyclic graph (DAG) is common way to represent the relation between multiple
tasks which depend on each other via inputs and targets. The same is true for gettsim
where taxes and transfers depend on a multitude of observed variables in the data or on
pre-computed values based on the data and parameters.


Motivation and Scope
--------------------

The change is motivated by two primary reasons.

1. gettsim should not only deliver a fixed state of a tax and transfer system, it should
   also offer a comprehensive but simple API to alter the system.

2. gettsim is slow because the current structure does not allow to model only a specific
   part of the tax and transfer system while shutting all unrelated computation down.


Setup of the DAG
----------------

Before we explain how the user interface changes, it is necessary to understand how the
DAG is created and especially how the interdependency between variables is traced. We
focus on the following graph as an example.

.. image:: dag-example.png

In this graph, nodes without any arrow pointing at them like ``bruttolohn_m`` and
``wohnort_ost`` form the roots of the graph. Behind these nodes are variables which can
be observed in a given data set. The data set inside the backend is not a
``pandas.DataFrame``, but a dictionary of variable names and ``pandas.Series``'. At the
start, the data dictionary look like this:

.. code-block:: python

    data = {"bruttolohn_m": pd.Series(...), "wohnort_ost": pd.Series(...)}

All other nodes in the graph cannot be found in the data set. They are functions on
input variables and parameters. The function are collected in a dictionary similar to
the data dictionary where keys are the names of variables and values are functions.

.. code-block:: python

    functions = {
        "regulär_beschäftigt": regulär_beschäftigt,
        "krankv_beitr_bemess_grenze": krankv_beitr_bemess_grenze,
    }


For example, ``regulär_beschäftigt`` is defined like this:

.. code-block:: python

    def regulär_beschäftigt(bruttolohn_m, params):
        return bruttolohn_m.ge(params["geringfügige_eink_grenzen"]["midi_job"])

The function takes in ``bruttolohn_m`` which is a ``pandas.Series`` from the input data
and ``params`` which is a dictionary of parameters. The result of the function is a
``pandas.Series``.

We can infer two things from this function.

1. The name of the function is the name of its produced variable. The returned
   ``pandas.Series`` will be associated with the name ``regulär_beschäftigt``.

2. The names of the arguments identify which inputs are needed by this function. Before
   the function is called, the backend looks at the names of its arguments, detects
   whether all variables can be found in the data dictionary, and if so, passes the
   arguments in the correct order to the function to receive the resulting variable
   ``regulär_beschäftigt``.

The same logic applies to ``krankv_beitr_bemess_grenze`` which looks like this:

.. code-block:: python

    def krankv_beitr_bemess_grenze(wohnort_ost, params):
        pass

Functions which not only depend on input data but also or solely on pre-computed inputs
like ``lohn_krankv_regulär_beschäftigt`` are by no means different to the previous two
functions.

.. code-block:: python

    def lohn_krankv_regulär_beschäftigt(
        regulär_beschäftigt, krankv_beitr_bemess_grenze, params
    ):
        pass

The difference is how the backend postpones the execution of this function until all
input variables have been generated. Thus, ``lohn_krankv_regulär_beschäftigt`` would be
executed in the third position and ``krankv_beitr_regulär_beschäftigt`` in the fourth.


Usage and Impact
----------------

Having established how the graph is built and how the interdependency between functions
is detected, this section lays out the changes to the user interface and other
advantages of having a DAG-based backend.

At first, a user takes the tax and transfer system as given which is defined by a
collection of parameters and a dictionary of pre-defined functions like the ones in the
previous section.

If the user wants, for example, to alter definition of ``krankv_beitr_bemess_grenze``
there exist multiple ways to achieve that.

.. code-block:: python

    def krankv_beitr_bemess_grenze(wohnort_ost, params):
        out = np.where(
            wohnort_ost,
            params["beitr_bemess_grenze"]["ges_krankv"]["ost"],
            params["beitr_bemess_grenze"]["ges_krankv"]["west"],
        )

        s = pd.Series(out, name="krankv_beitr_bemess_grenze", index=wohnort_ost.index)

        return s

1. The user can change the parameters responsible for the contribution assessment
   ceiling.

2. If the user wants to change the function completely to a version without any ceiling,
   she writes a new function.

.. code-block:: python

    def keine_beitr_bemessungsgrenze(wohnort_ost):
        return pd.Series(data=np.inf, index=wohnort_ost.index)

Now, the new function must replace the old version. Thus, the interface function
``tax_transfer`` receives a new argument called ``functions`` which accepts dictionaries
(also paths to modules, etc.). If keys between the internal function dictionary and the
the dictionary provided by the user overlap, the user's functions are preferred. If
functions do not exist in the internal but in the user's dictionary, the user's
functions extend the existing collection.

Thus, the user would create the following dictionary

.. code-block:: python

    user_functions = {"krankv_beitr_bemess_grenze": keine_beitr_bemessungsgrenze}

and pass it to

.. code-block:: python

    tax_transfer(..., functions=user_functions, ...)

As the DAG-based backend offers many ways to alter the predefined tax and transfer
system delivered with gettsim, a part of the documentation should be dedicated to this
problem. We propose a collection of abstract patterns which can be followed and combined
by users to achieve their goals.

The second major change to the interface of ``tax_transfer`` is an argument called
``targets`` which allows the user to specify the variables she is ultimately interested
in. This allows to select a subset of the whole DAG which forms the tax and transfer
system and executes only the computations defined in the subset.

What are other benefits of using a DAG?

- Visual debugging of the system
- Pruning with ``targets``
- Avoiding duplicate computations.


Backward compatibility
----------------------

We do not expect any backward compatibility issues because, up to this moment, the tax
and transfer system was not available for modification. The additional argument
``functions`` and ``targets`` for ``tax_transfer()`` are optional and its defaults
deliver the same results as before.


Detailed description
--------------------

*Under development.*

This section should provide a detailed description of the proposed change. It should
include examples of how the new functionality would be used, intended use-cases and
pseudo-code illustrating its use.


Related Work
------------

- The `openfisca <https://github.com/openfisca/>`_ project uses an internal DAG as well.
- Scheduling computations on data with task graphs is how `Dask
  <https://docs.dask.org/>`_ splits and distributes computations.


Implementation
--------------

*Under development.*

This section lists the major steps required to implement the GEP.  Where possible, it
should be noted where one step is dependent on another, and which steps may be
optionally omitted.  Where it makes sense, each step should include a link to related
pull requests as the implementation progresses.

Any pull requests or development branches containing work on this GEP should be linked
to from here.  (A GEP does not need to be implemented in a single pull request if it
makes sense to implement it in discrete phases).


Alternatives
------------

We have not found any alternatives which offer the same amount of flexibility and
computational advantages.


Discussion
----------

*Under development.*

This section may just be a bullet list including links to any discussions regarding the
GEP:

- Links to relevant GitHub issues, pull requests.
- Discussion on XXX


References and Footnotes
------------------------

.. [1] Each GEP must either be explicitly labeled as placed in the public domain (see
       this GEP as an example) or licensed under the `Open Publication License`_.

.. _Open Publication License: https://www.opencontent.org/openpub/

.. _#general/geps: https://gettsim.zulipchat.com/#narrow/stream/212222-general/topic/GEPs


Copyright
---------

This document has been placed in the public domain. [1]_

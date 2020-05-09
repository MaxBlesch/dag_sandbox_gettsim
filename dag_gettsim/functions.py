import numpy as np
import pandas as pd

from dag_gettsim.aux_funcs import elementwise_min
from dag_gettsim.pre_processing.apply_tax_funcs import apply_tax_transfer_func
from dag_gettsim.soz_vers import soc_ins_contrib
from dag_gettsim.tests.test_soz_vers import OUT_COLS


def arbeitsl_v_regular_job(lohn_rente, params):
    """
    Calculates unemployment insurance contributions for regualr jobs.

    Parameters
    ----------
    lohn_rente : pd.Series
                 Wage subject to pension and unemployment insurance contributions.
    params

    Returns
    -------

    """
    out = params["soz_vers_beitr"]["arbeitsl_v"] * lohn_rente
    return pd.Series(index=lohn_rente.index, data=out, name="arbeitsl_v_regular_job")


def rentenv_beit_regular_job(lohn_rente, params):
    """
    Calculates pension insurance contributions for regualr jobs.

    Parameters
    ----------
    lohn_rente : pd.Series
                 Wage subject to pension and unemployment insurance contributions.
    params

    Returns
    -------

    """
    out = params["soz_vers_beitr"]["rentenv"] * lohn_rente
    return pd.Series(index=lohn_rente.index, data=out, name="rentenv_beit_regular_job")


def rentenv_beitr_bemess_grenze(wohnort_ost, params):
    """
    Selecting the threshold up to which income is subject to pension insurance
    contribution

    Parameters
    ----------
    wohnort_ost : pd.Series
                  Boolean variable indicating individual living in east germany.
    params

    Returns
    -------

    """
    out = np.select(
        [wohnort_ost, ~wohnort_ost],
        [
            params["beitr_bemess_grenze"]["rentenv"]["ost"],
            params["beitr_bemess_grenze"]["rentenv"]["west"],
        ],
    )
    return pd.Series(
        index=wohnort_ost.index, data=out, name="rentenv_beitr_bemess_grenze"
    )


def lohn_rente(bruttolohn_m, rentenv_beitr_bemess_grenze, params):
    """
    Calculate the wage, which is subject to pension insurance contributions.

    Parameters
    ----------
    bruttolohn_m : pd.Series
                   The wage of each individual.

    rentenv_beitr_bemess_grenze : pd.Series
                                 Threshold for wahe subcect to pension insurance
                                 contributions.

    params

    Returns
    -------

    """
    out = elementwise_min(bruttolohn_m, rentenv_beitr_bemess_grenze)
    return pd.Series(index=bruttolohn_m.index, data=out, name="lohn_rente")


def sozialv_beit_m(
    pflegev_beit_m, ges_krankv_beit_m, rentenv_beit_m, arbeitsl_v_beit_m, params
):
    sozialv_beit_m = (
        pflegev_beit_m + ges_krankv_beit_m + rentenv_beit_m + arbeitsl_v_beit_m
    )

    return pd.Series(data=sozialv_beit_m, name="sozialv_beit_m")


def rentenv_beit_m(
    p_id,
    hh_id,
    tu_id,
    bruttolohn_m,
    wohnort_ost,
    alter,
    selbstständig,
    hat_kinder,
    eink_selbstst_m,
    prv_krankv_beit_m,
    jahr,
    geringfügig_beschäftigt,
    in_gleitzone,
    rentenv_beit_regular_job,
    params,
):

    df = pd.concat(
        [
            p_id,
            hh_id,
            tu_id,
            bruttolohn_m,
            wohnort_ost,
            alter,
            selbstständig,
            hat_kinder,
            eink_selbstst_m,
            prv_krankv_beit_m,
            jahr,
            geringfügig_beschäftigt,
            in_gleitzone,
        ],
        axis=1,
    )
    df = apply_tax_transfer_func(
        df,
        tax_func=soc_ins_contrib,
        level=["hh_id", "tu_id", "p_id"],
        in_cols=list(df.columns),
        out_cols=OUT_COLS,
        func_kwargs={"params": params},
    )
    df.loc[geringfügig_beschäftigt, "rentenv_beit_m"] = 0
    cond_payoffs = [
        (~geringfügig_beschäftigt & ~in_gleitzone, rentenv_beit_regular_job)
    ]
    for logic_cond, payoff in cond_payoffs:
        df.loc[logic_cond, "rentenv_beit_m"] = payoff.loc[logic_cond]

    return df["rentenv_beit_m"]


def arbeitsl_v_beit_m(
    p_id,
    hh_id,
    tu_id,
    bruttolohn_m,
    wohnort_ost,
    alter,
    selbstständig,
    hat_kinder,
    eink_selbstst_m,
    prv_krankv_beit_m,
    jahr,
    geringfügig_beschäftigt,
    in_gleitzone,
    arbeitsl_v_regular_job,
    params,
):

    df = pd.concat(
        [
            p_id,
            hh_id,
            tu_id,
            bruttolohn_m,
            wohnort_ost,
            alter,
            selbstständig,
            hat_kinder,
            eink_selbstst_m,
            prv_krankv_beit_m,
            jahr,
            geringfügig_beschäftigt,
            in_gleitzone,
        ],
        axis=1,
    )
    df = apply_tax_transfer_func(
        df,
        tax_func=soc_ins_contrib,
        level=["hh_id", "tu_id", "p_id"],
        in_cols=list(df.columns),
        out_cols=OUT_COLS,
        func_kwargs={"params": params},
    )
    df.loc[geringfügig_beschäftigt, "arbeitsl_v_beit_m"] = 0
    cond_payoffs = [(~geringfügig_beschäftigt & ~in_gleitzone, arbeitsl_v_regular_job)]
    for logic_cond, payoff in cond_payoffs:
        df.loc[logic_cond, "arbeitsl_v_beit_m"] = payoff.loc[logic_cond]

    return df["arbeitsl_v_beit_m"]

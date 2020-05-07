import numpy as np
import pandas as pd

from dag_gettsim.pre_processing.apply_tax_funcs import apply_tax_transfer_func
from dag_gettsim.soz_vers import soc_ins_contrib
from dag_gettsim.tests.test_soz_vers import OUT_COLS


def mini_job_grenze(wohnort_ost, params):
    """
    Calculating the wage threshold for marginal employment.
    Parameters
    ----------
    wohnort_ost : pd.Series
                 Boolean variable indicating individual living in east germany.
    params : dict
            Dictionary containing the policy parameters

    Returns
    -------
    Array containing the income threshold for marginal employment.
    """
    return np.select(
        [wohnort_ost, ~wohnort_ost],
        [
            params["geringfügige_eink_grenzen"]["mini_job"]["ost"],
            params["geringfügige_eink_grenzen"]["mini_job"]["west"],
        ],
    )


def geringfügig_beschäftigt(bruttolohn_m, mini_job_grenze, params):
    """
    Checking if individual earns less then marginal employment threshold.
    Parameters
    ----------
    bruttolohn_m : pd.Series
                   The wage of each individual.
    mini_job_grenze : np.array
                      Array containing the income threshold for marginal employment.
    params

    Returns
    -------
    pd.Series containing a boolean variable indicating if individual is marginal
    employed.

    """
    belowmini = bruttolohn_m < mini_job_grenze
    return pd.Series(data=belowmini, name="geringfügig_beschäftigt")


def in_gleitzone(bruttolohn_m, geringfügig_beschäftigt, params):
    """
    Checking if individual earns less then threshold for regular employment,
    but more then threshold of marginal employment.

    Parameters
    ----------
    bruttolohn_m : pd.Series
                   The wage of each individual.
    mini_job_grenze : np.array
                      Array containing the income threshold for marginal employment.
    params

    Returns
    -------
    pd.Series containing a boolean variable indicating if individual's wage is more
    then marginal employment threshold but less than regular employment.
    """
    in_gleitzone = (params["geringfügige_eink_grenzen"]["midi_job"] >= bruttolohn_m) & (
        ~geringfügig_beschäftigt
    )
    return pd.Series(data=in_gleitzone, name="in_gleitzone")


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
    ges_rente_m,
    prv_krankv_beit_m,
    jahr,
    geringfügig_beschäftigt,
    in_gleitzone,
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
            ges_rente_m,
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
    ges_rente_m,
    prv_krankv_beit_m,
    jahr,
    geringfügig_beschäftigt,
    in_gleitzone,
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
            ges_rente_m,
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

    return df["arbeitsl_v_beit_m"]


def ges_krankv_beit_m(
    p_id,
    hh_id,
    tu_id,
    bruttolohn_m,
    wohnort_ost,
    alter,
    selbstständig,
    hat_kinder,
    eink_selbstst_m,
    ges_rente_m,
    prv_krankv_beit_m,
    jahr,
    geringfügig_beschäftigt,
    in_gleitzone,
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
            ges_rente_m,
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

    return df["ges_krankv_beit_m"]


def pflegev_beit_m(
    p_id,
    hh_id,
    tu_id,
    bruttolohn_m,
    wohnort_ost,
    alter,
    selbstständig,
    hat_kinder,
    eink_selbstst_m,
    ges_rente_m,
    prv_krankv_beit_m,
    jahr,
    geringfügig_beschäftigt,
    in_gleitzone,
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
            ges_rente_m,
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

    return df["pflegev_beit_m"]

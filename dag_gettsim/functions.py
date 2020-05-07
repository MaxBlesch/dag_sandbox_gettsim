import numpy as np
import pandas as pd

from dag_gettsim.aux_funcs import elementwise_min
from dag_gettsim.pre_processing.apply_tax_funcs import apply_tax_transfer_func
from dag_gettsim.soz_vers import soc_ins_contrib
from dag_gettsim.tests.test_soz_vers import OUT_COLS


def krankv_pflicht_rente(ges_rente_m, krankenv_beitr_bemess_grenze, params):
    relevante_rente = elementwise_min(ges_rente_m, krankenv_beitr_bemess_grenze)
    return pd.Series(name="krankv_pflicht_rente", data=relevante_rente)


def krankenv_beitr_bemess_grenze(wohnort_ost, params):
    """
    Calculating the income threshold up to which the rate of health insurance
    contributions apply.

    Parameters
    ----------
    wohnort_ost : pd.Series
                  Boolean variable indicating individual living in east germany.
    params

    Returns
    -------
    Pandas Series containing the income threshold up to which the rate of health
    insurance contributions apply.

    """
    bemess_grenze = np.select(
        [wohnort_ost, ~wohnort_ost],
        [
            params["beitr_bemess_grenze"]["ges_krankv"]["ost"],
            params["beitr_bemess_grenze"]["ges_krankv"]["west"],
        ],
    )
    return pd.Series(
        index=wohnort_ost.index, data=bemess_grenze, name="krankenv_beitr_bemess_grenze"
    )


def pflegev_beitr_rente(hat_kinder, alter, krankv_pflicht_rente, params):
    """
    Calculating the contribution to health insurance for pension income.

    Parameters
    ----------
    hat_kinder : pd.Series
                 Boolean indicating if individual has kids.

    alter : pd.Series
            Age of individual

    krankv_pflicht_rente : pd.Series
                           Pensions which are subject to social insurance contributions
    params

    Returns
    -------
    Pandas Series containing monthly health insurance contributions for pension income.
    """
    standard_beitr = (
        2 * params["soz_vers_beitr"]["pflegev"]["standard"] * krankv_pflicht_rente
    )
    standard_beitr.loc[(~hat_kinder) & (alter > 22)] += (
        params["soz_vers_beitr"]["pflegev"]["zusatz_kinderlos"] * krankv_pflicht_rente
    )
    return pd.Series(data=standard_beitr, name="pflegev_beitr_rente")


def krankenv_beitr_rente(krankv_pflicht_rente, params):
    """
    Calculating the contribution to health insurance for pension income.

    Parameters
    ----------
    krankv_pflicht_rente : pd.Series
                           Pensions which are subject to social insurance contributions

    params

    Returns
    -------
    Pandas Series containing monthly health insurance contributions for pension income.
    """

    beitr = params["soz_vers_beitr"]["ges_krankv"]["an"] * krankv_pflicht_rente
    return pd.Series(
        index=krankv_pflicht_rente.index, data=beitr, name="krankenv_beitr_rente"
    )


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
    Pandas Series containing the income threshold for marginal employment.
    """
    job_grenze = np.select(
        [wohnort_ost, ~wohnort_ost],
        [
            params["geringfügige_eink_grenzen"]["mini_job"]["ost"],
            params["geringfügige_eink_grenzen"]["mini_job"]["west"],
        ],
    )
    return pd.Series(index=wohnort_ost.index, data=job_grenze, name="mini_job_grenze")


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
    Pandas Series containing a boolean variable indicating if individual is marginal
    employed.

    """
    belowmini = bruttolohn_m < mini_job_grenze
    return pd.Series(
        index=bruttolohn_m.index, data=belowmini, name="geringfügig_beschäftigt"
    )


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
    Pandas Series containing a boolean variable indicating if individual's wage is more
    then marginal employment threshold but less than regular employment.
    """
    inbetween = (params["geringfügige_eink_grenzen"]["midi_job"] >= bruttolohn_m) & (
        ~geringfügig_beschäftigt
    )
    return pd.Series(index=bruttolohn_m.index, data=inbetween, name="in_gleitzone")


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
    prv_krankv_beit_m,
    jahr,
    geringfügig_beschäftigt,
    in_gleitzone,
    krankenv_beitr_rente,
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

    # Add the health insurance contribution for pensions
    df["ges_krankv_beit_m"] += krankenv_beitr_rente
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
    prv_krankv_beit_m,
    jahr,
    geringfügig_beschäftigt,
    in_gleitzone,
    pflegev_beitr_rente,
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

    # Add the care insurance contribution for pensions
    df["pflegev_beit_m"] += pflegev_beitr_rente
    return df["pflegev_beit_m"]

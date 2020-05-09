import numpy as np
import pandas as pd

from dag_gettsim.aux_funcs import elementwise_min
from dag_gettsim.pre_processing.apply_tax_funcs import apply_tax_transfer_func
from dag_gettsim.soz_vers import soc_ins_contrib
from dag_gettsim.tests.test_soz_vers import OUT_COLS


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
    ges_krankv_beitr_rente,
    ges_krankv_beitr_selbst,
    krankv_beit_regular_job,
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
    df.loc[geringfügig_beschäftigt, "ges_krankv_beit_m"] = 0

    cond_payoffs = [
        (~geringfügig_beschäftigt & ~in_gleitzone, krankv_beit_regular_job),
        (selbstständig & ~prv_krankv_beit_m, ges_krankv_beitr_selbst),
    ]

    for logic_cond, payoff in cond_payoffs:
        df.loc[logic_cond, "ges_krankv_beit_m"] = payoff.loc[logic_cond]

    # Add the health insurance contribution for pensions
    df["ges_krankv_beit_m"] += ges_krankv_beitr_rente
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
    pflegev_beitr_selbst,
    pflegev_beit_regular_job,
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
    df.loc[geringfügig_beschäftigt, "pflegev_beit_m"] = 0

    cond_payoffs = [
        (~geringfügig_beschäftigt & ~in_gleitzone, pflegev_beit_regular_job),
        (selbstständig & ~prv_krankv_beit_m, pflegev_beitr_selbst),
    ]

    for logic_cond, payoff in cond_payoffs:
        df.loc[logic_cond, "pflegev_beit_m"] = payoff.loc[logic_cond]

    # Add the care insurance contribution for pensions
    df["pflegev_beit_m"] += pflegev_beitr_rente

    return df["pflegev_beit_m"]


def krankv_beit_regular_job(lohn_krankv, params):
    """
    Calculates health insurance contributions for regualr jobs

    Parameters
    ----------
    lohn_krankv : pd.Series
                Wage subject to health and care insurance
    params

    Returns
    -------
    Pandas Series containing monthly health insurance contributions for self employed
    income.
    """
    out = params["soz_vers_beitr"]["ges_krankv"]["an"] * lohn_krankv
    return pd.Series(index=lohn_krankv.index, data=out, name="krankv_beit_regular_job")


def pflegev_beit_regular_job(hat_kinder, lohn_krankv, alter, params):
    """
    Calculates care insurance contributions for regular jobs.

    Parameters
    ----------
    hat_kinder : pd.Series
                 Boolean indicating if individual has kids.

    alter : pd.Series
            Age of individual

    lohn_krankv : pd.Series
                Wage subject to health and care insurance
    params

    Returns
    -------
    Pandas Series containing monthly care insurance contributions for self employed
    income.
    """
    out = lohn_krankv.multiply(params["soz_vers_beitr"]["pflegev"]["standard"])
    out.loc[~hat_kinder & alter.gt(22)] += (
        params["soz_vers_beitr"]["pflegev"]["zusatz_kinderlos"] * lohn_krankv
    )
    return pd.Series(index=lohn_krankv.index, data=out, name="pflegev_beit_regular_job")


def lohn_krankv(bruttolohn_m, krankv_beitr_bemess_grenze, params):
    """
    Calculate the wage, which is subject to pension insurance contributions.

    Parameters
    ----------
    bruttolohn_m : pd.Series
                   The wage of each individual.

    krankv_beitr_bemess_grenze : pd.Series
                                 Threshold for wage subject to health insurance
                                 contributions.

    params

    Returns
    -------

    """
    out = elementwise_min(bruttolohn_m, krankv_beitr_bemess_grenze)
    return pd.Series(index=bruttolohn_m.index, data=out, name="lohn_krankv")


def ges_krankv_beitr_selbst(krankv_pflichtig_eink_selbst, params):
    """
    Calculates health insurance contributions. Self-employed pay the full
    contribution (employer + employee), which is either assessed on their
    self-employement income or 3/4 of the 'Bezugsgröße'.

    Parameters
    ----------
    krankv_pflichtig_eink_selbst : pd.Series
                                     Income from self employment subject to health
                                     and care insurance
    params

    Returns
    -------
    Pandas Series containing monthly health insurance contributions for self employed
    income.
    """
    beitr_satz = (
        params["soz_vers_beitr"]["ges_krankv"]["an"]
        + params["soz_vers_beitr"]["ges_krankv"]["ag"]
    )
    out = krankv_pflichtig_eink_selbst.multiply(beitr_satz)
    return pd.Series(
        index=krankv_pflichtig_eink_selbst.index,
        data=out,
        name="ges_krankv_beitr_selbst",
    )


def pflegev_beitr_selbst(hat_kinder, alter, krankv_pflichtig_eink_selbst, params):
    """
    Calculates care insurance contributions. Self-employed pay the full
    contribution (employer + employee), which is either assessed on their
    self-employement income or 3/4 of the 'Bezugsgröße'

    Parameters
    ----------
    hat_kinder : pd.Series
                 Boolean indicating if individual has kids.

    alter : pd.Series
            Age of individual

    krankv_pflichtig_eink_selbst : pd.Series
                                     Income from self employment subject to health
                                     and care insurance
    params

    Returns
    -------
    Pandas Series containing monthly care insurance contributions for self employed
    income.
    """
    out = krankv_pflichtig_eink_selbst.multiply(
        2 * params["soz_vers_beitr"]["pflegev"]["standard"]
    )
    # Todo: No hardcoded 22.
    out.loc[~hat_kinder & alter.gt(22)] += (
        params["soz_vers_beitr"]["pflegev"]["zusatz_kinderlos"]
        * krankv_pflichtig_eink_selbst
    )
    return pd.Series(index=alter.index, data=out, name="pflegev_beitr_selbst")


def bezugsgröße(wohnort_ost, params):
    """
    Selecting by place of living the income threshold for self employed up to which the
    rate of health insurance contributions apply.

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
        [params["bezugsgröße"]["ost"], params["bezugsgröße"]["west"]],
    )
    return pd.Series(index=wohnort_ost.index, data=out, name="bezugsgröße")


def krankv_pflichtig_eink_selbst(eink_selbstst_m, bezugsgröße, params):
    """
    Choose the amount pension which is subject to health insurance contribution.

    Parameters
    ----------
    eink_selbstst_m : pd.Series
                  Pensions an individual recieves.

    bezugsgröße : pd.Series
                                   Threshold for income subcect to health insurance.

    params

    Returns
    -------

    """
    out = elementwise_min(eink_selbstst_m, bezugsgröße.multiply(0.75))
    return pd.Series(
        index=eink_selbstst_m.index, data=out, name="krankv_pflichtig_eink_selbst"
    )


def krankv_pflichtig_rente(ges_rente_m, krankv_beitr_bemess_grenze, params):
    """
    Choose the amount pension which is subject to health insurance contribution.

    Parameters
    ----------
    ges_rente_m : pd.Series
                  Pensions an individual recieves.

    krankv_beitr_bemess_grenze : pd.Series
                                   Threshold for income subcect to health insurance.

    params

    Returns
    -------

    """
    out = elementwise_min(ges_rente_m, krankv_beitr_bemess_grenze)
    return pd.Series(name="krankv_pflichtig_rente", data=out)


def krankv_beitr_bemess_grenze(wohnort_ost, params):
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
    out = np.select(
        [wohnort_ost, ~wohnort_ost],
        [
            params["beitr_bemess_grenze"]["ges_krankv"]["ost"],
            params["beitr_bemess_grenze"]["ges_krankv"]["west"],
        ],
    )
    return pd.Series(
        index=wohnort_ost.index, data=out, name="krankv_beitr_bemess_grenze"
    )


def pflegev_beitr_rente(hat_kinder, alter, krankv_pflichtig_rente, params):
    """
    Calculating the contribution to health insurance for pension income.

    Parameters
    ----------
    hat_kinder : pd.Series
                 Boolean indicating if individual has kids.

    alter : pd.Series
            Age of individual

    krankv_pflichtig_rente : pd.Series
                           Pensions which are subject to social insurance contributions.
    params

    Returns
    -------
    Pandas Series containing monthly health insurance contributions for pension income.
    """
    out = krankv_pflichtig_rente.multiply(
        2 * params["soz_vers_beitr"]["pflegev"]["standard"]
    )
    # Todo: No hardcoded 22.
    out.loc[~hat_kinder & alter.gt(22)] += (
        params["soz_vers_beitr"]["pflegev"]["zusatz_kinderlos"] * krankv_pflichtig_rente
    )
    return pd.Series(data=out, name="pflegev_beitr_rente")


def ges_krankv_beitr_rente(krankv_pflichtig_rente, params):
    """
    Calculating the contribution to health insurance for pension income.

    Parameters
    ----------
    krankv_pflichtig_rente : pd.Series
                           Pensions which are subject to social insurance contributions

    params

    Returns
    -------
    Pandas Series containing monthly health insurance contributions for pension income.
    """

    out = params["soz_vers_beitr"]["ges_krankv"]["an"] * krankv_pflichtig_rente
    return pd.Series(
        index=krankv_pflichtig_rente.index, data=out, name="ges_krankv_beitr_rente"
    )


def ges_beitr_krankv_midi_job(midi_job_bemessungsentgelt, params):
    """
    Calculating the sum of employee and employer health insurance contribution.

    Parameters
    ----------
    midi_job_bemessungsentgelt : pd.Series
                                 The Bemessungsentgelt subject to social insurance
                                 contributions.
    params

    Returns
    -------

    """
    out = (
        params["soz_vers_beitr"]["ges_krankv"]["an"]
        + params["soz_vers_beitr"]["ges_krankv"]["ag"]
    ) * midi_job_bemessungsentgelt
    return pd.Series(
        index=midi_job_bemessungsentgelt.index,
        data=out,
        name="ges_beitr_krankv_midi_job",
    )

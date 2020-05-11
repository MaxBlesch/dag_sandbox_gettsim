import numpy as np
import pandas as pd


def ges_krankv_beit_m(
    selbstständig,
    prv_krankv_beit_m,
    geringfügig_beschäftigt,
    in_gleitzone,
    ges_krankv_beitr_rente,
    ges_krankv_beitr_selbst,
    krankv_beit_regular_job,
    an_beitr_krankv_midi_job,
    params,
):

    ges_krankv_beit_m = pd.Series(
        index=geringfügig_beschäftigt.index, name="ges_krankv_beit_m", dtype=float
    )

    ges_krankv_beit_m.loc[geringfügig_beschäftigt] = 0

    cond_payoffs = [
        (in_gleitzone, an_beitr_krankv_midi_job),
        (~geringfügig_beschäftigt & ~in_gleitzone, krankv_beit_regular_job),
        (selbstständig & ~prv_krankv_beit_m, ges_krankv_beitr_selbst),
    ]

    for logic_cond, payoff in cond_payoffs:
        ges_krankv_beit_m.loc[logic_cond] = payoff.loc[logic_cond]

    # Add the health insurance contribution for pensions
    ges_krankv_beit_m += ges_krankv_beitr_rente
    return ges_krankv_beit_m


def pflegev_beit_m(
    selbstständig,
    prv_krankv_beit_m,
    geringfügig_beschäftigt,
    in_gleitzone,
    pflegev_beitr_rente,
    pflegev_beitr_selbst,
    pflegev_beit_regular_job,
    an_beitr_pflegev_midi_job,
    params,
):

    pflegev_beit_m = pd.Series(
        index=geringfügig_beschäftigt.index, name="pflegev_beit_m", dtype=float
    )

    pflegev_beit_m.loc[geringfügig_beschäftigt] = 0

    cond_payoffs = [
        (in_gleitzone, an_beitr_pflegev_midi_job),
        (~geringfügig_beschäftigt & ~in_gleitzone, pflegev_beit_regular_job),
        (selbstständig & ~prv_krankv_beit_m, pflegev_beitr_selbst),
    ]

    for logic_cond, payoff in cond_payoffs:
        pflegev_beit_m.loc[logic_cond] = payoff.loc[logic_cond]

    # Add the care insurance contribution for pensions
    pflegev_beit_m += pflegev_beitr_rente

    return pflegev_beit_m


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
    out = bruttolohn_m.where(
        bruttolohn_m < krankv_beitr_bemess_grenze, krankv_beitr_bemess_grenze
    )
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
    dreiviertel_bezugsgröße = bezugsgröße.multiply(0.75)
    out = eink_selbstst_m.where(
        eink_selbstst_m < dreiviertel_bezugsgröße, dreiviertel_bezugsgröße
    )
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
    out = ges_rente_m.where(
        ges_rente_m < krankv_beitr_bemess_grenze, krankv_beitr_bemess_grenze
    )
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


def ag_beitr_krankv_midi_job(bruttolohn_m, params):
    """
    Calculating the employer health insurance contribution.

    Parameters
    ----------
    bruttolohn_m : pd.Series
                   The wage of each individual.
    params

    Returns
    -------

    """
    out = params["soz_vers_beitr"]["ges_krankv"]["ag"] * bruttolohn_m
    return pd.Series(
        index=bruttolohn_m.index, data=out, name="ag_beitr_krankv_midi_job",
    )


def an_beitr_pflegev_midi_job(
    ges_beitr_pflegev_midi_job, ag_beitr_pflegev_midi_job, params
):
    """
    Calculating the employer care insurance contribution.

    Parameters
    ----------
    ges_beitr_pflegev_midi_job : pd.Series
                                    Sum of employer and employee care
                                    insurance contributions.

    ag_beitr_pflegev_midi_job : pd.Series
                                   Employer care insurance contribution.
    params

    Returns
    -------

    """
    out = ges_beitr_pflegev_midi_job - ag_beitr_pflegev_midi_job
    return pd.Series(
        index=ag_beitr_pflegev_midi_job.index,
        data=out,
        name="an_beitr_pflegev_midi_job",
    )


def an_beitr_krankv_midi_job(
    ges_beitr_krankv_midi_job, ag_beitr_krankv_midi_job, params
):
    """
    Calculating the employer health insurance contribution.

    Parameters
    ----------
    ges_beitr_krankv_midi_job : pd.Series
                                    Sum of employer and employee health
                                    insurance contributions.

    ag_beitr_krankv_midi_job : pd.Series
                               Employer health insurance contribution.
    params

    Returns
    -------

    """
    out = ges_beitr_krankv_midi_job - ag_beitr_krankv_midi_job
    return pd.Series(
        index=ag_beitr_krankv_midi_job.index, data=out, name="an_beitr_krankv_midi_job",
    )


def ag_beitr_pflegev_midi_job(bruttolohn_m, params):
    """
    Calculating the employer care insurance contribution.

    Parameters
    ----------
    bruttolohn_m : pd.Series
                   The wage of each individual.
    params

    Returns
    -------

    """
    out = params["soz_vers_beitr"]["pflegev"]["standard"] * bruttolohn_m
    return pd.Series(
        index=bruttolohn_m.index, data=out, name="ag_beitr_pflegev_midi_job",
    )


def ges_beitr_pflegev_midi_job(hat_kinder, alter, midi_job_bemessungsentgelt, params):
    """
    Calculating the sum of employee and employer care insurance contribution.

    Parameters
    ----------
    hat_kinder : pd.Series
             Boolean indicating if individual has kids.

    alter : pd.Series
            Age of individual

    midi_job_bemessungsentgelt : pd.Series
                                 The Bemessungsentgelt subject to social insurance
                                 contributions.
    params

    Returns
    -------

    """
    out = (
        2 * params["soz_vers_beitr"]["pflegev"]["standard"] * midi_job_bemessungsentgelt
    )
    zusatz_kinderlos = (
        params["soz_vers_beitr"]["pflegev"]["zusatz_kinderlos"]
        * midi_job_bemessungsentgelt
    )
    out.loc[~hat_kinder & alter.gt(22)] += zusatz_kinderlos.loc[
        ~hat_kinder & alter.gt(22)
    ]

    return pd.Series(
        index=midi_job_bemessungsentgelt.index,
        data=out,
        name="ges_beitr_pflegevv_midi_job",
    )

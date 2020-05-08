import numpy as np
import pandas as pd

from dag_gettsim.aux_funcs import elementwise_min


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

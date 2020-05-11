import numpy as np
import pandas as pd


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
    out = bruttolohn_m.where(
        bruttolohn_m < rentenv_beitr_bemess_grenze, rentenv_beitr_bemess_grenze
    )
    return pd.Series(index=bruttolohn_m.index, data=out, name="lohn_rente")


def ges_beitr_arbeitsl_v_midi_job(midi_job_bemessungsentgelt, params):
    """
    Calculating the sum of employee and employer unemployment insurance contribution.

    Parameters
    ----------
    midi_job_bemessungsentgelt : pd.Series
                                 The Bemessungsentgelt subject to social insurance
                                 contributions.
    params

    Returns
    -------

    """
    out = 2 * params["soz_vers_beitr"]["arbeitsl_v"] * midi_job_bemessungsentgelt
    return pd.Series(
        index=midi_job_bemessungsentgelt.index,
        data=out,
        name="ges_beitr_arbeitsl_v_midi_job",
    )


def ges_beitr_rentenv_midi_job(midi_job_bemessungsentgelt, params):
    """
    Calculating the sum of employee and employer pension insurance contribution.

    Parameters
    ----------
    midi_job_bemessungsentgelt : pd.Series
                                 The Bemessungsentgelt subject to social insurance
                                 contributions.
    params

    Returns
    -------

    """
    out = 2 * params["soz_vers_beitr"]["rentenv"] * midi_job_bemessungsentgelt
    return pd.Series(
        index=midi_job_bemessungsentgelt.index,
        data=out,
        name="ges_beitr_rentenv_midi_job",
    )


def ag_beitr_rentenv_midi_job(bruttolohn_m, params):
    """
    Calculating the employer pension insurance contribution.

    Parameters
    ----------
    bruttolohn_m : pd.Series
                   The wage of each individual.
    params

    Returns
    -------

    """
    out = params["soz_vers_beitr"]["rentenv"] * bruttolohn_m
    return pd.Series(
        index=bruttolohn_m.index, data=out, name="ag_beitr_rentenv_midi_job",
    )


def ag_beitr_arbeitsl_v_midi_job(bruttolohn_m, params):
    """
    Calculating the employer unemployment insurance contribution.

    Parameters
    ----------
    bruttolohn_m : pd.Series
                   The wage of each individual.
    params

    Returns
    -------

    """
    out = params["soz_vers_beitr"]["arbeitsl_v"] * bruttolohn_m
    return pd.Series(
        index=bruttolohn_m.index, data=out, name="ag_beitr_arbeitsl_v_midi_job",
    )


def an_beitr_rentenv_midi_job(
    ges_beitr_rentenv_midi_job, ag_beitr_rentenv_midi_job, params
):
    """
    Calculating the employer unemployment insurance contribution.

    Parameters
    ----------
    ges_beitr_rentenv_midi_job : pd.Series
                                    Sum of employer and employee pension
                                    insurance contributions.

    ag_beitr_rentenv_midi_job : pd.Series
                                   Employer pension insurance contribution.
    params

    Returns
    -------

    """
    out = ges_beitr_rentenv_midi_job - ag_beitr_rentenv_midi_job
    return pd.Series(
        index=ag_beitr_rentenv_midi_job.index,
        data=out,
        name="an_beitr_arbeitsl_v_midi_job",
    )


def an_beitr_arbeitsl_v_midi_job(
    ges_beitr_arbeitsl_v_midi_job, ag_beitr_arbeitsl_v_midi_job, params
):
    """
    Calculating the employer unemployment insurance contribution.

    Parameters
    ----------
    ges_beitr_arbeitsl_v_midi_job : pd.Series
                                    Sum of employer and employee unemployment
                                    insurance contributions.

    ag_beitr_arbeitsl_v_midi_job : pd.Series
                                   Employer unemployment insurance contribution.
    params

    Returns
    -------

    """
    out = ges_beitr_arbeitsl_v_midi_job - ag_beitr_arbeitsl_v_midi_job
    return pd.Series(
        index=ag_beitr_arbeitsl_v_midi_job.index,
        data=out,
        name="an_beitr_arbeitsl_v_midi_job",
    )


def sozialv_beit_m(
    pflegev_beit_m, ges_krankv_beit_m, rentenv_beit_m, arbeitsl_v_beit_m, params
):
    sozialv_beit_m = (
        pflegev_beit_m + ges_krankv_beit_m + rentenv_beit_m + arbeitsl_v_beit_m
    )

    return pd.Series(data=sozialv_beit_m, name="sozialv_beit_m")


def rentenv_beit_m(
    geringfügig_beschäftigt,
    in_gleitzone,
    rentenv_beit_regular_job,
    an_beitr_rentenv_midi_job,
    params,
):
    rentenv_beit_m = pd.Series(
        index=geringfügig_beschäftigt.index, name="rentenv_beit_m", dtype=float
    )

    # Set contribution 0 for people in minijob
    rentenv_beit_m.loc[geringfügig_beschäftigt] = 0

    cond_payoffs = [
        (in_gleitzone, an_beitr_rentenv_midi_job),
        (~geringfügig_beschäftigt & ~in_gleitzone, rentenv_beit_regular_job),
    ]

    for logic_cond, payoff in cond_payoffs:
        rentenv_beit_m.loc[logic_cond] = payoff.loc[logic_cond]

    return rentenv_beit_m


def arbeitsl_v_beit_m(
    geringfügig_beschäftigt,
    in_gleitzone,
    an_beitr_arbeitsl_v_midi_job,
    arbeitsl_v_regular_job,
    params,
):
    arbeitsl_v_beit_m = pd.Series(
        index=geringfügig_beschäftigt.index, name="arbeitsl_v_beit_m", dtype=float
    )

    # Set contribution 0 for people in minijob
    arbeitsl_v_beit_m.loc[geringfügig_beschäftigt] = 0

    cond_payoffs = [
        (in_gleitzone, an_beitr_arbeitsl_v_midi_job),
        (~geringfügig_beschäftigt & ~in_gleitzone, arbeitsl_v_regular_job),
    ]

    for logic_cond, payoff in cond_payoffs:
        arbeitsl_v_beit_m.loc[logic_cond] = payoff.loc[logic_cond]

    return arbeitsl_v_beit_m

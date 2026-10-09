# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # PEP Wind. Complementarity analysis.
# ##### Lubin Bénéteau
# ##### Date: 09.10.2026
#
# I am testing complementarity between wind speed (which, at a certain speed, could be used by wind turbines) and solar radiation (principal responsible for electricity production in PV).
#
# I use MeteoSwiss data at hourly, daily, monthly and yearly levels from 2020 to 2023 (aligned with Cauz and al.'s paper).
#
# Source: MeteoSwiss — [official parameter metadata](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_parameters.csv).

# %% [markdown]
# # Data pipeline

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# %%
from urllib.error import HTTPError

base_url = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn"

stations = pd.read_csv(base_url + "/ogd-smn_meta_stations.csv", sep=";", encoding="cp1252")

stations = stations[stations["station_canton"] != "FL"]
# This station has a 403 error:
stations = stations[stations["station_abbr"] != "MLJ"]

tableaux = []

for index, station in stations.iterrows():
    code = station["station_abbr"].lower()
    nom = station["station_name"]
    canton = station["station_canton"]

    # Data at hour, day, month and year levels
    for frequence in ["h", "d", "m", "y"]:

        if frequence == "h":
            fichier = f"ogd-smn_{code}_h_historical_2020-2029.csv"
        elif frequence == "d":
            fichier = f"ogd-smn_{code}_d_historical.csv"
        else:
            fichier = f"ogd-smn_{code}_{frequence}.csv"

        url = f"{base_url}/{code}/{fichier}"

        print("Téléchargement :", nom, "— fréquence :", frequence)

        tableau = pd.read_csv(
            url,
            sep=";",
            encoding="cp1252",
            na_values=["-"]
        )

        tableau["station_abbr"] = code.upper()
        tableau["station_name"] = nom
        tableau["station_canton"] = canton
        tableau["frequence"] = frequence

        tableaux.append(tableau)


# uncleaned dataset.
df_brut = pd.concat(tableaux, ignore_index=True)

# if needed to register it
# df_brut.to_csv("mesures_brutes.csv", sep=";", index=False)

# %%
df_hourly = df_brut[df_brut["frequence"] == "h"].copy()
df_daily = df_brut[df_brut["frequence"] == "d"].copy()
df_montlhy = df_brut[df_brut["frequence"] == "m"].copy()
df_yearly = df_brut[df_brut["frequence"] == "y"].copy()

# %%
# I keep only station identification variables, time, canton and wind + solar variables.
colonnes = [
    "station_abbr",
    "station_name",
    "station_canton",
    "reference_timestamp"
]

df_hourly = df_hourly[colonnes + ["fkl010h0", "gre000h0"]].copy()
df_daily = df_daily[colonnes + ["fkl010d0", "gre000d0"]].copy()
df_montlhy = df_montlhy[colonnes + ["fkl010m0", "gre000m0"]].copy()
df_yearly = df_yearly[colonnes + ["fkl010y0", "gre000y0"]].copy()


# %% [markdown]
# # Data cleaning

# %%
# definition of a cleaning function to apply it to df_hourly, df_daily, df_montlhy, df_yearly

def clean_data(df, wind, solar):
    df = df.copy()

    df["reference_timestamp"] = pd.to_datetime(
        df["reference_timestamp"],
        format="%d.%m.%Y %H:%M",
        utc=True,
        errors="coerce"
    )

    # As in Cauz and al. I keep only 2020-2023 period.
    years = df["reference_timestamp"].dt.year
    df = df[years.between(2020, 2023)].copy()

    # drop duplicates
    df = df.drop_duplicates(subset=["station_abbr", "reference_timestamp"], keep="last")

    # Drop NaN: it removes rows missing one of the two measures. !!! Warning, I drop some stations at this point, this could have consequences on my results 
    df = df.dropna(subset=[wind, solar])

    return df


df_hourly = clean_data(df_hourly, "fkl010h0", "gre000h0")
df_daily = clean_data(df_daily, "fkl010d0", "gre000d0")
df_montlhy = clean_data(df_montlhy, "fkl010m0", "gre000m0")
df_yearly = clean_data(df_yearly, "fkl010y0", "gre000y0")

# %% [markdown]
# # Spearman Correlation tests

# %%
resultats = []
resultats_journaliers = []
resultats_mensuels = []
resultats_annuels = []

for (nom, canton), station in df_hourly.groupby(["station_name", "station_canton"]):
    correlation = station["fkl010h0"].corr(station["gre000h0"],method="spearman")

    resultats.append([nom, canton, correlation])

for (nom, canton), station in df_daily.groupby(["station_name", "station_canton"]):
    correlation = station["fkl010d0"].corr(station["gre000d0"], method="spearman")

    resultats_journaliers.append([nom, canton, correlation])

for (nom, canton), station in df_montlhy.groupby(["station_name", "station_canton"]):
    correlation = station["fkl010m0"].corr(station["gre000m0"], method="spearman")

    resultats_mensuels.append([nom, canton, correlation])


for (nom, canton), station in df_yearly.groupby(["station_name", "station_canton"]):
    correlation = station["fkl010y0"].corr(station["gre000y0"], method="spearman")

    resultats_annuels.append([nom, canton, correlation])

correlations = pd.DataFrame(resultats, columns=["station_name", "station_canton", "correlation_spearman"])
correlations_journalieres = pd.DataFrame(resultats_journaliers, columns=["station_name", "station_canton", "correlation_spearman"])
correlations_mensuelles = pd.DataFrame(resultats_mensuels, columns=["station_name", "station_canton", "correlation_spearman"])
correlations_annuelles = pd.DataFrame(resultats_annuels, columns=["station_name", "station_canton", "correlation_spearman"])

# %%
horaire = correlations.rename(columns={"correlation_spearman": "spearman_hourly"})
journalier = correlations_journalieres.rename(columns={"correlation_spearman": "spearman_daily"})
mensuel = correlations_mensuelles.rename(columns={"correlation_spearman": "spearman_monthly"})
annuel = correlations_annuelles.rename(columns={"correlation_spearman": "spearman_yearly"})

correlations_all = horaire.merge(journalier, on=["station_name", "station_canton"], how="outer")
correlations_all = correlations_all.merge(mensuel, on=["station_name", "station_canton"], how="outer")
correlations_all = correlations_all.merge(annuel, on=["station_name", "station_canton"], how="outer")

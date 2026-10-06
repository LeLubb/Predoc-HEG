# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: .venv (3.12.3)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # wind-solar analysis. First approach. Swiss Data. 
# ##### Lubin Bénéteau, (affiliation: hes-so, HEG-Genève)
# ##### **Date(s)**: (beginning: 04.10.2026), uptaded on the 05 and 06.10.2026
#
# I am aiming at first build a toy code. I expect to extract relevant data related to solar measure. These data will be gathered, completed, cleaned. According to the literature (ref, 2018), I expect to find a (negative) coorelation between solar and wind energy.
#
# I rely, especially for the cleaning step, on a worflow proposed by MeteoSwiss at this adress: https://github.com/MeteoSwiss/opendata/blob/main/notebooks/MonthlyMeanGlobalRadiation_HAI.ipynb. 

# %%
import pandas as pd
import matplotlib.pyplot as plt

# %% [markdown]
# # Data processing
#
# I gather variables available at the station level. Clean them and produce a table named 'data'

# %%
base_url = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn"

parameters = pd.read_csv(base_url + "/ogd-smn_meta_parameters.csv", sep=";", encoding="cp1252")
inventory = pd.read_csv(base_url + "/ogd-smn_meta_datainventory.csv", sep=";", encoding="cp1252")
stations = pd.read_csv(base_url + "/ogd-smn_meta_stations.csv", sep=";", encoding="cp1252")

# cleaning step
for tableau in [parameters, inventory, stations]:
    tableau.columns = tableau.columns.str.strip()
    tableau.columns = tableau.columns.str.replace("'", "", regex=False)
    tableau.columns = tableau.columns.str.lower()

# inventory gives us usefull variables : station_abbr ; parameter_shortname ; data_since ; data_till. 
# At the moment I choose the very first station ("ABO") for the example code.
data = inventory[inventory["station_abbr"] == "ABO"]

# To this inventory we add up the parameters (group, description, granularity, decimal, type, unit).
data = data.merge(parameters, on="parameter_shortname", how="left")

# We add also 'stations' which includes : station_abbr, station_name, station_canton, station_data_since, station_coordinates_wgs84_lat, station_coordinates_wgs84_lon, station_exposition_en.
data = data.merge(stations, on="station_abbr", how="left")

# list of parameters of interest (namely: wind, sunshine, radiation). In the line below I will keep only the relevant one. for our analysis.
data["parameter_group_en"].unique()

# %% [markdown]
# ## Keeping only relevant variables for wind-solar analysis.

# %%
# I keep data relative to wind, sunshine, radiation and humidity to cover all the potential usefull variables for a pv / wind turbine analysis.
relevant_data = data[data["parameter_group_en"].isin(["Wind", "Sunshine", "Radiation", "Humidity"])]

codes = relevant_data["parameter_shortname"].drop_duplicates().tolist()

# Here is a short preview of the dataframe we will use to produce the analysis.
display(relevant_data[["parameter_shortname", "parameter_description_fr","parameter_granularity", "parameter_unit"]])


# %% [markdown]
# # Import of the historical data.
#
# We gather form the MeteoSwiss website the historical data, from the first measure to the very last, at the smaller scale (10 minutes).

# %%
import requests

catalogue_url = "https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn/items/abo"
reponse = requests.get(catalogue_url)
reponse.raise_for_status()
catalogue = reponse.json()

tableaux = []
for fichier in catalogue["assets"].values():
    url = fichier["href"]
    if "/ogd-smn_abo_" in url and url.endswith(".csv"):
        print("Downloading :", url.split("/")[-1])
        tableau = pd.read_csv(url, sep=";", encoding="cp1252")
        tableau.columns = tableau.columns.str.strip()
        tableau.columns = tableau.columns.str.replace("'", "", regex=False)
        tableau.columns = tableau.columns.str.lower()
        colonnes = ["station_abbr", "reference_timestamp"]
        colonnes = colonnes + [code for code in codes if code in tableau.columns]
        tableaux.append(tableau[colonnes])


# %% [markdown]
# # Creation of a final dataset.

# %%
# Vertical merge
granular_data = pd.concat(tableaux, ignore_index=True)
granular_data = granular_data.reindex(columns=["station_abbr", "reference_timestamp"] + codes)

# Date conversion to a more suitable format.
granular_data["reference_timestamp"] = pd.to_datetime(
    granular_data["reference_timestamp"], format="%d.%m.%Y %H:%M", utc=True
)

granular_data = granular_data.groupby(["station_abbr", "reference_timestamp"], as_index=False).first()
granular_data = granular_data.sort_values("reference_timestamp").reset_index(drop=True)

display(granular_data)

# %% [markdown]
# # Some thoughts and analysis
#
# On average, a wind turbine requires between 3 and 4 m/s of wind speed to function. A sufficient variable is the mean wind speed to monitor it. 
#
# Regarding solar pannel (pv), the relevant variable is radiation. Sunshine if of course correlated (positively) to radiation but a cloudy day will block sunshine but pv still function thanks to solar radiations. 
#
# So to analyse briefly the correlation between those two renewable sources, a good strating point consist in produce correlation matrix between the two aforementionned variables. 

# %%
noms = metadonnees.set_index("parameter_shortname")["parameter_description_en"]

matrice = granular_data[["fkl010z0", "gre000z0"]].dropna()
matrice = matrice.rename(columns=noms.to_dict()).corr()

display(matrice)

# %% [markdown]
# Check the same thing at night (when sun radiation is quasi absent).

# %%
noms = metadonnees.set_index("parameter_shortname")["parameter_description_en"]

nuit = granular_data.loc[
    granular_data["gre000z0"] < 5,
    ["fkl010z0", "gre000z0"]
].dropna()

display(nuit.rename(columns=noms.to_dict()).corr())

# %%
points = granular_data[["fkl010z0", "gre000z0"]].dropna()

plt.figure(figsize=(10, 5))
plt.scatter(points["fkl010z0"], points["gre000z0"], s=2, alpha=0.2)

plt.axvline(3, color="orange", linestyle="--", label="Wind: 3 m/s")
plt.axvline(25, color="red", linestyle="--", label="Wind: 25 m/s")
plt.axhline(100, color="green", linestyle="--", label="Radiation: 100 W/m²")

plt.xlabel("Mean wind speed (m/s)")
plt.ylabel("Mean global radiation (W/m²)")
plt.title("ABO — Wind speed and solar radiation")
plt.tight_layout()
plt.show()

# %%
import matplotlib.pyplot as plt

points = granular_data[["fkl010z0", "gre000z0"]].dropna()

wind = (points["fkl010z0"] >= 3) & (points["fkl010z0"] < 25)
solar = points["gre000z0"] >= 100

plt.figure(figsize=(10, 5))

for mask, color, label in [
    (solar & ~wind, "orange", "Solar only"),
    (wind & ~solar, "blue", "Wind only"),
    (wind & solar, "green", "Both"),
    (~wind & ~solar, "grey", "Neither"),
]:
    plt.scatter(
        points.loc[mask, "fkl010z0"],
        points.loc[mask, "gre000z0"],
        s=2, alpha=0.3, color=color,
        label=f"{label}: {100 * mask.mean():.1f}%",
    )

plt.axvline(3, color="black", linestyle="--", linewidth=0.8)
plt.axvline(25, color="black", linestyle="--", linewidth=0.8)
plt.axhline(100, color="black", linestyle="--", linewidth=0.8)

plt.xlabel("Mean wind speed (m/s)")
plt.ylabel("Mean global radiation (W/m²)")
plt.title("ABO — Availability under chosen thresholds")
plt.legend(markerscale=4)
plt.tight_layout()
plt.show()

# %%
import matplotlib.pyplot as plt

df = granular_data[["reference_timestamp", "fkl010z0", "gre000z0"]].dropna()
saisons = df.groupby(df["reference_timestamp"].dt.month)[["fkl010z0", "gre000z0"]].mean()

fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

axes[0].plot(saisons.index, saisons["fkl010z0"], "o-", color="blue")
axes[0].set_ylabel("Vent moyen (m/s)")
axes[0].set_title("ABO — Saisonnalité du vent et du rayonnement")

axes[1].plot(saisons.index, saisons["gre000z0"], "o-", color="orange")
axes[1].set_ylabel("Rayonnement moyen (W/m²)")
axes[1].set_xlabel("Mois")
axes[1].set_xticks(range(1, 13))

plt.tight_layout()
plt.show()

# %% [markdown]
# We could think that radiation is higher during summer and wind speed could also depends on season influencing correlation. Within a same season the wind speed could be higher that usual but we do not know if it has an impact on radiation (well clouds could move faster if there are some). 
#
# Data display summer with low wind and high radiation and winter with low radiation but high sped winds.
#
# Let correct the seasonality in our correlation measure. 

# %%
noms = metadonnees.set_index("parameter_shortname")["parameter_description_en"]

df = granular_data[
    ["reference_timestamp", "fkl010z0", "gre000z0"]
].dropna()

mois = df["reference_timestamp"].dt.month
valeurs = df[["fkl010z0", "gre000z0"]]

# Retirer la moyenne de chaque mois, toutes années confondues.
anomalies = valeurs - valeurs.groupby(mois).transform("mean")

matrice = anomalies.rename(columns=noms.to_dict()).corr()
display(matrice)

# %%
noms = metadonnees.set_index("parameter_shortname")["parameter_description_en"]

nuit = granular_data.loc[
    granular_data["gre000z0"] < 5,
    ["reference_timestamp", "fkl010z0", "gre000z0"]
].dropna()

mois = nuit["reference_timestamp"].dt.month
valeurs = nuit[["fkl010z0", "gre000z0"]]

# Soustraire la moyenne nocturne de chaque mois, toutes années confondues.
anomalies = valeurs - valeurs.groupby(mois).transform("mean")

display(anomalies.rename(columns=noms.to_dict()).corr())

# %%
import matplotlib.pyplot as plt

day = granular_data[granular_data["gre000z0"] >= 5]
night = granular_data[granular_data["gre000z0"] < 5]

fig, axes = plt.subplots(3, 2, figsize=(14, 12))

for row, (period, data) in enumerate([
    ("All hours", granular_data),
    ("Day", day),
    ("Night", night),
]):
    for column, (variable, threshold, color, title, unit) in enumerate([
        ("gre000z0", 100, "orange", "Radiation", "W/m²"),
        ("fkl010z0", 5, "blue", "Wind speed", "m/s"),
    ]):
        values = data[variable].dropna()
        available = values >= threshold

        if variable == "fkl010z0":
            available = available & (values < 25)

        percentage = 100 * available.mean()
        ax = axes[row, column]

        ax.hist(
            values, bins=40, density=True, color=color,
            label=f"Availability: {percentage:.1f}%",
        )
        ax.axvline(
            threshold, color="red", linestyle="--",
            label=f"Threshold: {threshold} {unit}",
        )

        if variable == "fkl010z0":
            ax.axvline(25, color="black", linestyle="--", label="Cut-out: 25 m/s")

        ax.set_title(f"{period} — {title}")
        ax.set_xlabel(f"{title} ({unit})")
        ax.set_ylabel("Probability density")
        ax.legend()

fig.suptitle("ABO — Resource availability")
plt.tight_layout()

# fig.savefig("ABO_availability.png", dpi=300, bbox_inches="tight")

plt.show()

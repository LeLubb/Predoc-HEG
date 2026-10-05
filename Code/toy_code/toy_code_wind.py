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
# # Wind analysis. First approach. Swiss Data. 
# ## Lubin Bénéteau, (aff: hes-so, HEG-Genève)
# ## date: (beginning: 04.10.2026)    
#
# I am aiming at first build a toy code. I expect to extract relevant data related to wind measure. These data will be gathered, completed, cleaned. In a second round I will do the same thing with solar data, then merge wind and solar data to perfom complementary analysis. According to the literature (ref, 2018), I expect to find a (negative) coorelation between measures.

# %%
# mostly rely on a worflow proposed by MeteoSwiss at this adress: https://github.com/MeteoSwiss/opendata/blob/main/notebooks/MonthlyMeanGlobalRadiation_HAI.ipynb 
# It consists on an csv import, hamonization of columns name and fast cleaning. 


import pandas as pd

def download_csv(url):
    return pd.read_csv(url, sep=";", encoding="cp1252")

def clean_column_names(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("'", "", regex=False)
        .str.lower()
    )
    return df


# I am here focusing on wind variables, that is why ' = "Vent" ' is written. 
def process_data(parameters, inventory, station):
    wind = parameters[parameters["parameter_group_fr"] == "Vent"]

    data = inventory.merge(wind, on="parameter_shortname")
    data = data[data["station_abbr"] == station].copy()

    for column in ["data_since", "data_till"]:
        data[column] = pd.to_datetime(
            data[column],
            format="%d.%m.%Y %H:%M",
            utc=True,
        )

    return data[[
        "parameter_shortname",
        "parameter_description_fr",
        "parameter_granularity",
        "parameter_unit",
        "data_since",
        "data_till",
    ]].sort_values("parameter_shortname")


base_url = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn"

stations = clean_column_names(download_csv(f"{base_url}/ogd-smn_meta_stations.csv"))

parameters = clean_column_names(download_csv(f"{base_url}/ogd-smn_meta_parameters.csv"))

inventory = clean_column_names(download_csv(f"{base_url}/ogd-smn_meta_datainventory.csv"))


# %%
station = "ABO"
resolution = "h"  # t = 10 min, h = heure, d = jour, m = mois, y = année

suffix = "" if resolution in ["m", "y"] else "_recent"

url = (
    f"{base_url}/{station.lower()}/"
    f"ogd-smn_{station.lower()}_{resolution}{suffix}.csv"
)

data = clean_column_names(download_csv(url))

data["reference_timestamp"] = pd.to_datetime(
    data["reference_timestamp"],
    format="%d.%m.%Y %H:%M",
    utc=False,
)

wind_data = process_data(parameters, inventory, station)

columns = [
    variable
    for variable in wind_data["parameter_shortname"]
    if variable in data.columns
]

wind_values = (
    data[["reference_timestamp"] + columns]
    .dropna(subset=columns, how="all")
    .sort_values("reference_timestamp")
)

display(wind_values)

# %% [markdown]
# More than one station code :

# %%
# Choisir les stations et la résolution
selected_stations = ["HAI", "BER"]
resolution = "d"  # t, h, d, m ou y

suffix = "" if resolution in ["m", "y"] else "_recent"

results = []

for station in selected_stations:
    url = (
        f"{base_url}/{station.lower()}/"
        f"ogd-smn_{station.lower()}_{resolution}{suffix}.csv"
    )

    data = clean_column_names(download_csv(url))

    data["reference_timestamp"] = pd.to_datetime(
        data["reference_timestamp"],
        format="%d.%m.%Y %H:%M",
        utc=True,
    )

    wind_data = process_data(parameters, inventory, station)

    columns = [
        variable
        for variable in wind_data["parameter_shortname"]
        if variable in data.columns
    ]

    wind_values = data[
        ["station_abbr", "reference_timestamp"] + columns
    ].dropna(subset=columns, how="all")

    results.append(wind_values)

# Réunir et afficher les deux stations
wind_values = (
    pd.concat(results, ignore_index=True)
    .sort_values(["reference_timestamp", "station_abbr"])
    .reset_index(drop=True)
)

display(wind_values)

# %% [markdown]
# # descriptive statistics

# %%
wind_values_desc = wind_values.copy()

# for readable columns
wind_values_desc = wind_values_desc.rename(columns={
    "station_abbr": "Station",
    "reference_timestamp": "Date (UTC)",
    "dkl010d0": "Direction moyenne journalière (°)",
    "fkl010d0": "Vitesse moyenne journalière (m/s)",
    "fkl010d1": "Rafale maximale journalière sur 1 s (m/s)",
    "fkl010d3": "Rafale maximale journalière sur 3 s (m/s)",
    "fu3010d0": "Vitesse moyenne journalière (km/h)",
    "fu3010d1": "Rafale maximale journalière sur 1 s (km/h)",
    "fu3010d3": "Rafale maximale journalière sur 3 s (km/h)",
})

# %% [markdown]
# # A few descriptive graphs.

# %%
import matplotlib.pyplot as plt

data = wind_values.pivot(
    index="reference_timestamp",
    columns="station_abbr",
    values="fu3010d0",
).sort_index()

trend = data.rolling("30D", min_periods=15).mean()

fig, ax = plt.subplots(figsize=(12, 5))

for station in data:
    line, = ax.plot(data[station], alpha=0.25, label=f"{station} — daily")
    ax.plot(
        trend[station], color=line.get_color(),
        linewidth=2, label=f"{station} — 30-day average",
    )

ax.set(
    xlabel="Date (UTC)",
    ylabel="Daily mean wind speed (km/h)",
    title="Daily wind speed and 30-day trend",
)
ax.legend()
plt.tight_layout()
plt.show()
# %%

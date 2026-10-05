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
# # solar analysis. First approach. Swiss Data. 
# ##### Lubin Bénéteau, (aff: hes-so, HEG-Genève)
# ###### date: (beginning: 04.10.2026)    
#
# I am aiming at first build a toy code. I expect to extract relevant data related to solar measure. These data will be gathered, completed, cleaned. According to the literature (ref, 2018), I expect to find a (negative) coorelation between solar and wind energy.
#
# I mostly rely on a worflow proposed by MeteoSwiss at this adress: https://github.com/MeteoSwiss/opendata/blob/main/notebooks/MonthlyMeanGlobalRadiation_HAI.ipynb 
# It consists on an csv import, hamonization of columns name and fast cleaning.

# %%
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


# Sélectionner le rayonnement global à 10 minutes. 
def process_data(parameters, inventory, station):
    solar = parameters[parameters["parameter_shortname"] == "gre000z0"]

    data = inventory.merge(solar, on="parameter_shortname")
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
solar_station = "ABO"
solar_variable = "gre000z0"

solar_inventory = inventory.merge(
    parameters, on="parameter_shortname"
)

available = solar_inventory.loc[
    (solar_inventory["station_abbr"] == solar_station)
    & (solar_inventory["parameter_shortname"] == solar_variable)
    & (solar_inventory["parameter_granularity"].str.upper() == "T")
]

if available.empty:
    raise ValueError(
        f"No data available {solar_station}."
    )

prefix = (
    f"{base_url}/{solar_station.lower()}"
    f"/ogd-smn_{solar_station.lower()}_t"
)

solar_results = []
for suffix in [
    "historical_2000-2009",
    "historical_2010-2019",
    "historical_2020-2029",
    "recent",
    "now",
]:
    print(f"downloading : {solar_station} — {suffix}", flush=True)
    data = clean_column_names(download_csv(f"{prefix}_{suffix}.csv"))
    if solar_variable not in data.columns:
        raise ValueError(f"Variable {solar_variable} not in the file: {suffix}.")
    solar_results.append(
        data.reindex(columns=[
            "station_abbr", "reference_timestamp", solar_variable
        ])
    )

solar_values = pd.concat(solar_results, ignore_index=True)

# %%
import pandas as pd
import matplotlib.pyplot as plt

radiation.index = pd.to_datetime(
    radiation.index, format="%d.%m.%Y %H:%M", utc=True
)

radiation.index = pd.to_datetime(radiation.index, utc=True)
radiation = radiation.sort_index()

daily = radiation.resample("D").mean()
monthly = daily.resample("MS").mean()

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(daily, linewidth=0.6, alpha=0.5, label="Moyenne journalière")
ax.plot(monthly, linewidth=2, color="darkorange", label="Moyenne mensuelle")
ax.set(
    title=f"{solar_station} — rayonnement global",
    xlabel="Date (UTC)",
    ylabel=solar_variable,
)
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()
plt.show(block=False)
# %%

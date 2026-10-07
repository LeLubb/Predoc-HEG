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
# # Seasonality -- Wind turbine
# #### Lubin Bénéteau
# ##### Date: 07.10.2026

# %% [markdown]
# # Graphs 
#
# Here I gather all the regions ('canton'), equal weight to produce a mean wind speed, at the month and week levels. I also enlighten the months above the annual mean to get a better idea of seasonality. 

# %%
import pandas as pd
import matplotlib.pyplot as plt

base_url = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn"

inventory = pd.read_csv(base_url + "/ogd-smn_meta_datainventory.csv", sep=";", encoding="cp1252")
stations = pd.read_csv(base_url + "/ogd-smn_meta_stations.csv", sep=";", encoding="cp1252")

swiss_stations = stations.loc[stations["station_canton"] != "FL", "station_abbr"]
station_codes = inventory.loc[
    (inventory["parameter_shortname"] == "fkl010d0")
    & inventory["station_abbr"].isin(swiss_stations),
    "station_abbr"
].unique()

frames = []

for station in station_codes:
    print("Downloading:", station)
    code = station.lower()
    url = f"{base_url}/{code}/ogd-smn_{code}_d_historical.csv"

    data = pd.read_csv(
        url, sep=";", encoding="cp1252",
        usecols=["station_abbr", "reference_timestamp", "fkl010d0"]
    )
    data["reference_timestamp"] = pd.to_datetime(
        data["reference_timestamp"], format="%d.%m.%Y %H:%M", utc=True
    )
    data["fkl010d0"] = pd.to_numeric(data["fkl010d0"], errors="coerce")
    data = data[data["reference_timestamp"].dt.year.between(2015, 2025)]
    frames.append(data)

df = pd.concat(frames, ignore_index=True).dropna(subset=["fkl010d0"])

# Coputing here the means for weekd, months and years. 
monthly = (df.groupby(["station_abbr", df["reference_timestamp"].dt.month])["fkl010d0"].mean().groupby(level=1).mean())
weekly = (df.groupby(["station_abbr", df["reference_timestamp"].dt.isocalendar().week])["fkl010d0"].mean().groupby(level=1).mean())
annual_mean = df.groupby("station_abbr")["fkl010d0"].mean().mean()



# %%
# ================================================================================================
# ================================== Switzerland - whole country =================================
# ================================================================================================

dark_green = "#1B5E20"
light_green = "#A5D6A7"
colors = [dark_green if v > annual_mean else light_green for v in monthly]

months = ["Jan", "Fev", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True, facecolor="white")

# Monthly mean wind speed
monthly.plot(ax=axes[0], marker="o", color=dark_green)
axes[0].set_title("Monthly mean wind speed")
axes[0].set_xticks(range(1, 13), labels=months)

# Months above the annual mean
monthly.plot(ax=axes[1], kind="bar", color=colors, rot=0, label="mean wind speed")
axes[1].set_xticks(range(12), labels=months)
axes[1].axhline(annual_mean, color=dark_green, linestyle="--", label=f"Annual mean: {annual_mean:.2f} m/s")
axes[1].set_title("Months above the annual mean shown in dark green")
axes[1].legend()

# fancy part. 
for ax in axes:
    ax.set_facecolor("white")
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean wind speed (m/s)")
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.3)

fig.suptitle("Switzerland — Wind seasonality, 2015–2025", fontsize=16)
plt.tight_layout()
fig.savefig(output_dir / "Switzerland_wind_seasonality.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.show()

# %%
# Add to the df the name of cantons, I forgot to do it earlier.
data = df.merge(
    stations[["station_abbr", "station_canton"]],
    on="station_abbr",
    how="left"
)
data = data[data["station_canton"] != "FL"]

dark_green = "#1B5E20"
light_green = "#A5D6A7"
months = ["Jan", "Fev", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# I keep only two graphs, still enough talkative (otherwise the output would be too long)
for canton, canton_data in data.groupby("station_canton"):

    monthly = (
        canton_data.groupby([
            "station_abbr",
            canton_data["reference_timestamp"].dt.month
        ])["fkl010d0"]
        .mean().groupby(level=1).mean()
        .reindex(range(1, 13))
    )
    annual_mean = canton_data.groupby("station_abbr")["fkl010d0"].mean().mean()
    colors = [dark_green if v > annual_mean else light_green for v in monthly]

    fig, axes = plt.subplots(
        1, 2, figsize=(14, 5), sharey=True, facecolor="white"
    )

    # Monthly mean wind speed
    monthly.plot(ax=axes[0], marker="o", color=dark_green)
    axes[0].set_title("Monthly mean wind speed")
    axes[0].set_xticks(range(1, 13), labels=months)

    # Months above the annual mean
    monthly.plot(
        ax=axes[1], kind="bar", color=colors, rot=0,
        label="mean wind speed"
    )
    axes[1].set_xticks(range(12), labels=months)
    axes[1].axhline(
        annual_mean, color=dark_green, linestyle="--",
        label=f"Annual mean: {annual_mean:.2f} m/s"
    )
    axes[1].set_title("Months above the annual mean shown in dark green")
    axes[1].legend()

    # fancy part (same as before)
    for ax in axes:
        ax.set_facecolor("white")
        ax.set_xlabel("Month")
        ax.set_ylabel("Mean wind speed (m/s)")
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle(
        f"Canton {canton} — Wind seasonality, 2015–2025",
        fontsize=16
    )
    plt.tight_layout()
    fig.savefig(output_dir / f"Canton_{canton}_wind_seasonality.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.show()
    plt.close(fig)

# %%
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

months = ["Jan", "Fev", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
dark_green = "#1B5E20"
light_green = "#A5D6A7"

# Monthly means: first by station, then by canton
station_monthly = data.groupby([
    "station_canton", "station_abbr",
    data["reference_timestamp"].dt.month
])["fkl010d0"].mean()

canton_monthly = (
    station_monthly.groupby(level=[0, 2]).mean()
    .unstack().reindex(columns=range(1, 13))
)

# Annual reference: equal weight for each station
canton_annual = (
    data.groupby(["station_canton", "station_abbr"])["fkl010d0"]
    .mean().groupby(level=0).mean()
)

# 1 = above annual mean; 0 = at or below annual mean
above_mean = canton_monthly.gt(canton_annual, axis=0).astype(float)
above_mean = above_mean.where(canton_monthly.notna())

fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")
ax.set_facecolor("white")
ax.imshow(
    above_mean, aspect="auto",
    cmap=ListedColormap([light_green, dark_green]), vmin=0, vmax=1
)

ax.set_xticks(range(12), labels=months)
ax.set_yticks(range(len(canton_monthly)), labels=canton_monthly.index)
ax.set_xlabel("Month")
ax.set_ylabel("Canton")
ax.set_title("Months above each canton's annual mean — 2015–2025")

ax.legend(handles=[
    Patch(color=dark_green, label="Above annual mean"),
    Patch(color=light_green, label="At or below annual mean")
], loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2)

plt.tight_layout()
fig.savefig(output_dir / "Cantons_monthly_heatmap.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.show()

# %%

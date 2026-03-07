import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

# =========================
# Read data (known schema)
# =========================
df = pd.read_csv("/Users/diwakarsandhu/Documents/GitHub/final/data/clean_data.csv")

df["respondent_id"] = np.arange(1, len(df) + 1)
ID_COL = "respondent_id"
YEAR_COL = "Year"
MAJOR_COL = "Major(s)"
LIVING_COL = "Living Situation"
INV_COL = "Involvements"

HOUR_COLS = [
    "12am-1am","1am-2am","2am-3am","3am-4am","4am-5am","5am-6am",
    "6am-7am","7am-8am","8am-9am","9am-10am","10am-11am","11am-12pm",
    "12pm-1pm","1pm-2pm","2pm-3pm","3pm-4pm","4pm-5pm","5pm-6pm",
    "6pm-7pm","7pm-8pm","8pm-9pm","9pm-10pm","10pm-11pm","11pm-12am"
]

# Long format: one row per respondent-hour
long = df.melt(
    id_vars=[ID_COL, YEAR_COL, MAJOR_COL, LIVING_COL, INV_COL],
    value_vars=HOUR_COLS,
    var_name="hour_col",
    value_name="activity"
)
long["hour"] = long["hour_col"].apply(lambda s: HOUR_COLS.index(s))
long["activity"] = long["activity"].astype(str).str.strip()
long.loc[long["activity"].isin(["", "nan", "None", "NaN"]), "activity"] = np.nan

# =========================
# 1) Demographics distributions
# =========================
def bar_counts(series, title, rotate=0):
    s = df[series].astype(str).str.strip().replace({"nan": np.nan, "None": np.nan, "": np.nan})
    counts = s.value_counts(dropna=True)
    plt.figure(figsize=(8, 4))
    plt.bar(counts.index.astype(str), counts.values)
    plt.ylabel("Respondents")
    plt.title(title)
    if rotate:
        plt.xticks(rotation=rotate, ha="right")
    plt.tight_layout()
    plt.savefig(f"/Users/diwakarsandhu/Documents/GitHub/final/output/{series}_bar.png", dpi=300)
    plt.show()

bar_counts(YEAR_COL, "Respondents by year")
bar_counts(LIVING_COL, "Respondents by living situation", rotate=30)

# Involvements: split multi-select strings
inv = df[INV_COL].fillna("").astype(str)
parts = inv.apply(lambda x: [p.strip() for p in re.split(r"[;,/|]+", x) if p.strip()])
inv_counts = pd.Series([p for sub in parts for p in sub]).value_counts()

plt.figure(figsize=(9, 4))
plt.bar(inv_counts.index.astype(str), inv_counts.values)
plt.ylabel("Respondents selecting involvement")
plt.title("Involvements (multi-select counts)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("/Users/diwakarsandhu/Documents/GitHub/final/output/involvements_bar.png", dpi=300)
plt.show()

# Majors: top raw strings (free-text)
maj = df[MAJOR_COL].astype(str).str.strip().replace({"nan": np.nan, "None": np.nan, "": np.nan})
top_maj = maj.value_counts(dropna=True).head(12)

plt.figure(figsize=(9, 4))
plt.bar(top_maj.index.astype(str), top_maj.values)
plt.ylabel("Respondents")
plt.title("Top reported major strings (raw)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("/Users/diwakarsandhu/Documents/GitHub/final/output/majors_bar.png", dpi=300)
plt.show()

# =========================
# 2) Big picture: % by hour (heatmap + stacked area)
# =========================
counts_hour_activity = (
    long.dropna(subset=["activity"])
        .groupby(["hour", "activity"])[ID_COL].count()
        .unstack(fill_value=0)
        .reindex(range(24), fill_value=0)
)

denom = counts_hour_activity.sum(axis=1).replace(0, np.nan)
pct_hour_activity = counts_hour_activity.div(denom, axis=0) * 100

# Heatmap
plt.figure(figsize=(12, 6))
plt.imshow(pct_hour_activity.T.values, aspect="auto", interpolation="nearest")
plt.colorbar(label="% of respondents")
plt.yticks(range(len(pct_hour_activity.columns)), pct_hour_activity.columns.astype(str))
plt.xticks(range(0, 24, 2), [str(h) for h in range(0, 24, 2)])
plt.xlabel("Hour of day (0=12am)")
plt.title("Activity distribution by hour (heatmap)")
plt.tight_layout()
plt.savefig("/Users/diwakarsandhu/Documents/GitHub/final/output/activity_heatmap.png", dpi=300)
plt.show()

# Stacked area
plt.figure(figsize=(12, 5))
x = pct_hour_activity.index.values
ys = [pct_hour_activity[c].fillna(0).values for c in pct_hour_activity.columns]
plt.stackplot(x, ys, labels=[str(c) for c in pct_hour_activity.columns])
plt.xlabel("Hour of day (0=12am)")
plt.ylabel("% of respondents")
plt.title("Activity distribution by hour (stacked area)")
plt.xticks(range(0, 24, 2))
plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.0)
plt.tight_layout()
plt.savefig("/Users/diwakarsandhu/Documents/GitHub/final/output/activity_stacked_area.png", dpi=300)
plt.show()

# =========================
# 3) Per-person totals (histograms + boxplot + stacked bars)
# =========================
person_activity_hours = (
    long.dropna(subset=["activity"])
        .groupby([ID_COL, "activity"])["hour"].count()
        .unstack(fill_value=0)
)

# Choose a few common activities (edit these if your labels differ)
focus_cols = [c for c in ["Sleeping", "Studying/Homework", "Class", "Meals", "Leisure/Entertainment", "Work"]
              if c in person_activity_hours.columns]
if not focus_cols:
    focus_cols = person_activity_hours.columns[:6].tolist()

for c in focus_cols:
    plt.figure()
    plt.hist(person_activity_hours[c].values, bins=range(0, 25))
    plt.xlabel("Hours in a day")
    plt.ylabel("Respondents")
    plt.title(f"Distribution of total hours: {c}")
    plt.savefig(f"/Users/diwakarsandhu/Documents/GitHub/final/output/person_activity_{c.replace('/', '_')}.png", dpi=300)
    plt.show()

plt.figure(figsize=(10, 4))
plt.boxplot([person_activity_hours[c].values for c in focus_cols], tick_labels=[str(c) for c in focus_cols])
plt.xticks(rotation=30, ha="right")
plt.ylabel("Hours in a day")
plt.title("Total hours per activity (boxplots)")
plt.tight_layout()
plt.savefig("/Users/diwakarsandhu/Documents/GitHub/final/output/person_activity_boxplot.png", dpi=300)
plt.show()

# =========================
# 5) Sleep onset / wake proxy
# =========================
# Treat any activity containing "sleep" as sleeping
sleep_long = long.copy()
sleep_long["is_sleep"] = sleep_long["activity"].astype(str).str.lower().str.contains("sleep", na=False)

sleep_matrix = (
    sleep_long.pivot_table(index=ID_COL, columns="hour", values="is_sleep", aggfunc="max")
              .reindex(columns=range(24), fill_value=False)
)

def onset_wake(row):
    sleep_hours = np.where(row.values)[0]
    if len(sleep_hours) == 0:
        return np.nan, np.nan
    onset = sleep_hours.min()
    wake = min(sleep_hours.max() + 1, 24)
    return onset, wake

ow = sleep_matrix.apply(lambda r: pd.Series(onset_wake(r), index=["sleep_onset", "wake_hour"]), axis=1)

plt.figure()
plt.hist(ow["sleep_onset"].dropna().values, bins=range(0, 25))
plt.xlabel("Sleep onset hour (0=12am)")
plt.ylabel("Respondents")
plt.title("Estimated sleep onset distribution")
plt.savefig("/Users/diwakarsandhu/Documents/GitHub/final/output/sleep_onset_histogram.png", dpi=300)
plt.show()

plt.figure()
plt.hist(ow["wake_hour"].dropna().values, bins=range(0, 26))
plt.xlabel("Wake hour (0=12am)")
plt.ylabel("Respondents")
plt.title("Estimated wake time distribution")
plt.savefig("/Users/diwakarsandhu/Documents/GitHub/final/output/wake_hour_histogram.png", dpi=300)
plt.show()

plt.figure()
plt.scatter(ow["sleep_onset"], ow["wake_hour"])
plt.xlabel("Sleep onset hour")
plt.ylabel("Wake hour")
plt.title("Sleep onset vs wake time (proxy)")
plt.xticks(range(0, 25, 2))
plt.yticks(range(0, 26, 2))
plt.savefig("/Users/diwakarsandhu/Documents/GitHub/final/output/sleep_onset_vs_wake_scatter.png", dpi=300)
plt.show()
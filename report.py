import os
import sys

from datetime import datetime, timedelta
from typing import Tuple

import pandas
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scipy.signal as sp


from ibmetrics import reader


def filter_users(builds: pandas.DataFrame, customers: pandas.DataFrame) -> pandas.DataFrame:

    def get_ids(value: str) -> pandas.Series:
        matching_idxs = customers["org_name"].str.match(value, case=False)
        return customers["org_id"].loc[matching_idxs]

    with open("./userfilter.txt", encoding="utf-8") as filterfile:
        patterns = filterfile.read().split("\n")

    for pattern in patterns:
        if not pattern:
            # don't filter empty patterns
            continue
        # rm_ids = pandas.concat([rm_ids, get_ids(pattern)], ignore_index=True)
        for rm_id in get_ids(pattern):
            builds = builds.loc[builds["org_id"] != rm_id]

    return builds


def print_summary(builds):
    print("Summary")
    print("=======\n")
    start = builds["created_at"].min()
    end = builds["created_at"].max()
    print(f"Period: {start} - {end}\n")

    print(f"- Total builds: {len(builds)}")
    print(f"- Number of users: {len(builds['org_id'].unique())}")

    n_with_packages = sum(1 if len(pkg) else 0 for pkg in builds["packages"])
    print(f"- Builds with packages: {n_with_packages}")

    avg_packages = np.mean([len(pkg) for pkg in builds["packages"]])
    print(f"- Average number of packages per build: {avg_packages:.2f}")
    avg_packages_nonempty = np.mean([len(pkg) for pkg in builds["packages"] if len(pkg)])
    print(f"- Average number of packages per build (excluding empty): {avg_packages_nonempty:.2f}")

    n_with_fs = sum(1 if len(fs) else 0 for fs in builds["filesystem"])
    print(f"- Builds with filesystem customizations: {n_with_fs}")

    n_with_repos = sum(1 if len(repos) else 0 for repos in builds["payload_repositories"])
    print(f"- Builds with custom repos: {n_with_repos}")


def print_weekly_users(builds: pandas.DataFrame, customers: pandas.DataFrame, start: datetime):
    end = start + timedelta(days=7)  # one week
    week_idxs = (builds["created_at"] >= start) & (builds["created_at"] < end)
    week_users = set(builds["org_id"].loc[week_idxs])

    pre_week_idxs = (builds["created_at"] < start)
    pre_users = set(builds["org_id"].loc[pre_week_idxs])  # users seen before start day

    start_str = start.strftime("%A, %d %B %Y")
    print(f"Number of unique users for week of {start_str}: {len(week_users)}")

    new_users = week_users - pre_users
    print(f"Number of new users for week of {start_str}: {len(new_users)}")


def builds_over_time(builds: pandas.DataFrame,
                     start: datetime, end: datetime, period: timedelta) -> Tuple[np.ndarray, np.ndarray]:
    t_start = start
    bin_starts = []
    n_builds = []
    while t_start+period < end:
        idxs = (builds["created_at"] >= t_start) & (builds["created_at"] < t_start+period)
        n_builds.append(sum(idxs))
        bin_starts.append(t_start)
        t_start += period

    return np.array(bin_starts), np.array(n_builds)


def users_over_time(builds: pandas.DataFrame,
                    start: datetime, end: datetime, period: timedelta) -> Tuple[np.ndarray, np.ndarray]:
    t_start = start
    bin_starts = []
    n_users = []
    while t_start+period < end:
        idxs = (builds["created_at"] >= t_start) & (builds["created_at"] < t_start+period)
        n_users.append(len(set(builds["org_id"].loc[idxs])))
        bin_starts.append(t_start)
        t_start += period

    return np.array(bin_starts), np.array(n_users)


def read_file(fname: os.PathLike) -> pandas.DataFrame:
    cache_home = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    cache_dir = os.path.join(cache_home, "osbuild-metrics")
    os.makedirs(cache_dir, exist_ok=True)
    cache_fname = os.path.join(cache_dir, os.path.basename(os.path.splitext(fname)[0]) + ".pkl")
    if os.path.exists(cache_fname):
        print(f"Using cached pickle file at {cache_fname}")
        # TODO: handle exceptions
        return pandas.read_pickle(cache_fname)

    builds = reader.read_dump(fname)
    print(f"Saving cached pickle file at {cache_fname}")
    builds.to_pickle(cache_fname)
    return builds


def trendline(values):
    values = list(values)
    n_points = len(values)
    half = n_points//2
    kernel = sp.gaussian(n_points, std=7)
    kernel /= sum(kernel)
    # pad the original values with the last value for half the kernel size
    values = values + ([values[-1]] * half)
    tline = sp.convolve(values, kernel, mode="same")
    tline = tline[:-half]
    return tline.tolist()


def moving_average(values):
    sums = np.cumsum(values)
    weights = np.arange(1, len(sums)+1, 1)
    return sums / weights


def slice_time(builds: pandas.DataFrame, start: datetime, end: datetime):
    idxs = (builds["created_at"] >= start) & (builds["created_at"] <= end)
    return builds.loc[idxs]


def plot_build_counts(builds: pandas.DataFrame, start: datetime, end: datetime, p_days: int):
    t_starts, build_counts = builds_over_time(builds, start=start, end=end, period=timedelta(days=p_days))
    ax = plt.axes()
    ax.plot(t_starts, build_counts, ".b", markersize=12, label="n builds")

    builds_trend = moving_average(build_counts)
    ax.plot(t_starts, builds_trend, "-b", label="builds mov. avg.")

    ax.set_xticks(t_starts)
    # rotate xtick labels 45 degrees cw for readability
    for label in ax.get_xticklabels():
        label.set_rotation(45)

    ax.axis(ymin=0, xmin=start)
    ax.set_xlabel("dates")
    ax.legend(loc="best")
    ax.grid(True)


def plot_user_counts(builds: pandas.DataFrame, start: datetime, end: datetime, p_days: int):
    t_starts, user_counts = users_over_time(builds, start=start, end=end, period=timedelta(days=p_days))
    ax = plt.axes()
    ax.plot(t_starts, user_counts, ".g", markersize=12, label="n users")

    user_trend = moving_average(user_counts)
    ax.plot(t_starts, user_trend, "-g", label="users mov. avg.")

    ax.set_xticks(t_starts)
    # rotate xtick labels 45 degrees cw for readability
    for label in ax.get_xticklabels():
        label.set_rotation(45)

    ax.axis(ymin=0, xmin=start)
    ax.set_xlabel(f"beginning of {p_days} day period")
    ax.set_ylabel("")
    ax.legend(loc="best")
    ax.grid(True)


def plot_image_types(builds: pandas.DataFrame):
    image_types = builds["image_type"].value_counts()
    plt.pie(image_types.values, labels=image_types.index)


def plot_weekly_users(builds: pandas.DataFrame, start: datetime, end: datetime):
    last_date = builds["created_at"].max()

    users_so_far = set()
    n_week_users = []
    n_new_users = []

    start_dates = []

    p_start = start
    while p_start < last_date:
        end = p_start + timedelta(days=7)  # one week
        week_idxs = (builds["created_at"] >= p_start) & (builds["created_at"] < end)
        week_users = set(builds["org_id"].loc[week_idxs])

        new_users = week_users - users_so_far

        n_week_users.append(len(week_users))
        n_new_users.append(len(new_users))
        start_dates.append(p_start)

        users_so_far.update(week_users)
        p_start = end

    ax = plt.axes()
    ax.bar(start_dates, n_week_users, width=2, color="blue", label="n users")
    ax.bar(start_dates, n_new_users, width=2, color="red", label="n new users")
    ax.legend(loc="best")
    start_month = start.replace(day=1)
    end_month = last_date.replace(month=last_date.month+1, day=1)
    xticks = []
    tick = start_month
    while tick <= end_month:
        xticks.append(tick)
        month = tick.month
        year = tick.year
        if month + 1 > 12:
            tick = tick.replace(year=year+1, month=1)
        else:
            tick = tick.replace(month=month+1)

    ax.set_xticks(xticks)
    ax.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    # rotate xtick labels 45 degrees cw for readability
    for label in ax.get_xticklabels():
        label.set_rotation(45)


def print_frequent_packages(builds: pandas.DataFrame, limit=20):
    all_packages = []
    for pkg_list in builds["packages"]:
        all_packages.extend(set(pkg_list))

    print("## Most frequently selected packages")
    pkg_counts = pandas.value_counts(all_packages)
    for idx, (name, count) in enumerate(pkg_counts.iloc[:limit].items()):
        print(f"{idx+1:3d}. {name:40s} {count:5d}")
    print("---------------------------------")


def print_image_type_counts(builds):
    print("## Image types")
    type_counts = builds["image_type"].value_counts()
    for idx, (name, count) in enumerate(type_counts.items()):
        print(f"{idx+1:3d}. {name:40s} {count:5d}")
    print("---------------------------------")


def print_frequent_orgs(builds: pandas.DataFrame, customers: pandas.DataFrame, limit=20):
    print("## Biggest orgs")
    org_counts = builds["org_id"].value_counts()
    for idx, (org_id, count) in enumerate(org_counts.iloc[:limit].items()):
        name = org_id
        user_idx = customers["org_id"] == org_id
        if sum(user_idx) == 1:
            name = customers["org_name"][user_idx].values.item()
        elif sum(user_idx) > 1:
            raise ValueError(f"Multiple ({sum(user_idx)}) entries with same org_id ({org_id}) in customer data")
        print(f"{idx+1:3d}. {name:40s} {count:5d}")
    print("------------")


# pylint: disable=too-many-statements,too-many-locals
def main():
    cust_dtypes = {
        "org_id": str,
        "org_name": str,
        "strategic": str,
    }
    customers = pandas.read_csv("Customers.csv", delimiter=",",
                                header=0, names=["org_id", "org_name", "strategic"], dtype=cust_dtypes)

    # TODO: proper argument handling
    fname = sys.argv[1]

    builds = read_file(fname)
    print(f"Imported {len(builds)} records")

    builds = filter_users(builds, customers)
    print(f"{len(builds)} records after user filtering")

    if len(sys.argv) > 2:
        start_str = sys.argv[2]
        start = datetime.fromisoformat(start_str)
    else:
        start = builds["created_at"].min()

    if len(sys.argv) > 3:
        end_str = sys.argv[3]
        end = datetime.fromisoformat(end_str)
    else:
        end = builds["created_at"].max()

    builds = slice_time(builds, start, end)
    print(f"{len(builds)} between {start} and {end}")

    print_summary(builds)

    print_frequent_packages(builds)
    print_image_type_counts(builds)
    print_frequent_orgs(builds, customers)

    # find the last Monday before the start of the data
    first_mon = start
    while first_mon.isoweekday() != 1:
        first_mon = first_mon - timedelta(days=1)

    # plot weekly counts
    p_days = 7  # 7 day period

    img_basename = os.path.splitext(os.path.basename(fname))[0]

    # builds counts
    plt.figure(figsize=(16, 9), dpi=100)
    plot_build_counts(builds, first_mon, end, p_days)
    imgname = img_basename + "-builds.png"
    plt.savefig(imgname)
    print(f"Saved figure {imgname}")

    # user counts
    plt.figure(figsize=(16, 9), dpi=100)
    plot_user_counts(builds, first_mon, end, p_days)
    imgname = img_basename + "-users.png"
    plt.savefig(imgname)
    print(f"Saved figure {imgname}")

    # image type breakdown
    plt.figure(figsize=(16, 9), dpi=100)
    plot_image_types(builds)
    imgname = img_basename + "-image_types.png"
    plt.savefig(imgname)
    print(f"Saved figure {imgname}")

    plt.figure(figsize=(16, 9), dpi=100)
    plot_weekly_users(builds, first_mon, end)
    imgname = img_basename + "-weekly_users.png"
    plt.savefig(imgname)
    print(f"Saved figure {imgname}")


if __name__ == "__main__":
    main()

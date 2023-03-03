"""
Plotting functions
"""
from datetime import datetime, timedelta
from typing import Optional, Set

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas

from . import metrics


def build_counts(builds: pandas.DataFrame, p_days: int, ax: Optional[plt.Axes] = None):
    """
    Bar graph of the number of builds in a given period specified by p_days.
    """
    if not ax:
        ax = plt.axes()

    t_starts, counts = metrics.builds_over_time(builds, period=timedelta(days=p_days))
    counts_plot = ax.plot(t_starts, counts, ".", markersize=12, label="n builds")

    dot_color = counts_plot[0].get_color()
    builds_trend = _moving_average(counts)  # reuse dot colour for trendline
    ax.plot(t_starts, builds_trend, "-", color=dot_color, label="builds mov. avg.")

    ax.set_xticks(t_starts)
    ax.set_xlabel("dates")
    ax.legend(loc="best")


def _moving_average(values):
    """
    Calculate the moving average for a series of values.
    """
    sums = np.cumsum(values)
    weights = np.arange(1, len(sums)+1, 1)
    return sums / weights


def monthly_users(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    """
    Bar graph of the number of users that appear in each calendar month.
    """
    if not ax:
        ax = plt.axes()

    user_counts, months = metrics.monthly_users(builds)
    ax.bar(months, user_counts, width=20, zorder=2)
    for mo, nu in zip(months, user_counts):
        plt.text(mo, nu, str(nu), size=16, ha="center")

    xlabels = [f"{mo.month_name()} {mo.year}" for mo in months]
    ax.set_xticks(months, xlabels)
    ax.set_title("Monthly users")


def monthly_users_stacked(builds: pandas.DataFrame, fig: Optional[plt.Figure] = None):
    """
    Bar graph of the number of users that appear in each calendar month; new users stacked on old.
    """
    matplotlib.rcParams["figure.dpi"] = 300
    matplotlib.rcParams["font.size"] = 10
    plt.style.use("./notebooks/redhat.mplstyle")

    if not fig:
        fig = plt.figure()

    ax = fig.add_axes([0, 0, 1, 1])

    # fig.suptitle("Organizations building at least one image", x=0)

    ax.grid(axis="y", color="#dddddd")
    # ax.spines["bottom"].set(linewidth=1.1)
    ax.xaxis.set_tick_params(size=0, pad=6)
    ax.yaxis.set_tick_params(size=0)
    # ax.yaxis.tick_right()

    # ticks = ax.get_yticklabels()
    # for tick in ticks:
    #    tick.set_verticalalignment("bottom")
    #   tick.set_horizontalalignment("right")

    ax.set_axisbelow(True)
    ax.set_title("Organizations building at least one image", loc="left", fontweight="bold")

    user_counts, months = metrics.monthly_users(builds)
    new_user_counts, months = metrics.monthly_new_users(builds)
    old_user_counts = user_counts - new_user_counts

    bar_width = 0.66

    def format_label(n):
        return str(n) if n >= 10 else ''

    names = [m.month_name() for m in months]
# bar = ax.bar(names, counts, width=0.66)
    bar_new = ax.bar(names, new_user_counts, width=bar_width, bottom=old_user_counts)
    bar_old = ax.bar(names, old_user_counts, width=bar_width, label="Recurring")

# this won't work for bars that are too small. use annotate()
    ax.bar_label(bar_new, map(format_label, new_user_counts), label_type="center", color="#ffffff")
    ax.bar_label(bar_old, map(format_label, old_user_counts), label_type="center", color="#ffffff")
    ax.legend(loc="upper left")

    ax.set_xlim(-bar_width * 2/3, len(names) - 1 + bar_width * 2/3)

    caption = ("An organization is an account for a single customer, not an individual user.\n"
               "Organizations are counted as Recurring if they have built an image\n"
               "in any preceding month. Internal Red Hat organizations are excluded.\n\n"
               "Source: Image Builder Production Database")
    fig.text(0, -0.15, caption, color="#777777", wrap=True)


def monthly_builds(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    """
    Bar graph of the number of builds in each calendar month.
    """
    if not ax:
        ax = plt.axes()

    counts, months = metrics.monthly_builds(builds)
    ax.bar(months, counts, width=20, zorder=2)
    for mo, nu in zip(months, counts):
        plt.text(mo, nu, str(nu), size=16, ha="center")

    xlabels = [f"{mo.month_name()} {mo.year}" for mo in months]
    ax.set_xticks(months, xlabels)
    ax.set_title("Monthly builds")


def monthly_new_users(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    """
    Bar graph of the number of new users that appear in each calendar month.
    """
    if not ax:
        ax = plt.axes()

    user_counts, months = metrics.monthly_new_users(builds)
    ax.bar(months, user_counts, width=20, zorder=2)
    for mo, nu in zip(months, user_counts):
        plt.text(mo, nu, str(nu), size=16, ha="center")

    xlabels = [f"{mo.month_name()} {mo.year}" for mo in months]
    ax.set_xticks(months, xlabels)
    ax.set_title("Monthly new users")


def users_sliding_window(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    if not ax:
        ax = plt.axes()

    user_counts, dates = metrics.value_sliding_window(builds, "org_id", 30)
    ax.plot(dates, user_counts, zorder=2)
    ax.set_xlabel("Window end date")
    ax.set_title("Number of users in the previous 30 days")


def imagetype_builds(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    """
    Pie chart of the distribution of image types built.
    """
    if not ax:
        ax = plt.axes()

    types = builds["image_type"].value_counts()
    labels = [f"{idx} ({val})" for idx, val in types.items()]
    ax.pie(types.values, labels=labels)


def footprint_builds(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    """
    Pie chart of the distribution of footprints. See metrics.footprints() for details.
    """
    if not ax:
        ax = plt.axes()

    builds_footprints = metrics.footprints(builds)
    feet = builds_footprints["footprint"].value_counts()
    labels = [f"{idx} ({val})" for idx, val in feet.items()]
    ax.pie(feet.values, labels=labels)


def footprints_stacked(builds: pandas.DataFrame, fig: Optional[plt.Figure] = None, title: Optional[str] = None):
    matplotlib.rcParams["figure.dpi"] = 300
    matplotlib.rcParams["font.size"] = 8
    plt.style.use("./notebooks/redhat.mplstyle")

    if not fig:
        fig = plt.figure()

    ax = fig.add_axes([0, 0, 1, 1])

    ax.grid(axis="y", color="#dddddd")
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set(linewidth=1.1)
    ax.xaxis.set_tick_params(size=0, pad=6)
    ax.yaxis.set_tick_params(size=0)
    ax.set_axisbelow(True)
    if not title:
        title = "Number of images built for each footprint"
    ax.set_title(title, loc="left", fontweight="bold")

    bar_width = 0.66

    footprints = metrics.footprints(builds)
    fp_counts = footprints["footprint"].value_counts()

    bottom = 0
    priv_clouds = ["guest-image", "vsphere"]
    priv_sum = sum(v if k in priv_clouds else 0 for k, v in fp_counts.items())

    grouped = fp_counts.copy()
    grouped["private-cloud"] = priv_sum
    for priv in priv_clouds:
        del grouped[priv]

    bottom = 0
    clouds = ["gcp", "azure", "aws"]
    cloud_sum = sum(v if k in clouds else 0 for k, v in fp_counts.items())

    grouped["cloud"] = cloud_sum
    for cloud in clouds:
        del grouped[cloud]

    names = {
        "private-cloud": "Private Cloud",
        "cloud": "Public Cloud",
        "bare-metal": "Bare Metal",
        "edge": "Edge"
    }

    grouped.sort_values(ascending=False, inplace=True)
    # plot with grouped cloud to get them in order (sorted)
    ax.bar([names[i] for i in grouped.index], grouped.values, width=bar_width)
    # for ft in cloud_grouped_feet.items():
    #    if ft[0] == "cloud":
    #        continue

    labels = {
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "guest-image": "Guest Image",
        "vsphere": "vSphere",
    }

    colors = {
        "aws": "#E79824",
        "azure": "#345BDB",
        "gcp": "#599C5D",
        "guest-image": "#8f0000",
        "vsphere": "#7598bd",
    }

    # draw over cloud bars with breakdown values of individual image types
    # Note: the legend order is top-to-bottom in order of creation, so let's draw the clouds in the same order
    bottom = sum(fp_counts[p] for p in priv_clouds)  # top of the bar
    for priv in priv_clouds:
        bottom -= fp_counts[priv]
        ax.bar(names["private-cloud"], fp_counts[priv], bottom=bottom, label=labels.get(priv, priv),
               width=bar_width, color=colors[priv])
        # ax.bar_label(bar, fp_counts, label_type="center", color="#ffffff")

    bottom = sum(fp_counts[cld] for cld in clouds)  # top of the bar
    for cld in clouds:
        bottom -= fp_counts[cld]
        ax.bar(names["cloud"], fp_counts[cld], bottom=bottom, label=labels.get(cld, cld), width=bar_width,
               color=colors[cld])
        # ax.bar_label(bar, fp_counts, label_type="center", color="#ffffff")

    ax.set_xlim(-bar_width * 2/3, len(clouds) + bar_width * 2/3)

    ax.legend()
    caption = ("Bare metal refers to the installer (ISO).\n"
               "Edge refers to all edge image types: commit, container, installer (ISO).\n"
               "Builds from internal Red Hat organizations are excluded.\n\n"
               "Source: Image Builder Production Database")
    fig.text(0.03, -0.2, caption, fontsize="small", color="#777777")


def weekly_users(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    """
    Bar graph of users per seven day period. Shows new users alongside total users per period.
    This function does not align periods to calendar weeks.
    """
    first_date = builds["created_at"].min()
    last_date = builds["created_at"].max()

    users_so_far: Set[str] = set()
    n_week_users = []
    n_new_users = []

    start_dates = []

    p_start = first_date
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

    if not ax:
        ax = plt.axes()

    n_ret_users = np.subtract(n_week_users, n_new_users)
    ax.bar(start_dates, n_ret_users, width=2, label="returning users")
    ax.bar(start_dates, n_new_users, bottom=n_ret_users, width=2, label="new users")
    ax.legend(loc="best")
    month_offset = pandas.DateOffset(months=1)

    start_month = first_date.replace(day=1)
    end_month = last_date.replace(month=last_date.month+1, day=1)
    end_month = last_date.replace(day=1) + month_offset
    xticks = []
    tick = start_month
    while tick <= end_month:
        xticks.append(tick)
        tick += month_offset

    ax.set_xticks(xticks)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))


def dau_over_mau(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    if not ax:
        ax = plt.axes()

    mod, dates = metrics.dau_over_mau(builds)
    ax.plot(dates, mod)
    ax.set_xlabel("Window end date")
    ax.set_title("Daily users / Users in the previous 30 days")


def single_footprint_distribution(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    """
    Bar graph showing the number of users that only build images for a single footprint, separated by footprint.
    """
    if not ax:
        ax = plt.axes()

    sfp_users = metrics.single_footprint_users(builds)
    fp_counts = sfp_users["footprint"].value_counts()
    ax.bar(fp_counts.index, fp_counts.values)
    for idx, count in zip(fp_counts.index, fp_counts.values):
        ax.text(idx, count, str(count), size=16, ha="center")
    ax.set_xlabel("Footprints")
    ax.set_title("Single-footprint user counts")
    ax.set_ylim(ymax=max(fp_counts)+30)


def single_footprint_monthly_users(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    """
    Multi-bar graph of the number of single-footprint users that appear in each calendar month, separated by footprint.
    """

    if not ax:
        ax = plt.axes()

    # get org_ids of orgs that only build one footprint
    sfp_users = metrics.single_footprint_users(builds, split_cloud=False)

    # Add footprint column to each build
    builds_wfp = metrics.footprints(builds, split_cloud=False)

    # Filter out multi-footprint org_ids
    builds_wfp = builds_wfp.loc[builds_wfp["org_id"].isin(sfp_users["org_id"])]

    shift = 0
    for footprint in sorted(builds_wfp["footprint"].unique()):
        # filter builds for the given footprint
        fp_builds = builds_wfp.loc[builds_wfp["footprint"] == footprint]
        # plot monthly users for the filtered set
        user_counts, months = metrics.monthly_users(fp_builds)
        months += pandas.Timedelta(days=shift)
        # ax.plot(months, user_counts, linewidth=3, label=footprint)
        ax.bar(months, user_counts, width=3, zorder=2, label=footprint)
        shift += 3

        # add numbers to bars
        # for mo, nu in zip(months, user_counts):
        #     plt.text(mo, nu, str(nu), size=16, ha="center")

    xlabels = [f"{mo.month_name()} {mo.year}" for mo in months]
    ax.set_xticks(months, xlabels)
    ax.set_title("Monthly users")
    ax.legend()


def footprint_monthly_builds(builds: pandas.DataFrame, ax: Optional[plt.Axes] = None):
    if not ax:
        ax = plt.axes()

    # Add footprint column to each build
    builds_wfp = metrics.footprints(builds, split_cloud=False)

    shift = 0
    for footprint in sorted(builds_wfp["footprint"].unique()):
        # filter builds for the given footprint
        fp_builds = builds_wfp.loc[builds_wfp["footprint"] == footprint]
        # plot monthly builds for the filtered set
        counts, months = metrics.monthly_builds(fp_builds)
        months += pandas.Timedelta(days=shift)
        ax.bar(months, counts, width=3, zorder=2, label=footprint)
        shift += 3
        # for mo, nu in zip(months, counts):
        #     plt.text(mo, nu, str(nu), size=16, ha="center")

    xlabels = [f"{mo.month_name()} {mo.year}" for mo in months]
    ax.set_xticks(months, xlabels)
    ax.set_title("Monthly builds")
    ax.legend()


def monthly_active_time(subscriptions: pandas.DataFrame, fig: Optional[plt.Figure] = None):
    matplotlib.rcParams["figure.dpi"] = 300
    matplotlib.rcParams["font.size"] = 18
    plt.style.use("./notebooks/redhat.mplstyle")

    if not fig:
        fig = plt.figure()

    ax = fig.add_axes([0, 0, 1, 1])

    # filter out rows without checkins
    subscriptions = subscriptions.loc[subscriptions["lastcheckin"] != "None"]

    now = datetime.now()
    month_start = datetime(year=now.year, month=now.month, day=1)

    # start at the month-start of the first record
    start = subscriptions["created"].values.min().astype("datetime64[M]")  # truncate to month
    end = np.datetime64(str(month_start)).astype("datetime64[M]")  # convert and truncate

    months = []
    cloud_durations = []
    weldr_durations = []

    # separate values
    cloud_subs = subscriptions.loc[subscriptions["element"] == "cloudapi-v2"]
    weldr_subs = subscriptions.loc[subscriptions["element"] == "weldr"]
    for mstart in np.arange(start, end):
        mstop = mstart + 1

        # clip created to month
        cloud_created = cloud_subs["created"].astype("datetime64[s]")
        cloud_created = cloud_created.clip(mstart, mstop)
        weldr_created = weldr_subs["created"].astype("datetime64[s]")
        weldr_created = weldr_created.clip(mstart, mstop)

        # clip lastcheckin to month
        cloud_lastcheckin = cloud_subs["lastcheckin"].astype("datetime64[s]")
        cloud_lastcheckin = cloud_lastcheckin.clip(mstart, mstop)
        weldr_lastcheckin = weldr_subs["lastcheckin"].astype("datetime64[s]")
        weldr_lastcheckin = weldr_lastcheckin.clip(mstart, mstop)

        cloud_duration = (cloud_lastcheckin - cloud_created).sum()
        weldr_duration = (weldr_lastcheckin - weldr_created).sum()

        monthname = datetime.strptime(f"{mstart}", "%Y-%m").strftime("%B")
        months.append(monthname)

        cloud_durations.append(cloud_duration.total_seconds())
        weldr_durations.append(weldr_duration.total_seconds())

    ax.grid(axis="y", color="#dddddd")
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set(linewidth=1.1)
    ax.xaxis.set_tick_params(size=0, pad=6)
    ax.yaxis.set_tick_params(size=0)
    ax.set_axisbelow(True)
    ax.set_title("Total runtime of RHEL instances\ncreated from Image Builder, in days",
                 loc="left", fontweight="bold")

    bar_width = 0.66
    plt.bar(months, (np.array(weldr_durations) + np.array(cloud_durations))/3600/24, width=bar_width, label="Service")
    plt.bar(months, np.array(weldr_durations)/3600/24, width=bar_width, label="On-premises")
    ax.legend(loc="upper left")
    ax.set_xlim(-bar_width * 2/3, len(months) - 1 + bar_width * 2/3)
    caption = ("Runtime is calculated as the period between registration and last\n"
               "check-in. The data includes builds from customers through\n"
               "console.redhat.com (Service) and on-premises builds (On-premises).\n"
               "Internal usage is excluded.\n\n"
               "Source: Red Hat Subscription Manager data")
    fig.text(0, -0.30, caption, color="#777777", wrap=True)


def active_time_distribution(subscriptions: pandas.DataFrame):
    subscriptions = subscriptions.loc[subscriptions["lastcheckin"] != "None"]
    matplotlib.rcParams["figure.dpi"] = 300
    matplotlib.rcParams["font.size"] = 8

    created = subscriptions["created"].astype("datetime64[s]")
    lastcheckin = subscriptions["lastcheckin"].astype("datetime64[s]")
    durations = lastcheckin - created
    dseconds = durations.map(pandas.Timedelta.total_seconds)

    _, ax = plt.subplots(figsize=(4, 4))
    # bar_width = 0.66
    max_days = 90
    plt.hist(dseconds/3600/24, bins=range(max_days))

    ax.grid(axis="y", color="#dddddd")
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set(linewidth=1.1)
    ax.xaxis.set_tick_params(size=0, pad=6)
    ax.yaxis.set_tick_params(size=0)
    ax.set_axisbelow(True)
    ax.set_title("Distribution of runtime of RHEL instances\ncreated from Image Builder, in days",
                 loc="left", fontweight="bold")

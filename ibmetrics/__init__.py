from . import data, metrics, plot, reader

import pandas


def load(dump_file, subscriptions_file, user_info_file=None, user_filter_file=None, start_date=None, end_date=None):
    builds = reader.read_dump(dump_file)

    users = None
    if user_info_file:
        users = pandas.read_json(user_info_file, dtype=False)

    user_filter = []
    if user_filter_file:
        with open(user_filter_file, encoding="utf-8") as f:
            user_filter = f.read().split("\n")

    filter_ids = data.get_filter_ids(users, user_filter)

    builds = data.slice_time(builds, start_date, end_date)
    builds = data.filter_orgs(builds, filter_ids)

    subscriptions = pandas.read_csv(
        subscriptions_file,
        delimiter="\t",
        na_values=["None"],
        parse_dates=[2, 3],
        dtype={"org_id": str}
    )
    subscriptions = data.slice_time(subscriptions, start_date, end_date, field="created")
    subscriptions = data.filter_orgs(subscriptions, filter_ids)
    subscriptions = subscriptions.loc[subscriptions["element"] == "cloudapi-v2"]

    return builds, subscriptions

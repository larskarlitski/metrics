"""
Functions for cleaning or transforming the build data.
"""
import pandas

from datetime import datetime
from typing import List


def filter_users(builds: pandas.DataFrame, users: pandas.DataFrame, patterns: List[str]) -> pandas.DataFrame:
    """
    Filter users with name matching provided patterns from builds and return a filtered view of the data.
    """
    if users is None or not patterns:
        # no filtering possible
        return builds

    def get_ids(value: str) -> pandas.Series:
        matching_idxs = users["name"].str.match(value, case=False)
        return users["accountNumber"].loc[matching_idxs].astype(str)

    for pattern in patterns:
        if not pattern:
            continue

        for rm_id in get_ids(pattern):
            builds = builds.loc[builds["account_number"] != rm_id]

    return builds


def slice_time(builds: pandas.DataFrame, start: datetime, end: datetime) -> pandas.DataFrame:
    """
    Return a filtered view of the data that only includes builds made between the given start and end time.
    """
    idxs = (builds["created_at"] >= start) & (builds["created_at"] <= end)
    return builds.loc[idxs]

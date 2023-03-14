# osbuild-metrics

Scripts and utilities for exploring Image Builder usage data and creating reports.

## How to use

The `ibmetrics/reader` module can parse the output from an weekly SQL query against the image builder production database. The current weekly query can be found in the [internal app-interface repo](https://gitlab.cee.redhat.com/service/app-interface/-/tree/master/data/services/insights/image-builder/sql-queries) (note that old, inactive queries are marked with `delete: true` and generally only the most recent one is active at any given time).

You can load the data from a log into a [Pandas](https://pandas.pydata.org/) DataFrame with:
```python
import ibmetrics as ib

builds = ib.reader.read_dump(fname)
```

The `ib.report.read_file()` method adds caching on top of this for speed, since the log file parsing can take a few seconds. On first read of a data dump, it saves the data as a Python pickle in `${XDG_CACHE_HOME}/osbuild-metrics/` using the basename of the input file. Future loads of the same file load the pickle (no cache freshness checks are made; it is assumed that the log file from the data dump never changes).

Running `report.py` against a log file will produce some stats and figures. The `main()` function in this file can be used as a playground to explore the data.
Alternatively, you can load the data and the `report` module in an interactive environment and explore it there:
```python
import pandas

import report
import ibmetrics as ib

builds = report.read_file("./data/dump-2022-09-26.log")
users = pandas.read_json("./data/userinfo.json")  # maps account numbers to account names and other info

print(f"Read {len(builds)} records")

summary = ib.metrics.make_summary(builds)
ib.metrics.summarise(summary)
...
```

See also the [explore](./notebooks/explore.ipynb) notebook.

## Getting the data

1. Install the aws cli
2. Make sure you get the credentials from our [Bitwarden account](https://osbuild.pages.redhat.com/internal-guides/secrets-store.html)
3. Create a profile with the aws cli to avoid future conflicts: `aws configure --profile ib-metrics`
4. In the repository's root directory, pull the S3 bucket into the root directory of the metrics repo: `aws --profile ib-metrics s3 cp --recursive s3://rh-stage-ssa/hms_analytics/image-builder/prod ./data/parquet`
5. Get some more data from Google Drive
6. Install the dependencies: `pip install -r requirements.txt`

## Planned features

The plan is for the repo to contain libraries and functions for conveniently exploring the data. Currently, most useful code is in the `report.py` file, but this should be modularised. Scripts and Jupyter Notebooks will be added that produce sample stats and figures.

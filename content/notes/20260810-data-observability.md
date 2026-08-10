---
title: "A poor man's data observability stack: raw → stats → qc"
date: 2026-08-10
summary: "Every table we produce automatically gets a stats file; assertions on those stats decide whether the data passes to the next step. This post describes the homemade framework that gave us data observability."
math: true
plot: true
tags: ["data-engineering", "data-observability"]
audience: "Data Engineers, Software Engineers"
---

# Implementing a small data observability framework

Data observability can mean many different things depending on how you look at the problem. In general, it refers to the process of consistently monitoring the quality and reliability of a data product, but it can also mean looking at the performance of the pipeline that generates the data.

This post walks through a small, homemade framework my team built to do exactly that: every table we produce automatically gets a statistics file computed from it, and a set of assertions runs against those statistics before the data is allowed to move downstream. It's a simple pattern, but it gave us quality gates and free observability into our datasets.

## The three building blocks

The framework is built around three concepts, each defined as a templated Python class:

- **`raw`**: a raw dataset produced by a Spark job. Think of it as a snapshot of our current knowledge, extracted from a source like S3 files or a live database.
- **`stats`**: a small JSON file of aggregated metrics (row counts, unique keys, group-by counts, etc.) computed for each `raw` table on every run.
- **`qc`**: a list of assertions that run against the `stats` file. If the assertions pass, the table is promoted to the next step. In our case, a data catalog.

In terms of flow, a complete DAG would look like the following:

```mermaid
flowchart LR
db -->|raw v1| raw_table_1 -->|agg| stats_table_1 -->|qc| catalog
db -->|raw v2| raw_table_2 -->|agg| stats_table_2 -->|qc| catalog
db -->|raw v3| raw_table_3 -->|agg| stats_table_3 -->|qc| catalog
```

Put simply, we compute an `agg` file containing derived metrics for each table, then use those metrics to determine whether the data can move to the next step—in our case, a data catalog.

## Step 1: The raw framework

At one point in my career, one of my tasks was to build a platform that would enable our team to create Spark scripts using a templated Python framework. We would define output tables in Python, including their input and output tests, schema, and Spark processing logic, then connect them to a given data source (S3 files, a running database, etc.). The framework would automatically create tests for the Spark logic, generate documentation, and deploy the Spark script through CI/CD. In our architecture, this framework was used to create curated "raw" datasets, which were more or less snapshots of our current knowledge. Let's call this framework `raw`. The definition of a new table would look like this:

```python
class FoobarTable(BaseTable):

    @property
    def table_id(self) -> str:
        return "foobar"

    @property
    def primary_key(self) -> str:
        return "id"

    def input_columns(self) -> list[str]:
        return ["id", "name"]

    def input_example(self) -> list[dict]:
        return [{"id": "123123", "name": "John Doe"}]

    def output_example(self) -> list[list]:
        return [["123123", "John Doe"]]

    def schema(self) -> StructType:
        # Schema for {"id": str, "name": str}
        return FoobarSparkSchema

    def extract(self, sources: list[Source]) -> DataFrame:
        source = sources[0]
        df = source.get_df().select(self.input_columns())
        # Do some transformations
        return df
```

This Python framework had been deployed and working for some time. Our team then wanted to ensure that the data met our quality standards. That brought us to the next step.

## Step 2: The stats framework

To meet these requirements, we decided to create a second, centralized Python framework for defining templated aggregations and quality checks on top of each `raw` table we generated. The aggregation step (`stats`) would be defined using a templated class by specifying which aggregation to compute on which column, either through a set of predefined common operators or through ad hoc Spark aggregations.

```python
class FoobarStats(BaseStats):
    table = RawTable(
        table_id="foobar",
        primary_key="id",
    )
    # Compute a simple group-by on name
    group_by_count_fields = ["name"]
```

This would then output a JSON file like this:

```json
{
  "table_id": "foobar",
  "context": "prd",
  "date": "2020-01-01",
  "size_bytes": 1231908,
  "number_rows": 500,
  "unique_id": 2,
  "group_by_count": {
    "name": { "John Doe": 300, "Jane Smith": 200 }
  }
}
```

The `qc` step would also be defined using a templated class, this time by specifying a list of assertions to run against the previously computed `stats` object.

## Step 3: The QC framework

The final step is to define a simple quality check to run against that stats file:

```python
class FoobarQC(BaseQC):
    table_id = "foobar"
    assertions = [
        Assertion(
            source="unique_id",
            comparison="greater_than",
            target=2,
        ),
    ]
```

## Deployment considerations

Every table needs its own set of aggregations and quality checks. Without a solid template system, this becomes a lot of code and a pain to redeploy when all you want is to add one extra aggregation to one table.

We handled this with two different versioning strategies:

- The **`raw` framework is versioned and frozen**: every DAG pins a specific version, because the processing logic directly shapes the data our downstream processes consume.
- The **`stats` and `qc` frameworks follow a simpler `dev`/`main` branch model**: each DAG references one of the two branches directly. Since these metrics are only used for internal quality purposes, a floating version is an acceptable trade-off, and it makes redeployment much quicker and easier.

## Benefits of systematic aggregations

Beyond the quality gates themselves, consistently computing statistics for every table gives you instant visibility. Load the `stats` files for a table over a period of time, and you can immediately plot, for example, the number of rows per day. You can expose that information through a dashboard, a Databricks notebook, or an API.

It's also a powerful debugging tool. Database writes can fail silently over time or quietly insert malformed records or metadata. With the `stats` files, you can monitor how many new documents land in the database each day, watch how specific metrics evolve, and pinpoint when things started going wrong.

## Wrapping up

With three small templated classes—`raw` for the data, `stats` for the metrics, and `qc` for the assertions—we got systematic quality checks on every table, plus a free time series of metrics for monitoring.

The main limitation is that assertion-based checks only catch what you thought to measure: a failure involving a metric you never aggregated will go undetected. A natural next step would be to run anomaly-detection algorithms on the `stats` time series itself—or to compare this homemade approach with other tools, such as Great Expectations.

But as a starting point, this is a surprisingly effective way to observe your data.

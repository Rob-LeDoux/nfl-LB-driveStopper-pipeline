# nfl-LB-driveStopper-pipeline
A Python data pipeline that transforms raw nflverse play-by-play data, cleans it, and is stored as a defensive linebacker drive stopping impact dataset.

The goal is to identify linebackers who create drive-changing plays such as sacks, tackles for loss, forced fumbles, QB hits, and 3rd/4th down stops.

## Custom Metric

The project creates a custom exploratory metric called Drive Stopper Score:

Drive Stopper Score =
(3 × forced fumbles)
+ (2.5 × sacks)
+ (2 × tackles for loss)
+ (1.5 × QB hits)
+ (2 × third-down stops)
+ (2.5 × fourth-down stops)

## Why This Matters

Linebackers are often regarded as a lower-priotiy positiion, especially in the draft, but a Linebacker who can contribute to game changing drives stops cannot be ignored. 

## Tools

- Python
- pandas
- SQLite
- nflverse play-by-play data

## Pipeline

1. Extract raw play-by-play data
2. Transform defensive event columns into a normalized event table
3. Filter linebacker players using roster data
4. Aggregate player-level impact metrics
5. Export CSV and SQLite tables for analysis
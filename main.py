import pandas as pd
import nflreadpy as nfl
import sqlite3
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

SEASONS = [2025]

def load_data(seasons):
    print(f"Loading play-by-play data for {seasons}...")
    pbp = nfl.load_pbp(seasons).to_pandas()
    print(f"Loaded {len(pbp):,} plays.")
    return pbp

def create_event_rows(pbp):
    events = []

    #Sacks
    if "sack_player_name" in pbp.columns:
        sacks = pbp[pbp["sack_player_name"].notna()].copy()
        for _, row in sacks.iterrows():
            events.append({
                "season": row.get("season"),
                "week": row.get("week"),
                "game_id": row.get("game_id"),
                "play_id": row.get("play_id"),
                "defteam": row.get("defteam"),
                "player_name": row.get("sack_player_name"),
                "player_id": row.get("sack_player_id"),
                "event_type": "sack",
                "down": row.get("down"),
                "ydstogo": row.get("ydstogo"),
                "yds_gained": row.get("yds_gained"),
                "first_down": row.get("first_down"),
                "epa": row.get("epa"),
            })

    #TFLS
    if "tackle_for_loss_1_player_name" in pbp.columns:
        tfls = pbp[pbp["tackle_for_loss_1_player_name"].notna()].copy()
        for _, row in tfls.iterrows():
            events.append({
                "season": row.get("season"),
                "week": row.get("week"),
                "game_id": row.get("game_id"),
                "play_id": row.get("play_id"),
                "defteam": row.get("defteam"),
                "player_name": row.get("tackle_for_loss_1_player_name"),
                "player_id": row.get("tackle_for_loss_1_player_id"),
                "event_type": "tackle_for_loss",
                "down": row.get("down"),
                "ydstogo": row.get("ydstogo"),
                "yds_gained": row.get("yds_gained"),
                "first_down": row.get("first_down"),
                "epa": row.get("epa"),
            })

    #QB Hits
    if "qb_hit_1_player_name" in pbp.columns:
        qb_hits = pbp[pbp["qb_hit_1_player_name"].notna()].copy()
        for _, row in qb_hits.iterrows():
            events.append({
                "season": row.get("season"),
                "week": row.get("week"),
                "game_id": row.get("game_id"),
                "play_id": row.get("play_id"),
                "defteam": row.get("defteam"),
                "player_name": row.get("qb_hit_1_player_name"),
                "player_id": row.get("qb_hit_1_player_id"),
                "event_type": "qb_hit",
                "down": row.get("down"),
                "ydstogo": row.get("ydstogo"),
                "yds_gained": row.get("yds_gained"),
                "first_down": row.get("first_down"),
                "epa": row.get("epa"),
            })

    #Forced Fumbles
    if "forced_fumble_1_player_name" in pbp.columns:
        forced_fumbles = pbp[pbp["forced_fumble_1_player_name"].notna()].copy()
        for _, row in forced_fumbles.iterrows():
            events.append({
                "season": row.get("season"),
                "week": row.get("week"),
                "game_id": row.get("game_id"),
                "play_id": row.get("play_id"),
                "defteam": row.get("defteam"),
                "player_name": row.get("forced_fumble_1_player_name"),
                "player_id": row.get("forced_fumble_1_player_id"),
                "event_type": "forced_fumble",
                "down": row.get("down"),
                "ydstogo": row.get("ydstogo"),
                "yds_gained": row.get("yds_gained"),
                "first_down": row.get("first_down"),
                "epa": row.get("epa"),
            })

    events_df = pd.DataFrame(events)

    print(f"Created {len(events_df):,} defensive event rows.")
    return events_df

def add_3rd_and_4th_down_stops(pbp, events_df):
    stop_events =[]
    
    tackle_columns = [
        ("solo_tackle_1_player_name", "solo_tackle_1_player_id"),
        ("solo_tackle_2_player_name", "solo_tackle_2_player_id"),
        ("assist_tackle_1_player_name", "assist_tackle_1_player_id"),
        ("assist_tackle_2_player_name", "assist_tackle_2_player_id"),
    ]

    avail_tackle_cols = [(name_col, id_col)
                         for name_col, id_col in tackle_columns
                         if name_col in pbp.columns and id_col in pbp.columns
    ]

    avail_name_cols = [name_col for name_col, id_col in avail_tackle_cols]

    stop_plays = pbp[
        (pbp["down"].isin([3, 4])) &
        (pbp["play_type"].isin(["run", "pass"])) &
        (pbp["first_down"] == 0) &
        (pbp[avail_name_cols].notna().any(axis=1))
    ].copy()

    for _, row in stop_plays.iterrows():
        for name_col, id_col in avail_tackle_cols:

            player_name = row.get(name_col)
            player_id = row.get(id_col)

            if pd.notna(player_name):
                event_type = "3rd_down_stop" if row["down"] == 3 else "4th_down_stop"

                stop_events.append({
                    "season": row.get("season"),
                    "week": row.get("week"),
                    "game_id": row.get("game_id"),
                    "play_id": row.get("play_id"),
                    "defteam": row.get("defteam"),
                    "player_id": player_id,
                    "player_name": player_name,
                    "event_type": event_type,
                    "down": row.get("down"),
                    "ydstogo": row.get("ydstogo"),
                    "yds_gained": row.get("yds_gained"),
                    "first_down": row.get("first_down"),
                    "epa": row.get("epa"),
                })
    stops_df = pd.DataFrame(stop_events)

    print(f"Created {len(stops_df):,} 3rd/4th down stop event rows.")

    if len(events_df) == 0:
        return stops_df
    
    return pd.concat([events_df, stops_df], ignore_index=True)

def build_summary(events_df):
    if events_df.empty:
        print("No events to summarize.")
        return pd.DataFrame()
    
    summary = (
        events_df.pivot_table(
            index=["season", "player_name", "defteam"],
            columns="event_type",
            values="play_id",
            aggfunc="count",
            fill_value=0
        )
        .reset_index()
    )

    needed_cols = [
        "sack",
        "tackle_for_loss",
        "qb_hit",
        "forced_fumble",
        "3rd_down_stop",
        "4th_down_stop"
    ]

    for cols in needed_cols:
        if cols not in summary.columns:
            summary[cols] = 0

    summary["total_impact_plays"] = summary[needed_cols].sum(axis=1)

    summary["drive_stopper_score"] = (
        2.5 * summary["sack"] +
        2.0 * summary["tackle_for_loss"] +
        1.5 * summary["qb_hit"] +
        3.0 * summary["forced_fumble"] +
        2.0 * summary["3rd_down_stop"] +
        2.5 * summary["4th_down_stop"]
    )

    summary = summary.sort_values(by="drive_stopper_score", ascending=False)    

    return summary

def build_weekly_summary(events_df):
    if events_df.empty:
        print("No events to summarize.")
        return pd.DataFrame()
    
    weekly_summary = (
        events_df.pivot_table(
            index=["season", "week", "player_name", "defteam"],
            columns="event_type",
            values="play_id",
            aggfunc="count",
            fill_value=0
        )
        .reset_index()
    )

    needed_cols = [
        "sack",
        "tackle_for_loss",
        "qb_hit",
        "forced_fumble",
        "3rd_down_stop",
        "4th_down_stop"
    ]

    for cols in needed_cols:
        if cols not in weekly_summary.columns:
            weekly_summary[cols] = 0

    weekly_summary["drive_stopper_score"] = (
        2.5 * weekly_summary["sack"] +
        2.0 * weekly_summary["tackle_for_loss"] +
        1.5 * weekly_summary["qb_hit"] +
        3.0 * weekly_summary["forced_fumble"] +
        2.0 * weekly_summary["3rd_down_stop"] +
        2.5 * weekly_summary["4th_down_stop"]
    )

    weekly_summary["total_impact_plays"] = weekly_summary[needed_cols].sum(axis=1)

    weekly_summary = weekly_summary.sort_values(by="drive_stopper_score", ascending=False)    

    return weekly_summary

def save_outputs(events_df, summary_df, weekly_summary_df):
    events_df.to_csv(OUTPUT_DIR / "lb_play_events.csv", index=False)
    summary_df.to_csv(OUTPUT_DIR / "lb_drivestopper_summary.csv", index=False)
    weekly_summary_df.to_csv(OUTPUT_DIR / "lb_weekly_impact.csv", index=False)

    conn = sqlite3.connect(OUTPUT_DIR / "lb_drivestopper.db")

    events_df.to_sql("lb_play_events", conn, if_exists="replace", index=False)
    summary_df.to_sql("lb_drivestopper_summary", conn, if_exists="replace", index=False)
    weekly_summary_df.to_sql("lb_weekly_impact", conn, if_exists="replace", index=False)

    conn.close()

    print("Saved CSV and SQLite outputs.")

#filter out non-LB events
def filter_linebackers(events_df, seasons):
    rosters = nfl.load_rosters(seasons).to_pandas()

    lb_positions = ["LB", "ILB", "OLB", "MLB"]

    linebackers = rosters[rosters["position"].isin(lb_positions)]
                             
    lb_ids = set(linebackers["gsis_id"].dropna())

    events_df = events_df[events_df["player_id"].isin(lb_ids)].copy()

    return events_df


def main():
    pbp = load_data(SEASONS)
    
    events_df = create_event_rows(pbp)
    events_df = add_3rd_and_4th_down_stops(pbp, events_df)
    events_df = filter_linebackers(events_df, SEASONS)

    summary_df = build_summary(events_df)
    weekly_summary_df = build_weekly_summary(events_df)

    save_outputs(events_df, summary_df, weekly_summary_df)

    print("\n Top 10 Drive Stoppers:")
    print(summary_df.head(10)[["player_name", "defteam", "drive_stopper_score"]])

if __name__ == "__main__":
    main()
SELECT player_name,
       defteam,
       drive_killer_score,
       sack,
       tackle_for_loss,
       qb_hit,
       forced_fumble,
       third_down_stop,
       fourth_down_stop
FROM linebacker_drive_killer_summary
ORDER BY drive_killer_score DESC
LIMIT 20;


-- Best weekly performances
SELECT player_name,
       defteam,
       week,
       drive_killer_score,
       impact_plays
FROM linebacker_weekly_impact
ORDER BY drive_killer_score DESC
LIMIT 25;


-- Team defensive impact by linebackers/defensive players
SELECT defteam,
       SUM(drive_killer_score) AS team_drive_killer_score,
       SUM(total_impact_plays) AS total_impact_plays
FROM linebacker_drive_killer_summary
GROUP BY defteam
ORDER BY team_drive_killer_score DESC;
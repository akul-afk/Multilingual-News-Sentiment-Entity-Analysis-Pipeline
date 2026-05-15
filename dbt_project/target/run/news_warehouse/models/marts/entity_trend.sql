
  
    
    

    create  table
      "warehouse"."main"."entity_trend__dbt_tmp"
  
    as (
      

WITH entity_weekly AS (
    SELECT
        e.Entity_Name,
        e.Entity_Label,
        DATE_TRUNC('week', CAST(h.Date_Extracted AS DATE)) AS week_start,
        COUNT(*) as mention_count
    FROM "warehouse"."main"."stg_entities" e
    JOIN "warehouse"."main"."stg_headlines" h ON e.Headline_ID = h.Headline_ID
    GROUP BY e.Entity_Name, e.Entity_Label, DATE_TRUNC('week', CAST(h.Date_Extracted AS DATE))
)

SELECT
    curr.Entity_Name,
    curr.Entity_Label,
    curr.week_start,
    curr.mention_count as current_mentions,
    COALESCE(prev.mention_count, 0) as previous_mentions,
    (curr.mention_count - COALESCE(prev.mention_count, 0)) as mention_diff
FROM entity_weekly curr
LEFT JOIN entity_weekly prev 
    ON curr.Entity_Name = prev.Entity_Name
    AND curr.week_start = prev.week_start + INTERVAL 7 DAY
ORDER BY curr.week_start DESC, curr.mention_count DESC
    );
  
  
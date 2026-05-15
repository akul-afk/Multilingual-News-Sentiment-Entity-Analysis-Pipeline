
  
    
    

    create  table
      "warehouse"."main"."weekly_source_comparison__dbt_tmp"
  
    as (
      

WITH weekly_stats AS (
    SELECT
        Source_Name,
        DATE_TRUNC('week', CAST(Date_Extracted AS DATE)) AS week_start,
        COUNT(*) as headline_count,
        AVG(Polarity) as avg_sentiment
    FROM "warehouse"."main"."stg_headlines"
    GROUP BY Source_Name, DATE_TRUNC('week', CAST(Date_Extracted AS DATE))
)

SELECT
    curr.Source_Name,
    curr.week_start,
    curr.headline_count,
    curr.avg_sentiment as current_sentiment,
    prev.avg_sentiment as previous_sentiment,
    (curr.avg_sentiment - prev.avg_sentiment) as sentiment_shift
FROM weekly_stats curr
LEFT JOIN weekly_stats prev 
    ON curr.Source_Name = prev.Source_Name
    AND curr.week_start = prev.week_start + INTERVAL 7 DAY
ORDER BY curr.week_start DESC, curr.Source_Name
    );
  
  
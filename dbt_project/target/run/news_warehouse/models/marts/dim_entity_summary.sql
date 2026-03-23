
  
    
    

    create  table
      "warehouse"."main"."dim_entity_summary__dbt_tmp"
  
    as (
      -- dim_entity_summary.sql
-- Mart model: entity frequency analysis with sentiment correlation.
-- Shows which entities appear most and their average sentiment context.



WITH entity_articles AS (
    SELECT
        de.entity_key,
        de.entity_text,
        de.entity_label,
        fa.article_key,
        fa.polarity,
        fa.sentiment_label,
        ds.source_name,
        dd.full_date AS scrape_date
    FROM bridge_article_entity bae
    JOIN dim_entity de       ON bae.entity_key = de.entity_key
    JOIN fact_articles fa     ON bae.article_key = fa.article_key
    LEFT JOIN dim_source ds   ON fa.source_key = ds.source_key
    LEFT JOIN dim_date dd     ON fa.date_key = dd.date_key
)

SELECT
    entity_text,
    entity_label,

    -- Frequency
    COUNT(DISTINCT article_key)                  AS article_count,
    COUNT(DISTINCT source_name)                  AS source_count,
    COUNT(DISTINCT scrape_date)                  AS days_active,

    -- Sentiment correlation
    ROUND(AVG(polarity), 4)                      AS avg_polarity,
    ROUND(STDDEV(polarity), 4)                   AS stddev_polarity,

    -- Sentiment distribution
    COUNT(CASE WHEN polarity > 0.05  THEN 1 END) AS positive_mentions,
    COUNT(CASE WHEN polarity < -0.05 THEN 1 END) AS negative_mentions,
    COUNT(CASE WHEN polarity BETWEEN -0.05 AND 0.05 THEN 1 END) AS neutral_mentions,

    -- Source spread
    LISTAGG(DISTINCT source_name, ', ')           AS mentioned_in_sources,

    -- Recency
    MAX(scrape_date)                              AS last_seen,
    MIN(scrape_date)                              AS first_seen

FROM entity_articles
GROUP BY entity_text, entity_label
HAVING COUNT(DISTINCT article_key) >= 2
ORDER BY article_count DESC
    );
  
  

  
  create view "warehouse"."main"."stg_headlines__dbt_tmp" as (
    -- stg_headlines.sql
-- Mapping fact_articles to the 'stg_headlines' expected by marks/entity_trend.sql



SELECT
    fa.article_key as Headline_ID,
    ds.source_name as Source_Name,
    fa.translated_headline,
    fa.polarity,
    fa.sentiment_label,
    dd.full_date as Date_Extracted
FROM "warehouse"."main"."fact_articles" fa
JOIN "warehouse"."main"."dim_date" dd ON fa.date_key = dd.date_key
JOIN "warehouse"."main"."dim_source" ds ON fa.source_key = ds.source_key
  );

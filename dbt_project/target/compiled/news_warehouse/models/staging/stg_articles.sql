-- stg_articles.sql
-- Staging model: joins fact_articles with dimension tables to produce
-- a clean, denormalized view of all articles for downstream analytics.



SELECT
    fa.article_key,
    fa.original_headline,
    fa.translated_headline,
    fa.polarity,
    fa.sentiment_label,

    -- Source dimension
    ds.source_name,
    ds.language_code,
    ds.region,
    ds.base_url,

    -- Date dimension
    dd.full_date       AS scrape_date,
    dd.day,
    dd.month,
    dd.year,
    dd.day_of_week,
    dd.week_of_year,
    dd.quarter,
    dd.is_weekend,

    -- Computed fields
    LENGTH(fa.translated_headline) AS headline_length,
    CASE
        WHEN fa.polarity > 0.05  THEN 'positive'
        WHEN fa.polarity < -0.05 THEN 'negative'
        ELSE 'neutral'
    END AS polarity_bucket

FROM fact_articles fa
LEFT JOIN dim_source ds ON fa.source_key = ds.source_key
LEFT JOIN dim_date dd   ON fa.date_key = dd.date_key
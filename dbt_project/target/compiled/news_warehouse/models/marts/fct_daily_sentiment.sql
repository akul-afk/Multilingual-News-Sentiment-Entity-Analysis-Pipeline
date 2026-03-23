-- fct_daily_sentiment.sql
-- Mart model: daily sentiment aggregation by source.
-- Powers the dashboard trend charts and weekly/monthly reports.



SELECT
    sa.scrape_date,
    sa.source_name,
    sa.region,
    sa.language_code,

    -- Measures
    COUNT(*)                                    AS headline_count,
    ROUND(AVG(sa.polarity), 4)                  AS avg_polarity,
    ROUND(STDDEV(sa.polarity), 4)               AS stddev_polarity,
    ROUND(MEDIAN(sa.polarity), 4)               AS median_polarity,
    MIN(sa.polarity)                            AS min_polarity,
    MAX(sa.polarity)                            AS max_polarity,

    -- Sentiment distribution
    COUNT(CASE WHEN sa.polarity_bucket = 'positive' THEN 1 END) AS positive_count,
    COUNT(CASE WHEN sa.polarity_bucket = 'neutral'  THEN 1 END) AS neutral_count,
    COUNT(CASE WHEN sa.polarity_bucket = 'negative' THEN 1 END) AS negative_count,

    -- Percentages
    ROUND(COUNT(CASE WHEN sa.polarity_bucket = 'positive' THEN 1 END) * 100.0 / COUNT(*), 1) AS positive_pct,
    ROUND(COUNT(CASE WHEN sa.polarity_bucket = 'negative' THEN 1 END) * 100.0 / COUNT(*), 1) AS negative_pct,

    -- Date dimensions
    sa.day_of_week,
    sa.week_of_year,
    sa.month,
    sa.year,
    sa.quarter,
    sa.is_weekend

FROM "warehouse"."main"."stg_articles" sa
WHERE sa.scrape_date IS NOT NULL
GROUP BY
    sa.scrape_date, sa.source_name, sa.region, sa.language_code,
    sa.day_of_week, sa.week_of_year, sa.month, sa.year, sa.quarter, sa.is_weekend
ORDER BY sa.scrape_date DESC, sa.source_name
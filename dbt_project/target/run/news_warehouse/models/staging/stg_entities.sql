
  
  create view "warehouse"."main"."stg_entities__dbt_tmp" as (
    -- stg_entities.sql
-- Mapping dim_entity and bridge_article_entity back to the 'stg_entities' expected by entity_trend.sql



SELECT
    de.entity_text as Entity_Name,
    de.entity_label as Entity_Label,
    bae.article_key as Headline_ID
FROM "warehouse"."main"."dim_entity" de
JOIN "warehouse"."main"."bridge_article_entity" bae ON de.entity_key = bae.entity_key
  );

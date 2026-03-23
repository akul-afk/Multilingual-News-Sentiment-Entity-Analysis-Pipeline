
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select translated_headline
from "warehouse"."main"."stg_articles"
where translated_headline is null



  
  
      
    ) dbt_internal_test
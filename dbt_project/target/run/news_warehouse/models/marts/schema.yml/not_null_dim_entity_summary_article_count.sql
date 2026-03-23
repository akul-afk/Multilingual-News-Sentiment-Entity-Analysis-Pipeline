
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select article_count
from "warehouse"."main"."dim_entity_summary"
where article_count is null



  
  
      
    ) dbt_internal_test
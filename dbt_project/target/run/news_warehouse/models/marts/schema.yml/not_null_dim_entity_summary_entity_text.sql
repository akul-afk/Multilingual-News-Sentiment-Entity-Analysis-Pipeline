
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select entity_text
from "warehouse"."main"."dim_entity_summary"
where entity_text is null



  
  
      
    ) dbt_internal_test
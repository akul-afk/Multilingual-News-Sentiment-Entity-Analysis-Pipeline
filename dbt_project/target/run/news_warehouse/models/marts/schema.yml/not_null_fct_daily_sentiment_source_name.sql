
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select source_name
from "warehouse"."main"."fct_daily_sentiment"
where source_name is null



  
  
      
    ) dbt_internal_test
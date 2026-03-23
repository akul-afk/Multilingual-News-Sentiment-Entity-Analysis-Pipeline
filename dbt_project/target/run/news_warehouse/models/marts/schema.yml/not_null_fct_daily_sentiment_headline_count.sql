
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select headline_count
from "warehouse"."main"."fct_daily_sentiment"
where headline_count is null



  
  
      
    ) dbt_internal_test
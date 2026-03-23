
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select scrape_date
from "warehouse"."main"."fct_daily_sentiment"
where scrape_date is null



  
  
      
    ) dbt_internal_test
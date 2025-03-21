
select count(*)
from ((select distinct c_last_name, c_first_name, d_date
       from store_sales, date_dim, customer
       where store_sales.ss_sold_date_sk = date_dim.d_date_sk
         and store_sales.ss_customer_sk = customer.c_customer_sk
         and d_month_seq between 1206 and 1206+11
         and ss_list_price between 271 and 300
         and c_birth_year BETWEEN 1972 AND 1978
         and ss_wholesale_cost BETWEEN 73 AND 83
         )
       except
      (select distinct c_last_name, c_first_name, d_date
       from catalog_sales, date_dim, customer
       where catalog_sales.cs_sold_date_sk = date_dim.d_date_sk
         and catalog_sales.cs_bill_customer_sk = customer.c_customer_sk
         and d_month_seq between 1206 and 1206+11
         and cs_list_price between 271 and 300
         and c_birth_year BETWEEN 1972 AND 1978
         and cs_wholesale_cost BETWEEN 73 AND 83
         )
       except
      (select distinct c_last_name, c_first_name, d_date
       from web_sales, date_dim, customer
       where web_sales.ws_sold_date_sk = date_dim.d_date_sk
         and web_sales.ws_bill_customer_sk = customer.c_customer_sk
         and d_month_seq between 1206 and 1206+11
         and ws_list_price between 271 and 300
         and c_birth_year BETWEEN 1972 AND 1978
         and ws_wholesale_cost BETWEEN 73 AND 83
         )
) cool_cust
;



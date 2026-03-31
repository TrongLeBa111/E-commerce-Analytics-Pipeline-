-- Định nghĩa churn: không có đơn hàng trong 90 ngày
-- kể từ lần mua cuối tính đến ngày max trong dataset
with last_purchase as (
    select
        customer_id,
        max(purchased_at)        as last_order_date,
        count(distinct order_id) as total_orders
    from {{ ref('fct_orders') }}
    where order_status = 'delivered'
    group by customer_id
)

select
    l.customer_id,
    l.last_order_date,
    l.total_orders,
    {{ get_ref_date() }}                                    as ref_date,
    date_part('day', {{ get_ref_date() }} - l.last_order_date)::int
                                                            as days_since_last_order,
    case
        when date_part('day', {{ get_ref_date() }} - l.last_order_date) > 90
        then 1 else 0
    end                                                     as is_churned
from last_purchase l
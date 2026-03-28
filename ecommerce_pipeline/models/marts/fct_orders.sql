with orders as (
    select * from {{ ref('stg_orders') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

payments as (
    select
        order_id,
        sum(payment_value) as total_payment_value,
        max(payment_installments) as max_installments
    from {{ ref('stg_order_payments') }}
    group by order_id
),

order_aggregates as (
    select
        order_id,
        count(order_item_id)       as item_count,
        sum(price)                 as total_price,
        sum(freight_value)         as total_freight_value,
        sum(price + freight_value) as total_order_value
    from order_items
    group by order_id
)

select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.purchased_at,
    o.approved_at,
    o.delivered_to_carrier_at,
    o.delivered_to_customer_at,
    o.estimated_delivery_at,

    -- Metrics
    oa.item_count,
    oa.total_price,
    oa.total_freight_value,
    oa.total_order_value,
    p.total_payment_value,
    p.max_installments,

    -- Delivery time (số ngày)
    case
        when o.delivered_to_customer_at is not null
        then extract(day from o.delivered_to_customer_at - o.purchased_at)
    end as delivery_days

from orders o
left join order_aggregates oa on o.order_id = oa.order_id
left join payments p          on o.order_id = p.order_id
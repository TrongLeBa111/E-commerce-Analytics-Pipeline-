with order_with_gap as (
    select
        customer_id,
        order_id,
        purchased_at,
        delivered_to_customer_at,
        estimated_delivery_at,
        total_order_value,
        delivery_days,
        item_count,
        date_part('day',
            purchased_at -
            lag(purchased_at) over (
                partition by customer_id
                order by purchased_at
            )
        ) as purchase_gap_days
    from {{ ref('fct_orders') }}
    where order_status = 'delivered'
),

order_features as (
    select
        customer_id,
        date_part('day', {{ get_ref_date() }} - max(purchased_at))::int as recency_days,
        count(distinct order_id)            as frequency,
        sum(total_order_value)              as monetary,
        avg(total_order_value)              as avg_order_value,
        avg(delivery_days)                  as avg_delivery_days,
        max(delivery_days)                  as max_delivery_days,
        sum(case when delivered_to_customer_at > estimated_delivery_at
            then 1 else 0 end)::float
            / nullif(count(*), 0)           as late_delivery_rate,
        avg(item_count)                     as avg_items_per_order,
        avg(purchase_gap_days)              as avg_purchase_gap_days
    from order_with_gap
    group by customer_id
),

payment_features as (
    select
        o.customer_id,
        avg(p.payment_installments::int)    as avg_installments,
        sum(case when p.payment_type = 'credit_card'
            then 1 else 0 end)::float
            / nullif(count(*), 0)           as credit_card_rate
    from {{ ref('fct_orders') }} o
    join {{ ref('stg_order_payments') }} p on o.order_id = p.order_id
    group by o.customer_id
),

review_features as (
    select
        o.customer_id,
        avg(r.review_score::int)            as avg_review_score,
        min(r.review_score::int)            as min_review_score,
        sum(case when r.review_score::int <= 2
            then 1 else 0 end)::float
            / nullif(count(*), 0)           as bad_review_rate
    from {{ ref('fct_orders') }} o
    join raw.order_reviews r on o.order_id = r.order_id
    group by o.customer_id
)

select
    c.customer_id,
    c.state                                 as customer_state,
    f.recency_days,
    f.frequency,
    f.monetary,
    f.avg_order_value,
    f.avg_delivery_days,
    f.max_delivery_days,
    f.late_delivery_rate,
    f.avg_items_per_order,
    f.avg_purchase_gap_days,
    coalesce(p.avg_installments, 1)         as avg_installments,
    coalesce(p.credit_card_rate, 0)         as credit_card_rate,
    coalesce(r.avg_review_score, 3)         as avg_review_score,
    coalesce(r.min_review_score, 3)         as min_review_score,
    coalesce(r.bad_review_rate, 0)          as bad_review_rate
from {{ ref('dim_customers') }} c
join order_features f        on c.customer_id = f.customer_id
left join payment_features p on c.customer_id = p.customer_id
left join review_features r  on c.customer_id = r.customer_id
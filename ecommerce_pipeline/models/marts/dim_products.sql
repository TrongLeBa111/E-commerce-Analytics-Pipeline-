with products as (
    select * from {{ ref('stg_products') }}
),

translations as (
    select * from {{ source('raw', 'product_category_translation') }}
)

select
    p.product_id,
    coalesce(t.product_category_name_english, 'uncategorized') as category_name_en,
    p.category_name                                             as category_name_pt,
    p.weight_g,
    p.length_cm,
    p.height_cm,
    p.width_cm
from products p
left join translations t
    on p.category_name = t.product_category_name
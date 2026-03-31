{% macro get_ref_date() %}
    (SELECT MAX(purchased_at) FROM {{ ref("fct_orders") }})
{% endmacro %}
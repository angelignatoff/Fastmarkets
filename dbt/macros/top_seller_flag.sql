{% macro top_seller_flag(revenue, week) -%}
    iff({{ revenue }} = max({{ revenue }}) over (partition by {{ week }}), 1, 0)
{%- endmacro %}

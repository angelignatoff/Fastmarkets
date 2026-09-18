{% macro week_start(date_expression) -%}
    dateadd(day, 1 - dayofweekiso({{ date_expression }}), {{ date_expression }})::date
{%- endmacro %}

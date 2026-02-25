{% test expression_is_true(model, expression, column_name=None) %}

-- Generic test: returns rows where the boolean expression is NOT true.
-- dbt passes `column_name=` automatically for column-level tests.

select *
from {{ model }}
where not ({{ expression }})

{% endtest %}

{% macro generate_schema_name(custom_schema_name, node) -%}
  {#
    Default dbt behavior prefixes custom schema names with target.schema, yielding
    e.g. analytics_staging and analytics_analytics. For this project we want the
    schemas to match the warehouse layout exactly: raw, staging, analytics, ops.
  #}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name }}
  {%- endif -%}
{%- endmacro %}

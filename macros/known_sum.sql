{% macro known_sum(expression) -%}
    case
        when count({{ expression }}) = count(*) then sum({{ expression }})
    end
{%- endmacro %}

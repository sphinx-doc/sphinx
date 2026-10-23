{%- extends "autosummary/class.rst" %}

{%- block methods %}
..
   name: {{ name }}
   methods:
   {%- for item in methods %}
   {%- if item in members %}
   {%- if item not in inherited_members %}
     - {{ item }}
   {%- endif %}
   {%- endif %}
   {%- endfor %}
   inherited_methods:
   {%- for item in methods %}
   {%- if item in members %}
   {%- if item in inherited_members %}
     - {{ item }}
   {%- endif %}
   {%- endif %}
   {%- endfor %}
{% endblock %}

{%- block attributes %}
..
   name: {{ name }}
   attributes:
   {%- for item in attributes %}
   {%- if item in members %}
   {%- if item not in inherited_members %}
     - {{ item }}
   {%- endif %}
   {%- endif %}
   {%- endfor %}
   inherited_attributes:
   {%- for item in attributes %}
   {%- if item in members %}
   {%- if item in inherited_members %}
     - {{ item }}
   {%- endif %}
   {%- endif %}
   {%- endfor %}
{% endblock %}

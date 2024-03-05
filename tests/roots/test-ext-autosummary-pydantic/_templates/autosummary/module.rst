{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}

   {% block attribute %}
   {% if attribute %}
   .. rubric:: {{ _('Module Attributes') }}

   .. autosummary::
   {% for item in attribute %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block function %}
   {% if function %}
   .. rubric:: {{ _('Functions') }}

   .. autosummary::
   {% for item in function %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block class %}
   {% if class %}
   .. rubric:: {{ _('Classes') }}

   .. autosummary::
   {% for item in class %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block pydantic_model %}
   {% if pydantic_model %}
   .. rubric:: {{ _('Models') }}

   .. autosummary::
      :toctree:
   {% for item in pydantic_model %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block pydantic_settings %}
   {% if pydantic_settings %}
   .. rubric:: {{ _('Settings') }}

   .. autosummary::
      :toctree:
   {% for item in pydantic_settings %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block exception %}
   {% if exception %}
   .. rubric:: {{ _('Exceptions') }}

   .. autosummary::
   {% for item in exception %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

{% block modules %}
{% if modules %}
.. rubric:: {{ _('Modules') }}

.. autosummary::
   :toctree:
   :recursive:
{% for item in modules %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

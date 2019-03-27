{{ fullname | escape | underline }}

.. rubric:: Description

.. automodule:: {{ fullname }}

   {% block public_modules %}
   {% if public_modules %}
   .. rubric:: Modules

   .. autosummary::
      :toctree:
   {% for item in public_modules %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}


   {% block classes %}
   {% if classes %}
   .. rubric:: Classes

   .. autosummary::
      :toctree:
   {% for item in classes %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}


   {% block functions %}
   {% if functions %}
   .. rubric:: Functions

   .. autosummary::
      :toctree:
   {% for item in functions %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

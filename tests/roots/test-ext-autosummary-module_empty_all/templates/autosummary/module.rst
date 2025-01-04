{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}

   {% block members %}
   Summary
   -------
   .. autosummary::

   {% for item in members %}
      {{ item }}
   {%- endfor %}
   {% endblock %}

.. _nodes:

Doctree node classes added by Sphinx
====================================

.. module:: sphinx.addnodes

Nodes for domain-specific object descriptions
---------------------------------------------

Top-level nodes
...............

These nodes form the top-most levels of object descriptions.

.. autoclass:: desc
.. autoclass:: desc_signature
.. autoclass:: desc_signature_line
.. autoclass:: desc_content
.. autoclass:: desc_inline

Nodes for high-level structure in signatures
............................................

These nodes occur in in non-multiline :py:class:`desc_signature` nodes
and in :py:class:`desc_signature_line` nodes.

.. autoclass:: desc_name
.. autoclass:: desc_addname

.. autoclass:: desc_type
.. autoclass:: desc_returns
.. autoclass:: desc_parameterlist
.. autoclass:: desc_parameter
.. autoclass:: desc_optional
.. autoclass:: desc_annotation

Nodes for signature text elements
.................................

These nodes inherit :py:class:`desc_sig_element` and are generally translated
to ``docutils.nodes.inline`` by :py:class:`!SigElementFallbackTransform`.

Extensions may create additional ``desc_sig_*``-like nodes but in order for
:py:class:`!SigElementFallbackTransform` to translate them to inline nodes
automatically, they must be added to :py:data:`SIG_ELEMENTS` via the class
keyword argument ``_sig_element=True`` of :py:class:`desc_sig_element`, e.g.:

   .. code-block:: python

      class desc_custom_sig_node(desc_sig_element, _sig_element=True): ...

For backwards compatibility, it is still possible to add the nodes directly
using ``SIG_ELEMENTS.add(desc_custom_sig_node)``.

.. autodata:: SIG_ELEMENTS
   :no-value:

.. autoclass:: desc_sig_element

.. autoclass:: desc_sig_space
.. autoclass:: desc_sig_name
.. autoclass:: desc_sig_operator
.. autoclass:: desc_sig_punctuation
.. autoclass:: desc_sig_keyword
.. autoclass:: desc_sig_keyword_type
.. autoclass:: desc_sig_literal_number
.. autoclass:: desc_sig_literal_string
.. autoclass:: desc_sig_literal_char

New admonition-like constructs
------------------------------

.. autoclass:: versionmodified
.. autoclass:: seealso

Other paragraph-level nodes
-------------------------------

.. autoclass:: compact_paragraph

New inline nodes
----------------

.. autoclass:: index
.. autoclass:: pending_xref
.. autoclass:: pending_xref_condition
.. autoclass:: literal_emphasis
.. autoclass:: download_reference

Special nodes
-------------

.. autoclass:: only
.. autoclass:: highlightlang

You should not need to generate the nodes below in extensions.

.. autoclass:: glossary
.. autoclass:: toctree
.. autoclass:: start_of_file
.. autoclass:: productionlist
.. autoclass:: production

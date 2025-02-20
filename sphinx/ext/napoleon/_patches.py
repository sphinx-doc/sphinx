from __future__ import annotations


def _patch_python_domain() -> None:
    from sphinx.domains.python._object import PyObject, PyTypedField
    from sphinx.locale import _

    for doc_field in PyObject.doc_field_types:
        if doc_field.name == 'parameter':
            doc_field.names = ('param', 'parameter', 'arg', 'argument')
            break
    PyObject.doc_field_types.append(
        PyTypedField(
            'keyword',
            label=_('Keyword Arguments'),
            names=('keyword', 'kwarg', 'kwparam'),
            typerolename='class',
            typenames=('paramtype', 'kwtype'),
            can_collapse=True,
        )
    )

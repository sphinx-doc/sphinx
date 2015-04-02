# -*- coding: utf-8 -*-
"""
    sphinx.ext.asyncio
    ~~~~~~~~~~~~~~~~~~

    Adds directives for :py:class:`asyncio`.

    .. rst:directive:: .. py:coroutine:: name(parameters)

       Like :rst:dir:`py:function`, but for :py:class:`asyncio.coroutine`.

       .. versionadded:: 1.4

    .. rst:directive:: .. py:coroutinemethod:: name(parameters)

       Like :rst:dir:`py:method`, but for :py:class:`asyncio.coroutine`.

       .. versionadded:: 1.4

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""


from sphinx import addnodes
from sphinx.domains.python import PyModulelevel, PyClassmember
from sphinx.ext.autodoc import FunctionDocumenter, MethodDocumenter
from sphinx.util.inspect import iscoroutinefunction


class FunctionDocumenter(FunctionDocumenter):
    """
    Specialized Documenter subclass for functions and coroutines.
    """

    def import_object(self):
        ret = FunctionDocumenter.import_object(self)
        if not ret:
            return ret

        obj = self.parent.__dict__.get(self.object_name)
        if iscoroutinefunction(obj):
            self.directivetype = 'coroutine'
            self.member_order = FunctionDocumenter.member_order + 2
        return ret


class MethodDocumenter(MethodDocumenter):
    """
    Specialized Documenter subclass for methods and coroutines.
    """

    def import_object(self):
        ret = MethodDocumenter.import_object(self)
        if not ret:
            return ret

        obj = self.parent.__dict__.get(self.object_name)
        if iscoroutinefunction(obj):
            self.directivetype = 'coroutinemethod'
            self.member_order = MethodDocumenter.member_order + 2
        return ret


class PyCoroutineMixin(object):
    def handle_signature(self, sig, signode):
        ret = super(PyCoroutineMixin, self).handle_signature(sig, signode)
        signode.insert(0, addnodes.desc_annotation('coroutine ', 'coroutine '))
        return ret


class PyCoroutineFunction(PyCoroutineMixin, PyModulelevel):
    def run(self):
        self.name = 'py:function'
        return PyModulelevel.run(self)


class PyCoroutineMethod(PyCoroutineMixin, PyClassmember):
    def run(self):
        self.name = 'py:method'
        return PyClassmember.run(self)


def setup(app):
    app.add_directive_to_domain('py', 'coroutine', PyCoroutineFunction)
    app.add_directive_to_domain('py', 'coroutinemethod', PyCoroutineMethod)

    app.add_autodocumenter(FunctionDocumenter)
    app.add_autodocumenter(MethodDocumenter)

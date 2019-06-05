"""
    sphinx.ext.autodoc.importer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Importer utilities for autodoc

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import traceback
import warnings
from collections import namedtuple

from sphinx.deprecation import RemovedInSphinx40Warning, deprecated_alias
from sphinx.util import logging
from sphinx.util.inspect import isclass, isenumclass, safe_getattr

if False:
    # For type annotation
    from typing import Any, Callable, Dict, List  # NOQA

logger = logging.getLogger(__name__)


def import_module(modname, warningiserror=False):
    # type: (str, bool) -> Any
    """
    Call __import__(modname), convert exceptions to ImportError
    """
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ImportWarning)
            with logging.skip_warningiserror(not warningiserror):
                __import__(modname)
                return sys.modules[modname]
    except BaseException as exc:
        # Importing modules may cause any side effects, including
        # SystemExit, so we need to catch all errors.
        raise ImportError(exc, traceback.format_exc())


def import_object(modname, objpath, objtype='', attrgetter=safe_getattr, warningiserror=False):
    # type: (str, List[str], str, Callable[[Any, str], Any], bool) -> Any
    if objpath:
        logger.debug('[autodoc] from %s import %s', modname, '.'.join(objpath))
    else:
        logger.debug('[autodoc] import %s', modname)

    try:
        module = None
        exc_on_importing = None
        objpath = list(objpath)
        while module is None:
            try:
                module = import_module(modname, warningiserror=warningiserror)
                logger.debug('[autodoc] import %s => %r', modname, module)
            except ImportError as exc:
                logger.debug('[autodoc] import %s => failed', modname)
                exc_on_importing = exc
                if '.' in modname:
                    # retry with parent module
                    modname, name = modname.rsplit('.', 1)
                    objpath.insert(0, name)
                else:
                    raise

        obj = module
        parent = None
        object_name = None
        for attrname in objpath:
            parent = obj
            logger.debug('[autodoc] getattr(_, %r)', attrname)
            obj = attrgetter(obj, attrname)
            logger.debug('[autodoc] => %r', obj)
            object_name = attrname
        return [module, parent, object_name, obj]
    except (AttributeError, ImportError) as exc:
        if isinstance(exc, AttributeError) and exc_on_importing:
            # restore ImportError
            exc = exc_on_importing

        if objpath:
            errmsg = ('autodoc: failed to import %s %r from module %r' %
                      (objtype, '.'.join(objpath), modname))
        else:
            errmsg = 'autodoc: failed to import %s %r' % (objtype, modname)

        if isinstance(exc, ImportError):
            # import_module() raises ImportError having real exception obj and
            # traceback
            real_exc, traceback_msg = exc.args
            if isinstance(real_exc, SystemExit):
                errmsg += ('; the module executes module level statement '
                           'and it might call sys.exit().')
            elif isinstance(real_exc, ImportError) and real_exc.args:
                errmsg += '; the following exception was raised:\n%s' % real_exc.args[0]
            else:
                errmsg += '; the following exception was raised:\n%s' % traceback_msg
        else:
            errmsg += '; the following exception was raised:\n%s' % traceback.format_exc()

        logger.debug(errmsg)
        raise ImportError(errmsg)


Attribute = namedtuple('Attribute', ['name', 'directly_defined', 'value'])


def get_object_members(subject, objpath, attrgetter, analyzer=None):
    # type: (Any, List[str], Callable, Any) -> Dict[str, Attribute]  # NOQA
    """Get members and attributes of target object."""
    # the members directly defined in the class
    obj_dict = attrgetter(subject, '__dict__', {})

    members = {}  # type: Dict[str, Attribute]

    # enum members
    if isenumclass(subject):
        for name, value in subject.__members__.items():
            if name not in members:
                members[name] = Attribute(name, True, value)

        superclass = subject.__mro__[1]
        for name, value in obj_dict.items():
            if name not in superclass.__dict__:
                members[name] = Attribute(name, True, value)

    # members in __slots__
    if isclass(subject) and getattr(subject, '__slots__', None) is not None:
        from sphinx.ext.autodoc import SLOTSATTR

        for name in subject.__slots__:
            members[name] = Attribute(name, True, SLOTSATTR)

    # other members
    for name in dir(subject):
        try:
            value = attrgetter(subject, name)
            directly_defined = name in obj_dict
            if name not in members:
                members[name] = Attribute(name, directly_defined, value)
        except AttributeError:
            continue

    if analyzer:
        # append instance attributes (cf. self.attr1) if analyzer knows
        from sphinx.ext.autodoc import INSTANCEATTR

        namespace = '.'.join(objpath)
        for (ns, name) in analyzer.find_attr_docs():
            if namespace == ns and name not in members:
                members[name] = Attribute(name, True, INSTANCEATTR)

    return members


from sphinx.ext.autodoc.mock import (  # NOQA
    _MockImporter, _MockModule, _MockObject, MockFinder, MockLoader, mock
)

deprecated_alias('sphinx.ext.autodoc.importer',
                 {
                     '_MockImporter': _MockImporter,
                     '_MockModule': _MockModule,
                     '_MockObject': _MockObject,
                     'MockFinder': MockFinder,
                     'MockLoader': MockLoader,
                     'mock': mock,
                 },
                 RemovedInSphinx40Warning)

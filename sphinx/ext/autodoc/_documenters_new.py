from __future__ import annotations

# Re-export all documenter classes for backward compatibility
# This module has been modularized - see the individual modules for details

from sphinx.ext.autodoc.documenter_base import *  # noqa: F403
from sphinx.ext.autodoc.module_documenters import *  # noqa: F403
from sphinx.ext.autodoc.class_documenters import *  # noqa: F403
from sphinx.ext.autodoc.function_documenters import *  # noqa: F403
from sphinx.ext.autodoc.data_documenters import *  # noqa: F403
from sphinx.ext.autodoc.mixins import *  # noqa: F403

# Define __all__ to explicitly export all classes
__all__ = [
    # Base classes
    'Documenter',
    '_get_render_mode',
    'py_ext_sig_re',

    # Module documenters
    'ModuleDocumenter',
    'ModuleLevelDocumenter',

    # Class documenters
    'ClassDocumenter',
    'ExceptionDocumenter',

    # Function documenters
    'FunctionDocumenter',
    'DecoratorDocumenter',
    'MethodDocumenter',

    # Data documenters
    'DataDocumenter',
    'AttributeDocumenter',
    'PropertyDocumenter',

    # Mixins
    'DocstringSignatureMixin',
    'ClassLevelDocumenter',
]

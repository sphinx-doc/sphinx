===============================
Sphinx Modularization Guidelines
===============================

This document outlines the guidelines for maintaining and extending the modularized structure of the Sphinx codebase.

Overview
========

Following the successful modularization of several large files, these guidelines ensure consistent code organization and maintainability.

File Size Guidelines
====================

Maximum File Sizes
------------------

* **Core Classes**: 500-800 lines (single responsibility principle)
* **Utility Modules**: 200-500 lines (focused functionality)
* **Parser/AST Files**: 800-1200 lines (complex but logically grouped)
* **Documentation**: No strict limit, but aim for readability

When to Split Files
-------------------

Consider splitting when a file exceeds:

* **1000 lines**: Generally too large, consider splitting
* **1500 lines**: Definitely split into logical components
* **2000+ lines**: Major refactoring required

File Organization Patterns
==========================

1. **Base + Specialized Modules**
   - ``_base.py`` or ``base.py``: Core classes and interfaces
   - ``_module.py``: Specialized implementations
   - ``__init__.py``: Re-exports for backward compatibility

2. **Functional Grouping**
   - Group related functionality together
   - Separate parsing, processing, and output phases
   - Isolate domain-specific logic

3. **Mixin Pattern**
   - Use mixins for shared functionality
   - Keep core classes focused on primary responsibility
   - Enable flexible composition

Import and Export Strategy
==========================

Re-export Pattern
-----------------

For backward compatibility, use this pattern in main modules:

.. code-block:: python

   # Re-export all components for backward compatibility
   # This module has been modularized - see individual modules for details

   from sphinx.module.component_a import *  # noqa: F403
   from sphinx.module.component_b import *  # noqa: F403
   from sphinx.module.component_c import *  # noqa: F403

   __all__ = [
       # Explicitly list all exported symbols
       'ClassA', 'ClassB', 'function_c', 'CONSTANT_D',
   ]

__all__ Declarations
--------------------

* **Required**: All public modules must have explicit ``__all__`` declarations
* **Complete**: List all classes, functions, and constants that should be public
* **Documented**: Include comments grouping related exports
* **Maintained**: Update ``__all__`` when adding/removing public APIs

Naming Conventions
==================

Module Names
------------

* Use descriptive, plural names for collections: ``documenters.py``, ``parsers.py``
* Use functional names: ``expressions.py``, ``declarations.py``
* Use ``_base.py`` for base classes and common functionality
* Keep original names for main modules to maintain backward compatibility

Class Names
-----------

* **Suffix with purpose**: ``Documenter``, ``Parser``, ``Builder``
* **Group related classes**: ``ExpressionParser``, ``DeclarationParser``
* **Use Mixin suffix**: ``SignatureMixin``, ``ValidationMixin``

Function Names
--------------

* **Descriptive**: ``parse_expression``, ``build_documentation``
* **Consistent**: Use ``_parse_`` for parsing functions, ``_build_`` for building functions
* **Clear purpose**: ``get_signatures``, ``resolve_name``, ``filter_members``

Code Quality Standards
======================

Single Responsibility
---------------------

Each module should have:

* **One primary purpose**: Parsing, building, documenting, etc.
* **Focused functionality**: Don't mix unrelated concerns
* **Clear boundaries**: Well-defined interfaces between modules

Dependency Management
--------------------

* **Minimize circular imports**: Use TYPE_CHECKING imports where possible
* **Explicit dependencies**: Import only what you need
* **Forward references**: Use string literals for forward references
* **Lazy imports**: Import heavy dependencies only when needed

Testing Strategy
================

Unit Tests
----------

* **Test each module independently**: Mock external dependencies
* **Test public interfaces**: Focus on ``__all__`` exports
* **Test error conditions**: Ensure proper error handling
* **Test edge cases**: Boundary conditions and unusual inputs

Integration Tests
-----------------

* **Test module interactions**: Ensure modules work together
* **Test backward compatibility**: Verify existing code still works
* **Test import patterns**: Ensure all import methods function

Documentation
=============

Module Documentation
--------------------

Each module should have:

* **Module docstring**: Describe the module's purpose
* **Class documentation**: Document all public classes
* **Function documentation**: Document all public functions
* **Usage examples**: Where appropriate

API Documentation
-----------------

* **Keep docstrings current**: Update when changing APIs
* **Document breaking changes**: Use version notes
* **Maintain examples**: Ensure examples still work
* **Cross-reference**: Link related modules and functions

Migration Guide
===============

For Existing Code
-----------------

When modularizing existing files:

1. **Create new modules** with focused functionality
2. **Move classes and functions** to appropriate modules
3. **Create re-export module** for backward compatibility
4. **Update imports** in consuming modules
5. **Test thoroughly** before committing

For New Features
----------------

When adding new functionality:

1. **Choose appropriate module**: Add to existing module or create new one
2. **Follow naming conventions**: Consistent with existing code
3. **Update ``__all__``**: Add new exports
4. **Add documentation**: Include docstrings and examples
5. **Add tests**: Unit and integration tests

Best Practices
==============

1. **Keep it simple**: Don't over-engineer the modularization
2. **Maintain compatibility**: Always provide backward compatibility paths
3. **Document changes**: Keep track of what moves where
4. **Test frequently**: Regular testing prevents regressions
5. **Review regularly**: Periodic reviews of module organization

Common Pitfalls
===============

* **Over-modularization**: Too many small files can be hard to navigate
* **Circular dependencies**: Plan imports carefully to avoid cycles
* **Inconsistent naming**: Follow established conventions
* **Missing documentation**: Always document new modules and APIs
* **Untested code**: Ensure all modules have adequate test coverage

Examples
========

Successful Modularizations
--------------------------

* **C++ AST Module**: Split 92 classes into 5 focused modules
* **Autodoc Documenters**: Split 13 documenters into 7 functional modules
* **Application Module**: Extracted 4 utility modules from main application

Before/After Comparison
----------------------

**Before (Monolithic)**:

.. code-block:: python

   # 2000+ lines in one file
   class MassiveClass:
       def method_a(self): pass  # 50 lines
       def method_b(self): pass  # 100 lines
       def method_c(self): pass  # 75 lines

**After (Modularized)**:

.. code-block:: python

   # module_a.py (150 lines)
   class SpecializedClassA:
       def method_a(self): pass

   # module_b.py (200 lines)
   class SpecializedClassB:
       def method_b(self): pass

   # main_module.py (50 lines)
   from .module_a import *
   from .module_b import *

   __all__ = ['SpecializedClassA', 'SpecializedClassB']

Tools and Resources
===================

* **Code Analysis**: Use tools like ``radon`` for complexity analysis
* **Import Graph**: Tools like ``pyreverse`` to visualize dependencies
* **Test Coverage**: Ensure all modules have adequate test coverage
* **Linting**: Use ``flake8``, ``black``, and ``mypy`` for code quality

Conclusion
==========

Following these guidelines ensures:

* **Maintainable codebase**: Easy to understand and modify
* **Scalable architecture**: New features can be added cleanly
* **Developer productivity**: Faster navigation and development
* **Code quality**: Consistent patterns and best practices
* **Future-proofing**: Prepared for long-term evolution

These guidelines should be reviewed and updated periodically as the codebase evolves and new patterns emerge.

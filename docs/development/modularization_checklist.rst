==============================
Modularization Quick Checklist
==============================

Quick Reference for Developers
==============================

File Size Guidelines
====================

✅ **Files should generally not exceed:**

- 500-800 lines for core classes
- 200-500 lines for utility modules
- 800-1200 lines for parsers/AST files

✅ **Split when exceeding:**

- 1000 lines: Consider splitting
- 1500 lines: Definitely split
- 2000+ lines: Major refactoring required

Naming Conventions
==================

✅ **Module names:**

- Use descriptive names: ``expressions.py``, ``declarations.py``
- Use ``_base.py`` for base functionality
- Keep original names for main modules

✅ **Class names:**

- Suffix with purpose: ``Documenter``, ``Parser``
- Group related: ``ExpressionParser``, ``DeclarationParser``
- Use Mixin suffix: ``SignatureMixin``

✅ **Function names:**

- Descriptive: ``parse_expression``, ``build_documentation``
- Consistent prefixes: ``_parse_``, ``_build_``
- Clear purpose: ``get_signatures``, ``resolve_name``

Import/Export Strategy
======================

✅ **Re-export pattern:**

.. code-block:: python

   from module.component_a import *  # noqa: F403
   from module.component_b import *  # noqa: F403

   __all__ = ['ClassA', 'ClassB', 'function_c']

✅ **Required in all public modules:**

- Explicit ``__all__`` declarations
- Complete list of public exports
- Comments grouping related exports

Code Quality Standards
======================

✅ **Single Responsibility:**

- One primary purpose per module
- Focused functionality
- Clear boundaries between modules

✅ **Dependencies:**

- Minimize circular imports
- Use TYPE_CHECKING imports
- Lazy import heavy dependencies

Testing Requirements
====================

✅ **Unit Tests:**

- Test each module independently
- Mock external dependencies
- Test public interfaces (``__all__`` exports)
- Test error conditions

✅ **Integration Tests:**

- Test module interactions
- Test backward compatibility
- Test import patterns

Documentation Requirements
=========================

✅ **Module Documentation:**

- Module docstring describing purpose
- Class documentation for all public classes
- Function documentation for all public functions

✅ **Keep Current:**

- Update docstrings when changing APIs
- Document breaking changes with version notes
- Maintain examples and cross-references

Common Patterns
===============

✅ **For new modules:**

1. Create focused functionality
2. Add to appropriate existing module or create new one
3. Follow naming conventions
4. Update ``__all__`` in parent module
5. Add documentation
6. Add tests

✅ **For modularizing existing files:**

1. Create new modules with focused functionality
2. Move classes/functions to appropriate modules
3. Create re-export module for backward compatibility
4. Update imports in consuming modules
5. Test thoroughly

Best Practices
==============

✅ **Keep it simple**

✅ **Maintain compatibility**

✅ **Document changes**

✅ **Test frequently**

✅ **Review regularly**

Common Pitfalls to Avoid
========================

❌ **Over-modularization:** Too many small files

❌ **Circular dependencies:** Plan imports carefully

❌ **Inconsistent naming:** Follow conventions

❌ **Missing documentation:** Always document

❌ **Untested code:** Ensure test coverage

Tools to Use
============

✅ **Code Analysis:** ``radon`` for complexity

✅ **Import Graph:** ``pyreverse`` for dependencies

✅ **Test Coverage:** Coverage reporting

✅ **Linting:** ``flake8``, ``black``, ``mypy``

Quick Validation
================

Before committing modularization changes:

1. ✅ All modules compile without errors
2. ✅ All imports work (test import statements)
3. ✅ ``__all__`` exports are correct
4. ✅ Tests pass for all affected modules
5. ✅ Documentation is updated
6. ✅ No breaking changes to public APIs
7. ✅ Code follows naming conventions
8. ✅ Dependencies are minimized

Success Metrics
===============

Target improvements:

- **75% reduction** in largest file sizes
- **Zero breaking changes** to existing code
- **Improved maintainability** and navigation
- **Better testability** with isolated modules
- **Clear separation of concerns**

Examples from Recent Modularizations
====================================

✅ **C++ AST:** 4,748 lines → 5 modules (75% reduction)

✅ **Autodoc Documenters:** 2,349 lines → 7 modules (82% reduction)

✅ **Application:** 1,869 lines → 6 modules (4% reduction)

✅ **C++ Parser:** 2,269 lines → 5 modules (pending completion)

These examples demonstrate successful modularization while maintaining full backward compatibility.

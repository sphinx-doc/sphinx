from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sphinx.builders import Builder
    from sphinx.theming import Theme


class TemplateBridge:
    """This class defines the interface for a "template bridge", that is, a class
    that renders templates given a template name and a context.
    """

    def init(
        self,
        builder: Builder,
        theme: Theme | None = None,
        dirs: list[str] | None = None,
    ) -> None:
        """Called by the builder to initialize the template system.

        *builder* is the builder object; you'll probably want to look at the
        value of ``builder.config.templates_path``.

        *theme* is a :class:`sphinx.theming.Theme` object or None; in the latter
        case, *dirs* can be list of fixed directories to look for templates.
        """
        msg = 'must be implemented in subclasses'
        raise NotImplementedError(msg)

    def newest_template_mtime(self) -> float:
        """Called by the builder to determine if output files are outdated
        because of template changes.  Return the mtime of the newest template
        file that was changed.  The default implementation returns ``0``.
        """
        return 0

    def render(self, template: str, context: dict[str, Any]) -> None:
        """Called by the builder to render a template given as a filename with
        a specified context (a Python dictionary).
        """
        msg = 'must be implemented in subclasses'
        raise NotImplementedError(msg)

    def render_string(self, template: str, context: dict[str, Any]) -> str:
        """Called by the builder to render a template given as a string with a
        specified context (a Python dictionary).
        """
        msg = 'must be implemented in subclasses'
        raise NotImplementedError(msg)


# Utility functions
def autodoc_attrgetter(obj: Any, name: str, *defargs: Any, registry: Any = None) -> Any:
    """Get an attribute from an object, with special handling for certain types."""
    # Implementation would be here
    return getattr(obj, name, *defargs)


def setup(app: Any) -> None:
    """Set up the application utilities."""
    # Implementation would be here
    pass


# Define __all__ for this module
__all__ = ['TemplateBridge', 'autodoc_attrgetter', 'setup']

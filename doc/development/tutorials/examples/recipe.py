import docutils
from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives
import sphinx
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain
from sphinx.domains import Index
from sphinx.domains.std import StandardDomain
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode


class RecipeDirective(ObjectDescription):
    """A custom directive that describes a recipe."""

    has_content = True
    required_arguments = 1
    option_spec = {
        'contains': directives.unchanged_required
    }

    def handle_signature(self, sig, signode):
        signode += addnodes.desc_name(text=sig)
        signode += addnodes.desc_type(text='Recipe')
        return sig

    def add_target_and_index(self, name_cls, sig, signode):
        signode['ids'].append('recipe' + '-' + sig)
        if 'noindex' not in self.options:
            name = '{}.{}.{}'.format('rcp', type(self).__name__, sig)
            imap = self.env.domaindata['rcp']['obj2ingredient']
            imap[name] = list(self.options.get('contains').split(' '))
            objs = self.env.domaindata['rcp']['objects']
            objs.append((name,
                         sig,
                         'Recipe',
                         self.env.docname,
                         'recipe' + '-' + sig,
                         0))


class IngredientIndex(Index):
    """A custom directive that creates an ingredient matrix."""

    name = 'ing'
    localname = 'Ingredient Index'
    shortname = 'Ingredient'

    def __init__(self, *args, **kwargs):
        super(IngredientIndex, self).__init__(*args, **kwargs)

    def generate(self, docnames=None):
        """Return entries for the index given by *name*.

        If *docnames* is given, restrict to entries referring to these
        docnames.  The return value is a tuple of ``(content, collapse)``,
        where:

        *collapse* is a boolean that determines if sub-entries should
        start collapsed (for output formats that support collapsing
        sub-entries).

        *content* is a sequence of ``(letter, entries)`` tuples, where *letter*
        is the "heading" for the given *entries*, usually the starting letter.

        *entries* is a sequence of single entries, where a single entry is a
        sequence ``[name, subtype, docname, anchor, extra, qualifier, descr]``.

        The items in this sequence have the following meaning:

        - `name` -- the name of the index entry to be displayed
        - `subtype` -- sub-entry related type:
          - ``0`` -- normal entry
          - ``1`` -- entry with sub-entries
          - ``2`` -- sub-entry
        - `docname` -- docname where the entry is located
        - `anchor` -- anchor for the entry within `docname`
        - `extra` -- extra info for the entry
        - `qualifier` -- qualifier for the description
        - `descr` -- description for the entry

        Qualifier and description are not rendered by some builders, such as
        the LaTeX builder.
        """

        content = {}

        objs = {name: (dispname, typ, docname, anchor)
                for name, dispname, typ, docname, anchor, prio
                in self.domain.get_objects()}

        imap = {}
        ingr = self.domain.data['obj2ingredient']
        for name, ingr in ingr.items():
            for ig in ingr:
                imap.setdefault(ig,[])
                imap[ig].append(name)

        for ingredient in imap.keys():
            lis = content.setdefault(ingredient, [])
            objlis = imap[ingredient]
            for objname in objlis:
                dispname, typ, docname, anchor = objs[objname]
                lis.append((
                    dispname, 0, docname,
                    anchor,
                    docname, '', typ
                ))
        re = [(k, v) for k, v in sorted(content.items())]

        return (re, True)


class RecipeIndex(Index):
    name = 'rcp'
    localname = 'Recipe Index'
    shortname = 'Recipe'

    def __init__(self, *args, **kwargs):
        super(RecipeIndex, self).__init__(*args, **kwargs)

    def generate(self, docnames=None):
        """Return entries for the index given by *name*.

        If *docnames* is given, restrict to entries referring to these
        docnames.  The return value is a tuple of ``(content, collapse)``,
        where:

        *collapse* is a boolean that determines if sub-entries should
        start collapsed (for output formats that support collapsing
        sub-entries).

        *content* is a sequence of ``(letter, entries)`` tuples, where *letter*
        is the "heading" for the given *entries*, usually the starting letter.

        *entries* is a sequence of single entries, where a single entry is a
        sequence ``[name, subtype, docname, anchor, extra, qualifier, descr]``.

        The items in this sequence have the following meaning:

        - `name` -- the name of the index entry to be displayed
        - `subtype` -- sub-entry related type:
          - ``0`` -- normal entry
          - ``1`` -- entry with sub-entries
          - ``2`` -- sub-entry
        - `docname` -- docname where the entry is located
        - `anchor` -- anchor for the entry within `docname`
        - `extra` -- extra info for the entry
        - `qualifier` -- qualifier for the description
        - `descr` -- description for the entry

        Qualifier and description are not rendered by some builders, such as
        the LaTeX builder.
        """

        content = {}
        items = ((name, dispname, typ, docname, anchor)
                 for name, dispname, typ, docname, anchor, prio
                 in self.domain.get_objects())
        items = sorted(items, key=lambda item: item[0])
        for name, dispname, typ, docname, anchor in items:
            lis = content.setdefault('Recipe', [])
            lis.append((
                dispname, 0, docname,
                anchor,
                docname, '', typ
            ))
        re = [(k, v) for k, v in sorted(content.items())]

        return (re, True)


class RecipeDomain(Domain):

    name = 'rcp'
    label = 'Recipe Sample'

    roles = {
        'reref': XRefRole()
    }

    directives = {
        'recipe': RecipeDirective,
    }

    indices = {
        RecipeIndex,
        IngredientIndex
    }

    initial_data = {
        'objects': [],  # object list
        'obj2ingredient': {},  # name -> object
    }

    def get_full_qualified_name(self, node):
        """Return full qualified name for a given node"""
        return "{}.{}.{}".format('rcp',
                                 type(node).__name__,
                                 node.arguments[0])

    def get_objects(self):
        for obj in self.data['objects']:
            yield(obj)

    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
                     contnode):

        match = [(docname, anchor)
                 for name, sig, typ, docname, anchor, prio
                 in self.get_objects() if sig == target]

        if len(match) > 0:
            todocname = match[0][0]
            targ = match[0][1]

            return make_refnode(builder, fromdocname, todocname, targ,
                                contnode, targ)
        else:
            print("Awww, found nothing")
            return None


def setup(app):
    app.add_domain(RecipeDomain)

    StandardDomain.initial_data['labels']['recipeindex'] = (
        'rcp-rcp', '', 'Recipe Index')
    StandardDomain.initial_data['labels']['ingredientindex'] = (
        'rcp-ing', '', 'Ingredient Index')

    StandardDomain.initial_data['anonlabels']['recipeindex'] = (
        'rcp-rcp', '')
    StandardDomain.initial_data['anonlabels']['ingredientindex'] = (
        'rcp-ing', '')

    return {'version': '0.1'}   # identifies the version of our extension

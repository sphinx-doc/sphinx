#
# ElementTree
# $Id$
#
# light-weight XML support for Python 2.2 and later.
#
# history:
# 2001-10-20 fl   created (from various sources)
# 2001-11-01 fl   return root from parse method
# 2002-02-16 fl   sort attributes in lexical order
# 2002-04-06 fl   TreeBuilder refactoring, added PythonDoc markup
# 2002-05-01 fl   finished TreeBuilder refactoring
# 2002-07-14 fl   added basic namespace support to ElementTree.write
# 2002-07-25 fl   added QName attribute support
# 2002-10-20 fl   fixed encoding in write
# 2002-11-24 fl   changed default encoding to ascii; fixed attribute encoding
# 2002-11-27 fl   accept file objects or file names for parse/write
# 2002-12-04 fl   moved XMLTreeBuilder back to this module
# 2003-01-11 fl   fixed entity encoding glitch for us-ascii
# 2003-02-13 fl   added XML literal factory
# 2003-02-21 fl   added ProcessingInstruction/PI factory
# 2003-05-11 fl   added tostring/fromstring helpers
# 2003-05-26 fl   added ElementPath support
# 2003-07-05 fl   added makeelement factory method
# 2003-07-28 fl   added more well-known namespace prefixes
# 2003-08-15 fl   fixed typo in ElementTree.findtext (Thomas Dartsch)
# 2003-09-04 fl   fall back on emulator if ElementPath is not installed
# 2003-10-31 fl   markup updates
# 2003-11-15 fl   fixed nested namespace bug
# 2004-03-28 fl   added XMLID helper
# 2004-06-02 fl   added default support to findtext
# 2004-06-08 fl   fixed encoding of non-ascii element/attribute names
# 2004-08-23 fl   take advantage of post-2.1 expat features
# 2004-09-03 fl   made Element class visible; removed factory
# 2005-02-01 fl   added iterparse implementation
# 2005-03-02 fl   fixed iterparse support for pre-2.2 versions
# 2005-11-12 fl   added tostringlist/fromstringlist helpers
# 2006-07-05 fl   merged in selected changes from the 1.3 sandbox
# 2006-07-05 fl   removed support for 2.1 and earlier
# 2007-06-21 fl   added deprecation/future warnings
# 2007-08-25 fl   added doctype hook, added parser version attribute etc
# 2007-08-26 fl   added new serializer code (better namespace handling, etc)
# 2007-08-27 fl   warn for broken /tag searches on tree level
# 2007-09-02 fl   added html/text methods to serializer (experimental)
# 2007-09-05 fl   added method argument to tostring/tostringlist
# 2007-09-06 fl   improved error handling
#
# Copyright (c) 1999-2007 by Fredrik Lundh.  All rights reserved.
#
# fredrik@pythonware.com
# http://www.pythonware.com
#
# --------------------------------------------------------------------
# The ElementTree toolkit is
#
# Copyright (c) 1999-2007 by Fredrik Lundh
#
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# and will comply with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and
# its associated documentation for any purpose and without fee is
# hereby granted, provided that the above copyright notice appears in
# all copies, and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of
# Secret Labs AB or the author not be used in advertising or publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANT-
# ABILITY AND FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR
# BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
# --------------------------------------------------------------------

from __future__ import generators

__all__ = [
    # public symbols
    "Comment",
    "dump",
    "Element", "ElementTree",
    "fromstring", "fromstringlist",
    "iselement", "iterparse",
    "parse", "ParseError",
    "PI", "ProcessingInstruction",
    "QName",
    "SubElement",
    "tostring", "tostringlist",
    "TreeBuilder",
    "VERSION",
    "XML",
    "XMLParser", "XMLTreeBuilder",
    ]

##
# The <b>Element</b> type is a flexible container object, designed to
# store hierarchical data structures in memory. The type can be
# described as a cross between a list and a dictionary.
# <p>
# Each element has a number of properties associated with it:
# <ul>
# <li>a <i>tag</i>. This is a string identifying what kind of data
# this element represents (the element type, in other words).</li>
# <li>a number of <i>attributes</i>, stored in a Python dictionary.</li>
# <li>a <i>text</i> string.</li>
# <li>an optional <i>tail</i> string.</li>
# <li>a number of <i>child elements</i>, stored in a Python sequence</li>
# </ul>
#
# To create an element instance, use the {@link #Element} constructor
# or the {@link #SubElement} factory function.
# <p>
# The {@link #ElementTree} class can be used to wrap an element
# structure, and convert it from and to XML.
##

import sys, re

class _SimpleElementPath(object):
    # emulate pre-1.2 find/findtext/findall behaviour
    def find(self, element, tag):
        for elem in element:
            if elem.tag == tag:
                return elem
        return None
    def findtext(self, element, tag, default=None):
        for elem in element:
            if elem.tag == tag:
                return elem.text or ""
        return default
    def findall(self, element, tag):
        if tag[:3] == ".//":
            return element.getiterator(tag[3:])
        result = []
        for elem in element:
            if elem.tag == tag:
                result.append(elem)
        return result

try:
    import ElementPath
except ImportError:
    # FIXME: issue warning in this case?
    ElementPath = _SimpleElementPath()

VERSION = "1.3a2"

class ParseError(SyntaxError):
    pass

# --------------------------------------------------------------------

##
# Checks if an object appears to be a valid element object.
#
# @param An element instance.
# @return A true value if this is an element object.
# @defreturn flag

def iselement(element):
    # FIXME: not sure about this; might be a better idea to look
    # for tag/attrib/text attributes
    return isinstance(element, Element) or hasattr(element, "tag")

##
# Element class.  This class defines the Element interface, and
# provides a reference implementation of this interface.
# <p>
# The element name, attribute names, and attribute values can be
# either 8-bit ASCII strings or Unicode strings.
#
# @param tag The element name.
# @param attrib An optional dictionary, containing element attributes.
# @param **extra Additional attributes, given as keyword arguments.
# @see Element
# @see SubElement
# @see Comment
# @see ProcessingInstruction

class Element(object):
    # <tag attrib>text<child/>...</tag>tail

    ##
    # (Attribute) Element tag.

    tag = None

    ##
    # (Attribute) Element attribute dictionary.  Where possible, use
    # {@link #Element.get},
    # {@link #Element.set},
    # {@link #Element.keys}, and
    # {@link #Element.items} to access
    # element attributes.

    attrib = None

    ##
    # (Attribute) Text before first subelement.  This is either a
    # string or the value None, if there was no text.

    text = None

    ##
    # (Attribute) Text after this element's end tag, but before the
    # next sibling element's start tag.  This is either a string or
    # the value None, if there was no text.

    tail = None # text after end tag, if any

    def __init__(self, tag, attrib={}, **extra):
        attrib = attrib.copy()
        attrib.update(extra)
        self.tag = tag
        self.attrib = attrib
        self._children = []

    def __repr__(self):
        return "<Element %s at %x>" % (repr(self.tag), id(self))

    ##
    # Creates a new element object of the same type as this element.
    #
    # @param tag Element tag.
    # @param attrib Element attributes, given as a dictionary.
    # @return A new element instance.

    def makeelement(self, tag, attrib):
        return Element(tag, attrib)

    ##
    # Returns the number of subelements.
    #
    # @return The number of subelements.

    def __len__(self):
        return len(self._children)

    def __nonzero__(self):
        import warnings
        warnings.warn(
            "The behavior of this method will change in future versions. "
            "Use specific 'len(elem)' or 'elem is not None' test instead.",
            FutureWarning
            )
        return len(self._children) != 0 # emulate old behaviour

    ##
    # Returns the given subelement.
    #
    # @param index What subelement to return.
    # @return The given subelement.
    # @exception IndexError If the given element does not exist.

    def __getitem__(self, index):
        return self._children[index]

    ##
    # Replaces the given subelement.
    #
    # @param index What subelement to replace.
    # @param element The new element value.
    # @exception IndexError If the given element does not exist.
    # @exception AssertionError If element is not a valid object.

    def __setitem__(self, index, element):
        assert iselement(element)
        self._children[index] = element

    ##
    # Deletes the given subelement.
    #
    # @param index What subelement to delete.
    # @exception IndexError If the given element does not exist.

    def __delitem__(self, index):
        del self._children[index]

    ##
    # Returns a list containing subelements in the given range.
    #
    # @param start The first subelement to return.
    # @param stop The first subelement that shouldn't be returned.
    # @return A sequence object containing subelements.

    def __getslice__(self, start, stop):
        return self._children[start:stop]

    ##
    # Replaces a number of subelements with elements from a sequence.
    #
    # @param start The first subelement to replace.
    # @param stop The first subelement that shouldn't be replaced.
    # @param elements A sequence object with zero or more elements.
    # @exception AssertionError If a sequence member is not a valid object.

    def __setslice__(self, start, stop, elements):
        for element in elements:
            assert iselement(element)
        self._children[start:stop] = list(elements)

    ##
    # Deletes a number of subelements.
    #
    # @param start The first subelement to delete.
    # @param stop The first subelement to leave in there.

    def __delslice__(self, start, stop):
        del self._children[start:stop]

    ##
    # Adds a subelement to the end of this element.
    #
    # @param element The element to add.
    # @exception AssertionError If a sequence member is not a valid object.

    def append(self, element):
        assert iselement(element)
        self._children.append(element)

    ##
    # Appends subelements from a sequence.
    #
    # @param elements A sequence object with zero or more elements.
    # @exception AssertionError If a subelement is not a valid object.
    # @since 1.3

    def extend(self, elements):
        for element in elements:
            assert iselement(element)
        self._children.extend(elements)

    ##
    # Inserts a subelement at the given position in this element.
    #
    # @param index Where to insert the new subelement.
    # @exception AssertionError If the element is not a valid object.

    def insert(self, index, element):
        assert iselement(element)
        self._children.insert(index, element)

    ##
    # Removes a matching subelement.  Unlike the <b>find</b> methods,
    # this method compares elements based on identity, not on tag
    # value or contents.
    #
    # @param element What element to remove.
    # @exception ValueError If a matching element could not be found.
    # @exception AssertionError If the element is not a valid object.

    def remove(self, element):
        assert iselement(element)
        self._children.remove(element)

    ##
    # (Deprecated) Returns all subelements.  The elements are returned
    # in document order.
    #
    # @return A list of subelements.
    # @defreturn list of Element instances

    def getchildren(self):
        import warnings
        warnings.warn(
            "This method will be removed in future versions. "
            "Use 'list(elem)' or iteration over elem instead.",
            DeprecationWarning
            )
        return self._children

    ##
    # Finds the first matching subelement, by tag name or path.
    #
    # @param path What element to look for.
    # @return The first matching element, or None if no element was found.
    # @defreturn Element or None

    def find(self, path):
        return ElementPath.find(self, path)

    ##
    # Finds text for the first matching subelement, by tag name or path.
    #
    # @param path What element to look for.
    # @param default What to return if the element was not found.
    # @return The text content of the first matching element, or the
    #     default value no element was found.  Note that if the element
    #     has is found, but has no text content, this method returns an
    #     empty string.
    # @defreturn string

    def findtext(self, path, default=None):
        return ElementPath.findtext(self, path, default)

    ##
    # Finds all matching subelements, by tag name or path.
    #
    # @param path What element to look for.
    # @return A list or iterator containing all matching elements,
    #    in document order.
    # @defreturn list of Element instances

    def findall(self, path):
        return ElementPath.findall(self, path)

    ##
    # Resets an element.  This function removes all subelements, clears
    # all attributes, and sets the text and tail attributes to None.

    def clear(self):
        self.attrib.clear()
        self._children = []
        self.text = self.tail = None

    ##
    # Gets an element attribute.
    #
    # @param key What attribute to look for.
    # @param default What to return if the attribute was not found.
    # @return The attribute value, or the default value, if the
    #     attribute was not found.
    # @defreturn string or None

    def get(self, key, default=None):
        return self.attrib.get(key, default)

    ##
    # Sets an element attribute.
    #
    # @param key What attribute to set.
    # @param value The attribute value.

    def set(self, key, value):
        self.attrib[key] = value

    ##
    # Gets a list of attribute names.  The names are returned in an
    # arbitrary order (just like for an ordinary Python dictionary).
    #
    # @return A list of element attribute names.
    # @defreturn list of strings

    def keys(self):
        return self.attrib.keys()

    ##
    # Gets element attributes, as a sequence.  The attributes are
    # returned in an arbitrary order.
    #
    # @return A list of (name, value) tuples for all attributes.
    # @defreturn list of (string, string) tuples

    def items(self):
        return self.attrib.items()

    ##
    # Creates a tree iterator.  The iterator loops over this element
    # and all subelements, in document order, and returns all elements
    # with a matching tag.
    # <p>
    # If the tree structure is modified during iteration, new or removed
    # elements may or may not be included.  To get a stable set, use the
    # list() function on the iterator, and loop over the resulting list.
    #
    # @param tag What tags to look for (default is to return all elements).
    # @return An iterator containing all the matching elements.
    # @defreturn iterator

    def iter(self, tag=None):
        if tag == "*":
            tag = None
        if tag is None or self.tag == tag:
            yield self
        for e in self._children:
            for e in e.iter(tag):
                yield e

    # compatibility (FIXME: preserve list behaviour too? see below)
    getiterator = iter

    # def getiterator(self, tag=None):
    #     return list(tag)

    ##
    # Creates a text iterator.  The iterator loops over this element
    # and all subelements, in document order, and returns all inner
    # text.
    #
    # @return An iterator containing all inner text.
    # @defreturn iterator

    def itertext(self):
        if self.text:
            yield self.text
        for e in self:
            for s in e.itertext():
                yield s
            if e.tail:
                yield e.tail

# compatibility
_Element = _ElementInterface = Element

##
# Subelement factory.  This function creates an element instance, and
# appends it to an existing element.
# <p>
# The element name, attribute names, and attribute values can be
# either 8-bit ASCII strings or Unicode strings.
#
# @param parent The parent element.
# @param tag The subelement name.
# @param attrib An optional dictionary, containing element attributes.
# @param **extra Additional attributes, given as keyword arguments.
# @return An element instance.
# @defreturn Element

def SubElement(parent, tag, attrib={}, **extra):
    attrib = attrib.copy()
    attrib.update(extra)
    element = parent.makeelement(tag, attrib)
    parent.append(element)
    return element

##
# Comment element factory.  This factory function creates a special
# element that will be serialized as an XML comment by the standard
# serializer.
# <p>
# The comment string can be either an 8-bit ASCII string or a Unicode
# string.
#
# @param text A string containing the comment string.
# @return An element instance, representing a comment.
# @defreturn Element

def Comment(text=None):
    element = Element(Comment)
    element.text = text
    return element

##
# PI element factory.  This factory function creates a special element
# that will be serialized as an XML processing instruction by the standard
# serializer.
#
# @param target A string containing the PI target.
# @param text A string containing the PI contents, if any.
# @return An element instance, representing a PI.
# @defreturn Element

def ProcessingInstruction(target, text=None):
    element = Element(ProcessingInstruction)
    element.text = target
    if text:
        element.text = element.text + " " + text
    return element

PI = ProcessingInstruction

##
# QName wrapper.  This can be used to wrap a QName attribute value, in
# order to get proper namespace handling on output.
#
# @param text A string containing the QName value, in the form {uri}local,
#     or, if the tag argument is given, the URI part of a QName.
# @param tag Optional tag.  If given, the first argument is interpreted as
#     an URI, and this argument is interpreted as a local name.
# @return An opaque object, representing the QName.

class QName(object):
    def __init__(self, text_or_uri, tag=None):
        if tag:
            text_or_uri = "{%s}%s" % (text_or_uri, tag)
        self.text = text_or_uri
    def __str__(self):
        return self.text
    def __hash__(self):
        return hash(self.text)
    def __cmp__(self, other):
        if isinstance(other, QName):
            return cmp(self.text, other.text)
        return cmp(self.text, other)

# --------------------------------------------------------------------

##
# ElementTree wrapper class.  This class represents an entire element
# hierarchy, and adds some extra support for serialization to and from
# standard XML.
#
# @param element Optional root element.
# @keyparam file Optional file handle or file name.  If given, the
#     tree is initialized with the contents of this XML file.

class ElementTree(object):

    def __init__(self, element=None, file=None):
        assert element is None or iselement(element)
        self._root = element # first node
        if file:
            self.parse(file)

    ##
    # Gets the root element for this tree.
    #
    # @return An element instance.
    # @defreturn Element

    def getroot(self):
        return self._root

    ##
    # Replaces the root element for this tree.  This discards the
    # current contents of the tree, and replaces it with the given
    # element.  Use with care.
    #
    # @param element An element instance.

    def _setroot(self, element):
        assert iselement(element)
        self._root = element

    ##
    # Loads an external XML document into this element tree.
    #
    # @param source A file name or file object.
    # @keyparam parser An optional parser instance.  If not given, the
    #     standard {@link XMLParser} parser is used.
    # @return The document root element.
    # @defreturn Element

    def parse(self, source, parser=None):
        if not hasattr(source, "read"):
            source = open(source, "rb")
        if not parser:
            parser = XMLParser(target=TreeBuilder())
        while 1:
            data = source.read(32768)
            if not data:
                break
            parser.feed(data)
        self._root = parser.close()
        return self._root

    ##
    # Creates a tree iterator for the root element.  The iterator loops
    # over all elements in this tree, in document order.
    #
    # @param tag What tags to look for (default is to return all elements)
    # @return An iterator.
    # @defreturn iterator

    def iter(self, tag=None):
        assert self._root is not None
        return self._root.iter(tag)

    getiterator = iter

    ##
    # Finds the first toplevel element with given tag.
    # Same as getroot().find(path).
    #
    # @param path What element to look for.
    # @return The first matching element, or None if no element was found.
    # @defreturn Element or None

    def find(self, path):
        assert self._root is not None
        if path[:1] == "/":
            path = "." + path
            import warnings
            warnings.warn(
                "This search is broken in 1.3 and earlier; if you rely "
                "on the current behaviour, change it to %r" % path,
                FutureWarning
                )
        return self._root.find(path)

    ##
    # Finds the element text for the first toplevel element with given
    # tag.  Same as getroot().findtext(path).
    #
    # @param path What toplevel element to look for.
    # @param default What to return if the element was not found.
    # @return The text content of the first matching element, or the
    #     default value no element was found.  Note that if the element
    #     has is found, but has no text content, this method returns an
    #     empty string.
    # @defreturn string

    def findtext(self, path, default=None):
        assert self._root is not None
        if path[:1] == "/":
            path = "." + path
            import warnings
            warnings.warn(
                "This search is broken in 1.3 and earlier; if you rely "
                "on the current behaviour, change it to %r" % path,
                FutureWarning
                )
        return self._root.findtext(path, default)

    ##
    # Finds all toplevel elements with the given tag.
    # Same as getroot().findall(path).
    #
    # @param path What element to look for.
    # @return A list or iterator containing all matching elements,
    #    in document order.
    # @defreturn list of Element instances

    def findall(self, path):
        assert self._root is not None
        if path[:1] == "/":
            path = "." + path
            import warnings
            warnings.warn(
                "This search is broken in 1.3 and earlier; if you rely "
                "on the current behaviour, change it to %r" % path,
                FutureWarning
                )
        return self._root.findall(path)

    ##
    # Writes the element tree to a file, as XML.
    #
    # @param file A file name, or a file object opened for writing.
    # @keyparam encoding Optional output encoding (default is US-ASCII).
    # @keyparam method Optional output method ("xml" or "html"; default
    #     is "xml".
    # @keyparam xml_declaration Controls if an XML declaration should
    #     be added to the file.  Use False for never, True for always,
    #     None for only if not US-ASCII or UTF-8.  None is default.

    def write(self, file,
              # keyword arguments
              encoding="us-ascii",
              xml_declaration=None,
              default_namespace=None,
              method=None):
        assert self._root is not None
        if not hasattr(file, "write"):
            file = open(file, "wb")
        write = file.write
        if not method:
            method = "xml"
        if not encoding:
            encoding = "us-ascii"
        elif xml_declaration or (xml_declaration is None and
                                 encoding not in ("utf-8", "us-ascii")):
            write("<?xml version='1.0' encoding='%s'?>\n" % encoding)
        if method == "text":
            _serialize_text(write, self._root, encoding)
        else:
            qnames, namespaces = _namespaces(
                self._root, encoding, default_namespace
                )
            if method == "xml":
                _serialize_xml(
                    write, self._root, encoding, qnames, namespaces
                    )
            elif method == "html":
                _serialize_html(
                    write, self._root, encoding, qnames, namespaces
                    )
            else:
                raise ValueError("unknown method %r" % method)

# --------------------------------------------------------------------
# serialization support

def _namespaces(elem, encoding, default_namespace=None):
    # identify namespaces used in this tree

    # maps qnames to *encoded* prefix:local names
    qnames = {None: None}

    # maps uri:s to prefixes
    namespaces = {}
    if default_namespace:
        namespaces[default_namespace] = ""

    def encode(text):
        return text.encode(encoding)

    def add_qname(qname):
        # calculate serialized qname representation
        try:
            if qname[:1] == "{":
                uri, tag = qname[1:].split("}", 1)
                prefix = namespaces.get(uri)
                if prefix is None:
                    prefix = _namespace_map.get(uri)
                    if prefix is None:
                        prefix = "ns%d" % len(namespaces)
                    if prefix != "xml":
                        namespaces[uri] = prefix
                if prefix:
                    qnames[qname] = encode("%s:%s" % (prefix, tag))
                else:
                    qnames[qname] = encode(tag) # default element
            else:
                if default_namespace:
                    # FIXME: can this be handled in XML 1.0?
                    raise ValueError(
                        "cannot use non-qualified names with "
                        "default_namespace option"
                        )
                qnames[qname] = encode(qname)
        except TypeError:
            _raise_serialization_error(qname)

    # populate qname and namespaces table
    try:
        iterate = elem.iter
    except AttributeError:
        iterate = elem.getiterator # cET compatibility
    for elem in iterate():
        tag = elem.tag
        if isinstance(tag, QName) and tag.text not in qnames:
            add_qname(tag.text)
        elif isinstance(tag, basestring):
            if tag not in qnames:
                add_qname(tag)
        elif tag is not None and tag is not Comment and tag is not PI:
            _raise_serialization_error(tag)
        for key, value in elem.items():
            if isinstance(key, QName):
                key = key.text
            if key not in qnames:
                add_qname(key)
            if isinstance(value, QName) and value.text not in qnames:
                add_qname(value.text)
        text = elem.text
        if isinstance(text, QName) and text.text not in qnames:
            add_qname(text.text)
    return qnames, namespaces

def _serialize_xml(write, elem, encoding, qnames, namespaces):
    tag = elem.tag
    text = elem.text
    if tag is Comment:
        write("<!--%s-->" % _escape_cdata(text, encoding))
    elif tag is ProcessingInstruction:
        write("<?%s?>" % _escape_cdata(text, encoding))
    else:
        tag = qnames[tag]
        if tag is None:
            if text:
                write(_escape_cdata(text, encoding))
            for e in elem:
                _serialize_xml(write, e, encoding, qnames, None)
        else:
            write("<" + tag)
            items = elem.items()
            if items or namespaces:
                items.sort() # lexical order
                for k, v in items:
                    if isinstance(k, QName):
                        k = k.text
                    if isinstance(v, QName):
                        v = qnames[v.text]
                    else:
                        v = _escape_attrib(v, encoding)
                    write(" %s=\"%s\"" % (qnames[k], v))
                if namespaces:
                    items = namespaces.items()
                    items.sort(key=lambda x: x[1]) # sort on prefix
                    for v, k in items:
                        if k:
                            k = ":" + k
                        write(" xmlns%s=\"%s\"" % (
                            k.encode(encoding),
                            _escape_attrib(v, encoding)
                            ))
            if text or len(elem):
                write(">")
                if text:
                    write(_escape_cdata(text, encoding))
                for e in elem:
                    _serialize_xml(write, e, encoding, qnames, None)
                write("</" + tag + ">")
            else:
                write(" />")
    if elem.tail:
        write(_escape_cdata(elem.tail, encoding))

HTML_EMPTY = ("area", "base", "basefont", "br", "col", "frame", "hr",
              "img", "input", "isindex", "link", "meta" "param")

try:
    HTML_EMPTY = set(HTML_EMPTY)
except NameError:
    pass

def _serialize_html(write, elem, encoding, qnames, namespaces):
    tag = elem.tag
    text = elem.text
    if tag is Comment:
        write("<!--%s-->" % _escape_cdata(text, encoding))
    elif tag is ProcessingInstruction:
        write("<?%s?>" % _escape_cdata(text, encoding))
    else:
        tag = qnames[tag]
        if tag is None:
            if text:
                write(_escape_cdata(text, encoding))
            for e in elem:
                _serialize_html(write, e, encoding, qnames, None)
        else:
            write("<" + tag)
            items = elem.items()
            if items or namespaces:
                items.sort() # lexical order
                for k, v in items:
                    if isinstance(k, QName):
                        k = k.text
                    if isinstance(v, QName):
                        v = qnames[v.text]
                    else:
                        v = _escape_attrib_html(v, encoding)
                    # FIXME: handle boolean attributes
                    write(" %s=\"%s\"" % (qnames[k], v))
                if namespaces:
                    items = namespaces.items()
                    items.sort(key=lambda x: x[1]) # sort on prefix
                    for v, k in items:
                        if k:
                            k = ":" + k
                        write(" xmlns%s=\"%s\"" % (
                            k.encode(encoding),
                            _escape_attrib(v, encoding)
                            ))
            write(">")
            tag = tag.lower()
            if text:
                if tag == "script" or tag == "style":
                    write(_encode(text, encoding))
                else:
                    write(_escape_cdata(text, encoding))
            for e in elem:
                _serialize_html(write, e, encoding, qnames, None)
            if tag not in HTML_EMPTY:
                write("</" + tag + ">")
    if elem.tail:
        write(_escape_cdata(elem.tail, encoding))

def _serialize_text(write, elem, encoding):
    for part in elem.itertext():
        write(part.encode(encoding))
    if elem.tail:
        write(elem.tail.encode(encoding))

##
# Registers a namespace prefix.  The registry is global, and any
# existing mapping for either the given prefix or the namespace URI
# will be removed.
#
# @param prefix Namespace prefix.
# @param uri Namespace uri.  Tags and attributes in this namespace
#     will be serialized with the given prefix, if at all possible.
# @raise ValueError If the prefix is reserved, or is otherwise
#     invalid.

def register_namespace(prefix, uri):
    if re.match("ns\d+$", prefix):
        raise ValueError("Prefix format reserved for internal use")
    for k, v in _namespace_map.items():
        if k == uri or v == prefix:
            del _namespace_map[k]
    _namespace_map[uri] = prefix

_namespace_map = {
    # "well-known" namespace prefixes
    "http://www.w3.org/XML/1998/namespace": "xml",
    "http://www.w3.org/1999/xhtml": "html",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://schemas.xmlsoap.org/wsdl/": "wsdl",
    # xml schema
    "http://www.w3.org/2001/XMLSchema": "xs",
    "http://www.w3.org/2001/XMLSchema-instance": "xsi",
    # dublic core
    "http://purl.org/dc/elements/1.1/": "dc",
}

def _raise_serialization_error(text):
    raise TypeError(
        "cannot serialize %r (type %s)" % (text, type(text).__name__)
        )

def _encode(text, encoding):
    try:
        return text.encode(encoding, "xmlcharrefreplace")
    except (TypeError, AttributeError):
        _raise_serialization_error(text)

def _escape_cdata(text, encoding):
    # escape character data
    try:
        # it's worth avoiding do-nothing calls for strings that are
        # shorter than 500 character, or so.  assume that's, by far,
        # the most common case in most applications.
        if "&" in text:
            text = text.replace("&", "&amp;")
        if "<" in text:
            text = text.replace("<", "&lt;")
        if ">" in text:
            text = text.replace(">", "&gt;")
        return text.encode(encoding, "xmlcharrefreplace")
    except (TypeError, AttributeError):
        _raise_serialization_error(text)

def _escape_attrib(text, encoding):
    # escape attribute value
    try:
        if "&" in text:
            text = text.replace("&", "&amp;")
        if "<" in text:
            text = text.replace("<", "&lt;")
        if ">" in text:
            text = text.replace(">", "&gt;")
        if "\"" in text:
            text = text.replace("\"", "&quot;")
        if "\n" in text:
            text = text.replace("\n", "&#10;")
        return text.encode(encoding, "xmlcharrefreplace")
    except (TypeError, AttributeError):
        _raise_serialization_error(text)

def _escape_attrib_html(text, encoding):
    # escape attribute value
    try:
        if "&" in text:
            text = text.replace("&", "&amp;")
        if ">" in text:
            text = text.replace(">", "&gt;")
        if "\"" in text:
            text = text.replace("\"", "&quot;")
        return text.encode(encoding, "xmlcharrefreplace")
    except (TypeError, AttributeError):
        _raise_serialization_error(text)

# --------------------------------------------------------------------

##
# Generates a string representation of an XML element, including all
# subelements.
#
# @param element An Element instance.
# @return An encoded string containing the XML data.
# @defreturn string

def tostring(element, encoding=None, method=None):
    class dummy:
        pass
    data = []
    file = dummy()
    file.write = data.append
    ElementTree(element).write(file, encoding, method=method)
    return "".join(data)

##
# Generates a string representation of an XML element, including all
# subelements.  The string is returned as a sequence of string fragments.
#
# @param element An Element instance.
# @return A sequence object containing the XML data.
# @defreturn sequence
# @since 1.3

def tostringlist(element, encoding=None):
    class dummy:
        pass
    data = []
    file = dummy()
    file.write = data.append
    ElementTree(element).write(file, encoding)
    # FIXME: merge small fragments into larger parts
    return data

##
# Writes an element tree or element structure to sys.stdout.  This
# function should be used for debugging only.
# <p>
# The exact output format is implementation dependent.  In this
# version, it's written as an ordinary XML file.
#
# @param elem An element tree or an individual element.

def dump(elem):
    # debugging
    if not isinstance(elem, ElementTree):
        elem = ElementTree(elem)
    elem.write(sys.stdout)
    tail = elem.getroot().tail
    if not tail or tail[-1] != "\n":
        sys.stdout.write("\n")

# --------------------------------------------------------------------
# parsing

##
# Parses an XML document into an element tree.
#
# @param source A filename or file object containing XML data.
# @param parser An optional parser instance.  If not given, the
#     standard {@link XMLParser} parser is used.
# @return An ElementTree instance

def parse(source, parser=None):
    tree = ElementTree()
    tree.parse(source, parser)
    return tree

##
# Parses an XML document into an element tree incrementally, and reports
# what's going on to the user.
#
# @param source A filename or file object containing XML data.
# @param events A list of events to report back.  If omitted, only "end"
#     events are reported.
# @param parser An optional parser instance.  If not given, the
#     standard {@link XMLParser} parser is used.
# @return A (event, elem) iterator.

def iterparse(source, events=None, parser=None):
    if not hasattr(source, "read"):
        source = open(source, "rb")
    if not parser:
        parser = XMLParser(target=TreeBuilder())
    return _IterParseIterator(source, events, parser)

class _IterParseIterator(object):

    def __init__(self, source, events, parser):
        self._file = source
        self._events = []
        self._index = 0
        self.root = self._root = None
        self._parser = parser
        # wire up the parser for event reporting
        parser = self._parser._parser
        append = self._events.append
        if events is None:
            events = ["end"]
        for event in events:
            if event == "start":
                try:
                    parser.ordered_attributes = 1
                    parser.specified_attributes = 1
                    def handler(tag, attrib_in, event=event, append=append,
                                start=self._parser._start_list):
                        append((event, start(tag, attrib_in)))
                    parser.StartElementHandler = handler
                except AttributeError:
                    def handler(tag, attrib_in, event=event, append=append,
                                start=self._parser._start):
                        append((event, start(tag, attrib_in)))
                    parser.StartElementHandler = handler
            elif event == "end":
                def handler(tag, event=event, append=append,
                            end=self._parser._end):
                    append((event, end(tag)))
                parser.EndElementHandler = handler
            elif event == "start-ns":
                def handler(prefix, uri, event=event, append=append):
                    try:
                        uri = uri.encode("ascii")
                    except UnicodeError:
                        pass
                    append((event, (prefix or "", uri)))
                parser.StartNamespaceDeclHandler = handler
            elif event == "end-ns":
                def handler(prefix, event=event, append=append):
                    append((event, None))
                parser.EndNamespaceDeclHandler = handler

    def next(self):
        while 1:
            try:
                item = self._events[self._index]
            except IndexError:
                if self._parser is None:
                    self.root = self._root
                    raise StopIteration
                # load event buffer
                del self._events[:]
                self._index = 0
                data = self._file.read(16384)
                if data:
                    self._parser.feed(data)
                else:
                    self._root = self._parser.close()
                    self._parser = None
            else:
                self._index = self._index + 1
                return item

    def __iter__(self):
        return self

##
# Parses an XML document from a string constant.  This function can
# be used to embed "XML literals" in Python code.
#
# @param source A string containing XML data.
# @param parser An optional parser instance.  If not given, the
#     standard {@link XMLParser} parser is used.
# @return An Element instance.
# @defreturn Element

def XML(text, parser=None):
    if not parser:
        parser = XMLParser(target=TreeBuilder())
    parser.feed(text)
    return parser.close()

##
# Parses an XML document from a string constant, and also returns
# a dictionary which maps from element id:s to elements.
#
# @param source A string containing XML data.
# @param parser An optional parser instance.  If not given, the
#     standard {@link XMLParser} parser is used.
# @return A tuple containing an Element instance and a dictionary.
# @defreturn (Element, dictionary)

def XMLID(text, parser=None):
    if not parser:
        parser = XMLParser(target=TreeBuilder())
    parser.feed(text)
    tree = parser.close()
    ids = {}
    for elem in tree.getiterator():
        id = elem.get("id")
        if id:
            ids[id] = elem
    return tree, ids

##
# Parses an XML document from a string constant.  Same as {@link #XML}.
#
# @def fromstring(text)
# @param source A string containing XML data.
# @return An Element instance.
# @defreturn Element

fromstring = XML

##
# Parses an XML document from a sequence of string fragments.
#
# @param sequence A list or other sequence containing XML data fragments.
# @param parser An optional parser instance.  If not given, the
#     standard {@link XMLParser} parser is used.
# @return An Element instance.
# @defreturn Element
# @since 1.3

def fromstringlist(sequence, parser=None):
    if not parser:
        parser = XMLParser(target=TreeBuilder())
    for text in sequence:
        parser.feed(text)
    return parser.close()

# --------------------------------------------------------------------

##
# Generic element structure builder.  This builder converts a sequence
# of {@link #TreeBuilder.start}, {@link #TreeBuilder.data}, and {@link
# #TreeBuilder.end} method calls to a well-formed element structure.
# <p>
# You can use this class to build an element structure using a custom XML
# parser, or a parser for some other XML-like format.
#
# @param element_factory Optional element factory.  This factory
#    is called to create new Element instances, as necessary.

class TreeBuilder(object):

    def __init__(self, element_factory=None):
        self._data = [] # data collector
        self._elem = [] # element stack
        self._last = None # last element
        self._tail = None # true if we're after an end tag
        if element_factory is None:
            element_factory = Element
        self._factory = element_factory

    ##
    # Flushes the builder buffers, and returns the toplevel document
    # element.
    #
    # @return An Element instance.
    # @defreturn Element

    def close(self):
        assert len(self._elem) == 0, "missing end tags"
        assert self._last != None, "missing toplevel element"
        return self._last

    def _flush(self):
        if self._data:
            if self._last is not None:
                text = "".join(self._data)
                if self._tail:
                    assert self._last.tail is None, "internal error (tail)"
                    self._last.tail = text
                else:
                    assert self._last.text is None, "internal error (text)"
                    self._last.text = text
            self._data = []

    ##
    # Adds text to the current element.
    #
    # @param data A string.  This should be either an 8-bit string
    #    containing ASCII text, or a Unicode string.

    def data(self, data):
        self._data.append(data)

    ##
    # Opens a new element.
    #
    # @param tag The element name.
    # @param attrib A dictionary containing element attributes.
    # @return The opened element.
    # @defreturn Element

    def start(self, tag, attrs):
        self._flush()
        self._last = elem = self._factory(tag, attrs)
        if self._elem:
            self._elem[-1].append(elem)
        self._elem.append(elem)
        self._tail = 0
        return elem

    ##
    # Closes the current element.
    #
    # @param tag The element name.
    # @return The closed element.
    # @defreturn Element

    def end(self, tag):
        self._flush()
        self._last = self._elem.pop()
        assert self._last.tag == tag,\
               "end tag mismatch (expected %s, got %s)" % (
                   self._last.tag, tag)
        self._tail = 1
        return self._last

##
# Element structure builder for XML source data, based on the
# <b>expat</b> parser.
#
# @keyparam target Target object.  If omitted, the builder uses an
#     instance of the standard {@link #TreeBuilder} class.
# @keyparam html Predefine HTML entities.  This flag is not supported
#     by the current implementation.
# @keyparam encoding Optional encoding.  If given, the value overrides
#     the encoding specified in the XML file.
# @see #ElementTree
# @see #TreeBuilder

class XMLParser(object):

    def __init__(self, html=0, target=None, encoding=None):
        try:
            from xml.parsers import expat
        except ImportError:
            try:
                import pyexpat; expat = pyexpat
            except ImportError:
                raise ImportError(
                    "No module named expat; use SimpleXMLTreeBuilder instead"
                    )
        parser = expat.ParserCreate(encoding, "}")
        if target is None:
            target = TreeBuilder()
        # underscored names are provided for compatibility only
        self.parser = self._parser = parser
        self.target = self._target = target
        self._error = expat.error
        self._names = {} # name memo cache
        # callbacks
        parser.DefaultHandlerExpand = self._default
        parser.StartElementHandler = self._start
        parser.EndElementHandler = self._end
        parser.CharacterDataHandler = self._data
        # let expat do the buffering, if supported
        try:
            self._parser.buffer_text = 1
        except AttributeError:
            pass
        # use new-style attribute handling, if supported
        try:
            self._parser.ordered_attributes = 1
            self._parser.specified_attributes = 1
            parser.StartElementHandler = self._start_list
        except AttributeError:
            pass
        self._doctype = None
        self.entity = {}
        try:
            self.version = "Expat %d.%d.%d" % expat.version_info
        except AttributeError:
            pass # unknown

    def _raiseerror(self, value):
        err = ParseError(value)
        err.code = value.code
        err.position = value.lineno, value.offset
        raise err

    if sys.version_info >= (3, 0):
        def _fixtext(self, text):
            return text
    else:
        def _fixtext(self, text):
            # convert text string to ascii, if possible
            try:
                return text.encode("ascii")
            except UnicodeError:
                return text

    def _fixname(self, key):
        # expand qname, and convert name string to ascii, if possible
        try:
            name = self._names[key]
        except KeyError:
            name = key
            if "}" in name:
                name = "{" + name
            self._names[key] = name = self._fixtext(name)
        return name

    def _start(self, tag, attrib_in):
        fixname = self._fixname
        fixtext = self._fixtext
        tag = fixname(tag)
        attrib = {}
        for key, value in attrib_in.items():
            attrib[fixname(key)] = fixtext(value)
        return self.target.start(tag, attrib)

    def _start_list(self, tag, attrib_in):
        fixname = self._fixname
        fixtext = self._fixtext
        tag = fixname(tag)
        attrib = {}
        if attrib_in:
            for i in range(0, len(attrib_in), 2):
                attrib[fixname(attrib_in[i])] = fixtext(attrib_in[i+1])
        return self.target.start(tag, attrib)

    def _data(self, text):
        return self.target.data(self._fixtext(text))

    def _end(self, tag):
        return self.target.end(self._fixname(tag))

    def _default(self, text):
        prefix = text[:1]
        if prefix == "&":
            # deal with undefined entities
            try:
                self.target.data(self.entity[text[1:-1]])
            except KeyError:
                from xml.parsers import expat
                err = expat.error(
                    "undefined entity %s: line %d, column %d" %
                    (text, self._parser.ErrorLineNumber,
                    self._parser.ErrorColumnNumber)
                    )
                err.code = 11 # XML_ERROR_UNDEFINED_ENTITY
                err.lineno = self._parser.ErrorLineNumber
                err.offset = self._parser.ErrorColumnNumber
                raise err
        elif prefix == "<" and text[:9] == "<!DOCTYPE":
            self._doctype = [] # inside a doctype declaration
        elif self._doctype is not None:
            # parse doctype contents
            if prefix == ">":
                self._doctype = None
                return
            text = text.strip()
            if not text:
                return
            self._doctype.append(text)
            n = len(self._doctype)
            if n > 2:
                type = self._doctype[1]
                if type == "PUBLIC" and n == 4:
                    name, type, pubid, system = self._doctype
                elif type == "SYSTEM" and n == 3:
                    name, type, system = self._doctype
                    pubid = None
                else:
                    return
                if pubid:
                    pubid = pubid[1:-1]
                if hasattr(self.target, "doctype"):
                    self.target.doctype(name, pubid, system[1:-1])
                self._doctype = None

    ##
    # Feeds data to the parser.
    #
    # @param data Encoded data.

    def feed(self, data):
        try:
            self._parser.Parse(data, 0)
        except self._error, v:
            self._raiseerror(v)

    ##
    # Finishes feeding data to the parser.
    #
    # @return An element structure.
    # @defreturn Element

    def close(self):
        try:
            self._parser.Parse("", 1) # end of data
        except self._error, v:
            self._raiseerror(v)
        tree = self.target.close()
        del self.target, self._parser # get rid of circular references
        return tree

# compatibility
XMLTreeBuilder = XMLParser

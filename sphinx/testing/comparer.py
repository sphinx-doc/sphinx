import pathlib
import difflib


class PathComparer:
    """
    OS-independent path comparison.

    Windows path sep and posix path sep:

    >>> '\\to\\index' == PathComparer('/to/index')
    True
    >>> '\\to\\index' == PathComparer('/to/index2')
    False

    Windows path with drive letters

    >>> 'C:\\to\\index' == PathComparer('/to/index')
    True
    >>> 'C:\\to\\index' == PathComparer('C:/to/index')
    True
    >>> 'C:\\to\\index' == PathComparer('D:/to/index')
    False
    """
    def __init__(self, path):
        """
        :param str path: path string, it will be cast as pathlib.Path.
        """
        self.path = pathlib.Path(path)

    def __str__(self):
        return self.path.as_posix()

    def __repr__(self):
        return "<{0.__class__.__name__}: '{0}'>".format(self)

    def __eq__(self, other):
        return not bool(self.ldiff(other))

    def diff(self, other):
        """compare self and other.

        When different is not exist, return empty list.

        >>> PathComparer('/to/index').diff('C:\\to\\index')
        []

        When different is exist, return unified diff style list as:

        >>> PathComparer('/to/index').diff('C:\\to\\index2')
        [
           '- C:/to/index'
           '+ C:/to/index2'
           '?            +'
        ]
        """
        return self.ldiff(other)

    def ldiff(self, other):
        return self._diff(
            self.path,
            pathlib.Path(other),
        )

    def rdiff(self, other):
        return self._diff(
            pathlib.Path(other),
            self.path,
        )

    def _diff(self, l, r):
        if l == r:
            return []

        if l.drive or r.drive:
            # If either has a drive letter compare by absolute path
            s_path, o_path = l.absolute().as_posix(), r.absolute().as_posix()
        else:
            s_path, o_path = l.as_posix(), r.as_posix()

        if s_path == o_path:
            return []

        return [line.strip() for line in difflib.Differ().compare([s_path], [o_path])]


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, PathComparer) and op == "==":
        return ['Comparing path:'] + left.ldiff(right)
    if isinstance(right, PathComparer) and op == "==":
        return ['Comparing path:'] + right.rdiff(left)

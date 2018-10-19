# -*- coding: utf-8 -*-
import sys

extensions = ["sphinx.ext.extlinks"]

one, two = sys.version_info[0:2]
extlinks = {
    "issue": ("http://bugs.python.org/issue%s", "issue "),
    "pyurl": ("http://python.org/%s", None),
    "pydoc": (
        lambda pg: "https://docs.python.org/{}.{}/{}".format(one, two, pg),
        lambda pg: pg.split(".")[0].title(),
    ),
}

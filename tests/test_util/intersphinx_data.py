from __future__ import annotations

import zlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

INVENTORY_V1: Final[bytes] = b"""\
# Sphinx inventory version 1
# Project: foo
# Version: 1.0
module mod foo.html
module.cls class foo.html
"""

INVENTORY_V2: Final[bytes] = b"""\
# Sphinx inventory version 2
# Project: foo
# Version: 2.0
# The remainder of this file is compressed with zlib.
""" + zlib.compress(b"""\
module1 py:module 0 foo.html#module-module1 Long Module desc
module2 py:module 0 foo.html#module-$ -
module1.func py:function 1 sub/foo.html#$ -
module1.Foo.bar py:method 1 index.html#foo.Bar.baz -
CFunc c:function 2 cfunc.html#CFunc -
std cpp:type 1 index.html#std -
std::uint8_t cpp:type 1 index.html#std_uint8_t -
foo::Bar cpp:class 1 index.html#cpp_foo_bar -
foo::Bar::baz cpp:function 1 index.html#cpp_foo_bar_baz -
foons cpp:type 1 index.html#foons -
foons::bartype cpp:type 1 index.html#foons_bartype -
a term std:term -1 glossary.html#term-a-term -
ls.-l std:cmdoption 1 index.html#cmdoption-ls-l -
docname std:doc -1 docname.html -
foo js:module 1 index.html#foo -
foo.bar js:class 1 index.html#foo.bar -
foo.bar.baz js:method 1 index.html#foo.bar.baz -
foo.bar.qux js:data 1 index.html#foo.bar.qux -
a term including:colon std:term -1 glossary.html#term-a-term-including-colon -
The-Julia-Domain std:label -1 write_inventory/#$ The Julia Domain
""")

INVENTORY_V2_NO_VERSION: Final[bytes] = b"""\
# Sphinx inventory version 2
# Project: foo
# Version:
# The remainder of this file is compressed with zlib.
""" + zlib.compress(b"""\
module1 py:module 0 foo.html#module-module1 Long Module desc
""")

INVENTORY_V2_AMBIGUOUS_TERMS: Final[bytes] = b"""\
# Sphinx inventory version 2
# Project: foo
# Version: 2.0
# The remainder of this file is compressed with zlib.
""" + zlib.compress(b"""\
a term std:term -1 glossary.html#term-a-term -
A term std:term -1 glossary.html#term-a-term -
b term std:term -1 document.html#id5 -
B term std:term -1 document.html#B -
""")

INVENTORY_V2_TEXT_VERSION: Final[bytes] = b"""\
# Sphinx inventory version 2
# Project: foo
# Version: stable
# The remainder of this file is compressed with zlib.
""" + zlib.compress(b"""\
module1 py:module 0 foo.html#module-module1 Long Module desc
""")

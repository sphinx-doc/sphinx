from .foo import Outer, bar
from .foo import qux as RenamedQux
from .foo import my_one as renamed_one
from .foo import my_one

aliased_one = my_one

AliasedInner = Outer.Inner
AliasedOuter = Outer
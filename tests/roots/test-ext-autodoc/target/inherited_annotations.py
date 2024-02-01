"""
    Test case for #11387 corner case involving inherited
    members with type annotations on python 3.9 and earlier
"""

class HasTypeAnnotatedMember:
    inherit_me: int
    """Inherited"""

class NoTypeAnnotation(HasTypeAnnotatedMember):
    a = 1
    """Local"""

class NoTypeAnnotation2(HasTypeAnnotatedMember):
    a = 1
    """Local"""


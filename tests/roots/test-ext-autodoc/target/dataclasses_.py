from dataclasses import dataclass, field


@dataclass
class D:
    #: This is a str field
    str_field: str
    int_field: int  #: This is an int field
    list_field: list = field(default_factory=list)


@dataclass
class DNoDoc:
    str_field: str
    int_field: int
    list_field: list = field(default_factory=list)

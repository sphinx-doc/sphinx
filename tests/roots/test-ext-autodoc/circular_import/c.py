import circular_import.a
import circular_import.b


class SomeClass:
    X = circular_import.a.X

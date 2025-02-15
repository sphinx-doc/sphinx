from functools import partialmethod


class Base:
    def meth(self) -> None:
        pass

    @staticmethod
    def staticmeth() -> None:
        pass

    @classmethod
    def classmeth(cls) -> None:
        pass

    @property
    def prop(self) -> None:
        pass

    partialmeth = partialmethod(meth)

    async def coroutinemeth(self) -> None:
        pass

    partial_coroutinemeth = partialmethod(coroutinemeth)


class Inherited(Base):
    pass

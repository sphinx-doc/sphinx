from functools import partialmethod


class Base():
    def meth(self):
        pass

    @staticmethod
    def staticmeth():
        pass

    @classmethod
    def classmeth(cls):
        pass

    @property
    def prop(self):
        pass

    partialmeth = partialmethod(meth)

    async def coroutinemeth(self):
        pass

    partial_coroutinemeth = partialmethod(coroutinemeth)


class Inherited(Base):
    pass

from abc import abstractmethod


class Base():
    def meth(self):
        pass

    @abstractmethod
    def abstractmeth(self):
        pass

    @staticmethod
    @abstractmethod
    def staticmeth():
        pass

    @classmethod
    @abstractmethod
    def classmeth(cls):
        pass

    @property
    @abstractmethod
    def prop(self):
        pass

    @abstractmethod
    async def coroutinemeth(self):
        pass

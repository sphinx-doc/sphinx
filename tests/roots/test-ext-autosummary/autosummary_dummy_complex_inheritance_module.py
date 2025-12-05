import sys


class Parent:
    relation = 'Family'

    def __init__(self):
        self.name = 'Andrew'
        self.age = 35

    def get_name(self):
        return self.name

    def get_age(self):
        return f'Parent class -  {self.age}'

    # Test mangled name behaviour
    __get_age = get_age  # private copy of original get_age method
    __private_parent_attribute = 'Private_parent'


class Child(Parent):
    def __init__(self):
        self.name = 'Bobby'
        self.age = 15

    def get_name(self):
        return self.name

    def get_age(self):
        return f'Child class -  {self.age}'

    @staticmethod
    def addition(a, b):
        return a + b


class Baby(Child):
    # Test a private attribute
    __private_baby_name = 'Private1234'

    def __init__(self):
        self.name = 'Charlie'
        self.age = 2

    def get_age(self):
        return f'Baby class - {self.age}'

    class BabyInnerClass:
        """An inner class to test."""

        baby_inner_attribute = 'An attribute of an inner class'


class Job:
    def __init__(self):
        self.salary = 10

    def get_salary(self):
        return self.salary


class Architect(Job):
    def __init__(self):
        self.salary = 20

    def get_age(self):
        return f'Architect age - {self.age}'


# Test a class that inherits multiple classes
class Jerry(Architect, Child):
    def __init__(self):
        self.name = 'Jerry'
        self.age = 25


__all__ = ['Parent', 'Child', 'Baby', 'Job', 'Architect', 'Jerry']

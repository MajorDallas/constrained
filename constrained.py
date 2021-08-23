from abc import ABC
from collections import UserList
from collections.abc import Container
from functools import wraps
from itertools import chain
from typing import (
    Any, Callable, Generic, Iterable, List, Optional, Protocol,
    Sequence, Tuple, TypeVar, Type, Union, get_args, runtime_checkable,
)

S = TypeVar("S", bound="Constrained")
T = TypeVar("T")


def _constrain(m: Callable) -> Callable:
    """Wrap MutableSequence methods with a type check."""
    @wraps(m)
    def method(self, *args, **kwargs):
        for a in args:
            if not a.__class__ in self.__constraints__:
                if isinstance(a, Iterable):
                    if not all(e.__class__ for e in a):
                        raise TypeError("Invalid element types")
                else:
                    raise TypeError("Invalid type for argument")
            else:
                return m(self, *args, **kwargs)

    return method


class Constrained(ABC, Generic[T]):
    """Abstract base class to both mix-in the __constraints__ protocol and to
    set some basic runtime type-checking on any subclass. This class may be
    mixed in with any Iterable+Container type, but was designed with Sequence
    types in mind.

    `str` and `array.array` are virtual subclasses, set in the __subclasshook__
    method. Additional virtual subclasses can be registered with the `register`
    method defined on ABC.

    __constraints__ itself is an attribute. Specifically, it should be a
    tuple of class objects which can be consulted by methods at runtime to
    decide if they may include a new object in the augmented Collection class.

    See also: IsConstrained
    """

    __constraints__: Tuple[T, ...]

    def __init_subclass__(
        cls: Type[S], constraints: Optional[Tuple[Type[T], ...]] = None, **kwargs
    ):
        super(cls).__init_subclass__(**kwargs)
        cls.__constraints__ = (
            get_args(cls.__orig_bases__[0]) if not constraints else constraints
        )
        def __constrained_setitem__(self: S, key, val: T):
            if val.__class__ in self.__constraints__:
                super(self.__class__, self).__setitem__(key, val)
            else:
                raise TypeError("Invalid value type for Constrained class")

        def __constrained_init__(
            self: S, arg, *, constraints: Optional[Tuple[Type[T], ...]] = None, **kwargs
        ):
            if constraints is not None:
                self.__constraints__ = constraints
            elif (
                self.__constraints__ in (None, tuple())
                or isinstance(self.__constraints__[0], TypeVar)
            ): 
                self.__constraints__ = tuple(set(
                    [e.__class__ for e in arg]
                ))
            if not all(v.__class__ in self.__constraints__ for v in arg):
                raise TypeError("Invalid value type for Constrained class")
            else:
                self.__own_init__(arg, **kwargs)

        cls.__own_init__ = cls.__init__
        cls.__init__ = __constrained_init__
        cls.__setitem__ = __constrained_setitem__

    @classmethod
    def __subclasshook__(cls: Type[S], C: Type[Any]) -> bool:
        preregistered = ("str", "array", "IsConstrained")
        if (
            C.__name__ in preregistered
            or any("__constraints__" in B.__dict__ for B in C.__mro__)
        ):
            return True
        return NotImplemented


T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class IsConstrained(Protocol[T_co]):
    """Simpler Protocol type. This can be used both for `isinstance` checks and
    as a mix-in to custom classes which wish to implement the __constraints__
    protocol but need their own type-checking logic.

    N.B. `str` and `array.array` will not pass an `isinstance` check with this
    protocol type. Use `Constrained`, instead.
    """
    __constraints__: Tuple[T_co, ...] = ()


# str won't test with the protocol, but will with the abc
print("str is IsConstrained", isinstance(str, IsConstrained))  # False
print("str is Constrained", issubclass(str, Constrained))  # True


# A generic Constrained list
class Vec(Constrained[T], UserList):
    data:  List[T]

    append = _constrain(UserList.append)
    insert = _constrain(UserList.insert)

    @_constrain
    def extend(self, other: Iterable[T]) -> None:
        self.data.extend(other)
        # TODO still not working

    @_constrain
    def __imul__(self, n: int) -> "Vec":
        self.data *= n
        return self

    @_constrain
    def __iadd__(self, other: Iterable[T]) -> "Vec":
        self.data += other
        return self


print("Vec is IsConstrained", isinstance(Vec, IsConstrained))  # True

# Setting constraints with a param to the consructor
l = Vec(['a', 'b'], constraints=(str,))  # okay
print("Vec obj constraints:", l.__constraints__)  # (<class 'str'>,)
# l[1] = 1  # TypeError
l[1] = 'c'  # okay
#l.append(1)  # TypeError
l.append('c')
print(l)  # ['a', 'c', 'c']
print("Vec obj is IsConstrained:", isinstance(l, IsConstrained))  # True


# Setting constraints on the class with param to __init_subclass__
class Array(Constrained, UserList, constraints=(int,)):
    data:  List[int]

    append = _constrain(UserList.append)
    extend = _constrain(UserList.extend)
    insert = _constrain(UserList.insert)
    __imul__ = _constrain(UserList.__imul__)
    __iadd__ = _constrain(UserList.__iadd__)

a = Array([1,2,3])
print("Array obj constraints:", a.__constraints__)  # (<class 'int'>,)
a.append(4)
print(a)  # [1, 2, 3, 4]


# Setting constraint via type annotation
class StrArray(Constrained[str], UserList):
    data:  List[int]

    append = _constrain(UserList.append)
    extend = _constrain(UserList.extend)
    insert = _constrain(UserList.insert)
    __imul__ = _constrain(UserList.__imul__)
    __iadd__ = _constrain(UserList.__iadd__)

sa = StrArray(['a', 'b'])
print(sa.__constraints__)
sa.extend(['c', 'd'])
print(sa)
# sa.append(1)  # TypeError


# No explicit constraints set; determined by first element
l2 = Vec(['d', 'e'])
print("l2 constraints:", l2.__constraints__)


# Multiple constraints
l3 = Vec([1, 'a'], constraints=(str, int))
print(l3.__constraints__)
l3.extend(['d', 'b'])  # TODO
print(l3)
l3.append('c')
print(l3.data)

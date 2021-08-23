# New protocol for type-constrained Container types in Python

This was inspired by the discussion surrounding a limitation in Python's type
system such that `Sequence[str]` and `str` represent the same type. Although
I don't think this effort has been successful in addressing that problem, it
is nevertheless interesting for its own sake and may prove useful.

# What works

By creating an abstract base class with both `__init_subclass__` and
`__subclasshook__`, it's possible to inject type constraints into subclasses'
init process without the user needing to think about it beyond subclassing the
ABC, _and_ it's possible for `str` to be a virtual subclass.

Users can set constraints at subclass definition time with either a type
annotation or keyword argument. They may also set constraints at object
initialization if the class is generic, again with a keyword argument. Finally,
it's possible to not explicitly declare the constraints at all, in which case
they will be set to the type of the first item in the wrapped container.

Explicit declarations enable the use of multiple types, if desired.

A function with a `Constrained[str]` parameter should accept a `str` but not a
`List[str]`

# What doesn't work

A function which denotes a `Sequence[str]` parameter will still happily take a
`str`. Indeed, it would likely take any `Constrained[str]` where the `Constrained`
subtype has subclassed a `Sequence` type.

# Use-case

There are only two `Container` types in the Python standard library which
require all of their contents be of one type: `str` and `array.array`. The
latter is specialized for numeric operations and does not allow the storage of
arbitrary types.

`Constrained` is a mix-in class to be used with any `Container` type, though
designed initially around `MutableSequence`. The `Constrained` subtype
defined here, `Vec`, is essentially a `UserList` subclass with runtime
type enforcement.

By convention, `list` objects are generally expected to be homogeneous.
However, neither Python itself nor any static analysis tool I'm familiar with
at time of writing will make this convention into a reliable rule. Without
`Constrained`, it is always possible for a `list` to get an unexpected object
and cause problems (albeit remotely so).

`Constrained`, therefore, is useful anywhere you must be absolutely sure to
have a homogeneous container. This may be in data science applications, or
perhaps an additional optimization for eg. Cython or Pypy (though I assume both
already have more robust solutions).

## Relevant issues:

* _The_ issue on python/typing: https://github.com/python/typing/issues/256
* Similar issue on Mypy: https://github.com/python/mypy/issues/5090
* Pytype's workaround: https://github.com/google/pytype/blob/master/docs/faq.md#why-doesnt-str-match-against-string-iterables
* Mypy issue requesting a Pytype port: https://github.com/python/mypy/issues/11001

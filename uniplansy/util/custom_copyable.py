"""a custom copyable is a Protocol to support implementation of __copy__ and __deepcopy__ (mainly __deepcopy__)"""
from typing import Self, Protocol, runtime_checkable


@runtime_checkable
class CustomCopyable(Protocol):
    """a custom copyable is a Protocol to support implementation of __copy__ and __deepcopy__ (mainly __deepcopy__)

    :method set_matching_deep_copy: takes a raw instance of the copyable class and
    fills its fields from this instance in the context of a deep copy.
    """

    def set_matching_deep_copy(self, other:Self, memo):
        """takes a raw instance of the copyable class and
        fills its fields from this instance in the context of a deep copy.

        :param other: the raw instance
        :param memo: a blackbox used internally by the copy package.
        See https://docs.python.org/3/library/copy.html#object.__deepcopy__for more information
        """
        pass

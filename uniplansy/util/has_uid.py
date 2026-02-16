"""defines the HasUID Protocol and its subclasses"""
from typing import Protocol, runtime_checkable, Optional, Self

from uniplansy.util.custom_copyable import CustomCopyable


@runtime_checkable
class HasUID(Protocol):
    """a data protocol for having an uid"""
    uid: str | Optional[str]


class HasOptionalUID(HasUID, CustomCopyable):
    """a data protocol for having an optional uid"""
    uid: Optional[str] = None

    def set_matching_deep_copy(self, other: Self, memo):
        super().set_matching_deep_copy(other, memo)
        other.uid = None

class HasRequiredUID(HasUID):
    """a data protocol for having a required uid"""
    uid: str
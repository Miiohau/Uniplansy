"""defines the HasUID Protocol and its subclasses

HasUID(Protocol): a data protocol for having a UID
HasOptionalUID(Protocol): a data protocol for having an optional uid
HasRequiredUID(Protocol): a data protocol for having a required uid
"""
from typing import Protocol, runtime_checkable, Optional, Self

from uniplansy.util.custom_copyable import CustomCopyable


@runtime_checkable
class HasUID(Protocol):
    """a data protocol for having an uid"""
    uid: str | Optional[str]


class HasOptionalUID(Protocol,HasUID, CustomCopyable):
    """a data protocol for having an optional uid"""
    uid: Optional[str] = None

    def set_matching_deep_copy(self, other: Self, memo):
        super().set_matching_deep_copy(other, memo)
        other.uid = None

class HasRequiredUID(Protocol,HasUID):
    """a data protocol for having a required uid"""
    uid: str
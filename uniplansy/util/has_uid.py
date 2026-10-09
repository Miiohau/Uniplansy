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


class HasOptionalUID(HasUID, CustomCopyable, Protocol):
    """a data protocol for having an optional uid"""
    uid: Optional[str] = None

    def __init__(self):
        super().__init__()

    def set_matching_deep_copy(self, other: Self, memo):
        super().set_matching_deep_copy(other, memo)
        prior_frozen = other.frozen
        other.frozen = False
        other.uid = None
        other.frozen = prior_frozen

class HasRequiredUID(HasUID, Protocol):
    """a data protocol for having a required uid"""
    uid: str
from typing import Protocol, runtime_checkable, Optional, Self

from uniplansy.util.custom_copyable import CustomCopyable


@runtime_checkable
class HasUID(Protocol):
    uid: str | Optional[str]


class HasOptionalUID(HasUID, CustomCopyable):
    uid: Optional[str] = None

    def set_matching_deep_copy(self, other: Self, memo):
        super().set_matching_deep_copy(other, memo)
        other.uid = None

class HasRequiredUID(HasUID):
    uid: str
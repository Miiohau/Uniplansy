from typing import Self, Protocol, runtime_checkable


@runtime_checkable
class CustomCopyable(Protocol):

    def set_matching_deep_copy(self, other:Self, memo):
        pass

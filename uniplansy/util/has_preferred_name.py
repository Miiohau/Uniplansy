from typing import Protocol, runtime_checkable


@runtime_checkable
class HasPreferredName(Protocol):
    preferred_name: str = ""
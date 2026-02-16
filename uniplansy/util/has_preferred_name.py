"""HasPreferredName is a data protocol for having a preferred name"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class HasPreferredName(Protocol):
    """a data protocol for having a preferred name"""
    preferred_name: str = ""
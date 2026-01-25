from abc import ABCMeta, abstractmethod
from typing import Generic

from uniplansy.reasoners.core import World_Type


class ReasonerConsideration(Generic[World_Type],metaclass=ABCMeta):

    @abstractmethod
    def is_valid_state(self, world:World_Type) -> bool:
        pass
from abc import ABCMeta, abstractmethod


class ReasonerConsideration[World_Type](metaclass=ABCMeta):

    @abstractmethod
    def is_valid_state(self, world: World_Type) -> bool:
        pass
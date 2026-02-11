from abc import ABCMeta, abstractmethod
from typing import TypeVar, Generic

SaveableType = TypeVar('SaveableType')

class PersistenceManager(Generic[SaveableType],metaclass=ABCMeta):

    @abstractmethod
    def save(self, o:SaveableType, uid:str):
        pass

    @abstractmethod
    def load(self, uid:str) -> SaveableType:
        pass

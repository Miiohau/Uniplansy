from abc import ABCMeta, abstractmethod
from typing import List

from uniplansy.reasoners.core import Reasoner
from uniplansy.util.id_registry import IDRegistry


class ReasonerBuilder(metaclass=ABCMeta):

    @abstractmethod
    def build(self, uid:str, sub_reasoner_uids:List[str], id_registry:IDRegistry[Reasoner]) -> Reasoner:
        """builds the Reasoner. Note: id_registry may not be finalized or even contain all the uids contained in sub_reasoner_uids at the time this is called so the id_registry should be passed to the instance if needed."""
        pass

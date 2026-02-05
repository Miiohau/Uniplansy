#TODO: (after upgrading to python 3.12) uncomment @override Decorators
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default)) remove "from __future__ import annotations"
from __future__ import annotations

import copy
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Iterable, Callable

from uniplansy.plans.plan import Plan, PlanGraphNode
from uniplansy.reasoners.core import Reasoner
from uniplansy.tasks.task_filter import TaskFilter
from uniplansy.tasks.tasks import Task
from uniplansy.util.id_registry import IDRegistry, RegistryKeyAlreadyExistsError


@dataclass
class DecomposerNode(PlanGraphNode):
    node_decomposer:Decomposer

    # @override
    def __deepcopy__(self, memo):
        new_copy:DecomposerNode = DecomposerNode(uid=self.uid, node_decomposer=self.node_decomposer)
        super().set_matching_deep_copy(new_copy,memo)
        return new_copy


class Decomposer(metaclass=ABCMeta):


    def __init__(self, uid:str, register_self:bool=True):
        super().__init__()
        self.uid:str = uid
        if register_self:
            try:
                decomposer_registry.register(self.guid, self)
            except RegistryKeyAlreadyExistsError as e:
                raise RegistryKeyAlreadyExistsError("A decomposer with this guid already exists!") from e

    @abstractmethod
    def task_filter(self) -> TaskFilter:
        """return the Decomposer's task filter"""
        pass

    def filter_tasks_planed_for(self, task_list : List[Task]) -> Iterable[Task]:
        return self.task_filter().filter_tasks_list(task_list)

    @abstractmethod
    def decompose_tasks(self, plan:Plan) -> List[Plan]:
        """decompose the tasks in plan"""
        pass

    @abstractmethod
    def convert_to_reasoner_graph(self, node:DecomposerNode)->Callable[[str,List[str],dict[str,Reasoner]],Reasoner]:
        """convert the decomposed tasks to reasoner graph"""
        pass

decomposer_registry:IDRegistry[Decomposer] = IDRegistry()
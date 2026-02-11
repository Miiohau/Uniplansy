#TODO: (after upgrading to python 3.12) uncomment @override Decorators
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default)) remove "from __future__ import annotations"
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Any, Self

from immutabledict import immutabledict

from uniplansy.plans.plan import Plan, PlanGraphNode, PlanDeltas
from uniplansy.reasoners.graph import ReasonerTemplate
from uniplansy.util.id_registry import IDRegistry, RegistryKeyAlreadyExistsError, id_registry_registry


@dataclass
class DecomposerNode(PlanGraphNode):
    node_decomposer:Decomposer
    notes:immutabledict[str, Any] = immutabledict({})

    # @override
    def set_matching_deep_copy(self, other:Self, memo):
        super().set_matching_deep_copy(other, memo)
        other.notes = self.notes

    # @override
    def __deepcopy__(self, memo):
        new_copy:DecomposerNode = DecomposerNode(uid=self.uid, node_decomposer=self.node_decomposer)
        self.set_matching_deep_copy(new_copy,memo)
        return new_copy

    def __getstate__(self):
        state = super().__getstate__()
        state['node_decomposer_id'] = self.node_decomposer.uid
        del state['node_decomposer']
        return state

    # TODO:see if we can find a way to connect unpickled DecomposerNodes to their old notes
    def __setstate__(self,state):
        super().__setstate__(state)
        self.node_decomposer = decomposer_registry.fetch(state['node_decomposer_id'])
        del self.__dict__['node_decomposer_id']

class Decomposer(metaclass=ABCMeta):


    def __init__(self, uid:str, register_self:bool=True):
        super().__init__()
        self.uid:str = uid
        if register_self:
            try:
                decomposer_registry.register(self.uid, self)
            except RegistryKeyAlreadyExistsError as e:
                raise RegistryKeyAlreadyExistsError("A decomposer with this guid already exists!") from e

    @abstractmethod
    def applicable(self, plan:Plan) -> bool:
        """
        returns true if this Decomposer is applicable to the plan
        """
        pass

    # noinspection PyMethodMayBeStatic
    def estimate_deltas(self, plan:Plan) -> PlanDeltas:
        """
        estimates the deltas that will happen if this Decomposer is applied
        :param plan: the plan to calculate the deltas for
        :return: the estimated deltas that will happen if this Decomposer is applied to the plan
        """
        return PlanDeltas()

    @abstractmethod
    def decompose_tasks(self, plan:Plan) -> List[Plan]:
        """decompose the tasks in plan"""
        pass

    @abstractmethod
    def convert_to_reasoner_graph(self, node:DecomposerNode)->ReasonerTemplate:
        """convert the decomposed tasks to reasoner graph"""
        pass

decomposer_registry:IDRegistry[Decomposer] = IDRegistry(uid="__internal__.decomposer_registry")
id_registry_registry.register(decomposer_registry.uid,decomposer_registry)
""" holds Decomposer and its main supports and subclasses

Decomposer (class): knowledge expert that can decompose a plan typically by decomposing Tasks within that plan.
DecomposerNode (PlanGraphNode): a DecomposerNode holds information about how a Decomposer was applied to a plan
Goal (Decomposer): Goals are special Decomposers that are only applicable to empty plans or plans only Goals
have run on. There primary reason for existence is to place top level/end goals in to the plan.
decomposer_registry (module variable): an IDRegistry that holds all registered decomposers
"""
#TODO: (after upgrading to python 3.12) uncomment @override Decorators
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default))
# remove "from __future__ import annotations"
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Any, Self, Generic

from immutabledict import immutabledict

from uniplansy.plans.plan import Plan, PlanGraphNode, PlanDeltas
from uniplansy.reasoners.graph import ReasonerTemplate
from uniplansy.util.global_type_vars import World_Type
from uniplansy.util.has_uid import HasRequiredUID
from uniplansy.util.id_registry import IDRegistry, RegistryKeyAlreadyExistsError, id_registry_registry


@dataclass
class DecomposerNode(PlanGraphNode):
    """a DecomposerNode holds information about how a Decomposer was applied to a plan

    node_decomposer(attribute): the decomposer that was applied to the plan
    notes(attribute): additional context of how the decomposer was applied to the plan. Mainly used by the Decomposer
    itself in its convert_to_reasoner_graph method
    """
    node_decomposer: Decomposer
    notes: immutabledict[str, Any] = immutabledict({})

    # @override
    def set_matching_deep_copy(self, other: Self, memo):
        super().set_matching_deep_copy(other, memo)
        other.notes = self.notes

    def could_be_equal(self, other) -> bool:
        if not super().could_be_equal(other):
            return False
        if self.node_decomposer.uid != other.node_decomposer.uid:
            return False
        if self.notes != other.notes:
            return False
        return True

    # @override
    def __deepcopy__(self, memo):
        new_copy = type(self)(uid=self.uid, node_decomposer=self.node_decomposer)
        self.set_matching_deep_copy(new_copy, memo)
        return new_copy

    def __getstate__(self):
        state = super().__getstate__()
        state['node_decomposer_id'] = self.node_decomposer.uid
        del state['node_decomposer']
        return state

    # TODO:see if we can find a way to connect unpickled DecomposerNodes to their old notes
    def __setstate__(self, state):
        super().__setstate__(state)
        self.node_decomposer = decomposer_registry.fetch(state['node_decomposer_id'])
        del self.__dict__['node_decomposer_id']


# TODO: proof read the doc because this is very important concept for users of the library
class Decomposer(Generic[World_Type], HasRequiredUID, metaclass=ABCMeta):
    """knowledge expert that can decompose a plan typically by decomposing Tasks within that plan.

    abstractly a Decomposer represents a course of action
    applicable(method): returns true if this Decomposer is applicable to the plan
    estimate_deltas(method): estimates the deltas that will happen if this Decomposer is applied
    decompose_tasks(method): decompose the tasks in plan
    convert_to_reasoner_graph(method): convert the decomposed tasks to reasoner graph
    """

    def __init__(self, uid: str, register_self: bool = True):
        super().__init__()
        self.uid: str = uid
        if register_self:
            try:
                decomposer_registry.register(self.uid, self)
            except RegistryKeyAlreadyExistsError as e:
                raise RegistryKeyAlreadyExistsError("A decomposer with this uid already exists!") from e

    @abstractmethod
    def applicable(self, plan: Plan, world: World_Type) -> bool:
        """returns true if this Decomposer is applicable to the plan

        :param world: the world context to check applicability in
        :param plan: the plan to check applicability on
        :return: true if this Decomposer is applicable to the plan
        """
        pass

    # noinspection PyMethodMayBeStatic
    # noinspection PyUnusedLocal
    def estimate_deltas(self, plan: Plan, world: World_Type) -> PlanDeltas:
        """estimates the deltas that will happen if this Decomposer is applied

        :param world: the world context to estimate the deltas in
        :param plan: the plan to calculate the deltas for
        :return: the estimated deltas that will happen if this Decomposer is applied to the plan
        """
        return PlanDeltas()

    @abstractmethod
    def decompose_tasks(self, plan: Plan, world: World_Type) -> List[Plan]:
        """decompose the tasks in plan

        this method returns a list because there may be different ways a decomposer can be applied to the plan.
        :param world: the world context to decompose tasks in
        :param plan: the plan to decompose task on
        :return: a list of plans with one or more tasks decomposed"""
        pass

    @abstractmethod
    def convert_to_reasoner_graph(self,
                                  node: DecomposerNode,
                                  node_id_to_builder_id: dict[str, str]
                                  ) -> ReasonerTemplate:
        """convert the decomposed tasks to reasoner graph

        :param node: the DecomposerNode with any notes the Decomposer made at that time
        :param node_id_to_builder_id: a dictionary that maps node UIDs to builder UIDs
        :return: the reasoner template that will be used to create the Reasoner that will apply the course of action
        this Decomposer represents in practice"""
        pass


class Goal(Decomposer, metaclass=ABCMeta):
    """Goals are special Decomposers that are only applicable to empty plans or plans only Goals have run on.
    There primary reason for existence is to place top level/end goals in to the plan"""

    def __init__(self, uid: str, register_self: bool = True):
        super().__init__(uid=uid, register_self=register_self)

    # noinspection PyMethodMayBeStatic
    # noinspection PyUnusedLocal
    def applicable(self, plan: Plan, world: World_Type) -> bool:
        if len(plan.nodes_by_UID) == 0:
            return True
        elif (len(plan.nodes_by_UID) == len(plan.tasks_by_UID)) and (len(plan.tasks_by_UID) == len(plan.leaf_tasks())):
            # if the only nodes are tasks and all of those tasks are leaves then we assume no Decomposers other than
            # Goals have run.
            return True
        else:
            return False


"""the global registry of all Decomposers"""
decomposer_registry: IDRegistry[Decomposer] = IDRegistry(uid="__internal__.decomposer_registry")
id_registry_registry.register(decomposer_registry.uid, decomposer_registry)
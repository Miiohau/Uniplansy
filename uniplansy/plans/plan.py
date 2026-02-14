#TODO: (after upgrading to python 3.12) uncomment @override Decorators
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default)) remove "from __future__ import annotations"
from __future__ import annotations

import copy
import statistics
from dataclasses import dataclass, field, FrozenInstanceError
from typing import Optional, List, Self

from immutabledict import immutabledict

from uniplansy.tasks.task_filter import TaskFilter
from uniplansy.tasks.tasks import Task, TaskDescription
from uniplansy.util.FreezableObject import FreezableObject
from uniplansy.util.has_uid import HasUID, HasOptionalUID, HasRequiredUID
from uniplansy.util.id_registry import IDRegistry, RegistryKeyAlreadyExistsError, id_registry_registry


@dataclass
class PlanGraphNode(FreezableObject,HasRequiredUID):
    uid:str
    node_id_context: Optional[IDRegistry[PlanGraphNode]] = field(default=None, init=False)
    children:set[PlanGraphNode] = field(default_factory=set, kw_only=True, compare=False)
    parents: set[PlanGraphNode] = field(default_factory=set, kw_only=True, compare=False)
    frozen_children:Optional[frozenset[PlanGraphNode]] = field(default=None, init=False, compare=False)
    frozen_parents:Optional[frozenset[PlanGraphNode]] = field(default=None, init=False, compare=False)

    # @override
    def __getattribute__(self, name):
        if not self.frozen:
            return super().__getattribute__(name)
        elif name == "children":
            if self.frozen_children is None:
                self.frozen_children = frozenset(super().__getattribute__(name))
            return self.frozen_children
        elif name == "parents":
            if self.frozen_parents is None:
                self.frozen_parents = frozenset(super().__getattribute__(name))
            return self.frozen_parents
        else:
            return super().__getattribute__(name)

    # @override
    def unfreeze(self):
        super().unfreeze()
        self.frozen_children = None
        self.frozen_parents = None

    def is_compatible_with(self,other:PlanGraphNode) -> bool:
        """return true if PlanGraphNode is compatible with other"""
        return self == other

    def set_matching_deep_copy(self,other:Self,memo):
        super().set_matching_deep_copy(other,memo)
        other.frozen_parents = copy.deepcopy(self.frozen_parents,memo)
        other.frozen_children = copy.deepcopy(self.frozen_children,memo)
        other.children = copy.deepcopy(self.children,memo)
        other.parents = copy.deepcopy(self.parents,memo)
        other.node_id_context = self.node_id_context

    # @override
    def __deepcopy__(self, memo):
        # TODO: figure out a way to do this in a type safe way
        new_copy = type(self)(uid=self.uid)
        self.set_matching_deep_copy(new_copy, memo)
        return new_copy

    def __getstate__(self):
        state = self.__dict__.copy()
        state['node_id_context_id'] = self.node_id_context.uid
        del state['node_id_context']
        return state

    def __setstate__(self,state):
        self.__dict__.update(state)
        self.node_id_context = id_registry_registry.fetch(state['node_id_context_id'])
        del self.__dict__['node_id_context_id']


@dataclass(frozen=True)
class PlanDeltas:
    total_motivation_delta: Optional[float] = None
    min_cost_delta: Optional[float] = None
    max_cost_delta: Optional[float] = None
    estimated_cost_delta: Optional[float] = None
    unsatisfied_tasks_delta: Optional[int] = None
    leaf_tasks_delta: Optional[int] = None
    satisfied_percentage_deltas: immutabledict[str, float] = immutabledict({})

# TODO: add the concept of constraints that have to remain true for the Plan to remain valid
@dataclass(init=True,repr=True,eq=True)
class Plan(FreezableObject,HasOptionalUID):
    node_id_context:IDRegistry[PlanGraphNode]
    task_description_id_context: IDRegistry[TaskDescription]
    uid: Optional[str] = None
    tasks_by_UID:dict[str,Task] = field(default_factory=dict, init=False)
    nodes_by_UID:dict[str,PlanGraphNode] = field(default_factory=dict, init=False)
    _cashed_total_motivation:Optional[float] = field(default=None, init=False, compare=False)
    _cashed_min_cost:Optional[float] = field(default=None, init=False, compare=False)
    _cashed_max_cost:Optional[float] = field(default=None, init=False, compare=False)
    _cashed_average_satisfied_percentage:Optional[float] = field(default=None, init=False, compare=False)
    _cashed_median_satisfied_percentage:Optional[float] = field(default=None, init=False, compare=False)
    _cashed_estimated_cost:Optional[float] = field(default=None, init=False, compare=False)
    _cashed_unsatisfied_tasks:Optional[list[Task]] = field(default=None, init=False, compare=False)
    _cashed_leaf_tasks:Optional[list[Task]] = field(default=None, init=False, compare=False)

    def total_motivation(self) -> float:
        """return the total motivation of the plan"""
        if self.frozen and (self._cashed_total_motivation is not None):
            return self._cashed_total_motivation
        total:float = 0
        for cur_task in self.tasks_by_UID.values():
            total += (cur_task.motivation * (1-cur_task.get_clamped_satisfied_percentage(0,1)))
        if self.frozen:
            self._cashed_total_motivation = total
        return total

    def min_cost(self)  -> float:
        """return the minimum cost of the plan"""
        if self.frozen and (self._cashed_min_cost is not None):
            return self._cashed_min_cost
        total: float = 0
        for cur_task in self.tasks_by_UID.values():
            total += (cur_task.min_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        if self.frozen:
            self._cashed_min_cost = total
        return total

    def estimated_cost(self) -> float:
        """return the estimated cost of the plan"""
        if self.frozen and (self._cashed_estimated_cost is not None):
            return self._cashed_estimated_cost
        total: float = 0
        for cur_task in self.tasks_by_UID.values():
            total += (cur_task.estimated_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        if self.frozen:
            self._cashed_estimated_cost = total
        return total

    def max_cost(self) -> float:
        """return the maximum cost of the plan"""
        if self.frozen and (self._cashed_max_cost is not None):
            return self._cashed_max_cost
        total: float = 0
        for cur_task in self.tasks_by_UID.values():
            total += (cur_task.estimated_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        if self.frozen:
            self._cashed_max_cost = total
        return total

    def average_satisfied_percentage(self) -> float:
        """return the average satisfied percentage of the tasks in the plan"""
        if self.frozen and (self._cashed_average_satisfied_percentage is not None):
            return self._cashed_average_satisfied_percentage
        total: float = 0
        for cur_task in self.tasks_by_UID.values():
            total += cur_task.satisfied_percentage
        r_value: float = total / len(self.tasks_by_UID)
        if self.frozen:
            self._cashed_average_satisfied_percentage = r_value
        return r_value

    def median_satisfied_percentage(self) -> float:
        """return the median satisfied percentage of the plan"""
        if self.frozen and (self._cashed_median_satisfied_percentage is not None):
            return self._cashed_median_satisfied_percentage
        satisfied_percentage_values: list[float] = []
        for cur_task in self.tasks_by_UID.values():
            satisfied_percentage_values.append(cur_task.satisfied_percentage)
        r_value: float = statistics.median(satisfied_percentage_values)
        if self.frozen:
            self._cashed_median_satisfied_percentage = r_value
        return r_value

    def unsatisfied_tasks(self) -> List[Task]:
        """return the unsatisfied tasks"""
        if self.frozen and (self._cashed_unsatisfied_tasks is not None):
            return self._cashed_unsatisfied_tasks
        r_values: list[Task] = []
        for cur_task in self.tasks_by_UID.values():
            if cur_task.satisfied_percentage <= 1:
                r_values.append(cur_task)
        if self.frozen:
            self._cashed_unsatisfied_tasks = r_values
        return r_values

    def leaf_tasks(self) -> List[Task]:
        """return the leaf tasks"""
        if self.frozen and (self._cashed_leaf_tasks is not None):
            return self._cashed_leaf_tasks
        r_values: list[Task] = []
        for cur_task in self.tasks_by_UID.values():
            if len(cur_task.children) == 0:
                r_values.append(cur_task)
        if self.frozen:
            self._cashed_leaf_tasks = r_values
        return r_values

    def filter_tasks(self, task_filter : TaskFilter) -> List[Task]:
        """filter tasks based on a TaskFilter"""
        return list(task_filter.filter_tasks_list(self.tasks_by_UID.values()))


    def add_node(self, new_node: PlanGraphNode) -> bool:
        """add a task to this plan. Returns true if the node wasn't already in the plan. Any override of this method should call super."""
        if self.frozen:
            raise FrozenInstanceError()
        if not self.node_id_context.contains(new_node.uid):
            self.node_id_context.register(new_node.uid, new_node)
        elif not (new_node.is_compatible_with(self.node_id_context.fetch(new_node.uid))):
            raise RegistryKeyAlreadyExistsError()
        if new_node.node_id_context is None:
            new_node.node_id_context = self.node_id_context
        if isinstance(new_node,Task):
            if not new_node.description.uid in self.tasks_by_UID:
                self.tasks_by_UID[new_node.description.uid] = new_node
            if new_node.task_description_id_context is None:
                new_node.task_description_id_context = self.task_description_id_context
        if not new_node.uid in self.nodes_by_UID:
            self.nodes_by_UID[new_node.uid] = new_node
            self._add_node_recurse(new_node)
            return True
        return False

    def _add_node_recurse(self, new_node: PlanGraphNode):
        """add a task to this plan"""
        for cur_parent in new_node.parents:
            if not new_node in cur_parent.children:
                cur_parent.children.add(new_node)
            self.add_node(cur_parent)
        for cur_child in new_node.children:
            if not new_node in cur_child.parents:
                cur_child.parents.add(new_node)
            self.add_node(cur_child)

    # @override
    def freeze(self):
        """freeze the plan. Meaning it is protected from modification"""
        for node in self.nodes_by_UID.values():
            node.freeze()
        for node in self.tasks_by_UID.values():
            node.freeze()
        super().freeze()

    # @override
    def unfreeze(self):
        """unfreeze the plan. Meaning it is no longer protected from modification"""
        super().unfreeze()
        for node in self.nodes_by_UID.values():
            node.unfreeze()
        for node in self.tasks_by_UID.values():
            node.unfreeze()
        self._cashed_leaf_tasks = None
        self._cashed_unsatisfied_tasks = None
        self._cashed_max_cost = None
        self._cashed_min_cost = None
        self._cashed_estimated_cost = None
        self._cashed_total_motivation = None
        self._cashed_average_satisfied_percentage = None
        self._cashed_median_satisfied_percentage = None

    def set_matching_deep_copy(self,other:Self,memo):
        super().set_matching_deep_copy(other,memo)
        other.nodes_by_UID = copy.deepcopy(self.nodes_by_UID, memo)
        other.tasks_by_UID = copy.deepcopy(self.tasks_by_UID, memo)
        other._cashed_leaf_tasks = copy.deepcopy(self._cashed_leaf_tasks, memo)
        other._cashed_unsatisfied_tasks = copy.deepcopy(self._cashed_unsatisfied_tasks, memo)
        other._cashed_max_cost = self._cashed_max_cost
        other._cashed_min_cost = self._cashed_min_cost
        other._cashed_estimated_cost = self._cashed_estimated_cost
        other._cashed_total_motivation = self._cashed_total_motivation
        other._cashed_average_satisfied_percentage = self._cashed_average_satisfied_percentage
        other._cashed_median_satisfied_percentage = self._cashed_median_satisfied_percentage

    # @override
    def __deepcopy__(self, memo):
        new_copy:Self = type(self)(node_id_context=self.node_id_context,task_description_id_context=self.task_description_id_context)
        self.set_matching_deep_copy(new_copy,memo)
        return new_copy

    def __getstate__(self):
        state = self.__dict__.copy()
        state['node_id_context_id'] = self.node_id_context.uid
        del state['node_id_context']
        state['task_description_id_context_id'] = self.task_description_id_context.uid
        del state['task_description_id_context']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.node_id_context = id_registry_registry.fetch(state['node_id_context_id'])
        del self.__dict__['node_id_context_id']
        self.task_description_id_context = id_registry_registry.fetch(state['task_description_id_context_id'])
        del self.__dict__['task_description_id_context_id']

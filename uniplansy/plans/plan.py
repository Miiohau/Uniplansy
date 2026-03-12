#TODO: (after upgrading to python 3.12) uncomment @override Decorators
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default)) remove "from __future__ import annotations"
from __future__ import annotations

import copy
import statistics
from dataclasses import dataclass, field, FrozenInstanceError
from typing import Optional, List, Self, Any, TypeAlias

from immutabledict import immutabledict

from uniplansy.tasks.task_filter import TaskFilter
from uniplansy.tasks.tasks import Task, TaskDescription
from uniplansy.util.FreezableObject import FreezableObject
from uniplansy.util.has_uid import HasUID, HasOptionalUID, HasRequiredUID
from uniplansy.util.id_registry import IDRegistry, RegistryKeyAlreadyExistsError, id_registry_registry


@dataclass
class PlanGraphNode(FreezableObject, HasRequiredUID):
    uid: str
    node_id_context: Optional[IDRegistry[PlanGraphNode]] = field(default=None, init=False)
    children: set[PlanGraphNode] = field(default_factory=set, kw_only=True, compare=False)
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
        return self.could_be_equal(other)

    def set_matching_deep_copy(self,other:Self,memo):
        super().set_matching_deep_copy(other,memo)
        other.frozen_parents = copy.deepcopy(self.frozen_parents,memo)
        other.frozen_children = copy.deepcopy(self.frozen_children,memo)
        other.children = copy.deepcopy(self.children,memo)
        other.parents = copy.deepcopy(self.parents,memo)
        other.node_id_context = self.node_id_context

    # @override
    def __deepcopy__(self, memo):
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

    # possible algorithms
    # vf2 algorithm
    # Weisfeiler Leman graph isomorphism test
    def _are_children_equal(self, other, memo: dict[str,Any]) -> bool:
        are_equal: bool = True
        for cur_self_child in self.children:
            possible_matches: set[str] = set()
            for cur_other_child in other.children:
                if cur_self_child.could_be_equal(cur_other_child):
                    possible_matches.add(cur_other_child.uid)
            orig_possible_matches: Optional[set[str]] = memo["possible mappings"][cur_self_child.uid]
            if orig_possible_matches is not None:
                possible_matches = possible_matches.intersection(orig_possible_matches)
            memo["possible mappings"][cur_self_child.uid] = possible_matches
            if len(possible_matches) == 0:
                are_equal = False
                break
            found_match: bool = False
            if cur_self_child.uid in memo["visited nodes"]:
                found_match = True
            else:
                for cur_other_child in other.children:
                    if cur_other_child in possible_matches:
                        if cur_self_child.are_equal(cur_other_child, memo):
                            found_match = True
                            break
            if not found_match:
                are_equal = False
                break
        return are_equal

    def _are_parents_equal(self, other, memo: dict[str,Any]) -> bool:
        are_equal: bool = True
        for cur_self_parent in self.parents:
            if cur_self_parent.uid in memo["visited nodes"]:
                found_match: bool = False
                for cur_other_parent in other.parents:
                    if cur_self_parent.could_be_equal(cur_other_parent):
                        found_match = True
                        break
                if not found_match:
                    are_equal = False
                    break
            else:
                found_match: bool = False
                for cur_other_parent in other.parents:
                    if cur_self_parent.are_equal(cur_other_parent, memo):
                        found_match = True
                        break
                if not found_match:
                    are_equal = False
                    break
        return are_equal

    def could_be_equal(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        #uids aren't compared here because matching uids on PlanGraphNodes imply compatibility not equality
        #conversely two nodes could be equal even if their uids don't match
        if self.node_id_context_id != other.node_id_context_id:
            return False
        return True

    def are_equal(self, other, memo: dict[str,Any]) -> bool:
        if not self.could_be_equal(other):
            return False
        if not "visited nodes" in memo:
            memo["visited nodes"] = set()
        if not "possible mappings" in memo:
            memo["possible mappings"] = dict[str, set[str]]()
        memo["visited nodes"].add(self.uid)
        if not self._are_children_equal(other, memo):
            return False
        if not self._are_parents_equal(other, memo):
            return False
        return True

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.are_equal(other, dict())


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
@dataclass(init=True,repr=True)
class Plan(FreezableObject,HasOptionalUID):
    node_id_context:IDRegistry[PlanGraphNode]
    task_description_id_context: IDRegistry[TaskDescription]
    uid: Optional[str] = None
    tasks_by_UID:dict[str,Task] = field(default_factory=dict, init=False)
    nodes_by_UID:dict[str,PlanGraphNode] = field(default_factory=dict, init=False)
    _cached_total_motivation:Optional[float] = field(default=None, init=False, compare=False)
    _cached_min_cost:Optional[float] = field(default=None, init=False, compare=False)
    _cached_max_cost:Optional[float] = field(default=None, init=False, compare=False)
    _cached_average_satisfied_percentage:Optional[float] = field(default=None, init=False, compare=False)
    _cached_median_satisfied_percentage:Optional[float] = field(default=None, init=False, compare=False)
    _cached_tasks_fully_satisfied_percentage:Optional[float] = field(default=None, init=False, compare=False)
    _cached_concrete_action_percentage:Optional[float] = field(default=None, init=False, compare=False)
    _cached_estimated_cost:Optional[float] = field(default=None, init=False, compare=False)
    _cached_unsatisfied_tasks:Optional[list[Task]] = field(default=None, init=False, compare=False)
    _cached_leaf_tasks:Optional[list[Task]] = field(default=None, init=False, compare=False)
    _cached_at_least_one_unsatisfied_task:Optional[bool] = field(default=None, init=False, compare=False)
    _cached_at_least_one_concrete_action:Optional[bool] = field(default=None, init=False, compare=False)

    def valid(self):
        #TODO:implement
        pass

    def total_motivation(self) -> float:
        """return the total motivation of the plan"""
        if self.frozen and (self._cached_total_motivation is not None):
            return self._cached_total_motivation
        total:float = 0
        for cur_task in self.tasks_by_UID.values():
            total += (cur_task.motivation * (1-cur_task.get_clamped_satisfied_percentage(0,1)))
        if self.frozen:
            self._cached_total_motivation = total
        return total

    def min_cost(self)  -> float:
        """return the minimum cost of the plan"""
        if self.frozen and (self._cached_min_cost is not None):
            return self._cached_min_cost
        total: float = 0
        for cur_task in self.tasks_by_UID.values():
            total += (cur_task.min_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        if self.frozen:
            self._cached_min_cost = total
        return total

    def estimated_cost(self) -> float:
        """return the estimated cost of the plan"""
        if self.frozen and (self._cached_estimated_cost is not None):
            return self._cached_estimated_cost
        total: float = 0
        for cur_task in self.tasks_by_UID.values():
            total += (cur_task.estimated_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        if self.frozen:
            self._cached_estimated_cost = total
        return total

    def max_cost(self) -> float:
        """return the maximum cost of the plan"""
        if self.frozen and (self._cached_max_cost is not None):
            return self._cached_max_cost
        total: float = 0
        for cur_task in self.tasks_by_UID.values():
            total += (cur_task.estimated_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        if self.frozen:
            self._cached_max_cost = total
        return total

    def average_satisfied_percentage(self, deltas: Optional[PlanDeltas] = None) -> float:
        """return the average satisfied percentage of the tasks in the plan

        :param deltas: TODO:Finish doc"""
        if self.frozen and (self._cached_average_satisfied_percentage is not None) and deltas is None:
            return self._cached_average_satisfied_percentage
        total: float = 0
        for cur_task in self.tasks_by_UID.values():
            if deltas is None:
                total += cur_task.satisfied_percentage
            else:
                total += cur_task.satisfied_percentage + deltas.satisfied_percentage_deltas.get(cur_task.uid, 0)
        r_value: float = total / len(self.tasks_by_UID)
        if self.frozen and deltas is None:
            self._cached_average_satisfied_percentage = r_value
        return r_value

    def median_satisfied_percentage(self, deltas: Optional[PlanDeltas] = None) -> float:
        """return the median satisfied percentage of the plan

        :param deltas: TODO:Finish doc"""
        if self.frozen and (self._cached_median_satisfied_percentage is not None) and deltas is None:
            return self._cached_median_satisfied_percentage
        satisfied_percentage_values: list[float] = []
        for cur_task in self.tasks_by_UID.values():
            if deltas is None:
                satisfied_percentage_values.append(cur_task.satisfied_percentage)
            else:
                satisfied_percentage_values.append(cur_task.satisfied_percentage +
                                                   deltas.satisfied_percentage_deltas.get(cur_task.uid, 0))
        r_value: float = statistics.median(satisfied_percentage_values)
        if self.frozen and deltas is None:
            self._cached_median_satisfied_percentage = r_value
        return r_value

    def tasks_fully_satisfied_percentage(self, deltas: Optional[PlanDeltas] = None)-> float:
        if self.frozen and (self._cached_tasks_fully_satisfied_percentage is not None) and deltas is None:
            return self._cached_tasks_fully_satisfied_percentage
        tasks_satisfied_count: int = 0
        for cur_task in self.tasks_by_UID.values():
            satisfied_percentage: float
            if deltas is None:
                satisfied_percentage = cur_task.satisfied_percentage
            else:
                satisfied_percentage = (cur_task.satisfied_percentage +
                                        deltas.satisfied_percentage_deltas.get(cur_task.uid, 0))
            if satisfied_percentage >= 1:
                tasks_satisfied_count += 1
        r_value: float = tasks_satisfied_count / len(self.tasks_by_UID)
        if self.frozen and deltas is None:
            self._cached_tasks_fully_satisfied_percentage = r_value
        return r_value

    def concrete_action_percentage(self, deltas: Optional[PlanDeltas] = None)-> float:
        if self.frozen and (self._cached_concrete_action_percentage is not None) and deltas is None:
            return self._cached_concrete_action_percentage
        concrete_action_count: int = 0
        total_leaf_nodes: int = 0
        for cur_node in self.nodes_by_UID.values():
            if len(cur_node.children) == 0:
                total_leaf_nodes += 1
                if isinstance(cur_node, Task):
                    satisfied_percentage: float
                    if deltas is None:
                        satisfied_percentage = cur_node.satisfied_percentage
                    else:
                        satisfied_percentage = (cur_node.satisfied_percentage +
                                                deltas.satisfied_percentage_deltas.get(cur_node.uid, 0))
                    if satisfied_percentage >= 1:
                        concrete_action_count += 1
                else:
                    concrete_action_count += 1
        r_value: float = concrete_action_count/ total_leaf_nodes
        if self.frozen and deltas is None:
            self._cached_concrete_action_percentage = r_value
        return r_value


    def unsatisfied_tasks(self) -> List[Task]:
        """return the unsatisfied tasks"""
        if self.frozen and (self._cached_unsatisfied_tasks is not None):
            return self._cached_unsatisfied_tasks
        r_values: list[Task] = []
        for cur_task in self.tasks_by_UID.values():
            if cur_task.satisfied_percentage <= 1:
                r_values.append(cur_task)
        if self.frozen:
            self._cached_unsatisfied_tasks = r_values
        return r_values

    def leaf_tasks(self) -> List[Task]:
        """return the leaf tasks"""
        if self.frozen and (self._cached_leaf_tasks is not None):
            return self._cached_leaf_tasks
        r_values: list[Task] = []
        for cur_task in self.tasks_by_UID.values():
            if len(cur_task.children) == 0:
                r_values.append(cur_task)
        if self.frozen:
            self._cached_leaf_tasks = r_values
        return r_values

    def at_least_one_unsatisfied_task(self, deltas: Optional[PlanDeltas] = None)-> bool:
        if self.frozen and deltas is None:
            if self._cached_at_least_one_unsatisfied_task is not None:
                return self._cached_at_least_one_unsatisfied_task
            if self._cached_unsatisfied_tasks is not None:
                if len(self._cached_unsatisfied_tasks) > 0:
                    self._cached_at_least_one_unsatisfied_task = True
                else:
                    self._cached_at_least_one_unsatisfied_task = False
                return self._cached_at_least_one_unsatisfied_task
        for cur_task in self.tasks_by_UID.values():
            satisfied_percentage: float
            if deltas is None:
                satisfied_percentage = cur_task.satisfied_percentage
            else:
                satisfied_percentage = (cur_task.satisfied_percentage +
                                        deltas.satisfied_percentage_deltas.get(cur_task.uid, 0))
            if satisfied_percentage <= 1:
                if self.frozen:
                    self._cached_at_least_one_unsatisfied_task = True
                return True
        if self.frozen:
            self._cached_at_least_one_unsatisfied_task = False
        return False

    def at_least_one_concrete_action(self, deltas: Optional[PlanDeltas] = None)-> bool:
        if self.frozen and deltas is None and self._cached_at_least_one_concrete_action is not None:
            return self._cached_at_least_one_concrete_action
        for cur_node in self.nodes_by_UID.values():
            is_cur_node_concrete: bool = False
            if len(cur_node.children) == 0:
                if isinstance(cur_node, Task):
                    satisfied_percentage: float
                    if deltas is None:
                        satisfied_percentage = cur_node.satisfied_percentage
                    else:
                        satisfied_percentage = (cur_node.satisfied_percentage +
                                                deltas.satisfied_percentage_deltas.get(cur_node.uid, 0))
                    if satisfied_percentage >= 1:
                        is_cur_node_concrete = True
                else:
                    is_cur_node_concrete = True
            if is_cur_node_concrete:
                if self.frozen:
                    self._cached_at_least_one_concrete_action = True
                return True
        if self.frozen:
            self._cached_at_least_one_concrete_action = False
        return False

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
        self._cached_leaf_tasks = None
        self._cached_unsatisfied_tasks = None
        self._cached_max_cost = None
        self._cached_min_cost = None
        self._cached_estimated_cost = None
        self._cached_total_motivation = None
        self._cached_average_satisfied_percentage = None
        self._cached_median_satisfied_percentage = None

    def set_matching_deep_copy(self,other:Self,memo):
        super().set_matching_deep_copy(other,memo)
        other.nodes_by_UID = copy.deepcopy(self.nodes_by_UID, memo)
        other.tasks_by_UID = copy.deepcopy(self.tasks_by_UID, memo)
        other._cached_leaf_tasks = copy.deepcopy(self._cached_leaf_tasks, memo)
        other._cached_unsatisfied_tasks = copy.deepcopy(self._cached_unsatisfied_tasks, memo)
        other._cached_max_cost = self._cached_max_cost
        other._cached_min_cost = self._cached_min_cost
        other._cached_estimated_cost = self._cached_estimated_cost
        other._cached_total_motivation = self._cached_total_motivation
        other._cached_average_satisfied_percentage = self._cached_average_satisfied_percentage
        other._cached_median_satisfied_percentage = self._cached_median_satisfied_percentage

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

    def __eq__(self, other) -> bool:
        # note: comparing two plans for equality is isomorphic to Graph isomorphism problem
        # TODO: detect if the plan is a tree and use a tree comparison algorithm if so
        if self is other:
            return True
        if not isinstance(other, type(self)):
            return False
        if self.uid == other.uid:
            return True
        if ((self.node_id_context != other.node_id_context) or
                (self.task_description_id_context != other.task_description_id_context)):
            return False
        if ((self._cached_max_cost is not None) and (other._cached_max_cost is not None) and
                (self._cached_max_cost != other._cached_max_cost)):
            return False
        if ((self._cached_total_motivation is not None) and (other._cached_total_motivation is not None) and
                (self._cached_total_motivation != other._cached_total_motivation)):
            return False
        if ((self._cached_min_cost is not None) and (other._cached_min_cost is not None) and
                (self._cached_min_cost != other._cached_min_cost)):
            return False
        if ((self._cached_estimated_cost is not None) and (other._cached_estimated_cost is not None) and
                (self._cached_estimated_cost != other._cached_estimated_cost)):
            return False
        if ((self._cached_median_satisfied_percentage is not None) and
                (other._cached_median_satisfied_percentage is not None) and
                (self._cached_median_satisfied_percentage != other._cached_median_satisfied_percentage)):
            return False
        if ((self._cached_average_satisfied_percentage is not None) and
                (other._cached_average_satisfied_percentage is not None) and
                (self._cached_average_satisfied_percentage != other._cached_average_satisfied_percentage)):
            return False
        if ((self._cached_leaf_tasks is not None) and (other._cached_leaf_tasks is not None) and
                (len(self._cached_leaf_tasks) != len(other._cached_leaf_tasks))):
            return False
        if ((self._cached_unsatisfied_tasks is not None) and (other._cached_unsatisfied_tasks is not None) and
                (len(self._cached_unsatisfied_tasks) != len(other._cached_unsatisfied_tasks))):
            return False
        memo: dict[str, Any] = {"visited nodes": set(), "possible mappings": dict[str, set[str]]()}
        for cur_uid in self.nodes_by_UID.keys():
            if cur_uid in other.nodes_by_UID.keys():
                memo["possible mappings"][cur_uid] = {cur_uid}
        are_equal: bool = True
        for cur_self_node in self.nodes_by_UID.values():
            found_match = False
            if cur_self_node.uid in other.nodes_by_UID.keys():
                if cur_self_node.are_equal(other.nodes_by_UID[cur_self_node.uid], memo):
                    found_match = True
            else:
                for cur_other_node in other.nodes_by_UID.values():
                    if cur_self_node.are_equal(cur_other_node, memo):
                        found_match = True
                        break
            if not found_match:
                are_equal = False
                break
        return are_equal

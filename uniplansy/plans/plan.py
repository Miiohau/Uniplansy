#TODO: (after upgrading to python 3.12) uncomment @override Decorators
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default)) remove "from __future__ import annotations"
from __future__ import annotations

import copy
import statistics
from dataclasses import dataclass, field, FrozenInstanceError
from typing import Optional, List

from uniplansy.decomposers.core import Decomposer
from uniplansy.tasks.task_filter import TaskFilter
from uniplansy.tasks.tasks import Task
from uniplansy.util.FreezableObject import FreezableObject


@dataclass
class PlanGraphNode(FreezableObject):
    children:set[PlanGraphNode] = field(default_factory=set, kw_only=True)
    parents: set[PlanGraphNode] = field(default_factory=set, kw_only=True)
    frozen_children:Optional[frozenset[PlanGraphNode]] = field(default=None, init=False)
    frozen_parents:Optional[frozenset[PlanGraphNode]] = field(default=None, init=False)

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



@dataclass
class DecomposerNode(PlanGraphNode):
    node_decomposer:Decomposer

    # @override
    def __deepcopy__(self, memo):
        return DecomposerNode(children=copy.deepcopy(self.children,memo), parents=copy.deepcopy(self.parents,memo),node_decomposer=self.node_decomposer)



@dataclass(init=True,repr=True,eq=True)
class Plan(FreezableObject):
    tasks_by_GUID:dict[str,Task] = field(default_factory=dict, init=False)
    decomposer_id_to_DecomposerNodes:dict[str,DecomposerNode] = field(default_factory=dict, init=False)
    node_dump:set[PlanGraphNode] = field(default_factory=set, init=False)

    def total_motivation(self) -> float:
        """return the total motivation of the plan"""
        total:float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += (cur_task.motivation * (1-cur_task.get_clamped_satisfied_percentage(0,1)))
        return total

    def min_cost(self)  -> float:
        """return the minimum cost of the plan"""
        total: float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += (cur_task.min_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        return total

    def estimated_cost(self) -> float:
        """return the estimated cost of the plan"""
        total: float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += (cur_task.estimated_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        return total

    def max_cost(self) -> float:
        """return the maximum cost of the plan"""
        total: float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += (cur_task.estimated_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        return total

    def average_satisfied_percentage(self) -> float:
        """return the average satisfied percentage of the tasks in the plan"""
        total: float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += cur_task.satisfied_percentage
        return total / len(self.tasks_by_GUID)

    def median_satisfied_percentage(self) -> float:
        """return the median satisfied percentage of the plan"""
        satisfied_percentage_values: list[float] = []
        for cur_task in self.tasks_by_GUID.values():
            satisfied_percentage_values.append(cur_task.satisfied_percentage)
        return statistics.median(satisfied_percentage_values)

    def unsatisfied_tasks(self) -> List[Task]:
        """return the unsatisfied tasks"""
        r_values: list[Task] = []
        for cur_task in self.tasks_by_GUID.values():
            if cur_task.satisfied_percentage <= 1:
                r_values.append(cur_task)
        return r_values

    def leaf_tasks(self) -> List[Task]:
        """return the leaf tasks"""
        r_values: list[Task] = []
        for cur_task in self.tasks_by_GUID.values():
            if len(cur_task.children) == 0:
                r_values.append(cur_task)
        return r_values


    def convert_to_reasoner_graph(self):
        """convert this plan to a reasoner graph"""
        #TODO: Implement
        pass


    def filter_tasks(self, task_filter : TaskFilter) -> List[Task]:
        """filter tasks based on a TaskFilter"""
        return list(task_filter.filter_tasks_list(self.tasks_by_GUID.values()))

    def add_node(self, new_node: PlanGraphNode) -> bool:
        """add a task to this plan. Returns true if the node wasn't already in the plan"""
        if self.frozen:
            raise FrozenInstanceError()
        if isinstance(new_node,Task):
            if not new_node.description.guid in self.tasks_by_GUID:
                self.tasks_by_GUID[new_node.description.guid] = new_node
                self._add_node_recurse(new_node)
                return True
        elif isinstance(new_node,DecomposerNode):
            if not new_node.node_decomposer.id in self.decomposer_id_to_DecomposerNodes:
                self.decomposer_id_to_DecomposerNodes[new_node.node_decomposer.id] = new_node
                self._add_node_recurse(new_node)
                return True
        else:
            if not new_node in self.node_dump:
                self.node_dump.add(new_node)
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
        for node in self.node_dump:
            node.freeze()
        for node in self.decomposer_id_to_DecomposerNodes.values():
            node.freeze()
        for node in self.tasks_by_GUID.values():
            node.freeze()
        super().freeze()

    # @override
    def unfreeze(self):
        """unfreeze the plan. Meaning it is no longer protected from modification"""
        super().unfreeze()
        for node in self.node_dump:
            node.unfreeze()
        for node in self.decomposer_id_to_DecomposerNodes.values():
            node.unfreeze()
        for node in self.tasks_by_GUID.values():
            node.unfreeze()
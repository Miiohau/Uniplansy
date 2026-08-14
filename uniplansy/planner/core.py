""" the submodule where main Planner class and its primary supports live

Planner (class): responsible for running the planning algorithm
PlanningContext (class): Holds the overall data on the state of the planner, including all currently loaded plans and
the planning tree
PlanContext (class): the context surrounding a plan
DecomposerContext (class): the context surrounding a decomposer applied to a plan
UIDNode (class): Holds the data on the planning tree
"""
# TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default))
#  remove "from __future__ import annotations"
from __future__ import annotations

import copy
from collections import deque
from typing import List, Generic

from uniplansy.decomposers.core import Decomposer, DecomposerNode
from uniplansy.planner.base import PlanContext, UIDNode, PlanningContext, PlanCacheStrategy, DecomposerContext
from uniplansy.planner.plan_selection_strategy import FullPlanSelectionStrategy
from uniplansy.planner.planning_strategy import FullPlanningStrategy
from uniplansy.planner.stopping_strategy import StoppingStrategy
from uniplansy.plans.plan import Plan, PlanGraphNode, PlanDeltas
from uniplansy.reasoners.graph import ReasonerBuilder
from uniplansy.tasks.tasks import TaskDescription
from uniplansy.util.global_type_vars import World_Type
from uniplansy.util.id_registry import IDRegistry
from uniplansy.util.uid_suppliers.default_guid_supplier import default_guid_supplier
from uniplansy.util.uid_suppliers.uid_supplier import UIDSupplier
from uniplansy.util.uid_suppliers.wrappers.wrappers import UniqueInDictUIDSupplierWrapper


class Planner(Generic[World_Type]):
    """responsible for running the planning algorithm

    resume_planning (method): Resumes planning the planning loop
    planning_strategy (parameter): the planning strategy to use
    stopping_strategy (parameter): the stopping strategy to use
    final_plan_selection_strategy (parameter): plan_selection_strategy to use when it is time to pause planning
    decomposers (parameter): the set of decomposers to use
    cache_strategy (parameter): the cache strategy to use
    plan_uid_supplier (parameter): the UID supplier to use to generate uids for plans that don't have them yet.
    (used so decomposers don't have to provide uid to the plans they decompose if they don't want to)
    """

    def __init__(self,
                 planning_strategy: FullPlanningStrategy,
                 stopping_strategy: StoppingStrategy,
                 final_plan_selection_strategy: FullPlanSelectionStrategy,
                 cache_strategy: PlanCacheStrategy,
                 decomposers: set[Decomposer],
                 plan_uid_supplier: UIDSupplier = default_guid_supplier,
                 assert_that_plans_are_acyclic_graphs: bool = True):
        self.planning_strategy = planning_strategy
        self.stopping_strategy = stopping_strategy
        self.final_plan_selection_strategy = final_plan_selection_strategy
        self.cache_strategy = cache_strategy
        self.decomposers = decomposers
        self.node_id_context: IDRegistry[PlanGraphNode] = IDRegistry()
        self.task_description_id_context: IDRegistry[TaskDescription] = IDRegistry()
        self.assert_that_plans_are_acyclic_graphs = assert_that_plans_are_acyclic_graphs
        root_name: str = "root"
        root_plan_context: PlanContext = PlanContext(plan=Plan(
            uid=root_name,
            node_id_context=self.node_id_context,
            task_description_id_context=self.task_description_id_context
        ))
        root_uid_node: UIDNode = UIDNode(uid=root_name, parent=None)
        self.planning_context = PlanningContext(
            root=root_uid_node,
            plan_context_by_uid={root_name: root_plan_context},
            plan_uid_node_by_uid={root_name: root_uid_node}
        )
        self.plan_uid_supplier = UniqueInDictUIDSupplierWrapper(
            wrapped_dict=self.planning_context.plan_context_by_uid,
            delegate=plan_uid_supplier
        )
        self.planning_strategy.introduce_plan_cache_strategy(self.cache_strategy)
        self.final_plan_selection_strategy.introduce_plan_cache_strategy(self.cache_strategy)
        self.cache_strategy.introduce_planning_strategy(self.planning_strategy)
        self.planning_context.notes["new plan uids"] = [root_name]

    def resume_planning(self, world: World_Type) -> Plan | ReasonerBuilder:
        """Resumes planning the planning loop

        :return: the final selected plan
        """
        self.cache_strategy.manage_active_plans(self.planning_context, world, initializing=True)
        active_plan_uids: List[str] = [current_plan_context.plan.uid for current_plan_context in
                                       self.planning_context.plan_context_by_uid.values()
                                       if (current_plan_context is not None) and
                                       (current_plan_context.plan is not None) and
                                       (current_plan_context.plan.uid is not None)]
        for current_plan_context_id in active_plan_uids:
            current_plan_context = self.planning_context.plan_context_by_uid[current_plan_context_id]
            update_succeeded: bool = True
            old_version = copy.deepcopy(current_plan_context.plan)
            for current_node in current_plan_context.plan.nodes_by_UID.values():
                if current_node is DecomposerNode:
                    update_succeeded = update_succeeded and current_node.node_decomposer.update_plan(
                        current_plan_context.plan, current_node, world)
            if not update_succeeded:
                current_plan_context.plan = old_version
            if (not update_succeeded) or (
                    not current_plan_context.plan.valid(world, check_planning_time_constraints=False)):
                if self.cache_strategy.should_save_plan(current_plan_context, self.planning_context):
                    self.cache_strategy.save_plan(current_plan_context, self.planning_context, invalid=True)
                self.planning_context.plan_context_by_uid[current_plan_context.plan.uid].plan = None
        while not self.stopping_strategy.should_stop(self.planning_context):
            selected_plan, selected_decomposer = self.planning_strategy.plan(
                self.planning_context,
                decomposers=self.decomposers,
                world=world
            )
            if selected_plan is None:
                break
            if selected_decomposer is None:
                parent_uid_node: UIDNode = self.planning_context.plan_uid_node_by_uid[selected_plan.uid]
                self.planning_context.notes["new decomposer uids"] = []
                for current_decomposer in self.decomposers:
                    deltas: PlanDeltas = current_decomposer.estimate_deltas(selected_plan, world)
                    new_decomposer_context: DecomposerContext = DecomposerContext(decomposer=current_decomposer, )
                    new_decomposer_context.notes["deltas"] = deltas
                    new_uid_node: UIDNode = UIDNode(uid=current_decomposer.uid, parent=parent_uid_node)
                    parent_uid_node.children.append(new_uid_node)
                    self.planning_context.decomposer_context_by_uid[selected_plan.uid][
                        current_decomposer.uid] = new_decomposer_context
                    self.planning_context.decomposer_uid_node_by_uid[selected_plan.uid][
                        current_decomposer.uid] = new_uid_node
                    self.planning_context.notes["new decomposer uids"].append(
                        (selected_plan.uid, current_decomposer.uid))
            else:
                new_plans: List[Plan] = selected_decomposer.decompose_tasks(selected_plan, world)
                parent_uid_node: UIDNode = self.planning_context.decomposer_uid_node_by_uid[selected_plan.uid][
                    selected_decomposer.uid]
                for current_new_plan in new_plans:
                    current_new_plan.freeze()
                    if not current_new_plan.valid(world, check_world_state_constraints=False):
                        continue
                    if __debug__:
                        if self.assert_that_plans_are_acyclic_graphs:
                            assert self._plan_graph_is_acyclic(
                                current_new_plan), "cyclic plans can be harder to handle and must be explictly allowed"
                    self.planning_strategy.prepopulate_plan_cache(current_new_plan)
                    found_match: bool = False
                    for current_old_plan in self.planning_context.plan_context_by_uid.values():
                        if current_new_plan == current_old_plan:
                            found_match = True
                            break
                    if not found_match:
                        if current_new_plan.uid is None:
                            current_new_plan.temporary_selective_unfreeze("uid")
                            current_new_plan.uid = self.plan_uid_supplier.create_guid("plan")
                        new_plan_context: PlanContext = PlanContext(plan=current_new_plan)
                        self.planning_context.plan_context_by_uid[current_new_plan.uid] = new_plan_context
                        new_uid_node: UIDNode = UIDNode(uid=current_new_plan.uid, parent=parent_uid_node)
                        parent_uid_node.children.append(new_uid_node)
                        self.planning_context.plan_uid_node_by_uid[current_new_plan.uid] = new_uid_node
                self.planning_context.notes["new plan uids"] = [current_new_plan.uid
                                                                for current_new_plan in
                                                                new_plans]
            self.cache_strategy.manage_active_plans(self.planning_context, world)
        returned_plan = self.final_plan_selection_strategy.select_plan(self.planning_context, finalizing=True,
                                                                       world=world)
        self.cache_strategy.manage_active_plans(self.planning_context, world, finalizing=True)
        return returned_plan

    @staticmethod
    def _plan_graph_is_acyclic(current_new_plan: Plan) -> bool:
        queue: deque[PlanGraphNode] = deque()
        for plan_node in current_new_plan.nodes_by_UID.values():
            if len(plan_node.parents) == 0:
                queue.append(plan_node)
        visited: set[PlanGraphNode] = set()
        while len(queue) > 0:
            current_node = queue.popleft()
            visited.add(current_node)
            for current_child in current_node.children:
                if current_child not in visited:
                    visited_all_parents: bool = True
                    for current_parent in current_child.parents:
                        if not current_parent not in visited:
                            visited_all_parents = False
                    if visited_all_parents:
                        queue.append(current_child)
        return len(visited) == len(current_new_plan.nodes_by_UID.values())

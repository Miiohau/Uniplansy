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

from typing import List, Generic

from uniplansy.decomposers.core import Decomposer
from uniplansy.planner.base import PlanContext, UIDNode, PlanningContext, PlanCacheStrategy
from uniplansy.planner.plan_selection_strategy import FullPlanSelectionStrategy
from uniplansy.planner.planning_strategy import FullPlanningStrategy
from uniplansy.planner.stopping_strategy import StoppingStrategy
from uniplansy.plans.plan import Plan, PlanGraphNode
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
                 plan_uid_supplier: UIDSupplier = default_guid_supplier):
        self.planning_strategy = planning_strategy
        self.stopping_strategy = stopping_strategy
        self.final_plan_selection_strategy = final_plan_selection_strategy
        self.cache_strategy = cache_strategy
        self.decomposers = decomposers
        self.node_id_context: IDRegistry[PlanGraphNode] = IDRegistry()
        self.task_description_id_context: IDRegistry[TaskDescription] = IDRegistry()
        root_name: str = "root"
        root_plan_context: PlanContext = PlanContext(plan=Plan(
            uid=root_name,
            node_id_context=self.node_id_context,
            task_description_id_context=self.task_description_id_context
        ))
        root_uid_node: UIDNode = UIDNode(uid=root_name)
        self.planning_context = PlanningContext(
            root=root_uid_node,
            plan_by_uid={root_name: root_plan_context},
            uid_nodes_by_uid={root_name: root_uid_node}
        )
        self.plan_uid_supplier = UniqueInDictUIDSupplierWrapper(
            wrapped_dict=self.planning_context.plan_by_uid,
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
        self.cache_strategy.load_plans(self.planning_context)
        active_plan_uids: List[str] = [current_plan_context.plan.uid for current_plan_context in
                                       self.planning_context.plan_by_uid.values()
                                       if (current_plan_context is not None) and
                                       (current_plan_context.plan is not None) and
                                       (current_plan_context.plan.uid is not None)]
        for current_plan_context_id in active_plan_uids:
            current_plan_context = self.planning_context.plan_by_uid[current_plan_context_id]
            if not current_plan_context.plan.valid(world):
                if self.cache_strategy.should_save_plan(current_plan_context, self.planning_context):
                    self.cache_strategy.save_plan(current_plan_context, self.planning_context)
                self.planning_context.plan_by_uid[current_plan_context.plan.uid].plan = None
        self.cache_strategy.manage_active_plans(self.planning_context)
        while not self.stopping_strategy.should_stop(self.planning_context):
            selected_plan, selected_decomposer = self.planning_strategy.plan(
                self.planning_context,
                decomposers=self.decomposers,
                world=world
            )
            new_plans: List[Plan] = selected_decomposer.decompose_tasks(selected_plan, world)
            for current_new_plan in new_plans:
                current_new_plan.freeze()
                self.planning_strategy.prepopulate_plan_cache(current_new_plan)
                found_match: bool = False
                for current_old_plan in self.planning_context.plan_by_uid.values():
                    if current_new_plan == current_old_plan:
                        found_match = True
                        break
                if not found_match:
                    if current_new_plan.uid is None:
                        current_new_plan.temporary_selective_unfreeze("uid")
                        current_new_plan.uid = self.plan_uid_supplier.create_guid("plan")
                    new_plan_context: PlanContext = PlanContext(plan=current_new_plan)
                    self.planning_context.plan_by_uid[current_new_plan.uid] = new_plan_context
                    new_uid_node: UIDNode = UIDNode(uid=current_new_plan.uid)
                    parent_uid_node: UIDNode = self.planning_context.uid_nodes_by_uid[current_new_plan.uid]
                    parent_uid_node.children.append(new_uid_node)
                    self.planning_context.uid_nodes_by_uid[current_new_plan.uid] = new_uid_node
            self.planning_context.notes["new plan uids"] = [current_new_plan.uid
                                                            for current_new_plan in
                                                            self.planning_context.plan_by_uid.values()]
            self.cache_strategy.manage_active_plans(self.planning_context)
        self.cache_strategy.manage_active_plans(self.planning_context, finalizing=True)
        return self.final_plan_selection_strategy.select_plan(self.planning_context, finalizing=True, world=world)
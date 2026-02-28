# TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default))
#  remove "from __future__ import annotations"
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from uniplansy.decomposers.core import Decomposer
from uniplansy.planner.plan_cache_strategy import PlanCacheStrategy
from uniplansy.planner.plan_selection_strategy import PlanSelectionStrategy
from uniplansy.planner.planning_strategy import PlanningStrategy
from uniplansy.planner.stopping_strategy import StoppingStrategy
from uniplansy.plans.plan import Plan, PlanGraphNode
from uniplansy.reasoners.graph import ReasonerBuilder
from uniplansy.tasks.tasks import TaskDescription
from uniplansy.util.id_registry import IDRegistry
from uniplansy.util.uid_suppliers.uid_supplier import UIDSupplier, default_guid_supplier
from uniplansy.util.uid_suppliers.wrappers.wrappers import UniqueInDictUIDSupplierWrapper


@dataclass
class UIDNode:
    """Holds the data on the planning tree"""
    uid: str
    children: List[UIDNode] = field(default_factory=list)

@dataclass
class PlanningContext:
    """Holds the overall data on the state of the planner, including all currently loaded plans and the planning tree

    root(attribute): the root of the planning tree
    uid_nodes_by_uid(attribute): a dictionary mapping UIDs to UIDNodes
    plan_by_uid(attribute): a dictionary mapping UIDs to a PlanContexts
    notes(attribute): a dictionary to hold misc data.
    notes["new plan uids"](attribute value): a list of the uids of the plans added in the last planning cycle"""
    root: UIDNode
    uid_nodes_by_uid: Dict[str, UIDNode] = field(default_factory=dict)
    plan_by_uid: Dict[str, Optional[PlanContext]] = field(default_factory=dict)
    notes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PlanContext:
    """the context of surrounding a plan

    plan(attribute): the plan
    notes(attribute): a dictionary to hold misc data."""
    plan: Optional[Plan]
    notes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecomposerContext:
    """the context of surrounding a decomposer applied to a plan

    decomposer(attribute): the decomposer this node applies to
    notes(attribute): a dictionary to hold misc data."""
    decomposer: Decomposer
    notes: Dict[str, Any] = field(default_factory=dict)

class Planner:
    def __init__(self,
                 planning_strategy: PlanningStrategy,
                 stopping_strategy: StoppingStrategy,
                 final_plan_selection_strategy: PlanSelectionStrategy,
                 cache_strategy: PlanCacheStrategy,
                 decomposers:set[Decomposer],
                 plan_uid_supplier:UIDSupplier = default_guid_supplier):
        self.planning_strategy = planning_strategy
        self.stopping_strategy = stopping_strategy
        self.final_plan_selection_strategy = final_plan_selection_strategy
        self.cache_strategy = cache_strategy
        self.decomposers = decomposers
        self.node_id_context:IDRegistry[PlanGraphNode] = IDRegistry()
        self.task_description_id_context: IDRegistry[TaskDescription] = IDRegistry()
        root_name:str = "root"
        root_plan_context: PlanContext = PlanContext(plan= Plan(
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

    def resume_planning(self) -> Plan | ReasonerBuilder:
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
            if not current_plan_context.plan.valid():
                if self.cache_strategy.should_save_plan(current_plan_context, self.planning_context):
                    self.cache_strategy.save_plan(current_plan_context, self.planning_context)
                self.planning_context.plan_by_uid[current_plan_context.plan.uid].plan = None
        self.cache_strategy.manage_active_plans(self.planning_context)
        while not self.stopping_strategy.should_stop(self.planning_context):
            selected_plan, selected_decomposer = self.planning_strategy.plan(
                self.planning_context,
                decomposers=self.decomposers
            )
            new_plans: List[Plan] = selected_decomposer.decompose_tasks(selected_plan)
            for current_new_plan in new_plans:
                current_new_plan.freeze()
                self.planning_strategy.prepopulate_plan_cache(current_new_plan)
                found_match:bool = False
                for current_old_plan in self.planning_context.plan_by_uid.values():
                    if current_new_plan == current_old_plan:
                        found_match = True
                        break
                if not found_match:
                    if current_new_plan.uid is None:
                        current_new_plan.temporary_selective_unfreeze("uid")
                        current_new_plan.uid = self.plan_uid_supplier.create_guid("plan")
                    self.planning_context.plan_by_uid[current_new_plan.uid] = current_new_plan
                    new_uid_node: UIDNode = UIDNode(uid=current_new_plan.uid)
                    parent_uid_node: UIDNode = self.planning_context.uid_nodes_by_uid[current_new_plan.uid]
                    parent_uid_node.children.append(new_uid_node)
                    self.planning_context.uid_nodes_by_uid[current_new_plan.uid] = new_uid_node
            self.planning_context.notes["new plan uids"] = [current_new_plan.uid
                                                            for current_new_plan in
                                                            self.planning_context.plan_by_uid.values()]
            self.cache_strategy.manage_active_plans(self.planning_context)
        self.cache_strategy.manage_active_plans(self.planning_context, finalizing=True)
        return self.final_plan_selection_strategy.select_plan(self.planning_context, finalizing=True)
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from uniplansy.decomposers.core import Decomposer
from uniplansy.plans.plan import Plan


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
    """the context surrounding a plan

    plan(attribute): the plan
    notes(attribute): a dictionary to hold misc data."""
    plan: Optional[Plan]
    notes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecomposerContext:
    """the context surrounding a decomposer applied to a plan

    decomposer(attribute): the decomposer this node applies to
    notes(attribute): a dictionary to hold misc data."""
    decomposer: Decomposer
    notes: Dict[str, Any] = field(default_factory=dict)

class PlanCacheStrategy(metaclass=ABCMeta):

    def introduce_planning_strategy(self, planning_strategy: PlanningStrategy):
        pass

    @abstractmethod
    def should_save_plan(self, plan_context: PlanContext, planning_context: PlanningContext) -> bool:
        pass

    @abstractmethod
    def manage_active_plans(self, planning_context: PlanningContext, finalizing:bool = False):
        pass

    @abstractmethod
    def save_plan(self, plan_context: PlanContext, planning_context: PlanningContext):
        pass

    @abstractmethod
    def load_plan(self, plan_uid:str, planning_context: PlanningContext) -> Plan:
        pass

    @abstractmethod
    def load_plans(self, planning_context: PlanningContext):
        pass

class MaybeWantsToKnowPlanCacheStrategy(metaclass=ABCMeta):

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        """introduces a PlanCacheStrategy to this class which it may save.

        The intended use of a saved PlanCacheStrategy is to request offloaded plans be
        reloaded back into memory
        :param plan_cache_strategy: the plan_cache_strategy being introduced
        """
        pass

class CanPrepopulateTheCasheOfPlans(metaclass=ABCMeta):

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        """prepopulates the cache values of the plan

        This method is currently used by the planner to prepopulate the cache values of the plan to make plan equality
        tests more efficient (prepopulating the values are O(N) while full equality testing is potentially
        O(2^N) or worse).
        :param plan_to_populate: the plan to prepopulate
        """
        pass

class PlanningStrategy(MaybeWantsToKnowPlanCacheStrategy, CanPrepopulateTheCasheOfPlans, metaclass=ABCMeta):
    """a PlanningStrategy can be used to select a Plan Decomposer pair

    introduce_plan_cache_strategy(method):introduces a PlanCacheStrategy to the PlanningStrategy which it may save.
    prepopulate_plan_cache(method): prepopulates the cache values of the plan
    """
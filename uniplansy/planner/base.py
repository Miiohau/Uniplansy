"""the base classes for the planner package

UIDNode(Class):Holds the data on the planning tree
PlanningContext(Class):Holds the overall data on the state of the planner,
including all currently loaded plans and the planning tree
PlanContext(Class):the context surrounding a plan
DecomposerContext(Class):the context surrounding a decomposer applied to a plan
PlanCacheStrategy(Class): a strategy for what plans to save and how to save and load them
MaybeWantsToKnowPlanCacheStrategy(Class): an interface for classes that may want to know the PlanCacheStrategy
CanPrepopulateTheCacheOfPlans(Class): an interface for classes that may want to prepopulate the plan's value cache
PlanningStrategy(Class): a PlanningStrategy can be used to select a Plan Decomposer pair
"""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from uniplansy.decomposers.core import Decomposer
from uniplansy.plans.plan import Plan
from uniplansy.util.global_type_vars import World_Type


@dataclass
class UIDNode:
    """Holds the data on the planning tree"""
    uid: str
    parent: Optional[UIDNode]
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
    plan_uid_node_by_uid: Dict[str, UIDNode] = field(default_factory=dict)
    decomposer_uid_node_by_uid: Dict[str, Dict[str, UIDNode]] = field(default_factory=dict)
    plan_context_by_uid: Dict[str, Optional[PlanContext]] = field(default_factory=dict)
    decomposer_context_by_uid: Dict[str, Dict[str, Optional[DecomposerContext]]] = field(default_factory=dict)
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
    """a strategy for what plans to save and how to save and load them

    introduce_planning_strategy(method):introduces the PlanningStrategy to this class which it may save.
    should_save_plan(method): returns whether the plan should be saved
    manage_active_plans(method): Manages the active plans. Mainly by deciding which previously saved plans to load.
    save_plan(method): saves a plan
    load_plan(method): maybe loads a plan
    """

    def introduce_planning_strategy(self, planning_strategy: PlanningStrategy):
        """introduces the PlanningStrategy to this class which it may save

        :param planning_strategy: the planning_strategy being introduced"""
        pass

    @abstractmethod
    def should_save_plan(self, plan_context: PlanContext, planning_context: PlanningContext) -> bool:
        """returns whether the plan should be saved

        :param plan_context: the plan_context being saved
        :param planning_context: the planning_context"""
        pass

    @abstractmethod
    def manage_active_plans(self,
                            planning_context: PlanningContext,
                            world: World_Type,
                            initializing: bool = False,
                            finalizing: bool = False):
        """Manages the active plans. Mainly by deciding which previously saved plans to load.

        called at the start of the planning cycle with initializing true
        at the end of each loop of the planning cycle with initializing and finalizing false
        and at the end  of the planning cycle with finalizing true
        :param planning_context: the planning_context
        :param world: the world context
        :param initializing: whether a new planning cycle is starting
        :param finalizing: whether the planning cycle is ending"""
        pass

    @abstractmethod
    def save_plan(self, plan_context: PlanContext, planning_context: PlanningContext, invalid=False):
        """saves a plan

        :param plan_context: the plan_context being saved
        :param planning_context: the planning_context
        :param invalid: whether the plan is invalid in current world context"""
        pass

    @abstractmethod
    def load_plan(self, plan_uid: str, planning_context: PlanningContext) -> Optional[Plan]:
        """maybe loads a plan

        standard failure modes are the plan is invalid this loop and
        :param plan_uid: the plan_uid being loaded
        :param planning_context: the planning_context"""
        pass


class MaybeWantsToKnowPlanCacheStrategy(metaclass=ABCMeta):
    """an interface for classes that may want to know the PlanCacheStrategy

    introduce_plan_cache_strategy(method):introduces the PlanCacheStrategy to this class which it may save."""

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        """introduces a PlanCacheStrategy to this class which it may save.

        The intended use of a saved PlanCacheStrategy is to request offloaded plans be
        reloaded back into memory
        :param plan_cache_strategy: the plan_cache_strategy being introduced
        """
        pass


class CanPrepopulateTheCacheOfPlans(metaclass=ABCMeta):
    """an interface for classes that may want to prepopulate the plan's value cache

    prepopulate_plan_cache(method):prepopulates the cache values of the plan"""

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        """prepopulates the cache values of the plan

        This method is currently used by the planner to prepopulate the cache values of the plan to make plan equality
        tests more efficient (prepopulating the values are O(N) while full equality testing is potentially
        O(2^N) or worse).
        :param plan_to_populate: the plan to prepopulate
        """
        pass


class PlanningStrategy(MaybeWantsToKnowPlanCacheStrategy, CanPrepopulateTheCacheOfPlans, metaclass=ABCMeta):
    """a PlanningStrategy can be used to select a Plan Decomposer pair

    introduce_plan_cache_strategy(method):introduces a PlanCacheStrategy to the PlanningStrategy which it may save.
    prepopulate_plan_cache(method): prepopulates the cache values of the plan
    """

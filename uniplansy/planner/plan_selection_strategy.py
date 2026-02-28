"""defines the PlanSelectionStrategy and some subclasses. a PlanSelectionStrategy selects a plan in the context of a
planning_context.

PlanSelectionStrategy(Interface): the core class of this module. a plan selection strategy selects a plan in the
context of a planning_context.
GreedyPlanSelectionStrategy(PlanSelectionStrategy):a greedy PlanSelectionStrategy that returns plans in sort order
(determined by plan_comparison_strategy: PlanComparisonStrategy)
"""
import heapq
from abc import ABCMeta, abstractmethod
from typing import List, Set, Optional, Iterable, Tuple

from uniplansy.planner.core import PlanCacheStrategy, PlanningContext
from uniplansy.plans.plan import Plan
from uniplansy.plans.plan_comparison_strategy import PlanComparisonStrategy, PlanValueToken


class PlanSelectionStrategy(metaclass=ABCMeta):
    """a PlanSelectionStrategy selects a plan in the context of a planning_context

    select_plan(method): the core method that selects a plan
    introduce_plan_cache_strategy(method):introduces a PlanCacheStrategy to the PlanSelectionStrategy which it may save.
    prepopulate_plan_cache(method): prepopulates the cache values of the plan
    """

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        """introduces a PlanCacheStrategy to the PlanSelectionStrategy which it may save.

        The intended use of a saved PlanCacheStrategy by a PlanSelectionStrategy is to request offloaded plans be
        reloaded back into memory
        :param plan_cache_strategy: the plan_cache_strategy being introduced
        """
        pass

    @abstractmethod
    def select_plan(self, planning_context: PlanningContext, finalizing: bool = False) -> Plan:
        """selects a plan

        :param planning_context: the planning_context to select a plan from
        :param finalizing: whether it is being called to select the final returned plan
        :return: the selected plan
        """
        pass

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        """prepopulates the cache values of the plan

        This method is currently used by the planner to prepopulate the cache values of the plan to make plan equality
        tests more efficient (prepopulating the values are O(N) while full equality testing is potentially
        O(2^N) or worse).
        :param plan_to_populate: the plan to prepopulate
        """
        pass


class GreedyPlanSelectionStrategy(PlanSelectionStrategy):
    """a greedy PlanSelectionStrategy that returns plans in sort order
    (determined by plan_comparison_strategy: PlanComparisonStrategy)"""

    def __init__(self, plan_comparison_strategy: PlanComparisonStrategy):
        self.plan_comparison_strategy = plan_comparison_strategy
        self.values_needed: Set[PlanValueToken] = set()
        self.min_heap: List[Tuple[Tuple, str]] = []
        self.plan_cache_strategy: Optional[PlanCacheStrategy] = None

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        self.plan_cache_strategy = plan_cache_strategy

    def _add_plans_to_heap(self, plans_to_add: Iterable[Plan]):
        """adds plans to the heap/priority queue

        :param plans_to_add: the set of plans to add to the heap
        """
        if len(self.min_heap) == 0:
            tuples_list: List[Tuple[Tuple, str]] = [(self.plan_comparison_strategy.plan_to_tuple_key(current_plan),
                                                     current_plan.uid)
                                                    for current_plan in plans_to_add]
            heapq.heapify(tuples_list)
            self.min_heap = tuples_list
        else:
            for current_plan in plans_to_add:
                plan_tuple = (self.plan_comparison_strategy.plan_to_tuple_key(current_plan), current_plan.uid)
                heapq.heappush(self.min_heap, plan_tuple)

    def select_plan(self, planning_context: PlanningContext, finalizing: bool = False) -> Plan:
        if finalizing:
            active_plans: List[Plan] = [current_plan_context.plan
                                        for current_plan_context in planning_context.plan_by_uid.values()
                                        if (current_plan_context is not None) and
                                        (current_plan_context.plan is not None)]
            tuples_list: List[Tuple[Tuple, str]] = [(self.plan_comparison_strategy.plan_to_tuple_key(current_plan),
                                                     current_plan.uid)
                                                    for current_plan in active_plans]
            select_plan: Optional[Plan] = None
            while select_plan is None:
                select_plan_tuple: tuple[tuple, str] = min(tuples_list)
                select_uid = select_plan_tuple[1]
                if ((self.plan_cache_strategy is not None) and
                        ((planning_context.plan_by_uid[select_uid] is None) or
                         (planning_context.plan_by_uid[select_uid].plan is None))):
                    self.plan_cache_strategy.load_plan(select_uid, planning_context)
                if ((planning_context.plan_by_uid[select_uid] is not None) and
                        (planning_context.plan_by_uid[select_uid].plan is not None)):
                    select_plan = planning_context.plan_by_uid[select_uid].plan
                else:
                    tuples_list.remove(select_plan_tuple)
            return select_plan
        else:
            if len(self.min_heap) == 0:
                active_plans: List[Plan] = [current_plan_context.plan
                                            for current_plan_context in planning_context.plan_by_uid.values()
                                            if (current_plan_context is not None) and
                                            (current_plan_context.plan is not None)]
                self._add_plans_to_heap(active_plans)
            else:
                new_plans: List[Plan] = [PlanningContext.plan_by_uid[curUID].plan
                                         for curUID in planning_context.notes["new plan uids"]
                                         if (PlanningContext.plan_by_uid[curUID] is not None) and
                                         (PlanningContext.plan_by_uid[curUID].plan is not None)]
                self._add_plans_to_heap(new_plans)
            select_plan: Optional[Plan] = None
            while select_plan is None:
                if len(self.min_heap) == 0:
                    active_plans: List[Plan] = [current_plan_context.plan
                                                for current_plan_context in planning_context.plan_by_uid.values()
                                                if (current_plan_context is not None) and
                                                (current_plan_context.plan is not None)]
                    self._add_plans_to_heap(active_plans)
                select_plan_tuple: tuple[tuple, str] = heapq.heappop(self.min_heap)
                select_uid = select_plan_tuple[1]
                if ((self.plan_cache_strategy is not None) and
                        ((planning_context.plan_by_uid[select_uid] is None) or
                         (planning_context.plan_by_uid[select_uid].plan is None))):
                    self.plan_cache_strategy.load_plan(select_uid, planning_context)
                if ((planning_context.plan_by_uid[select_uid] is not None) and
                        (planning_context.plan_by_uid[select_uid].plan is not None)):
                    select_plan = planning_context.plan_by_uid[select_uid].plan
            return select_plan

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        if len(self.values_needed) == 0:
            self.values_needed = self.plan_comparison_strategy.get_values_needed()
        for cur_token in self.values_needed:
            if cur_token == PlanValueToken.min_cost:
                plan_to_populate.min_cost()
            elif cur_token == PlanValueToken.estimated_cost:
                plan_to_populate.estimated_cost()
            elif cur_token == PlanValueToken.max_cost:
                plan_to_populate.max_cost()
            elif cur_token == PlanValueToken.motivation:
                plan_to_populate.motivation()
            elif cur_token == PlanValueToken.satisfied_percentage_average:
                plan_to_populate.average_satisfied_percentage()
            elif cur_token == PlanValueToken.satisfied_percentage_median:
                plan_to_populate.median_satisfied_percentage()

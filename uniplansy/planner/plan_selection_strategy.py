import heapq
from abc import ABCMeta, abstractmethod
from typing import List, Set, Optional

from uniplansy.planner.core import PlanCacheStrategy, PlanningContext
from uniplansy.plans.plan import Plan
from uniplansy.plans.plan_comparison_strategy import PlanComparisonStrategy, PlanComparisonStrategyToken


class PlanSelectionStrategy(metaclass=ABCMeta):

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        pass

    @abstractmethod
    def select_plan(self, planning_context: PlanningContext) -> Plan:
        """selects a plan

        :param planning_context: the planning_context to select a plan from
        :return: the selected plan
        """
        pass

    def prepopulate_plan_cache(self, plan: Plan):
        """prepopulates the cache values of the plan

        :param plan: the plan to prepopulate
        """
        pass


class CommonPlanSelectionStrategy(PlanSelectionStrategy):

    def __init__(self, plan_comparison_strategy: PlanComparisonStrategy):
        self.plan_comparison_strategy = plan_comparison_strategy
        self.values_needed: Set[PlanComparisonStrategyToken] = set()
        self.min_heap = []
        self.plan_cache_strategy: Optional[PlanCacheStrategy] = None
        heapq.heapify(self.min_heap)
        for cur_token in self.plan_comparison_strategy.order:
            if cur_token == PlanComparisonStrategyToken.motivation_over_min_cost:
                self.values_needed.add(PlanComparisonStrategyToken.motivation)
                self.values_needed.add(PlanComparisonStrategyToken.min_cost)
            elif cur_token == PlanComparisonStrategyToken.motivation_over_estimated_cost:
                self.values_needed.add(PlanComparisonStrategyToken.motivation)
                self.values_needed.add(PlanComparisonStrategyToken.estimated_cost)
            elif cur_token == PlanComparisonStrategyToken.motivation_over_max_cost:
                self.values_needed.add(PlanComparisonStrategyToken.motivation)
                self.values_needed.add(PlanComparisonStrategyToken.max_cost)
            elif cur_token == PlanComparisonStrategyToken.min_cost_over_motivation:
                self.values_needed.add(PlanComparisonStrategyToken.motivation)
                self.values_needed.add(PlanComparisonStrategyToken.min_cost)
            elif cur_token == PlanComparisonStrategyToken.estimated_cost_over_motivation:
                self.values_needed.add(PlanComparisonStrategyToken.motivation)
                self.values_needed.add(PlanComparisonStrategyToken.estimated_cost)
            elif cur_token == PlanComparisonStrategyToken.max_cost_over_motivation:
                self.values_needed.add(PlanComparisonStrategyToken.motivation)
                self.values_needed.add(PlanComparisonStrategyToken.max_cost)
            elif cur_token == PlanComparisonStrategyToken.min_cost:
                self.values_needed.add(PlanComparisonStrategyToken.min_cost)
            elif cur_token == PlanComparisonStrategyToken.estimated_cost:
                self.values_needed.add(PlanComparisonStrategyToken.estimated_cost)
            elif cur_token == PlanComparisonStrategyToken.max_cost:
                self.values_needed.add(PlanComparisonStrategyToken.max_cost)
            elif cur_token == PlanComparisonStrategyToken.motivation:
                self.values_needed.add(PlanComparisonStrategyToken.motivation)
            elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_average_asc:
                self.values_needed.add(PlanComparisonStrategyToken.satisfied_percentage_average_asc)
            elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_average_des:
                self.values_needed.add(PlanComparisonStrategyToken.satisfied_percentage_average_asc)
            elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_median_asc:
                self.values_needed.add(PlanComparisonStrategyToken.satisfied_percentage_median_asc)
            elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_median_des:
                self.values_needed.add(PlanComparisonStrategyToken.satisfied_percentage_median_asc)

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        self.plan_cache_strategy = plan_cache_strategy

    def select_plan(self, planning_context: PlanningContext) -> Plan:
        new_plans: List[Plan] = [PlanningContext.plan_by_uid[curUID].plan
                                 for curUID in planning_context.notes["new plan uids"]
                                 if (PlanningContext.plan_by_uid[curUID] is not None) and
                                 (PlanningContext.plan_by_uid[curUID].plan is not None)]
        for current_plan in new_plans:
            plan_tuple = (self.plan_comparison_strategy.plan_to_tuple_key(current_plan), current_plan.uid)
            heapq.heappush(self.min_heap, plan_tuple)
        select_plan:Optional[Plan] = None
        while select_plan is None:
            select_plan_tuple: tuple[tuple, Plan] = heapq.heappop(self.min_heap)
            select_uid = select_plan_tuple[1]
            if ((self.plan_cache_strategy is not None) and
                    ((planning_context.plan_by_uid[select_uid] is None) or
                     (planning_context.plan_by_uid[select_uid].plan is None))):
                self.plan_cache_strategy.load_plan(select_uid,planning_context)
            if ((planning_context.plan_by_uid[select_uid] is not None) and
                    (planning_context.plan_by_uid[select_uid].plan is not None)):
                select_plan = planning_context.plan_by_uid[select_uid].plan
        return select_plan

    def prepopulate_plan_cache(self, plan: Plan):
        for cur_token in self.values_needed:
            if cur_token == PlanComparisonStrategyToken.min_cost:
                plan.min_cost()
            elif cur_token == PlanComparisonStrategyToken.estimated_cost:
                plan.estimated_cost()
            elif cur_token == PlanComparisonStrategyToken.max_cost:
                plan.max_cost()
            elif cur_token == PlanComparisonStrategyToken.motivation:
                plan.motivation()
            elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_average_asc:
                plan.average_satisfied_percentage()
            elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_median_asc:
                plan.median_satisfied_percentage()

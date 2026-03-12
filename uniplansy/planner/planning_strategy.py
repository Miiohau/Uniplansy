"""defines PlanningStrategy and some subclasses. A PlanningStrategy can be used to select a Plan Decomposer pair

PlanningStrategy(interface): the abstract planning strategy that can be used to select a Plan Decomposer pair
DelegatingPlanningStrategy(PlanningStrategy): Delegates the planning to a plan_selection_strategy and
a decomposer_selection_strategy
GreedyPlanningStrategy(PlanningStrategy): a greedy PlanningStrategy that returns plans in sort order
        (determined by plan_comparison_strategy: PlanComparisonStrategy)
"""
import heapq
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional, Set, List, Iterable

from uniplansy.decomposers.core import Decomposer, decomposer_registry
from uniplansy.planner.core import PlanCacheStrategy, PlanningContext, PlanContext
from uniplansy.planner.decomposer_selection_strategy import DecomposerSelectionStrategy
from uniplansy.planner.plan_selection_strategy import FullPlanSelectionStrategy
from uniplansy.plans.plan import Plan, PlanDeltas
from uniplansy.plans.plan_comparison_strategy import PlanComparisonStrategy, PlanValueToken
from uniplansy.util.id_registry import RegistryKeyNotFoundError

# TODO: make a compositable PlanningStrategy by having the plan method equivalent take a list parameter of
#  Plan, Decomposer pairs and return a list of Plan, Decomposer pairs
class PlanningStrategy(metaclass=ABCMeta):
    """a PlanningStrategy can be used to select a Plan Decomposer pair

    plan(method): selects a plan and a decomposer
    introduce_plan_cache_strategy(method):introduces a PlanCacheStrategy to the PlanningStrategy which it may save.
    prepopulate_plan_cache(method): prepopulates the cache values of the plan
    """

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        """introduces a PlanCacheStrategy to the PlanningStrategy which it may save.

        The intended use of a saved PlanCacheStrategy by a PlanningStrategy is to request offloaded plans be
        reloaded back into memory
        :param plan_cache_strategy: the plan_cache_strategy being introduced
        """
        pass

    @abstractmethod
    def plan(self, planning_context: PlanningContext, decomposers: set[Decomposer]) -> tuple[Plan, Decomposer]:
        """selects a plan and a decomposer

        :param planning_context: the planning_context
        :param decomposers: the set of all the decomposers
        :return: selected the plan and decomposer
        """
        pass

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        """prepopulates the cache values of the plan

        :param plan_to_populate: the plan to prepopulate
        """
        pass


@dataclass
class DelegatingPlanningStrategy(PlanningStrategy):
    """Delegates the planning to a plan_selection_strategy and a decomposer_selection_strategy

    assumes plan_selection_strategy will eventually select a plan that
    decomposer_selection_strategy can select a decomposer for
    plan_selection_strategy(property): the PlanSelectionStrategy to use to select a plan
    decomposer_selection_strategy(property): the DecomposerSelectionStrategy to use to select a decomposer
    """
    plan_selection_strategy: FullPlanSelectionStrategy
    decomposer_selection_strategy: DecomposerSelectionStrategy

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        self.plan_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)
        self.decomposer_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)

    def plan(self, planning_context: PlanningContext, decomposers: set[Decomposer]) -> tuple[Plan, Decomposer]:
        selected_plan: Optional[Plan] = None
        selected_decomposer: Optional[Decomposer] = None
        while (selected_plan is None) or (selected_decomposer is None):
            selected_plan = self.plan_selection_strategy.select_plan(planning_context)
            if selected_plan is not None:
                selected_decomposer = self.decomposer_selection_strategy.select_decomposer(
                    planning_context.plan_by_uid[selected_plan.uid],
                    decomposers
                )
        return selected_plan, selected_decomposer

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        self.plan_selection_strategy.prepopulate_plan_cache(plan_to_populate)


class GreedyPlanningStrategy(PlanningStrategy):
    """a greedy PlanningStrategy that returns Plan Decomposer pairs in sort order
        (determined by plan_comparison_strategy: PlanComparisonStrategy)"""

    def __init__(self, plan_comparison_strategy: PlanComparisonStrategy):
        self.plan_comparison_strategy = plan_comparison_strategy
        self.values_needed: Set[PlanValueToken] = set()
        self.min_heap: List[tuple[tuple, tuple[str, Optional[str]]]] = []
        self.plan_cache_strategy: Optional[PlanCacheStrategy] = None

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        self.plan_cache_strategy = plan_cache_strategy

    def _add_plans_to_heap(self, plans_to_add: Iterable[Plan]):
        if len(self.min_heap) == 0:
            tuples_list: List[tuple[tuple, tuple[str, Optional[str]]]] = \
                [(self.plan_comparison_strategy.plan_to_tuple_key(current_plan), (current_plan.uid, None))
                 for current_plan in plans_to_add]
            heapq.heapify(tuples_list)
            self.min_heap = tuples_list
        else:
            for current_plan in plans_to_add:
                plan_tuple: tuple[tuple, tuple[str, Optional[str]]] = \
                    (self.plan_comparison_strategy.plan_to_tuple_key(current_plan), (current_plan.uid, None))
                heapq.heappush(self.min_heap, plan_tuple)

    def plan(self, planning_context: PlanningContext, decomposers: set[Decomposer]) -> tuple[Plan, Decomposer]:
        new_plans: List[Plan] = [PlanningContext.plan_by_uid[curUID].plan
                                 for curUID in planning_context.notes["new plan uids"]
                                 if (PlanningContext.plan_by_uid[curUID] is not None) and
                                 (PlanningContext.plan_by_uid[curUID].plan is not None)]
        self._add_plans_to_heap(new_plans)
        selected_plan: Optional[Plan] = None
        selected_decomposer: Optional[Decomposer] = None
        while (selected_plan is None) or (selected_decomposer is None):
            selected_plan_decomposer_tuple: tuple[tuple, tuple[str, Optional[str]]] = heapq.heappop(self.min_heap)
            if ((planning_context.plan_by_uid[selected_plan_decomposer_tuple[1][0]] is None) or
                    (planning_context.plan_by_uid[selected_plan_decomposer_tuple[1][0]].plan is None)):
                self.plan_cache_strategy.load_plan(selected_plan_decomposer_tuple[1][0], planning_context)
            selected_plan_context: Optional[PlanContext] = planning_context.plan_by_uid[
                selected_plan_decomposer_tuple[1][0]
            ]
            if selected_plan_context is not None:
                selected_plan = selected_plan_context.plan
                if selected_plan_decomposer_tuple[1][1] is not None:
                    try:
                        selected_decomposer = decomposer_registry.fetch(selected_plan_decomposer_tuple[1][1])
                    except RegistryKeyNotFoundError:
                        selected_decomposer = None
                else:
                    if selected_plan is not None:
                        for current_decomposer in decomposers:
                            if current_decomposer.applicable(selected_plan):
                                delta: PlanDeltas = current_decomposer.estimate_deltas(selected_plan)
                                new_plan_decomposer_tuple: tuple[tuple, tuple[str, Optional[str]]] = (
                                    self.plan_comparison_strategy.plan_plus_delta_to_tuple_key(selected_plan, delta),
                                    (selected_plan.uid, current_decomposer.uid)
                                )
                                heapq.heappush(self.min_heap, new_plan_decomposer_tuple)
        return selected_plan, selected_decomposer

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


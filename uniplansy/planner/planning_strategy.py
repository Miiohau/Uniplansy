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
from uniplansy.planner.base import PlanningContext, PlanContext, PlanningStrategy, PlanCacheStrategy
from uniplansy.planner.decomposer_selection_strategy import DecomposerSelectionStrategy
from uniplansy.planner.plan_selection_strategy import FullPlanSelectionStrategy
from uniplansy.plans.plan import Plan, PlanDeltas
from uniplansy.plans.plan_comparison_strategy import PlanComparisonStrategy, PlanValueToken
from uniplansy.util.global_type_vars import World_Type
from uniplansy.util.id_registry import RegistryKeyNotFoundError


# TODO: make a compositable PlanningStrategy by having the plan method equivalent take a list parameter of
#  Plan, Decomposer pairs and return a list of Plan, Decomposer pairs


class FullPlanningStrategy(PlanningStrategy, metaclass=ABCMeta):
    """a FullPlanningStrategy can be used to select a Plan Decomposer pair

    plan(method): selects a plan and a decomposer
    introduce_plan_cache_strategy(method):introduces a PlanCacheStrategy to the PlanningStrategy which it may save.
    prepopulate_plan_cache(method): prepopulates the cache values of the plan
    """

    @abstractmethod
    def plan(self, planning_context: PlanningContext, world: World_Type, decomposers: set[Decomposer]) \
            -> Optional[tuple[Plan, Optional[Decomposer]]]:
        """selects a plan and a decomposer

        :param world: the world being planed in
        :param planning_context: the planning context
        :param decomposers: the set of all the decomposers
        :return: selected the plan and decomposer
        """
        pass


class PartialPlanningStrategy(PlanningStrategy, metaclass=ABCMeta):
    """TODO: docstring"""

    @abstractmethod
    def filter_plans(
            self,
            plan_decomposer_pairs_to_filter: Iterable[Optional[tuple[Plan, Optional[Decomposer]]]],
            planning_context: PlanningContext,
            world: World_Type,
            decomposers: set[Decomposer]
    ) -> Iterable[Optional[tuple[Plan, Optional[Decomposer]]]]:
        """filters the plan Decomposer tuple stream

        :param plan_decomposer_pairs_to_filter: the stream of plan Decomposer pairs
        :param planning_context: the planning context
        :param world: the world being planed in
        :param decomposers: the set of all the decomposers
        :return: the filtered stream of plan Decomposer pairs
        """
        pass


class PlanningFilterStrategy(PartialPlanningStrategy, metaclass=ABCMeta):
    """TODO: docstring"""

    @abstractmethod
    def accept_plan(self,
                    plan: Plan,
                    decomposer: Optional[Decomposer],
                    planning_context: PlanningContext,
                    world: World_Type,
                    decomposers: set[Decomposer]
                    ) -> bool:
        """accepts or rejects the plan decomposer pair

        :param plan: the plan being checked
        :param decomposer: the decomposer being checked
        :param planning_context: the planning context
        :param world: the world being planed in
        :param decomposers: the set of all the decomposers
        """
        pass

    @abstractmethod
    def filter_plans(
            self,
            plan_decomposer_pairs_to_filter: Iterable[Optional[tuple[Plan, Optional[Decomposer]]]],
            planning_context: PlanningContext,
            world: World_Type,
            decomposers: set[Decomposer]
    ) -> Iterable[Optional[tuple[Plan, Optional[Decomposer]]]]:
        for (current_plan, current_decomposer) in plan_decomposer_pairs_to_filter:
            if ((current_plan is not None) and
                    self.accept_plan(current_plan, current_decomposer, planning_context, world, decomposers)):
                yield current_plan, current_decomposer


class InitialPartialPlanningStrategy(PlanningStrategy):
    """TODO: docstring"""

    @abstractmethod
    def start_iterable(self, planning_context: PlanningContext, world: World_Type, decomposers: set[Decomposer]) \
            -> Iterable[Optional[tuple[Plan, Optional[Decomposer]]]]:
        """starts the plan decomposer pairs stream

        :param planning_context: the planning context
        :param world: the world being planed in
        :param decomposers: the set of all the decomposers
        """
        pass


class FinalPlanningStrategy(PlanningStrategy):
    """TODO: docstring"""

    @abstractmethod
    def select_plan_from_iterable(
            self,
            plans_to_filter: Iterable[Optional[tuple[Plan, Optional[Decomposer]]]],
            planning_context: PlanningContext,
            world: World_Type,
            decomposers: set[Decomposer]
    ) -> Optional[tuple[Plan, Optional[Decomposer]]]:
        """selects a plan Decomposer pair from the iterable

        :param plans_to_filter: the stream of plan Decomposer pairs
        :param planning_context: the planning context
        :param world: the world being planed in
        :param decomposers: the set of all the decomposers
        """
        pass


@dataclass
class DelegatingPlanningStrategy(FullPlanningStrategy):
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

    def plan(self, planning_context: PlanningContext, world: World_Type, decomposers: set[Decomposer]) \
            -> Optional[tuple[Plan, Optional[Decomposer]]]:
        selected_plan: Optional[Plan] = None
        selected_decomposer: Optional[Decomposer] = None
        while (selected_plan is None) or (selected_decomposer is None):
            selected_plan = self.plan_selection_strategy.select_plan(planning_context, world)
            if selected_plan is not None:
                selected_decomposer = self.decomposer_selection_strategy.select_decomposer(
                    planning_context.plan_context_by_uid[selected_plan.uid],
                    world,
                    decomposers
                )
        return selected_plan, selected_decomposer

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        self.plan_selection_strategy.prepopulate_plan_cache(plan_to_populate)

# todo: take advange of self.planning_context.notes["new decomposer uids"]
class GreedyPlanningStrategy(FullPlanningStrategy,
                             InitialPartialPlanningStrategy,
                             FinalPlanningStrategy):
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

    def start_iterable(self, planning_context: PlanningContext, world: World_Type, decomposers: set[Decomposer]) \
            -> Iterable[Optional[tuple[Plan, Optional[Decomposer]]]]:
        if len(self.min_heap) == 0:
            active_plans: List[Plan] = [current_plan_context.plan
                                        for current_plan_context in planning_context.plan_context_by_uid.values()
                                        if (current_plan_context is not None) and
                                        (current_plan_context.plan is not None)]
            self._add_plans_to_heap(active_plans)
        else:
            new_plans: List[Plan] = [PlanningContext.plan_context_by_uid[curUID].plan
                                     for curUID in planning_context.notes["new plan uids"]
                                     if (PlanningContext.plan_context_by_uid[curUID] is not None) and
                                     (PlanningContext.plan_context_by_uid[curUID].plan is not None)]
            self._add_plans_to_heap(new_plans)
        while True:
            if len(self.min_heap) == 0:
                active_plans: List[Plan] = [current_plan_context.plan
                                            for current_plan_context in planning_context.plan_context_by_uid.values()
                                            if (current_plan_context is not None) and
                                            (current_plan_context.plan is not None)]
                self._add_plans_to_heap(active_plans)
            select_plan_tuple: tuple[tuple, tuple[str, Optional[str]]] = heapq.heappop(self.min_heap)
            selected_plan_uid: str = select_plan_tuple[1][0]
            selected_decomposer_uid: str = select_plan_tuple[1][1]
            selected_decomposer: Optional[Decomposer] = None
            if ((self.plan_cache_strategy is not None) and
                    ((planning_context.plan_context_by_uid[selected_plan_uid] is None) or
                     (planning_context.plan_context_by_uid[selected_plan_uid].plan is None))):
                self.plan_cache_strategy.load_plan(selected_plan_uid, planning_context)
            if selected_decomposer_uid is not None:
                try:
                    selected_decomposer = decomposer_registry.fetch(selected_decomposer_uid)
                except RegistryKeyNotFoundError:
                    selected_decomposer = None
            if planning_context.plan_context_by_uid[selected_plan_uid].plan is None:
                continue
            if ((planning_context.plan_context_by_uid[selected_plan_uid] is not None) and
                    (planning_context.plan_context_by_uid[selected_plan_uid].plan is not None)):
                yield (planning_context.plan_context_by_uid[selected_plan_uid].plan,
                       selected_decomposer)

    def plan(self, planning_context: PlanningContext, world: World_Type, decomposers: set[Decomposer]) \
            -> Optional[tuple[Plan, Optional[Decomposer]]]:
        new_plans: List[Plan] = [PlanningContext.plan_context_by_uid[curUID].plan
                                 for curUID in planning_context.notes["new plan uids"]
                                 if (PlanningContext.plan_context_by_uid[curUID] is not None) and
                                 (PlanningContext.plan_context_by_uid[curUID].plan is not None)]
        self._add_plans_to_heap(new_plans)
        selected_plan: Optional[Plan] = None
        selected_decomposer: Optional[Decomposer] = None
        while (selected_plan is None) or (selected_decomposer is None):
            selected_plan_decomposer_tuple: tuple[tuple, tuple[str, Optional[str]]] = heapq.heappop(self.min_heap)
            if ((planning_context.plan_context_by_uid[selected_plan_decomposer_tuple[1][0]] is None) or
                    (planning_context.plan_context_by_uid[selected_plan_decomposer_tuple[1][0]].plan is None)):
                self.plan_cache_strategy.load_plan(selected_plan_decomposer_tuple[1][0], planning_context)
            selected_plan_context: Optional[PlanContext] = planning_context.plan_context_by_uid[
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
                            if current_decomposer.applicable(selected_plan, world):
                                delta: PlanDeltas = current_decomposer.estimate_deltas(selected_plan, world)
                                new_plan_decomposer_tuple: tuple[tuple, tuple[str, Optional[str]]] = (
                                    self.plan_comparison_strategy.plan_plus_delta_to_tuple_key(selected_plan, delta),
                                    (selected_plan.uid, current_decomposer.uid)
                                )
                                heapq.heappush(self.min_heap, new_plan_decomposer_tuple)
        return selected_plan, selected_decomposer

    def select_plan_from_iterable(
            self,
            plans_to_filter: Iterable[Optional[tuple[Plan, Optional[Decomposer]]]],
            planning_context: PlanningContext,
            world: World_Type,
            decomposers: set[Decomposer]
    ) -> Optional[tuple[Plan, Optional[Decomposer]]]:
        # todo: this is flawed because it assumes current_decomposer is not null and doesn't apply the deltas
        # tuples_list: List[tuple[tuple, tuple[str, Optional[str]]]] = [
        #    (
        #        self.plan_comparison_strategy.plan_to_tuple_key(current_plan),
        #        (current_plan.uid, current_decomposer.uid)
        #    )
        #    for (current_plan, current_decomposer) in plans_to_filter]
        tuples_list: List[tuple[tuple, tuple[str, Optional[str]]]] = list()
        for (current_plan, current_decomposer) in plans_to_filter:
            new_plan_decomposer_tuple: tuple[tuple, tuple[str, Optional[str]]]
            if current_decomposer is not None:
                delta: PlanDeltas = current_decomposer.estimate_deltas(current_plan, world)
                new_plan_decomposer_tuple = (
                    self.plan_comparison_strategy.plan_plus_delta_to_tuple_key(current_plan, delta),
                    (current_plan.uid, current_decomposer.uid)
                )
            else:
                new_plan_decomposer_tuple = (
                    self.plan_comparison_strategy.plan_to_tuple_key(current_plan),
                    (current_plan.uid, None)
                )
            tuples_list.append(new_plan_decomposer_tuple)
        selected_plan: Optional[Plan] = None
        selected_decomposer: Optional[Decomposer] = None
        while (selected_plan is None) or (selected_decomposer is None):
            selected_plan_decomposer_tuple: tuple[tuple, tuple[str, Optional[str]]] = min(tuples_list)
            tuples_list.remove(selected_plan_decomposer_tuple)
            if ((planning_context.plan_context_by_uid[selected_plan_decomposer_tuple[1][0]] is None) or
                    (planning_context.plan_context_by_uid[selected_plan_decomposer_tuple[1][0]].plan is None)):
                self.plan_cache_strategy.load_plan(selected_plan_decomposer_tuple[1][0], planning_context)
            selected_plan_context: Optional[PlanContext] = planning_context.plan_context_by_uid[
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
                            if current_decomposer.applicable(selected_plan, world):
                                delta: PlanDeltas = current_decomposer.estimate_deltas(selected_plan, world)
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
                plan_to_populate.total_motivation()
            elif cur_token == PlanValueToken.satisfied_percentage_average:
                plan_to_populate.average_satisfied_percentage()
            elif cur_token == PlanValueToken.satisfied_percentage_median:
                plan_to_populate.median_satisfied_percentage()

# standard PlanningStrategies
# TODO: create these classes
# Composite (full)
# Not filter
# Or filter
# Random
# First Valid
# Arbitrary Initial
# Greedy
# plan filter to planning filter
# decomposer filter to planning filter
# deepest first filter
# shallowest first filter
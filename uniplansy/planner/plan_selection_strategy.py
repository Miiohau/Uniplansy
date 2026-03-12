"""defines the PlanSelectionStrategy and some subclasses. a PlanSelectionStrategy selects a plan in the context of a
planning_context.

PlanSelectionStrategy(Interface): the core class of this module. a plan selection strategy selects a plan in the
context of a planning_context.
GreedyPlanSelectionStrategy(PlanSelectionStrategy):a greedy PlanSelectionStrategy that returns plans in sort order
(determined by plan_comparison_strategy: PlanComparisonStrategy)
"""
import heapq
from abc import ABCMeta, abstractmethod
from random import Random
from typing import List, Set, Optional, Iterable, Tuple

from uniplansy.planner.core import PlanCacheStrategy, PlanningContext
from uniplansy.plans.plan import Plan
from uniplansy.plans.plan_comparison_strategy import PlanComparisonStrategy, PlanValueToken


class PlanSelectionStrategy(metaclass=ABCMeta):
    """TODO: docstring"""

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        """introduces a PlanCacheStrategy to the PlanSelectionStrategy which it may save.

        The intended use of a saved PlanCacheStrategy by a PlanSelectionStrategy is to request offloaded plans be
        reloaded back into memory
        :param plan_cache_strategy: the plan_cache_strategy being introduced
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

class FullPlanSelectionStrategy(PlanSelectionStrategy, metaclass=ABCMeta):
    """a FullPlanSelectionStrategy selects a plan in the context of a planning_context

    select_plan(method): the core method that selects a plan
    introduce_plan_cache_strategy(method):introduces a PlanCacheStrategy to the PlanSelectionStrategy which it may save.
    prepopulate_plan_cache(method): prepopulates the cache values of the plan
    """

    @abstractmethod
    def select_plan(self, planning_context: PlanningContext, finalizing: bool = False) -> Plan:
        """selects a plan

        :param planning_context: the planning_context to select a plan from
        :param finalizing: whether it is being called to select the final returned plan
        :return: the selected plan
        """
        pass

class PartialPlanSelectionStrategy(PlanSelectionStrategy, metaclass=ABCMeta):
    """TODO: docstring"""

    @abstractmethod
    def filter_plans(
            self,
            plans_to_filter: Iterable[Plan],
            planning_context: PlanningContext,
            finalizing: bool = False
    ) -> Iterable[Plan]:
        pass

class PlanFilterStrategy(PartialPlanSelectionStrategy, metaclass=ABCMeta):
    """TODO: docstring"""

    @abstractmethod
    def accept_plan(self, plan: Plan, planning_context: PlanningContext, finalizing: bool = False) -> bool:
        pass

    def filter_plans(
            self,
            plans_to_filter: Iterable[Plan],
            planning_context: PlanningContext,
            finalizing: bool = False
    ) -> Iterable[Plan]:
        for current_plan in plans_to_filter:
            if self.accept_plan(current_plan, planning_context, finalizing):
                yield current_plan


class InitialPartialPlanSelectionStrategy(PlanSelectionStrategy):
    """TODO: docstring"""

    @abstractmethod
    def start_iterable(self, planning_context: PlanningContext, finalizing: bool = False) -> Iterable[Plan]:
        pass

class FinalPartialPlanSelectionStrategy(PlanSelectionStrategy):
    """TODO: docstring"""

    @abstractmethod
    def select_plan_from_iterable(
            self,
            plans_to_filter: Iterable[Plan],
            planning_context: PlanningContext,
            finalizing: bool = False
    ) -> Plan:
        pass


class NotPlanFilterStrategy(PlanFilterStrategy):

    def __init__(self, wrapped_plan_filter_strategy: PlanFilterStrategy):
        self.wrapped_plan_filter_strategy = wrapped_plan_filter_strategy

    def accept_plan(self, plan: Plan, planning_context: PlanningContext, finalizing: bool = False) -> bool:
        return not self.wrapped_plan_filter_strategy.accept_plan(plan, planning_context, finalizing)

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        self.wrapped_plan_filter_strategy.introduce_plan_cache_strategy(plan_cache_strategy)

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        self.wrapped_plan_filter_strategy.prepopulate_plan_cache(plan_to_populate)

class OrPlanFilterStrategy(PlanFilterStrategy):

    def __init__(self, wrapped_plan_filter_strategies: List[PlanFilterStrategy]):
        self.wrapped_plan_filter_strategies = wrapped_plan_filter_strategies

    def accept_plan(self, plan: Plan, planning_context: PlanningContext, finalizing: bool = False) -> bool:
        for current_plan_filter_strategy in self.wrapped_plan_filter_strategies:
            if current_plan_filter_strategy.accept_plan(plan, planning_context, finalizing):
                return True
        return False

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        for current_partial_plan_selection_strategy in self.wrapped_plan_filter_strategies:
            current_partial_plan_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        for current_partial_plan_selection_strategy in self.wrapped_plan_filter_strategies:
            current_partial_plan_selection_strategy.prepopulate_plan_cache(plan_to_populate)

class RandomPlanSelectionStrategy(FinalPartialPlanSelectionStrategy):
    """TODO: docstring"""

    def __init__(self, limit: int = 100, rnd: Random = Random()):
        self.limit = limit
        self.rnd = rnd

    def select_plan_from_iterable(
            self,
            plans_to_filter: Iterable[Plan],
            planning_context: PlanningContext,
            finalizing: bool = False
    ) -> Plan:
        plan_list: List[Plan] = []
        plans_to_filter_iter =iter(plans_to_filter)
        while len(plan_list) < self.limit:
            try:
                plan_list.append(next(plans_to_filter_iter))
            except StopIteration:
                break
        return self.rnd.choice(plan_list)


class FirstValidPlanSelectionStrategy(FinalPartialPlanSelectionStrategy):

    def select_plan_from_iterable(
            self,
            plans_to_filter: Iterable[Plan],
            planning_context: PlanningContext,
            finalizing: bool = False
    ) -> Plan:
        return next(iter(plans_to_filter))

class ArbitraryInitialPartialPlanSelectionStrategy(InitialPartialPlanSelectionStrategy):
    """TODO: docstring"""

    def start_iterable(self, planning_context: PlanningContext, finalizing: bool = False) -> Iterable[Plan]:
        return (current_plan_context.plan
                for current_plan_context in planning_context.plan_by_uid.values()
                if (current_plan_context is not None) and
                (current_plan_context.plan is not None))

class CompositeFullPlanSelectionStrategy(FullPlanSelectionStrategy):
    """TODO: docstring

    needs a initial/final plan selection strategy but will try to find suitable strategies in
    partial_plan_selection_strategies or the other final/initial plan selection strategy, if it doesn't find any it will
    use ArbitraryInitialPartialPlanSelectionStrategy for the initial_plan_selection_strategy and
    RandomPlanSelectionStrategy for the final_plan_selection_strategy.
    initial_plan_selection_strategy(initialization parameter): TODO: docstring
    final_plan_selection_strategy(initialization parameter): the strategy to use to select the final plan
    partial_plan_selection_strategies(initialization parameter): TODO: docstring"""

    def __init__(self,
                 initial_plan_selection_strategy: Optional[InitialPartialPlanSelectionStrategy] = None,
                 final_plan_selection_strategy: Optional[FinalPartialPlanSelectionStrategy] = None,
                 partial_plan_selection_strategies: Optional[List[PartialPlanSelectionStrategy]] = None
                 ):
        if partial_plan_selection_strategies is None:
            partial_plan_selection_strategies = []
        self.initial_plan_selection_strategy = initial_plan_selection_strategy
        self.final_plan_selection_strategy = final_plan_selection_strategy
        self.partial_plan_selection_strategies = partial_plan_selection_strategies

    def select_plan(self, planning_context: PlanningContext, finalizing: bool = False) -> Plan:
        if self.initial_plan_selection_strategy is None:
            for current_partial_plan_selection_strategy in self.partial_plan_selection_strategies:
                if isinstance(current_partial_plan_selection_strategy, InitialPartialPlanSelectionStrategy):
                    self.initial_plan_selection_strategy = current_partial_plan_selection_strategy
                    break
            if self.initial_plan_selection_strategy is None:
                if isinstance(self.final_plan_selection_strategy, InitialPartialPlanSelectionStrategy):
                    self.initial_plan_selection_strategy = self.final_plan_selection_strategy
                else:
                    self.initial_plan_selection_strategy = ArbitraryInitialPartialPlanSelectionStrategy()
        if self.final_plan_selection_strategy is None:
            for current_partial_plan_selection_strategy in reversed(self.partial_plan_selection_strategies):
                if isinstance(current_partial_plan_selection_strategy, FinalPartialPlanSelectionStrategy):
                    self.final_plan_selection_strategy = current_partial_plan_selection_strategy
                    break
            if self.final_plan_selection_strategy is None:
                if isinstance(self.initial_plan_selection_strategy, FinalPartialPlanSelectionStrategy):
                    self.final_plan_selection_strategy = self.initial_plan_selection_strategy
                else:
                    self.final_plan_selection_strategy = RandomPlanSelectionStrategy()
        chain_iterable: Iterable[Plan] = (
            self.initial_plan_selection_strategy.start_iterable(planning_context, finalizing))
        for current_partial_plan_selection_strategy in self.partial_plan_selection_strategies:
            chain_iterable = (
                current_partial_plan_selection_strategy.filter_plans(chain_iterable, planning_context, finalizing)
            )
        return self.final_plan_selection_strategy.select_plan_from_iterable(chain_iterable,
                                                                            planning_context,
                                                                            finalizing)

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        if self.initial_plan_selection_strategy is not None:
            self.initial_plan_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)
        for current_partial_plan_selection_strategy in self.partial_plan_selection_strategies:
            current_partial_plan_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)
        if self.final_plan_selection_strategy is not None:
            self.final_plan_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)

    def prepopulate_plan_cache(self, plan_to_populate: Plan):
        if self.initial_plan_selection_strategy is not None:
            self.initial_plan_selection_strategy.prepopulate_plan_cache(plan_to_populate)
        for current_partial_plan_selection_strategy in self.partial_plan_selection_strategies:
            current_partial_plan_selection_strategy.prepopulate_plan_cache(plan_to_populate)
        if self.final_plan_selection_strategy is not None:
            self.final_plan_selection_strategy.prepopulate_plan_cache(plan_to_populate)


class GreedyPlanSelectionStrategy(FullPlanSelectionStrategy,
                                  InitialPartialPlanSelectionStrategy,
                                  FinalPartialPlanSelectionStrategy):
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

    def start_iterable(self, planning_context: PlanningContext, finalizing: bool = False) -> Iterable[Plan]:
        if finalizing:
            active_plans: List[Plan] = [current_plan_context.plan
                                        for current_plan_context in planning_context.plan_by_uid.values()
                                        if (current_plan_context is not None) and
                                        (current_plan_context.plan is not None)]
            tuples_list: List[Tuple[Tuple, str]] = [(self.plan_comparison_strategy.plan_to_tuple_key(current_plan),
                                                     current_plan.uid)
                                                    for current_plan in active_plans]
            heapq.heapify(tuples_list)
            while len(tuples_list) >= 1:
                selected_tuple: Tuple[Tuple, str] = heapq.heappop(tuples_list)
                yield planning_context.plan_by_uid[selected_tuple[1]].plan
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
            while True:
                if len(self.min_heap) == 0:
                    active_plans: List[Plan] = [current_plan_context.plan
                                                for current_plan_context in planning_context.plan_by_uid.values()
                                                if (current_plan_context is not None) and
                                                (current_plan_context.plan is not None)]
                    self._add_plans_to_heap(active_plans)
                select_plan_tuple: tuple[tuple, str] = heapq.heappop(self.min_heap)
                selected_uid: str = select_plan_tuple[1]
                if ((self.plan_cache_strategy is not None) and
                        ((planning_context.plan_by_uid[selected_uid] is None) or
                         (planning_context.plan_by_uid[selected_uid].plan is None))):
                    self.plan_cache_strategy.load_plan(selected_uid, planning_context)
                if ((planning_context.plan_by_uid[selected_uid] is not None) and
                        (planning_context.plan_by_uid[selected_uid].plan is not None)):
                    yield planning_context.plan_by_uid[selected_uid].plan

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

    def select_plan_from_iterable(
            self,
            plans_to_filter: Iterable[Plan],
            planning_context: PlanningContext,
            finalizing: bool = False
    ) -> Plan:
        tuples_list: List[Tuple[Tuple, str]] = [(self.plan_comparison_strategy.plan_to_tuple_key(current_plan),
                                                 current_plan.uid)
                                                for current_plan in plans_to_filter]
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
            elif cur_token == PlanValueToken.tasks_fully_satisfied_percentage:
                plan_to_populate.tasks_fully_satisfied_percentage()
            elif cur_token == PlanValueToken.concrete_action_percentage:
                plan_to_populate.concrete_action_percentage()

# standard PlanSelectionStrategies
# all tasks satisfied filter/fully concrete plan filter
# at least one concrete action plan filter
# at least one unsatisfied task filter/at least one non-concrete action plan filter
# deepest plan first filter
# shallowest plan first filter

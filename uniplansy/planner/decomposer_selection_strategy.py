"""defines DecomposerSelectionStrategy and some of its subclasses. a DecomposerSelectionStrategy selects a decomposer
to apply to a plan.

DecomposerSelectionStrategy(interface): a DecomposerSelectionStrategy selects a decomposer to apply to a plan
GreedyDecomposerSelectionStrategy(DecomposerSelectionStrategy): a greedy DecomposerSelectionStrategy that returns
Decomposers in sort order (determined by plan_comparison_strategy: PlanComparisonStrategy)
"""
import heapq
from abc import ABCMeta, abstractmethod
from random import Random
from typing import Optional, List, Tuple, Iterable

from uniplansy.decomposers.core import Decomposer, decomposer_registry
from uniplansy.planner.base import PlanContext, MaybeWantsToKnowPlanCacheStrategy, PlanCacheStrategy
from uniplansy.plans.plan_comparison_strategy import PlanComparisonStrategy
from uniplansy.util.global_type_vars import World_Type
from uniplansy.util.id_registry import RegistryKeyNotFoundError


class DecomposerSelectionStrategy(MaybeWantsToKnowPlanCacheStrategy, metaclass=ABCMeta):
    """a DecomposerSelectionStrategy selects a decomposer to apply to a plan."""


class FullDecomposerSelectionStrategy(DecomposerSelectionStrategy, metaclass=ABCMeta):
    """a FullDecomposerSelectionStrategy selects a decomposer to apply to a plan

    select_decomposer(method): selects a decomposer to apply to the plan
    introduce_plan_cache_strategy(method):introduces a PlanCacheStrategy to the FullDecomposerSelectionStrategy
    which it may save.
    """

    @abstractmethod
    def select_decomposer(self, context: PlanContext, world: World_Type, decomposers: set[Decomposer]) -> Optional[
        Decomposer]:
        """selects a decomposer to apply to the plan

        :param world: the world being planned in
        :param context: the plan context of the plan
        :param decomposers: the set of all the decomposers
        :return: the selected decomposer or None if there are no applicable decomposers
        """
        pass


class PartialDecomposerSelectionStrategy(DecomposerSelectionStrategy, metaclass=ABCMeta):

    def filter_decomposers(self, decomposers_to_filter: Iterable[Decomposer], context: PlanContext,
                           world: World_Type) -> Iterable[Decomposer]:
        """TODO: docstring

                :param decomposers_to_filter:
                :param context:
                :param world:
                """
        pass


class DecomposerFilterStrategy(PartialDecomposerSelectionStrategy, metaclass=ABCMeta):
    """TODO: docstring"""

    @abstractmethod
    def accept_decomposer(self, decomposer: Decomposer, plan_context: PlanContext, world: World_Type) -> bool:
        """TODO: docstring

        :param decomposer: the decomposer being checked
        :param plan_context: the plan context of the plan
        :param world: the world being planed in
        """
        pass

    def filter_decomposers(
            self,
            decomposers_to_filter: Iterable[Decomposer],
            plan_context: PlanContext,
            world: World_Type
    ) -> Iterable[Decomposer]:
        for current_decomposer in decomposers_to_filter:
            if self.accept_decomposer(current_decomposer, plan_context, world):
                yield current_decomposer


class InitialPartialDecomposerSelectionStrategy(DecomposerSelectionStrategy):
    """TODO: docstring"""

    @abstractmethod
    def start_iterable(self, plan_context: PlanContext, world: World_Type, decomposers: set[Decomposer]) -> Iterable[
        Decomposer]:
        """TODO: docstring

        :param plan_context:
        :param world:
        :param decomposers:
        """
        pass


class FinalPartialDecomposerSelectionStrategy(DecomposerSelectionStrategy):
    """TODO: docstring"""

    @abstractmethod
    def select_plan_from_iterable(
            self,
            decomposers_to_filter: Iterable[Decomposer],
            plan_context: PlanContext,
            world: World_Type
    ) -> Decomposer:
        """TODO: docstring

        :param decomposers_to_filter:
        :param plan_context:
        :param world:
        """
        pass


class NotDecomposerFilterStrategy(DecomposerFilterStrategy):

    def __init__(self, wrapped_plan_filter_strategy: DecomposerFilterStrategy):
        self.wrapped_plan_filter_strategy = wrapped_plan_filter_strategy

    def accept_decomposer(self, decomposer: Decomposer, plan_context: PlanContext, world: World_Type) -> bool:
        return not self.wrapped_plan_filter_strategy.accept_decomposer(decomposer, plan_context, world)

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        self.wrapped_plan_filter_strategy.introduce_plan_cache_strategy(plan_cache_strategy)


class OrDecomposerFilterStrategy(DecomposerFilterStrategy):

    def __init__(self, wrapped_plan_filter_strategies: List[DecomposerFilterStrategy]):
        self.wrapped_plan_filter_strategies = wrapped_plan_filter_strategies

    def accept_decomposer(self, decomposer: Decomposer, plan_context: PlanContext, world: World_Type) -> bool:
        for current_plan_filter_strategy in self.wrapped_plan_filter_strategies:
            if current_plan_filter_strategy.accept_decomposer(decomposer, plan_context, world):
                return True
        return False

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        for current_partial_plan_selection_strategy in self.wrapped_plan_filter_strategies:
            current_partial_plan_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)


class AndDecomposerFilterStrategy(DecomposerFilterStrategy):

    def __init__(self, wrapped_plan_filter_strategies: List[DecomposerFilterStrategy]):
        self.wrapped_plan_filter_strategies = wrapped_plan_filter_strategies

    def accept_decomposer(self, decomposer: Decomposer, plan_context: PlanContext, world: World_Type) -> bool:
        for current_plan_filter_strategy in self.wrapped_plan_filter_strategies:
            if not current_plan_filter_strategy.accept_decomposer(decomposer, plan_context, world):
                return False
        return True

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        for current_partial_plan_selection_strategy in self.wrapped_plan_filter_strategies:
            current_partial_plan_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)


class RandomPlanSelectionStrategy(FinalPartialDecomposerSelectionStrategy):
    """TODO: docstring"""

    def __init__(self, limit: int = 100, rnd: Random = Random()):
        self.limit = limit
        self.rnd = rnd

    def select_plan_from_iterable(
            self,
            decomposers_to_filter: Iterable[Decomposer],
            plan_context: PlanContext,
            world: World_Type,
            finalizing: bool = False
    ) -> Decomposer:
        decomposer_list: List[Decomposer] = []
        decomposers_to_filter_iter = iter(decomposers_to_filter)
        while len(decomposer_list) < self.limit:
            try:
                decomposer_list.append(next(decomposers_to_filter_iter))
            except StopIteration:
                break
        return self.rnd.choice(decomposer_list)


class FirstValidPlanSelectionStrategy(FinalPartialDecomposerSelectionStrategy):

    def select_plan_from_iterable(
            self,
            decomposers_to_filter: Iterable[Decomposer],
            plan_context: PlanContext,
            world: World_Type
    ) -> Decomposer:
        return next(iter(decomposers_to_filter))


class ArbitraryInitialPartialPlanSelectionStrategy(InitialPartialDecomposerSelectionStrategy):
    """TODO: docstring"""

    def start_iterable(self, plan_context: PlanContext, world: World_Type, decomposers: set[Decomposer]) -> Iterable[
        Decomposer]:
        return (current_decomposer
                for current_decomposer in decomposers
                if (current_decomposer.applicable(plan_context.plan, world)))


class CompositeFullPlanSelectionStrategy(FullDecomposerSelectionStrategy):
    """TODO: docstring

    needs a initial/final decomposer selection strategy but will try to find suitable strategies in
    partial_decomposer_selection_strategies or the other final/initial decomposer selection strategy,
    if it doesn't find any it will use
    ArbitraryInitialPartialDecomposerSelectionStrategy for the initial_decomposer_selection_strategy and
    RandomDecomposerSelectionStrategy for the final_plan_selection_strategy.
    initial_decomposer_selection_strategy(initialization parameter): TODO: docstring
    final_decomposer_selection_strategy(initialization parameter): the strategy to use to select the final plan
    partial_decomposer_selection_strategies(initialization parameter): TODO: docstring"""

    def __init__(self,
                 initial_decomposer_selection_strategy: Optional[InitialPartialDecomposerSelectionStrategy] = None,
                 final_decomposer_selection_strategy: Optional[FinalPartialDecomposerSelectionStrategy] = None,
                 partial_decomposer_selection_strategies: Optional[List[PartialDecomposerSelectionStrategy]] = None
                 ):
        if partial_decomposer_selection_strategies is None:
            partial_decomposer_selection_strategies = []
        self.initial_decomposer_selection_strategy = initial_decomposer_selection_strategy
        self.final_decomposer_selection_strategy = final_decomposer_selection_strategy
        self.partial_decomposer_selection_strategies = partial_decomposer_selection_strategies

    def select_decomposer(self, plan_context: PlanContext, world: World_Type,
                          decomposers: set[Decomposer]) -> Decomposer:
        if self.initial_decomposer_selection_strategy is None:
            for current_partial_decomposer_selection_strategy in self.partial_decomposer_selection_strategies:
                if isinstance(current_partial_decomposer_selection_strategy, InitialPartialDecomposerSelectionStrategy):
                    self.initial_decomposer_selection_strategy = current_partial_decomposer_selection_strategy
                    break
            if self.initial_decomposer_selection_strategy is None:
                if isinstance(self.final_decomposer_selection_strategy, InitialPartialDecomposerSelectionStrategy):
                    self.initial_decomposer_selection_strategy = self.final_decomposer_selection_strategy
                else:
                    self.initial_decomposer_selection_strategy = ArbitraryInitialPartialPlanSelectionStrategy()
        if self.final_decomposer_selection_strategy is None:
            for current_partial_decomposer_selection_strategy in reversed(self.partial_decomposer_selection_strategies):
                if isinstance(current_partial_decomposer_selection_strategy, FinalPartialDecomposerSelectionStrategy):
                    self.final_decomposer_selection_strategy = current_partial_decomposer_selection_strategy
                    break
            if self.final_decomposer_selection_strategy is None:
                if isinstance(self.initial_decomposer_selection_strategy, FinalPartialDecomposerSelectionStrategy):
                    self.final_decomposer_selection_strategy = self.initial_decomposer_selection_strategy
                else:
                    self.final_decomposer_selection_strategy = RandomPlanSelectionStrategy()
        chain_iterable: Iterable[Decomposer] = (
            self.initial_decomposer_selection_strategy.start_iterable(plan_context, world, decomposers))
        for current_partial_decomposer_selection_strategy in self.partial_decomposer_selection_strategies:
            chain_iterable = (
                current_partial_decomposer_selection_strategy.filter_decomposers(chain_iterable,
                                                                                 plan_context,
                                                                                 world)
            )
        return self.final_decomposer_selection_strategy.select_plan_from_iterable(chain_iterable,
                                                                                  plan_context,
                                                                                  world)

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        if self.initial_decomposer_selection_strategy is not None:
            self.initial_decomposer_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)
        for current_partial_plan_selection_strategy in self.partial_decomposer_selection_strategies:
            current_partial_plan_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)
        if self.final_decomposer_selection_strategy is not None:
            self.final_decomposer_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)


class GreedyDecomposerSelectionStrategy(FullDecomposerSelectionStrategy, InitialPartialDecomposerSelectionStrategy,
                                        FinalPartialDecomposerSelectionStrategy):
    """a greedy DecomposerSelectionStrategy that returns Decomposers in sort order
        (determined by plan_comparison_strategy: PlanComparisonStrategy)"""

    heap_key: str = "GreedyDecomposerSelectionStrategy.decomposer heap"

    def __init__(self, plan_comparison_strategy: PlanComparisonStrategy):
        self.plan_comparison_strategy = plan_comparison_strategy

    def _add_decomposers_to_heap(self, decomposers_to_add: Iterable[Decomposer], plan_context: PlanContext,
                                 world: World_Type):
        """adds plans to the heap/priority queue

        :param decomposers_to_add: the set of plans to add to the heap
        """
        if not (GreedyDecomposerSelectionStrategy.heap_key in PlanContext.notes.keys()):
            tuples_list: List[Tuple[Tuple, str]] = [
                (self.plan_comparison_strategy.plan_plus_delta_to_tuple_key(plan_context.plan,
                                                                            current_decomposer.estimate_deltas(
                                                                                plan_context.plan, world)),
                 current_decomposer.uid)
                for current_decomposer in decomposers_to_add
                if (current_decomposer.applicable(plan_context.plan, world))]
            heapq.heapify(tuples_list)
            PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key] = tuples_list
        else:
            for current_decomposer in decomposers_to_add:
                if current_decomposer.applicable(PlanContext.plan, world):
                    plan_tuple = (self.plan_comparison_strategy.plan_plus_delta_to_tuple_key(plan_context.plan,
                                                                                             current_decomposer.estimate_deltas(
                                                                                                 plan_context.plan,
                                                                                                 world)),
                                  current_decomposer.uid)
                    heapq.heappush(PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key], plan_tuple)

    def start_iterable(self, plan_context: PlanContext, world: World_Type, decomposers: set[Decomposer]) -> Iterable[
        Decomposer]:
        if ((not (GreedyDecomposerSelectionStrategy.heap_key in PlanContext.notes.keys())) or
                (len(PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key]) == 0)):
            self._add_decomposers_to_heap(decomposers, plan_context, world)
        while len(PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key]) > 0:
            selected_decomposer_tuple: tuple[tuple, str] = (
                heapq.heappop(PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key]))
            try:
                selected_decomposer = decomposer_registry.fetch(selected_decomposer_tuple[1])
            except RegistryKeyNotFoundError:
                selected_decomposer = None
            if selected_decomposer is not None:
                yield selected_decomposer

    def select_decomposer(self, context: PlanContext, world: World_Type, decomposers: set[Decomposer]) -> Optional[
        Decomposer]:
        if PlanContext.plan is None:
            return None
        if ((not (GreedyDecomposerSelectionStrategy.heap_key in PlanContext.notes.keys())) or
                (len(PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key]) == 0)):
            self._add_decomposers_to_heap(decomposers, context, world)
        selected_decomposer: Optional[Decomposer] = None
        while ((selected_decomposer is None) and
               (len(PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key]) > 0)):
            selected_decomposer_tuple: tuple[tuple, str] = (
                heapq.heappop(PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key]))
            try:
                selected_decomposer = decomposer_registry.fetch(selected_decomposer_tuple[1])
            except RegistryKeyNotFoundError:
                selected_decomposer = None
        return selected_decomposer

    def select_plan_from_iterable(self, decomposers_to_filter: Iterable[Decomposer], plan_context: PlanContext,
                                  world: World_Type) -> Decomposer:
        tuples_list: List[Tuple[Tuple, str]] = [
            (self.plan_comparison_strategy.plan_plus_delta_to_tuple_key(plan_context.plan,
                                                                        current_decomposer.estimate_deltas(
                                                                            plan_context.plan, world)),
             current_decomposer.uid)
            for current_decomposer in decomposers_to_filter]
        selected_decomposer: Optional[Decomposer] = None
        while ((selected_decomposer is None) and
               (len(tuples_list) > 0)):
            selected_decomposer_tuple: tuple[tuple, str] = min(tuples_list)
            try:
                selected_decomposer = decomposer_registry.fetch(selected_decomposer_tuple[1])
            except RegistryKeyNotFoundError:
                selected_decomposer = None
        return selected_decomposer

# standard PlanningStrategies
# TODO: create these classes

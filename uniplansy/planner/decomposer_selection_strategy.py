"""defines DecomposerSelectionStrategy and some of its subclasses. a DecomposerSelectionStrategy selects a decomposer
to apply to a plan.

DecomposerSelectionStrategy(interface): a DecomposerSelectionStrategy selects a decomposer to apply to a plan
GreedyDecomposerSelectionStrategy(DecomposerSelectionStrategy): a greedy DecomposerSelectionStrategy that returns
Decomposers in sort order (determined by plan_comparison_strategy: PlanComparisonStrategy)
"""
import heapq
from abc import ABCMeta, abstractmethod
from typing import Optional, List, Tuple

from uniplansy.decomposers.core import Decomposer, decomposer_registry
from uniplansy.planner.core import PlanCacheStrategy, PlanContext
from uniplansy.plans.plan import PlanDeltas
from uniplansy.plans.plan_comparison_strategy import PlanComparisonStrategy
from uniplansy.util.id_registry import RegistryKeyNotFoundError


class DecomposerSelectionStrategy(metaclass=ABCMeta):
    """a DecomposerSelectionStrategy selects a decomposer to apply to a plan

    select_decomposer(method): selects a decomposer to apply to the plan
    introduce_plan_cache_strategy(method):introduces a PlanCacheStrategy to the DecomposerSelectionStrategy
    which it may save.
    """

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        """introduces a PlanCacheStrategy to the DecomposerSelectionStrategy which it may save.

        :param plan_cache_strategy: the plan_cache_strategy being introduced
        """
        pass

    @abstractmethod
    def select_decomposer(self, context: PlanContext, decomposers: set[Decomposer]) -> Optional[Decomposer]:
        """selects a decomposer to apply to the plan

        :param context: the plan context of the plan
        :param decomposers: the set of all the decomposers
        :return: the selected decomposer or None if there are no applicable decomposers
        """
        pass


class GreedyDecomposerSelectionStrategy(DecomposerSelectionStrategy):
    """a greedy DecomposerSelectionStrategy that returns Decomposers in sort order
        (determined by plan_comparison_strategy: PlanComparisonStrategy)"""
    heap_key: str = "GreedyDecomposerSelectionStrategy.decomposer heap"

    def __init__(self, plan_comparison_strategy: PlanComparisonStrategy):
        self.plan_comparison_strategy = plan_comparison_strategy

    def select_decomposer(self, context: PlanContext, decomposers: set[Decomposer]) -> Optional[Decomposer]:
        if PlanContext.plan is None:
            return None
        if not (GreedyDecomposerSelectionStrategy.heap_key in PlanContext.notes.keys()):
            new_heap: List[Tuple[Tuple, str]] = []
            for current_decomposer in decomposers:
                if current_decomposer.applicable(PlanContext.plan):
                    delta: PlanDeltas = current_decomposer.estimate_deltas(PlanContext.plan)
                    new_decomposer_tuple: tuple[tuple, str] = (
                        self.plan_comparison_strategy.plan_plus_delta_to_tuple_key(PlanContext.plan, delta),
                        current_decomposer.uid
                    )
                    new_heap.append(new_decomposer_tuple)
            heapq.heapify(new_heap)
            PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key] = new_heap
        selected_decomposer: Optional[Decomposer] = None
        while selected_decomposer is None:
            selected_decomposer_tuple: tuple[tuple, str] = (
                heapq.heappop(PlanContext.notes[GreedyDecomposerSelectionStrategy.heap_key]))
            try:
                selected_decomposer = decomposer_registry.fetch(selected_decomposer_tuple[1])
            except RegistryKeyNotFoundError:
                selected_decomposer = None
        return selected_decomposer
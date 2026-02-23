from abc import ABCMeta, abstractmethod
from dataclasses import dataclass

from uniplansy.decomposers.core import Decomposer
from uniplansy.planner.core import PlanCacheStrategy, PlanningContext
from uniplansy.planner.decomposer_selection_strategy import DecomposerSelectionStrategy
from uniplansy.planner.plan_selection_strategy import PlanSelectionStrategy
from uniplansy.plans.plan import Plan


class PlanningStrategy(metaclass=ABCMeta):

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        pass

    @abstractmethod
    def plan(self, planning_context: PlanningContext, decomposers:set[Decomposer]) -> tuple[Plan, Decomposer]:
        """selected a plan and a decomposer

        :param planning_context: the planning_context
        :param decomposers: the set of all the decomposers
        :return: selected the plan and decomposer
        """
        pass

    def prepopulate_plan_cache(self, plan: Plan):
        """prepopulates the cache values of the plan

        :param plan: the plan to prepopulate
        """
        pass


@dataclass
class CommonPlanningStrategy(PlanningStrategy):
    plan_selection_strategy: PlanSelectionStrategy
    decomposer_selection_strategy: DecomposerSelectionStrategy

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        self.plan_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)
        self.decomposer_selection_strategy.introduce_plan_cache_strategy(plan_cache_strategy)

    def plan(self, planning_context: PlanningContext, decomposers:set[Decomposer]) -> tuple[Plan, Decomposer]:
        selected_plan = self.plan_selection_strategy.select_plan(planning_context)
        selected_decomposer = self.decomposer_selection_strategy.select_decomposer(
            planning_context.plan_by_uid[selected_plan.uid],
            decomposers
        )
        return selected_plan, selected_decomposer

    def prepopulate_plan_cache(self, plan: Plan):
        self.plan_selection_strategy.introduce_plan_cache_strategy(plan)

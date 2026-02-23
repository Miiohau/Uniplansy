from abc import ABCMeta, abstractmethod

from uniplansy.decomposers.core import Decomposer
from uniplansy.planner.core import PlanCacheStrategy, PlanContext


class DecomposerSelectionStrategy(metaclass=ABCMeta):

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        pass

    @abstractmethod
    def select_decomposer(self, context:PlanContext, decomposers:set[Decomposer]) -> Decomposer:
        """selects a decomposer to apply to the plan

        :param context: the plan context of the plan
        :param decomposers: the set of all the decomposers
        :return: the selected decomposer
        """
        pass

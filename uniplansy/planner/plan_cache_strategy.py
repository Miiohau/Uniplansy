from abc import ABCMeta, abstractmethod

from uniplansy.planner.core import PlanContext, PlanningContext
from uniplansy.planner.planning_strategy import PlanningStrategy
from uniplansy.plans.plan import Plan


class PlanCacheStrategy(metaclass=ABCMeta):

    def introduce_planning_strategy(self, planning_strategy: PlanningStrategy):
        pass

    @abstractmethod
    def should_save_plan(self, plan_context: PlanContext, planning_context: PlanningContext) -> bool:
        pass

    @abstractmethod
    def manage_active_plans(self, planning_context: PlanningContext, finalizing:bool = False):
        pass

    @abstractmethod
    def save_plan(self, plan_context: PlanContext, planning_context: PlanningContext):
        pass

    @abstractmethod
    def load_plan(self, plan_uid:str, planning_context: PlanningContext) -> Plan:
        pass

    @abstractmethod
    def load_plans(self, planning_context: PlanningContext):
        pass

class MaybeWantsToKnowPlanCacheStrategy(metaclass=ABCMeta):

    def introduce_plan_cache_strategy(self, plan_cache_strategy: PlanCacheStrategy):
        """introduces a PlanCacheStrategy to this class which it may save.

        The intended use of a saved PlanCacheStrategy is to request offloaded plans be
        reloaded back into memory
        :param plan_cache_strategy: the plan_cache_strategy being introduced
        """
        pass


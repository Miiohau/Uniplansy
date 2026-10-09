from typing import Optional

from uniplansy.planner.base import PlanCacheStrategy, PlanContext, PlanningContext
from uniplansy.plans.plan import Plan


class NullPlanCacheStrategy[World_Type](PlanCacheStrategy[World_Type]):

    def should_save_plan(self, plan_context: PlanContext, planning_context: PlanningContext) -> bool:
        return False

    def manage_active_plans(self,
                            planning_context: PlanningContext,
                            world: World_Type,
                            initializing: bool = False,
                            finalizing: bool = False):
        pass

    def save_plan(self, plan_context: PlanContext, planning_context: PlanningContext, invalid=False):
        pass

    def load_plan(self, plan_uid: str, planning_context: PlanningContext) -> Optional[Plan]:
        pass







"""defines a simple goal and simple leaf decomposer"""

from copy import deepcopy
from typing import List

from uniplansy.decomposers.core import Goal, DecomposerNode, Decomposer
from uniplansy.plans.plan import Plan
from uniplansy.reasoners.graph import ReasonerTemplate, CommonConjunctionReasonerBuilder, SimpleReasonerBuilder
from uniplansy.tasks.tasks import Task, TaskDescription
from uniplansy.util.global_type_vars import World_Type


class TestGoal(Goal):
    def convert_to_reasoner_graph(self, node: DecomposerNode,
                                  node_id_to_builder_id: dict[str, str]) -> ReasonerTemplate:
        new_template = CommonConjunctionReasonerBuilder()
        new_template.preferred_name = "test_goal_template"
        new_template.all_semantics = True
        for child in node.children:
            new_template.sub_reasoner_uids.append(node_id_to_builder_id[child.uid])
        return new_template

    def decompose_tasks(self, plan: Plan, world: World_Type) -> List[Plan]:
        new_plan = deepcopy(plan)
        new_plan.add_node(Task(
            uid="test_goal",
            description=TaskDescription(
                uid="test_goal_description",
                human_understandable_string="this is a test", )
        ))
        return [new_plan]


class TestDecomposer(Decomposer):

    # noinspection PyUnusedLocal
    @staticmethod
    def test_act(world, context) -> bool:
        print("this is a test")
        return True

    def convert_to_reasoner_graph(self, node: DecomposerNode,
                                  node_id_to_builder_id: dict[str, str]) -> ReasonerTemplate:
        new_template = SimpleReasonerBuilder(act_delegate=TestDecomposer.test_act)
        new_template.preferred_name = "actor"
        return new_template

    def decompose_tasks(self, plan: Plan, world: World_Type) -> List[Plan]:
        new_plan = deepcopy(plan)
        decomposer_node = DecomposerNode(uid="test_decomposer_node", node_decomposer=self)
        goal_node = new_plan.tasks_by_UID["test_goal"]
        goal_node.children.add(decomposer_node)
        goal_node.satisfied_percentage = 1
        decomposer_node.parents.add(goal_node)
        new_plan.add_node(decomposer_node)
        return [new_plan]

    def applicable(self, plan: Plan, world: World_Type) -> bool:
        return plan.tasks_by_UID["test_goal"].satisfied_percentage == 0
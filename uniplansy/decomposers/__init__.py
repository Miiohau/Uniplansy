""" Decomposers are knowledge experts that can decompose a plan typically by decomposing Tasks within that plan.

Decomposer (class): knowledge expert that can decompose a plan typically by decomposing Tasks within that plan.
DecomposerNode (PlanGraphNode): a DecomposerNode holds information about how a Decomposer was applied to a plan
Goal (Decomposer): Goals are special Decomposers that are only applicable to empty plans or plans only Goals
have run on. There primary reason for existence is to place top level/end goals in to the plan.
"""
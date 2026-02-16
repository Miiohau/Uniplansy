"""
the core package dealing with the classes and Strategy needed to run the planning algorithm
"""
# general workflow
# 1. load and initialize decomposers
# 2. create initial plan
# 3. while planning
# 4. select a plan to expand
# 5. if we don't already have list of possible decomposers for the plan: identify decomposers that can be applied.
# If none mark the plan as finalized so it isn't selected for expansion anymore
# 6. select a decomposer
# 7. add the plans output by the decomposer to possible plans
# 8. if there are no more decomposers that can be applied to the plan mark it as finalized so it isn't selected for
# expansion anymore
# 9. end while
# 10. select plan to be the output of the planning stage
# if no sub planners the plan is converted into a reasoner graph
# if sub planners set up the selected plan for them and run them
# ...
# 11. start replanning
# 12. restore set aside plans that are now "valid" again.
# (A "valid" plan might only being restored to be permanently dropped).
# 13. drop all invalid plans (some may be saved to be restored later)
# 14. start planning again

# customization points of above algorithm
# 1. the set of decomposers
# 2. how we select a plan to expand and which decomposer to use (PlanningStrategy,
# usually it is broken down into a PlanSelectionStrategy and a DecomposerSelectionStrategy)
# 3. how we select the plan to convert to a reasoner graph (PlanSelectionStrategy)
# 4. how the output plan is converted to a reasoner graph
# 5. if we save some invalid plans for later planning iterations and
# how we do that and how and when we restore them (PlanCasheStrategy)

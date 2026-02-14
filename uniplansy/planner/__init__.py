# general workflow
# load and initialize decomposers
# create initial plan
# while planning
# select a plan to expand
# if we don't already have list of possible decomposers for the plan: identify decomposers that can be applied. If none mark the plan as finalized so it isn't selected for expansion anymore
# select a decomposer
# add the plans output by the decomposer to possible plans
# if there are no more decomposers that can be applied to the plan mark it as finalized so it isn't selected for expansion anymore
# end while
# select plan to be the output of the planning stage
# if no sub planners the plan is converted into a reasoner graph
# if sub planners set up the selected plan for them and run them
# ...
# start replanning
# restore set aside plans that are now "valid" again. (A "valid" plan might only being restored to be permanently dropped).
# drop all invalid plans (some may be saved to be restored later)
# start planning again

# customization points of above algorithm
# the set of decomposers
# how we select a plan to expand (PlanSelectionStrategy)
# how we select a decomposer to use (DecomposerSelectionStrategy)
# how the output plan is converted to a reasoner graph
# if we save some invalid plans for later planning iterations and how we do that and how and when we restore them (PlanCasheStrategy)

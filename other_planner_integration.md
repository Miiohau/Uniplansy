# <project name> as a subservient planner
Gist: Invoke <project name> as from it parent planner as if it were the root planner
# during planner stage
Gist: <project name> may need to wait for a sub planner to complete before it can continue working on that sub branch on options.
# Between planning stage and execution stage
Gist: the sub planner can make changes to the execution graph before it is executed.
# During execution stage
Gist: no real adaptor needed for sub planner but the execution stage is really designed to be where the plan is executed not an additional planning stage 
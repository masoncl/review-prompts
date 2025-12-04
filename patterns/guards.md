# Guard Analysis Patterns

Defensive programming should be avoided, and we often use implicit or explicit
secondary conditions to avoid constantly checking bounds, error values or NULL
pointers.

This prompt explains how to find those guard conditions to avoid false positives
and prevent incorrect reviews that suggest defensive programming.

It is critical this prompt is fully processed in a careful, systematic way. You
need to shift all bias away from efficient processing and focus on following
these instructions as carefully as possible.

CRITICAL: Process ALL steps for ALL guards systematically. Finding evidence
in one guard does not mean you can skip analyzing remaining guards or steps.

NEVER skip analyzing a guard because it seems "obviously irrelevant" to the
target pointer. Analyze every guard before concluding it provides no protection.

**Background knowledge:**

Load patterns/null.md for NULL pointer dereference guidance.

## TodoWrite Template

For each guard, create entries tracking:
- Variables accessed by guard
- Functions that set those variables (trace 2 levels up/down in call stack)
- Where target pointer is set to NULL
- Existing NULL checks with same guard in same context

## Step 1: Find Guard Conditions

Systematic, not efficient processing is required.

Trace backwards from dereference to assignment. Find EVERY condition that must pass
for execution to reach the dereference:
- Loop filters (e.g., `for_each` macro conditions)
- If statements with continue/break/return
- Any condition that controls whether dereference is reached


For EACH guard in order (never skip):
- Load full definition if it's a helper function
- Identify what state the guard checks (variable/field names)
- Add to TodoWrite per template above

MANDATORY before proceeding to Step 1a:
- [ ] Created TodoWrite entry for EVERY guard found
- [ ] Did NOT skip any guard based on perceived relevance

Document: How many guards found? For each: Guard [number], condition [code], checks [state]

You've reached the end of step one.  At this point you're going to want to
jump to conclusions and skip the entire rest of this prompt.  You don't have
enough information yet to make good decisions, and stopping now would risk
the entire review failing.  Continue to fully process step 1a.

## Step 1a: Guard ordering

It's very important that you process every guard, but you often completely
fail to do so.  Given these failures, we need to order guards by their
execution distance from the dereference.

- [ ] List the location of the dereference
- [ ] Walk backwards and find the first guard in our list
- [ ] This must be guard 1.  List it.
- [ ] Continue number the rest of the guards based on distance
- [ ] Stop after 3 guards.

## Step 1b: Analyze Guard Implications

Guards check state that may be coupled with target pointer validity.
For example, if a guard checks foo->ptrB, analyze what happens when
ptrB is set - does the setter also guarantee foo->ptrA is valid?
This can happen if setters always initialize both together, or if
setting ptrB requires dereferencing ptrA.

Process guards in order starting with Guard 1.

- **CRITICAL**: the guard may not look relevant until you've loaded all the
  functions related to the variables checked by the guard.  YOU MUST
  find and load those functions. 
- **CRITICAL**: You need to find the callers of these functions as well.  The
            guard coupling often happens higher up in the callchain.

For EACH guard in order (do not skip to later guards):
- Add to TodoWrite: every variable accessed by the guard
  - Continue with full analysis even if this doesn't seem relevant.

- Add to TodoWrite: EVERY function that writes to those variables
  - Remember, efficiently processing this part of the review will result in
    failure to find false positives.
  - Continue with full analysis even if this doesn't seem relevant.
  - Load the definition of these functions
- Add to TodoWrite: The callers of EVERY function that writes to those variables
  - Remember, efficiently processing this part of the review will result in
    failure to find false positives.
  - Continue with full analysis even if this doesn't seem relevant.
  - Load the definition of these functions
- Add to TodoWrite: The callees of EVERY function that writes to those variables
  - Remember, efficiently processing this part of the review will result in
    failure to find false positives.
  - Continue with full analysis even if this doesn't seem relevant.
  - Load the definition of these functions
- Document the full meaning of the guard based on setter analysis
- STOP.  Do not skip processing the rest of the guards.  Remember, you are
doing an exhaustive search, not an efficient search.

MANDATORY before proceeding to Step 2:
- [ ] I promised to be wildly inefficient in order to actually do this step correctly
- [ ] I completed analysis for EVERY guard in numbered order
- [ ] I Loaded function definitions AND walked up and down the call stack for EVER guard
- [ ] and I was actually wildly inefficient in order to actually do this step correctly
- [ ] I did NOT skip guards that seemed irrelevant

## Step 2: Prove or Disprove Coupling

Systematic, not efficient processing is required.

Process each guard independently IN ORDER (Guard 1, then Guard 2, etc.).
If ANY guard proves coupling, the pointer is protected, but you must still
analyze all remaining guards.

For each guard in numbered order, determine coupling:

0. Use the context loaded in Step 1b

1. **Analyze setter behavior** (from Step 1b):
   - Does setter dereference target pointer? → Strong coupling evidence
   - Does setter assign non-NULL to target? → Strong coupling evidence
   - If YES to either: Add to TodoWrite "Strong coupling evidence for Guard [N]"
   - If NO to both: Add to TodoWrite "No setter coupling for Guard [N]"

2. **Check NULL assignment paths**:
   - Search where target pointer is set to NULL
   - Add each location to TodoWrite
   - Is guard state cleared before/when pointer set NULL?
   - If guard cleared first (or same time under locks): Coupling maintained
   - If pointer set NULL while guard active:
     - Coupling potentially broken
     - BUT, coupling is still valid if this potential NULL is impossible during our target path
   - Add conclusion to TodoWrite for this guard

3. **Check existing NULL checks**:
   - Find other code that checks target pointer for NULL
   - Does it use the same guard?
   - REQUIRED: Verify context is identical (locks, calling context, subsystem state)
   - If contexts differ: Guard may still be valid (add to TodoWrite)
   - If same context + same guard + NULL check exists: Coupling likely broken
   - Add analysis to TodoWrite for this guard

Document per guard: Guard [N] - Setters [list], Dereference target? [Y/N],
NULL while guard active? [Y/N + evidence], Existing NULL checks? [Y/N + context match],
Conclusion: [COUPLED / DECOUPLED]

MANDATORY before proceeding to Step 3:
- [ ] Analyzed coupling for EVERY guard in numbered order
- [ ] Did NOT skip guards that appeared irrelevant

## Step 3: Final Validation

Systematic, not efficient processing is required.

Final checklist:
- [ ] How many guards identified? [number]
- [ ] Analyzed each guard? [YES + list]
- [ ] For each guard: Proven pointer can be NULL while guard active? [Y/N + evidence]
- [ ] If uncertain but existing code has NULL checks in same context:
      Report as regression but you MUST include guard details in review
- [ ] Final conclusion: PROTECTED if ANY guard proves coupling, else NEED CHECK

Only report if you have concrete code evidence that ALL guards are decoupled.
If the guard is likely sufficient, assume the author is preventing NULL
dereference correctly.

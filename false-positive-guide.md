# False Positive Prevention Guide

## Core Principle
**If you cannot prove an issue exists with concrete evidence, do not report it.**

This file contains instructions to help you prove a given bug is real.  You
must follow every instruction in every section.  Do not skip steps, and you
must complete task POSITIVE.1 before completing the false positive check.

## Common False Positive Patterns

### 0. Context preservation
- If you're analyzing a git commit make sure the full commit message is still in context.  If not, reload it.
- If you're processing a patch instead of a commit, make sure the full
  patch description is still in context.  If not, reread it.
- Confirm this context is available for the false positive section
- Do not proceed with false positive verification without this context ready

### 1. Defensive Programming Requests
**Never suggest** defensive checks unless you can prove:
- The input comes from an untrusted source (ex: user/network)
- An actual path exists where invalid data reaches the code
- The current code can demonstrably fail

**Examples**:
- ❌ "Add bounds check here for safety"
- ❌ "This should validate the index"
- ✅ "User input at funcA() can reach this without validation"

### 2. API Misuse Assumptions
**Never report** issues based on theoretical API misuse unless you can prove:
  - An actual calling path exists that triggers the issue
  - The function naming/documentation doesn't clearly indicate usage constraints
  - Similar kernel APIs validate the same preconditions

### 3. Unverifiable Assumptions
**Trust the author** but try to prove them wrong
- Untrusted sources (network/user) need less proof
- Research assumptions and claims in commit messages, comments and code.  Try to prove them wrong.
- If you don't have concrete proof in the form of code snippets, assume the author is correct
- Design decisions are assumed intentional
- Read the entire commit message.  If the commit message explains a given bug,
ex: "For now, ignore this problem", consider the bug a false positive.
- Read the surrounding code comments.  If you find a bug and a comment
explictly explaining why they have chosen to add the bug, consider it a false
positive.

**Only report if**:
- You found specific code that proves you correct
- You can trace a concrete path that violates the code assumption
- You have proof, not just suspicion

### 4. Locking False Positives
**Before reporting** a locking issue:
- Check ALL calling functions for held locks
- Trace up 2-3 levels to find lock context
- Verify the actual lock requirements
- Consider RCU and other lockless mechanisms

**Common mistakes**:
- Missing that caller holds the required lock
- Not recognizing RCU-protected sections
- Assuming all shared data needs traditional locks

### 5. Use-After-Free Confusion
**Distinguish between**:
- Use-after-free (accessing freed memory) ← Report this
- Use-before-free (using then freeing) ← Don't report
- Free-after-use (normal cleanup) ← Don't report

**Verification**:
- Trace the exact sequence of operations
- Check if object ownership was transferred

### 6. Resource Leak Misconceptions
**Not a leak if**:
- Ownership was transferred to another subsystem
- Object was added to a list/queue for later processing
- Cleanup happens in a callback or delayed work
- It's in test code and doesn't affect the system

**Verify by**:
- Tracing object ownership changes
- Checking for async cleanup mechanisms
- Understanding subsystem ownership models

### 7. Order Changes
**Don't report** order changes unless you can prove:
- A race condition is introduced
- A dependency is violated
- An ABBA deadlock pattern emerges
- State becomes invalid

### 8. Races
**You're especially bad at finding races, assume you're wrong unless you have concrete proof**
- [ ] identify the EXACT data structure names and definitions
- [ ] identify the locks that should protect them
- [ ] prove the race exists with CODE SNIPPETS

**Just because** operations moved doesn't mean it's wrong.

### 8. Performance Tradeoffs
**Not a regression if**:
- Lower performance was an intentional tradeoff
- Commit message explains the performance impact
- Simplicity/maintainability was prioritized
- It's optimizing for a different use case

### 9. Intentional backwards compatibility
- Leaving stub sysfs or procfs files is not required, but also not a regression

**ONLY REPORT**: if you can prove the resource contract has been broken

### 10. Patch series
- look forward in git history on the current branch.  If this commit is
part of a series of related patches, check to see if later patches in the
series resolve the bug you found.
- Never search backwards in commit history.
- Never search other branches.  Only the current branch.

### 11. Subjective review patterns
- problems flagged by SR-* patterns are not bugs, they are opinions.
- But, they can still be wrong.  Focus on checking against the commit message,
nearby code, nearby comments, and the "debate yourself" section of the
verification checklist.

## TASK POSITIVE.1 Verification Checklist

Before reporting ANY regression, verify:

1. **Can I prove this path executes?**
   - [ ] Found calling code that reaches here
   - [ ] No impossible conditions blocking the path
   - [ ] Not in dead code or disabled features
2. **Is the bad behavior guaranteed?**
   - [ ] Not just "might happen" but "will happen"
   - [ ] Not just "increases risk" but "causes failure"
   - [ ] Concrete sequence leads to the issue
3. **Did I check the full context?**
   - [ ] Examined calling functions (2-3 levels up)
   - [ ] Checked initialization and cleanup paths
   - [ ] Verified subsystem conventions
4. **Is this actually wrong?**
   - [ ] Not an intentional design choice
   - [ ] Not a documented limitation
   - [ ] Not test code that's allowed to be imperfect
   - [ ] Not a potential future bug if the code changes, but a bug today
5. **Did I check the commit message and surrounding comments?**
   - [ ] The entire commit message was read and checked for explanations
   - [ ] All surroudning code comments were checked for explanations
6. **When complex multi-step conditions are required for the bug to exist**
   - [ ] Prove these conditions are actually possible
7. **Did I hallucinate a problem that doesn't actually exist?**
   - [ ] Check the bug report actually matches the code
   - [ ] Check your math.  Dividing by zero requires a zero in the denominator
8. **Did I check for future fixes in the same patch series?**
   - [ ] Check forward in git history (not back), only on this branch
9. **Debate yourself**
   - Do these two in order:
   - 8.1 [ ] Pretend you are the author of this patch.  Think extremely hard about
         the review, and try to prove the review is incorrect.
         - Make sure to double check for hallucinations or other places the
         review is simply inventing false information.
   - 8.2 [ ] Now pretend you're the reviewer.  Think extremely hard about any
         arguments from the theoritcal author and decide if this review is
         correct

## Special Cases

### Test Code
- Memory leaks in test programs → Usually OK
- File descriptor leaks in tests → Usually OK
- Unless it crashes/hangs the system → Report it

### Assertions and Warnings
- Removing WARN_ON/BUG_ON → Not a regression
- Removing BUILD_BUG_ON → Not a regression
- Unless removing critical runtime checks → Then report

### Reverts
- When reviewing reverts, focus on new issues
- Assume the original bug is known/handled
- Don't re-report the original problem

### Subsystem Exclusions
- fs/bcachefs → Skip all issues
- Staging drivers → Lower standards apply
- Example/test code → Focus on system impact only

## Final Filter

Before adding to report, think about the regression and ask:
1. **Do I have proof, not just suspicion?**
  - Code snippets showing all components required to trigger the bug count as proof
  - Existing defensive pattern checks for the same condition also count as proof.
  - Existing WARN_ON()/BUG_ON() don't count as proof.
2. **Would an expert see this as a real issue?**
3. **Is this worth the maintainer's time?**
4. **Am I being overly defensive?**

If any answer is "no" or "maybe", investigate further or discard.

## Remember
- **False positives waste everyone's time**
- **Kernel developers are experts** - respect their judgment
- **Real bugs have real proof**

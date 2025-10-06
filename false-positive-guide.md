# False Positive Prevention Guide

## Core Principle
**If you cannot prove an issue exists with concrete evidence, do not report it.**

This file contains instructions to help you prove a given bug is real.  You
must follow every instruction in every section.  Do not skip steps, and you
must complete task POSITIVE.1 before completing the false positive check.

## Common False Positive Patterns

### 1. Defensive Programming Requests
**Never suggest** defensive checks unless you can prove:
- The input comes from an untrusted source (user/network)
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

**Just because** operations moved doesn't mean it's wrong.

### 8. Performance Tradeoffs
**Not a regression if**:
- Lower performance was an intentional tradeoff
- Commit message explains the performance impact
- Simplicity/maintainability was prioritized
- It's optimizing for a different use case

**ONLY REPORT**: if you can prove the resource contract has been broken

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
5. **Did I check the commit message and surrounding comments?**
   - [ ] The entire commit message was read and checked for explanations
   - [ ] All surroudning code comments were checked for explanations
6. **When complex multi-step conditions are required for the bug to exist**
   - [ ] Prove these conditions are actually possible

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

Before adding to report, ask:
1. **Do I have proof, not just suspicion?**
2. **Would an expert see this as a real issue?**
3. **Is this worth the maintainer's time?**
4. **Am I being overly defensive?**

If any answer is "no" or "maybe", investigate further or discard.

## Remember
- **False positives waste everyone's time**
- **Kernel developers are experts** - respect their judgment
- **Real bugs have real proof**

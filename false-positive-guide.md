# False Positive Prevention Guide

## Core Principle
**If you cannot prove an issue exists with concrete evidence, do not report it.**

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

### 2. Unverifiable Assumptions
**Trust the author** but try to prove them wrong
- Research assumptions and claims in commit messages, comments and code.  Try to prove them wrong.
- If you don't have concrete proof in the form of code snippets, assume the author is correct
- Design decisions are assumed intentional

**Only report if**:
- You found specific code that proves you correct
- You can trace a concrete path that violates the code assumption
- You have proof, not just suspicion

### 3. Locking False Positives
**Before reporting** a locking issue:
- Check ALL calling functions for held locks
- Trace up 2-3 levels to find lock context
- Verify the actual lock requirements
- Consider RCU and other lockless mechanisms

**Common mistakes**:
- Missing that caller holds the required lock
- Not recognizing RCU-protected sections
- Assuming all shared data needs traditional locks

### 4. Use-After-Free Confusion
**Distinguish between**:
- Use-after-free (accessing freed memory) ← Report this
- Use-before-free (using then freeing) ← Don't report
- Free-after-use (normal cleanup) ← Don't report

**Verification**:
- Trace the exact sequence of operations
- Check if object ownership was transferred

### 5. Resource Leak Misconceptions
**Not a leak if**:
- Ownership was transferred to another subsystem
- Object was added to a list/queue for later processing
- Cleanup happens in a callback or delayed work
- It's in test code and doesn't affect the system

**Verify by**:
- Tracing object ownership changes
- Checking for async cleanup mechanisms
- Understanding subsystem ownership models

### 6. Order Changes
**Don't report** order changes unless you can prove:
- A race condition is introduced
- A dependency is violated
- An ABBA deadlock pattern emerges
- State becomes invalid

**Just because** operations moved doesn't mean it's wrong.

### 7. Performance Tradeoffs
**Not a regression if**:
- Lower performance was an intentional tradeoff
- Commit message explains the performance impact
- Simplicity/maintainability was prioritized
- It's optimizing for a different use case

### 8. Resource Contract Analysis
**Don't assume** resource switching is safe just because:
  - The new resource appears equivalent
  - No immediate crash occurs
  - Function comments don't mention the issue
  - funcA() { resource = funcB(resource); }
    - Just because funcA() accepts a replacement resource does not mean
      funcB properly manages locks, frees, and cleans up the resource it was passed

**DO verify**:
  - Original resource lock state, reference counts, ownership
  - Caller's expectation about which resource is returned
  - All cleanup paths handle the resource properly

**ONLY REPORT**: if you can prove the resource contract has been broken

## Verification Checklist

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

## Language to Avoid

When you DO find a real issue, avoid:
- "This is obviously wrong"
- "Critical security vulnerability"
- "This will definitely crash"
- "How did this pass review?"

Instead use:
- "This could potentially..."
- "Under these conditions..."
- "If X happens, then..."
- "Can this lead to...?"

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

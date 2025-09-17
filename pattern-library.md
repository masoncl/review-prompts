# Common Pattern Library

## Resource Management
**Lifecycle**: alloc→init→use→cleanup→free must be 1:1 matched
**List management**: list_del() from a free list without returning or using the object may be a leak
**Init Once**: Check for double-init of static/global resources (seqcount, workqueue)
**Error Cleanup**: Verify cleanup in ALL error paths between alloc and success
**Async Cleanup**: RCU callbacks/work queues may access uninitialized fields if init fails

## NULL/Error Handling
**NULL Safety**: Function taking pointers must handle NULL or have verified non-NULL callers
**ERR_PTR**: Don't mix NULL checks with ERR_PTR APIs (check IS_ERR not NULL)
**Error Overwrite**: Watch for `ret = func(); ... ret = 0;` patterns losing errors
**Required interfaces**: if documentation says an operations struct must supply a function pointer, and existing code does not always check for NULL before trusting the function, checks are not required

## Concurrency
**Race Windows**: No access after release_resource() - becomes owned by other thread
**Lock Context**: Atomic context (spinlock/IRQ) forbids sleeping locks (mutex/rwsem)
**Memory Ordering**: Lockless readers need READ_ONCE/WRITE_ONCE for shared fields

## Code Movement
**Variable Scope**: Moved code may use stale values if variables modified between old/new location
**Loop Variables**: Check loop bounds/conditions still valid at new location
**Context Dependencies**: Functions may require locks/state from original location
**Conditionals**: check return values of moved function calls, make sure they are used correctly in the new location
**Assertions**: it is not a regression to remove assertions (WARN/BUG/ASSERT etc) without replacing them

## Bounds Validation
**Validation Timing**: Bounds must be checked where used, not just where received
**Integer Overflow**: Watch 16/32-bit arithmetic before array indexing
**Dynamic Bounds**: Revalidate if size can change between check and use
**No defensive programming**: never suggest defensive bounds checks unless the source of the index is untrusted.

## State Machines
**Flag Coverage**: New flags must be checked by ALL relevant functions
**State Transitions**: Verify all paths handle new states/flags
**Infinite Loops**: New stop flags must be checked in existing loops

## Common Anti-Patterns
- Resource leak on error path
- Use-after-free/enqueue/release
- NULL deref in cleanup handlers  
- Double free/init/unlock
- Missing bounds check on user/network data
- Lock held across blocking operation
- Inverted lock ordering (AB vs BA)
- Missing memory barriers in lockless code

## Reverts
- When we revert a commit, assume we've checked for whatever bug or condition
that original commit was fixing.  Instead check to make sure the revert does
not introduce new problems we were not aware of.

## Avoiding false positives
- If you cannot verify/disprove a premise or statement made by the author, assume the
author is correct.

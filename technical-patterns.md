# Linux Kernel Technical Review Patterns

## Core Pattern Categories

### 1. Resource Management [RM]
**Principle**: Every resource must have balanced lifecycle: alloc→init→use→cleanup→free

| Pattern ID | Check | Risk | Common Location |
|------------|-------|------|-----------------|
| RM-001 | 1:1 matching of alloc/free operations | Memory leak | Error paths between alloc and success |
| RM-001a | Resource lifecycle consistency | Resource leak/corruption | Check all resource types and state transitions
| RM-002 | Init-once enforcement for static resources | Double init | Static/global initialization |
| RM-003 | Cleanup in ALL error paths | Resource leak | Between resource acquisition and function return |
| RM-004 | No access after release/enqueue | Use-after-free | Async callbacks, after enqueue operations |
| RM-005 | Proper refcount handling | Use-after-free/leak | refcount_dec_and_test returns true only at zero |
| RM-006 | Object state preservation in reassignment | Memory leak | foo = func(foo) patterns |
| RM-007 | List removal with proper handling | Memory leak | list_del() without return/use may leak |
| RM-008 | Assorted reference counts | Memory leak/Use-after-free | load definitions of ref counting functions to make sure you understand them correctly |

**Key Notes**:
- alloc/free and get/put matching in ALL paths
- State preservation: resource state consistent with return contract
- refcount_t counters do not get incremented after dropping to zero
- Async cleanup (RCU callbacks/work queues) may access uninitialized fields if init fails
- Don't assume error propagation happens based on return types, trace function callers/callees to verify it

### 2. Concurrency & Locking [CL]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| CL-001 | Correct lock type for context | Deadlock/sleep bug | Never sleep (mutex/rwsem) in atomic context |
| CL-002 | Lock ordering consistency | ABBA deadlock | Document and verify lock ordering when multiple held |
| CL-003 | Lock requirements traced 2-3 levels | Missing synchronization | Called functions may require locks |
| CL-004 | Race window analysis | Data corruption | Check between resource release and subsequent access |
| CL-005 | Memory ordering for lockless access | Data corruption | READ_ONCE/WRITE_ONCE for shared fields |
| CL-006 | Trylock→lock conversion safety | Deadlock | May introduce new deadlock scenarios |
| CL-007 | Cleanup ordering | Use-after-free | Stop users → wait completion → destroy resources |
| CL-008 | IRQ-safe locking | IRQ corruption | Use _irqsave if lock taken from IRQ context |
| CL-009 | Assorted locking | bugs | load definitions of locking functions to make sure you understand them correctly |

**Lock Context Compatibility Matrix**:
| Lock Type | Process | Softirq | Hardirq | Sleeps |
|-----------|---------|---------|---------|--------|
| spin_lock | ✓ | ✓ | ✓ | ✗ |
| spin_lock_bh | ✓ | ✗ | ✗ | ✗ |
| spin_lock_irqsave | ✓ | ✓ | ✓ | ✗ |
| mutex/rwsem | ✓ | ✗ | ✗ | ✓ |

- READ_ONCE() is not required when the data structure being read is protected by a lock we're currently holding

### 3. Error Handling [EH]

| Pattern ID | Check | Risk | Example |
|------------|-------|------|---------|
| EH-001 | NULL safety verification | NULL deref | Trace callers for NULL passing, especially cleanup paths |
| EH-002 | ERR_PTR vs NULL consistency | Wrong error check | Don't mix IS_ERR with NULL checks |
| EH-003 | Error value preservation | Lost errors | Watch for `ret = func(); ... ret = 0;` patterns |
| EH-004 | Return type changes handled | Wrong returns | When signatures change, verify ALL return statements |
| EH-005 | Required interface handling | NULL deref | Ops structs with required functions per documentation |

- If code checks for a condition via WARN_ON() or BUG_ON() assume that condition will never happen, unless you
can provide concrete evidence of that condition existing via code snippets and call traces

### 4. Bounds & Validation [BV]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| BV-001 | Bounds checked at point of use | Buffer overflow | Not just where received, but where accessed |
| BV-002 | Integer overflow before indexing | Buffer overflow | Watch 16/32-bit arithmetic before array access |
| BV-003 | Dynamic bounds revalidation | Buffer overflow | Revalidate if size can change between check and use |
| BV-004 | Untrusted data validation | Security | Only enforce on data from untrusted sources |

**Important**: Never suggest defensive bounds checks unless you can prove the source is untrusted.

### 5. Code Movement [CM]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| CM-001 | Variable scope at new location | Stale values | Variables may be modified between old/new location |
| CM-002 | Loop bounds still valid | Logic error | Check loop conditions at new location |
| CM-003 | Context dependencies preserved | Missing state | Functions may need locks/state from original location |
| CM-004 | Return value handling | Logic error | Verify return values used correctly in new location |
| CM-005 | Inverted conditionals | Logic error | Check for inverted logic when moving code |

### 6. State Machines & Flags [SM]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| SM-001 | New flag coverage | Missing handling | ALL relevant functions must check new flags |
| SM-002 | State transition completeness | Invalid state | All paths must handle new states/flags |
| SM-003 | Loop termination with new flags | Infinite loop | New stop flags checked in existing loops |

### 6. Math [MT]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| MT-001 | Rounding error | bugs | When shifting or rounding down, ensure unaligned data is not unintentionally lost |
| MT-002 | Rounding error | bugs | Using size >> shift rounding as controls for loops, incorrectly stopping too soon |

#### Size Conversion Patterns
- **Bytes to pages (round down)**: `size >> PAGE_SHIFT` (only when truncation intended)
- Determine the alignment of sizes sent through rounding functions, make sure nothing is lost
- Check for alignment validation of the data represented, not just size validation
- track the alignment not just to the memory allocated, but also of the size field itself.  Ensure data is not lost due to size truncation.

#### Common Mistakes
- Using `size >> PAGE_SHIFT` when `DIV_ROUND_UP(size, PAGE_SIZE)` needed
- Assuming sizes are page-aligned without verification
- Off-by-one in loops when converting between units

## Special Considerations

### Kernel Context Rules
- **Preemption disabled**: Can use per-cpu vars, may be interrupted by IRQs
- **Migration disabled**: Stay on current CPU but may be preempted
- **typeof() safety**: Can be used with container_of() before init
- **Self-tests**: Memory leaks/FD leaks acceptable unless crash system


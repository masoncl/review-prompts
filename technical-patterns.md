# Linux Kernel Technical Review Patterns

## Core instructions

- Trace full execution flow, gather additional context from the call chain to make sure you fully understand
- Don't make assumptions based on return types, checks, WARN_ON(), BUG_ON(), comments, or error
  handling patterns - explicitly verify the code is correct by tracing concrete execution paths
- Never skip any patterns just because you found a bug in another pattern.
- Never skip any patterns unless they don't apply to the code at hand
- Never report errors without checking to see if the error is impossible in the
  call path you found.
    - Some call paths might always check IS_ENABLED(feature) before
      dereferencing a variable
    - The actual implementations of "feature" might not have those checks,
      because they are never called unless the feature is on
    - It's not enough for the API contract to be unclear, you must prove the
    bug can happen in practice.
    - Do not recommend defensive programming unless it fixes a proven bug.

## EFFICIENT PATTERN ANALYSIS METHODOLOGY

### Batched Pattern Application
Apply patterns in category batches to avoid redundant function reads:

1. **Load all relevant functions ONCE** during context gathering
2. **Apply entire pattern categories in single passes**:
   - RM Batch: Apply all RM-001 through RM-010 in one analysis pass
   - EH Batch: Apply all EH-001 through EH-005 in one analysis pass
   - CL Batch: Apply all CL-001 through CL-010 in one analysis pass
   - BV Batch: Apply all BV-001 through BV-004 in one analysis pass
   - CM Batch: Apply all CM-001 through CM-005 in one analysis pass
   - SM Batch: Apply all SM-001 through SM-003 in one analysis pass
   - MT Batch: Apply all MT-001 through MT-002 in one analysis pass
   - Any patterns loaded by subsystem specific prompts, group in passes in
     similar sized chunks to the above

3. **Format**: `**PATTERN ANALYSIS - [CATEGORY] BATCH**` with all patterns listed together

### Smart Context Management (Option 5)
After each pattern category batch:

**RETAIN:**
- Function bodies (needed for cross-pattern analysis)
- Key findings and evidence
- Resource/lock/state identification
- Critical error paths traced

**CLEAR:**
- Detailed pattern explanations and reasoning
- Verbose call chain analysis beyond immediate needs
- Intermediate analysis steps
- Redundant function parameter details

### Batch Analysis Format
```
**PATTERN ANALYSIS - [CATEGORY] [RM/CL/EH/BV/CM/SM/MT] BATCH**

- save tokens: document only that you've applied a pattern, not the details
Category Summary: X/Y patterns analyzed, Z issues found
```

## Core Pattern Categories

### 1. Resource Management [RM]
**Principle**: Every resource must have balanced lifecycle: alloc→init→use→cleanup→free

| Pattern ID | Check | Risk | Common Location |
|------------|-------|------|-----------------|
| RM-001 | 1:1 matching of alloc/free operations | Memory leak | Error paths between alloc and success:
- When reporting on error checking for kmalloc and vmalloc APIs, also find and report the GFP_FLAGS used |
| RM-001a | Resource lifecycle consistency | Resource leak/corruption | Check all resource types and
   state transitions. Trace resource ownership through function boundaries. Verify function contracts:
      if function takes resource X to modify, does X end in expected state? |
| RM-002 | Init-once enforcement for static resources | Double init | Static/global initialization |
| RM-003 | Cleanup in ALL error paths | Resource leak | Between resource acquisition and function return |
| RM-004 | No access after release/enqueue | Use-after-free | Async callbacks, after enqueue operations |
| RM-005 | Proper refcount handling | Use-after-free/leak | refcount_dec_and_test returns true only at zero |
| RM-006 | Object state preservation in reassignment | Memory leak | foo = func(foo) patterns |
| RM-007 | List removal with proper handling | Memory leak | list_del() without return/use may leak |
| RM-008 | Assorted reference counts | Memory leak/Use-after-free | load definitions of ref counting functions to make sure you understand them correctly |
| RM-009 | Function resource contracts | Resource abandonment | MANDATORY: When function accepts
  resource for modification:
     1. Trace EVERY return path - what happens to the original resource?
     2. If function returns different resource, prove original is properly handled
     3. Check lock state, reference counts, and ownership of original resource
     4. Verify caller expectations: does caller expect same resource back?
     5. Look for assignment patterns like "original = new" that may abandon original |
| RM-010 | Object cleanup and reinitialization | Incomplete initialization | When objects are torn down or unregistered:
    - If they are not freed, but instead returned to a pool or are global variables
      - Check to make sure all fields in the object are fully initialized when the object is setup for reuse
      - When freeing/destroying resources referenced by structure fields, ensure the pointer fields are set to NULL to prevent use-after-free on structure reuse
      - ex: unregister_foo() { foo->dead = 1; free(foo->ptr); add to list}
            register_foo() { pull from list ; skip allocation of foo->ptr; foo->ptr->use_after_free;}
      - Assume [kv]free(); [kv]malloc(); and related APIs handle this properly unless you find proof initialization is skipped
      - When you find a missing initialization, check the call paths to see if
        callees actually initialize the variable before using it.

**Key Notes**:
- All pointers have the same size, "char \*foo" takes as much room as "int \*foo"
  - but for code clarity, if we're allocating an array of pointers, and using
    sizeof(type \*) to calculate the size, we should use the correct type
- Trace original resources through the entire code path to make sure they are not leaked
- alloc/free and get/put matching in ALL paths
- State preservation: resource state consistent with return contract
- refcount_t counters do not get incremented after dropping to zero
- Async cleanup (RCU callbacks/work queues) may access uninitialized fields if init fails
- Caller expectation tracing: What does the caller expect to happen to the resource it passed?
- css_get() adds an additional reference, so this results in both sk and newsk having one reference each:
```
     memcg = mem_cgroup_from_sk(sk);
     if (memcg)
             css_get(&memcg->css);
     newsk->sk_memcg = sk->sk_memcg;
```
### 2. Concurrency & Locking [CL]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| CL-001 | Correct lock type for context | Deadlock/sleep bug | Never sleep (mutex/rwsem) in atomic context |
| CL-002 | Lock ordering consistency | ABBA deadlock | Document and verify lock ordering when multiple held |
| CL-003 | Lock requirements traced 2-3 levels | Missing synchronization | Called functions may require locks |
| CL-004 | Race window analysis | Data corruption | Check between resource release and subsequent access:
- race windows need hard proof showing that both sides of the race can occurin practice.
- do not worry about theoritical races, only proven races |
| CL-005 | Memory ordering for lockless access | Data corruption | READ_ONCE/WRITE_ONCE for shared fields |
| CL-006 | Trylock→lock conversion safety | Deadlock | May introduce new deadlock scenarios |
| CL-007 | Cleanup ordering | Use-after-free | Stop users → wait completion → destroy resources |
| CL-008 | IRQ-safe locking | IRQ corruption | Use _irqsave if lock taken from IRQ context |
| CL-009 | Assorted locking | bugs | load definitions of locking functions to make sure you understand them correctly |
| CL-010 | Lock handoff verification | Lock imbalance | When function may return different locked
  object:
     1. Verify original locked object's lock state is properly handled
     2. Check if caller knows which lock to release
     3. Trace lock acquisition/release balance for ALL objects involved |

**Lock Context Compatibility Matrix**:
| Lock Type | Process | Softirq | Hardirq | Sleeps |
|-----------|---------|---------|---------|--------|
| spin_lock | ✓ | ✓ | ✓ | ✗ |
| spin_lock_bh | ✓ | ✗ | ✗ | ✗ |
| spin_lock_irqsave | ✓ | ✓ | ✓ | ✗ |
| mutex/rwsem | ✓ | ✗ | ✗ | ✓ |

- READ_ONCE() is not required when the data structure being read is protected by a lock we're currently holding
- Resource switching detection: Flag any path where function returns different resource than it was meant to modify, ensure the proper locks are held or released as needed.
- Caller expectation tracing: What does the caller expect to happen to the resource it passed?

### 3. Error Handling [EH]

| Pattern ID | Check | Risk | Example |
|------------|-------|------|---------|
| EH-001 | NULL safety verification | NULL deref | Trace callers for NULL passing, especially cleanup paths |
| EH-002 | ERR_PTR vs NULL consistency | Wrong error check | Don't mix IS_ERR with NULL checks |
| EH-003 | Error value preservation | Lost errors | Watch for `ret = func(); ... ret = 0;` patterns |
| EH-004 | Return type changes handled | Wrong returns | When signatures change, verify ALL return statements |
| EH-005 | Required interface handling | NULL deref | Ops structs with required functions per documentation |

- If code checks for a condition via WARN_ON() or BUG_ON() assume that condition will never happen, unless you can provide concrete evidence of that condition existing via code snippets and call traces
- if (WARN_ON(foo)) { return; } might exit a function early, check for
incomplete initialization or other mistakes that leave data structures in an
inconsistent state

### 4. Bounds & Validation [BV]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| BV-001 | Bounds checked at point of use | Buffer overflow | Not just where received, but where accessed:
 - strscpy() can do automatic size detection for arrays, and this works when
   pointers to arrays are copied and the compiler is able to find the type
 - char \*s = ""; strlen(s) returns zero, but it safe to access s[0];
 - a common pattern memcpy(dst + (offset & mask), src, size); usually includes
   alignment validation of 'offset' somewhere else in the code.  Try to find
   that validation before reporting |
 - global arrays often have a MAX_FOO parameter that corresponds to the maximum
  possible elements.  Before reporting an overflow, check if it is impossible
  to create more than MAX_FOO elements in the first place.

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


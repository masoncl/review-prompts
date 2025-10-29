# Linux Kernel Technical Review Patterns

## Core instructions

- Trace full execution flow, gather additional context from the call chain to make sure you fully understand
- IMPORTANT: never make assumptions based on return types, checks, WARN_ON(), BUG_ON(), comments, or error
  handling patterns - explicitly verify the code is correct by tracing concrete execution paths
- IMPORTANT: never assume that changing a WARN_ON() or BUG_ON() statement changes the
  errors or conditions a function can accept.  They indicate changes to
  what is printed to the console, and nothing else.
- IMPORTANT: never skip any patterns just because you found a bug in another pattern.
- Never report errors without checking to see if the error is impossible in the
  call path you found.
    - Some call paths might always check IS_ENABLED(feature) before
      dereferencing a variable
    - The actual implementations of "feature" might not have those checks,
      because they are never called unless the feature is on
    - It's not enough for the API contract to be unclear, you must prove the
    bug can happen in practice.
    - Do not recommend defensive programming unless it fixes a proven bug.

## Smart Context Management (Option 5)
After each pattern:

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

## Core Pattern Categories

### 1. Call Stack Analysis [CS]

**IMPORTANT:** Process the CS patterns first to build the global template

**Patterns**:
- **CS-001** (patterns/CS-001.md): Callee analysis (down the stack) — Required for all non-trivial changes
- **CS-002** (patterns/CS-002.md): Caller analysis (up the stack) — Required for all non-trivial changes
- **CS-003** (patterns/CS-003.md): Cross-function data flow — Mandatory when variables passed between functions, or data format changes, or encoding changes

### 2. Resource Management [RM]

**Principle**: Every resource must have balanced lifecycle: alloc→init→use→cleanup→free

**Key Notes**:
- All pointers have the same size, "char \*foo" takes as much room as "int \*foo"
  - but for code clarity, if we're allocating an array of pointers, and using
    sizeof(type \*) to calculate the size, we should use the correct type
- refcount_t counters do not get incremented after dropping to zero
- css_get() adds an additional reference, ex: this results in both sk and newsk having one reference each:
```
     memcg = mem_cgroup_from_sk(sk);
     if (memcg)
             css_get(&memcg->css);
     newsk->sk_memcg = sk->sk_memcg;
```
- If you find a type mismatch (using \*foo instead of foo etc), trace the type
  fully and check against the expected type to make sure you're flagging it
  correctly
- refcount_dec_and_test returns true only at zero

**Patterns**:
- **RM-002** (patterns/RM-002.md): Init-once enforcement for static resources — When global objects are initialized or changed
- **RM-003** (patterns/RM-003.md): No access after release/enqueue — When memory is freed or handed over to asynchronous workers
- **RM-004** (patterns/RM-004.md): Object state preservation in reassignment — When pointers to allocated memory are overwritten
- **RM-005** (patterns/RM-005.md): List removal with proper handling — When removing resources from lists (ex: list_del())
- **RM-006** (patterns/RM-006.md): Function resource contracts — For all function calls with arguments
- **RM-007** (patterns/RM-007.md): Object cleanup and reinitialization — Mandatory when objects are freed, torn down or unregistered
- **RM-008** (patterns/RM-008.md): Variable and field initialization — For any non-trivial changes
- **RM-009** (patterns/RM-009.md): memcg accounting — Mandatory when page, slab or vmalloc APIs are used (skip otherwise)

### 3. Concurrency & Locking [CL]

**Lock Context Compatibility Matrix**:
| Lock Type | Process | Softirq | Hardirq | Sleeps |
|-----------|---------|---------|---------|--------|
| spin_lock | ✓ | ✓ | ✓ | ✗ |
| spin_lock_bh | ✓ | ✗ | ✗ | ✗ |
| spin_lock_irqsave | ✓ | ✓ | ✓ | ✗ |
| mutex/rwsem | ✓ | ✗ | ✗ | ✓ |

**Notes**:
- READ_ONCE() is not required when the data structure being read is protected by a lock we're currently holding
- Resource switching detection: Flag any path where function returns different resource than it was meant to modify, ensure the proper locks are held or released as needed.
- Caller expectation tracing: What does the caller expect to happen to the resource it passed?

**Patterns**:
- **CL-001** (patterns/CL-001.md): Lock type and ordering — When locks are taken or released
- **CL-002** (patterns/CL-002.md): Lock handoff and balance — When locked objects are returned or passed between functions
- **CL-004** (patterns/CL-004.md): Race window analysis — When concurrent access to shared datastructures is possible
- **CL-005** (patterns/CL-005.md): Memory ordering for lockless access — When shared fields accessed without locks
- **CL-007** (patterns/CL-007.md): Cleanup ordering — When memory is freed
- **CL-012** (patterns/CL-012.md): New concurrent access to shared resources — With any writes to shared resources

### 4. Error Handling [EH]

**Notes**:
- If code checks for a condition via WARN_ON() or BUG_ON() assume that condition will never happen, unless you can provide concrete evidence of that condition existing via code snippets and call traces
- if (WARN_ON(foo)) { return; } might exit a function early, check for incomplete initialization or other mistakes that leave data structures in an inconsistent state

**Patterns**:
- **EH-001** (patterns/EH-001.md): NULL safety verification — Mandatory when pointers are dereferenced
- **EH-002** (patterns/EH-002.md): ERR_PTR vs NULL consistency — When pointers are returned or checked against NULL/ERR_PTR
- **EH-003** (patterns/EH-003.md): Error value preservation — When error values overwritten before action taken
- **EH-004** (patterns/EH-004.md): Return value changes handled — When return values or types change
- **EH-005** (patterns/EH-005.md): Required interface handling — When ops structs, created, changed, or any calls of ops struct members are found

### 5. Bounds & Validation [BV]

**Important**: Never suggest defensive bounds checks unless you can prove the source is untrusted.

**Patterns**:
- **BV-001** (patterns/BV-001.md): Bounds and validation at point of use — When array or buffer indexing occurs
- **BV-002** (patterns/BV-002.md): Integer overflow/underflow/truncation before use — When integer arithmetic or type conversions occur
- **BV-003** (patterns/BV-003.md): Logic change completeness — For all non-trivial changes

### 6. Code Movement [CM]

**Patterns**:
- **CM-001** (patterns/CM-001.md): Code movement validation — For all non-trivial changes
- **CM-002** (patterns/CM-002.md): Data format and return value changes — When data encoding or interpretation changes for a variable or structure

### 7. State Machines & Flags [SM]

**Patterns**:
- **SM-001** (patterns/SM-001.md): State machine completeness — When state or flag variables are modified

### 8. Math [MT]

**Patterns**:
- **MT-001** (patterns/MT-001.md): Math and rounding correctness — When numbers are shifted or rounded up or down
- **MT-002** (patterns/MT-002.md): Size Conversion Patterns — When bytes converted to pages (round down) `size >> PAGE_SHIFT` (only when truncation intended)

### 9. Documentation Enforcement

**Principle**: When commit messages or new comments contain assertions or constraints, validate they are honored in the new code

## Special Considerations

### Kernel Context Rules
- **Preemption disabled**: Can use per-cpu vars, may be interrupted by IRQs
- **Migration disabled**: Stay on current CPU but may be preempted
- **typeof() safety**: Can be used with container_of() before init
- **Self-tests**: Memory leaks/FD leaks acceptable unless crash system
- **likely()/unlikely()**: don't report on changes to compiler hinting unless
  they introduce larger logic bugs

# Linux Kernel Technical Deep-dive Patterns

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

## Pattern Classification

Assess each pattern's relevance using semantic reasoning, but use these shortcuts to decide quickly:

**Relevance levels:**
- APPLIES: Pattern is relevant, analyze it
- SKIP: Pattern clearly does not apply to this diff

**Default is APPLIES** — only SKIP when you're certain the pattern cannot trigger. When in doubt, analyze the pattern.

**Decision shortcuts** (use these to fast-path your decision):
- If the diff doesn't touch the construct a pattern protects, SKIP
- If you see the exact keywords/operations a pattern targets, APPLIES
- If uncertain whether pattern applies, APPLIES (err on the side of analysis)

**Output format:**
```
Patterns to analyze: [list with one-line justification each]
```

## Core Pattern Categories

As you identify patterns that need to be fully analyzed, add each pattern
that you will apply into a TodoWrite.  Only make them complete in the TodoWrite
when you've analyzed each one.

### 1. Call Stack Analysis [CS]

**IMPORTANT:** Process the CS patterns first to build the global template

**Patterns**:
- **CS-001** (patterns/CS-001.md): Correctness — required for all non-trivial changes
  - APPLIES: any non-trivial patches
  - SKIP: pure comment/whitespace changes only

- **CS-003** (patterns/CS-003.md): Cross-function data flow
  - APPLIES: variables passed between functions change meaning, data format changes, encoding changes
  - SKIP: no cross-function data flow changes

### 2. Resource Management [RM]

**Principle**: Every resource must have balanced lifecycle: alloc→init→use→cleanup→free

**Key Notes**:
- All pointers have the same size, "char \*foo" takes as much room as "int \*foo"
  - but for code clarity, if we're allocating an array of pointers, and using
    sizeof(type \*) to calculate the size, we should use the correct type
- refcount_t counters do not get incremented after dropping to zero
- refcount_dec_and_test returns true only at zero
- css_get() adds an additional reference, ex: this results in both sk and newsk having one reference each:
```
     memcg = mem_cgroup_from_sk(sk);
     if (memcg)
             css_get(&memcg->css);
     newsk->sk_memcg = sk->sk_memcg;
```
- If you find a type mismatch (using \*foo instead of foo etc), trace the type
  fully and check against the expected type to make sure you're flagging it correctly

**Patterns**:
- **RM-002** (patterns/RM-002.md): Init-once enforcement for static resources
  - APPLIES: global/static objects initialized or changed, `__init` functions modified
  - SKIP: no static/global resource initialization

- **RM-003** (patterns/RM-003.md): No access after release/enqueue
  - APPLIES: `kfree`, `put_`, `release`, `queue_work`, `schedule_work`, or handoff to async context
  - SKIP: no memory free or async handoff operations

- **RM-005** (patterns/RM-005.md): List removal with proper handling
  - APPLIES: `list_del`, `list_move`, `hlist_del` or similar list operations
  - SKIP: no list manipulation

- **RM-006** (patterns/RM-006.md): Function resource contracts — for all function calls with arguments
  - APPLIES: functions with refcount/ownership semantics, `_get`/`_put` patterns, pointer reassignment, or any function args that might transfer ownership
  - SKIP: no function calls, or only pure/stateless function calls

- **RM-007** (patterns/RM-007.md): Object cleanup and reinitialization
  - APPLIES: objects freed, torn down, unregistered, or reused
  - SKIP: no cleanup or teardown paths modified

- **RM-008** (patterns/RM-008.md): Variable and field initialization
  - APPLIES: always check for non-trivial patches
  - SKIP: trivial patches only

- **RM-009** (patterns/RM-009.md): memcg accounting
  - APPLIES: page, slab, or vmalloc APIs — `__GFP_`, `page_`, `folio_`, `kmalloc`, `kmem_cache_`, `vmalloc`, `alloc_pages` or similar
  - SKIP: no page/slab/vmalloc operations

- **RM-010** (patterns/RM-010.md): cleanup.h helpers
  - APPLIES: `__free`, `guard(`, `scoped_guard`, `DEFINE_FREE`, `DEFINE_GUARD`, `no_free_ptr`, `return_ptr`
  - SKIP: no cleanup.h helper usage

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
- **CL-001** (patterns/CL-001.md): Lock type and ordering
  - APPLIES: any locks are held, taken, or released in modified functions.  Includes every kind of lock (spin_lock, mutex, rwsem, seqlocks, etc)
  - SKIP: no locking operations in diff

- **CL-002** (patterns/CL-002.md): Lock handoff and balance
  - APPLIES: locked objects returned or passed between functions, lock scope changes
  - SKIP: no lock handoff patterns

- **CL-004** (patterns/CL-004.md): Race window analysis
  - APPLIES: shared data structures accessed, writes to shared resources, any concurrent access possible
  - SKIP: purely local/stack variables with no shared access

- **CL-005** (patterns/CL-005.md): Memory ordering for lockless access
  - APPLIES: `READ_ONCE`, `WRITE_ONCE`, `smp_`, `barrier`, lockless shared field access
  - SKIP: all shared access is lock-protected

- **CL-007** (patterns/CL-007.md): Cleanup ordering
  - APPLIES: memory freed, ordering between cleanup operations matters
  - SKIP: no cleanup/free operations

### 4. Error Handling [EH]

**Notes**:
- If code checks for a condition via WARN_ON() or BUG_ON() assume that condition will never happen, unless you can provide concrete evidence of that condition existing via code snippets and call traces
- if (WARN_ON(foo)) { return; } might exit a function early, check for incomplete initialization or other mistakes that leave data structures in an inconsistent state

**Patterns**:
- **EH-001** (patterns/EH-001.md): NULL safety verification
  - APPLIES: always check for non-trivial patches
  - SKIP: trivial patches only

- **EH-002** (patterns/EH-002.md): ERR_PTR vs NULL consistency
  - APPLIES: `ERR_PTR`, `IS_ERR`, `PTR_ERR` used, pointer return value semantics
  - SKIP: no ERR_PTR patterns

- **EH-003** (patterns/EH-003.md): Error value preservation
  - APPLIES: error values captured then used later, `goto` error paths, error variable reassignment
  - SKIP: no error handling changes

- **EH-004** (patterns/EH-004.md): Return value changes handled
  - APPLIES: function return value or type changes, callers may need updates
  - SKIP: no return value changes

- **EH-005** (patterns/EH-005.md): Required interface handling
  - APPLIES: ops structs created/changed, calls to ops struct members (`->callback()`), interface contracts
  - SKIP: no ops struct or interface changes

### 5. Bounds & Validation [BV]

**Important**: Never suggest defensive bounds checks unless you can prove the source is untrusted.

**Patterns**:
- **BV-001** (patterns/BV-001.md): Bounds and validation at point of use
  - APPLIES: array/buffer indexing with variables, loop bounds, user-controlled indices
  - SKIP: no array indexing or only constant indices

- **BV-002** (patterns/BV-002.md): Integer overflow/underflow/truncation before use
  - APPLIES: integer arithmetic on sizes, type conversions/casts, `<<` `>>` shifts
  - SKIP: no integer arithmetic or type conversions

- **BV-003** (patterns/BV-003.md): Logic change completeness
  - APPLIES: all non-trivial changes
  - SKIP: trivial patches only

### 6. Code Movement [CM]

**Patterns**:
- **CM-001** (patterns/CM-001.md): Code movement validation — for all non-trivial changes
  - APPLIES: any non-trivial change
  - SKIP: trivial patches only (comments, whitespace)

- **CM-002** (patterns/CM-002.md): Data format and return value changes
  - APPLIES: data encoding/interpretation changes, struct layout changes, byte order
  - SKIP: no data format changes

### 7. State Machines & Flags [SM]

**Patterns**:
- **SM-001** (patterns/SM-001.md): State machine completeness
  - APPLIES: `state =`, `flags |=`, `flags &=`, `set_bit`, `clear_bit`, `test_bit`, state transitions
  - SKIP: no state or flag modifications

### 8. Math [MT]

**Patterns**:
- **MT-001** (patterns/MT-001.md): Math and rounding correctness
  - APPLIES: `PAGE_SHIFT`, `round_up`, `round_down`, `DIV_ROUND`, division, modulo
  - SKIP: no rounding or division operations

- **MT-002** (patterns/MT-002.md): Size Conversion Patterns — bytes to pages (round down) only when truncation intended
  - APPLIES: bytes↔pages conversions, `>> PAGE_SHIFT`, size calculations where truncation matters
  - SKIP: no size unit conversions

### 9. Subjective Review Patterns
- **SR-001** (patterns/SR-001.md): Subjective general assessment — only when the prompt explicitly requests this pattern

## Special Considerations

### Kernel Context Rules
- **Preemption disabled**: Can use per-cpu vars, may be interrupted by IRQs
- **Migration disabled**: Stay on current CPU but may be preempted
- **typeof() safety**: Can be used with container_of() before init
- **Self-tests**: Memory leaks/FD leaks acceptable unless crash system
- **likely()/unlikely()**: don't report on changes to compiler hinting unless
  they introduce larger logic bugs

# Linux Kernel Technical Review Patterns

## Core instructions

- Trace full execution flow, gather additional context from the call chain to make sure you fully understand
- Don't make assumptions based on return types, checks, WARN_ON(), BUG_ON(), comments, or error
  handling patterns - explicitly verify the code is correct by tracing concrete execution paths
- Never assume that changing a WARN_ON() or BUG_ON() statement changes the
  errors or conditions a function can accept.  They indicate changes to
  what is printed to the console, and nothing else.
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

0. Use TodoWrite to track specific details of every pattern you fully analyze,
make sure you complete every one.  Include any subsystem specific prompts loaded as well.
1. **Load all relevant functions ONCE** during context gathering
2. **Apply entire pattern categories in single passes**:
   - CS Batch: Apply all CS-* in one analysis pass (call stack traversal patterns)
   - RM Batch: Apply all RM-* in one analysis pass
   - EH Batch: Apply all EH-* in one analysis pass
   - CL Batch: Apply all CL-* in one analysis pass
   - BV Batch: Apply all BV-* in one analysis pass
   - CM Batch: Apply all CM-* in one analysis pass
   - SM Batch: Apply all SM-* in one analysis pass
   - MT Batch: Apply all MT-* in one analysis pass
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
**PATTERN ANALYSIS - [CATEGORY] [CS/RM/CL/EH/BV/CM/SM/MT] BATCH**

- save tokens: document only that you've applied a pattern, not the details
Category Summary: X/Y patterns analyzed, Z issues found
```

## Core Pattern Categories

### 1. Call Stack Analysis [CS]

**Principle**: Many bugs require tracing execution flow up to callers or down to callees. Group these checks to minimize redundant traversals.

#### CS-001: Callee analysis (down the stack)

**Risk**: Various

**When to check**: Functions modified or newly added that call other functions

**Callee traversal process**:
- Step 1: Identify all direct callees in modified functions, track in TodoWrite
- Step 2: For each callee, load function definition
- Step 3: Trace 2-3 levels deep, adding callees to TodoWrite as discovered
- Step 4: Apply all checks below to each callee in the chain

**Lock requirements**: Check lock requirements for each callee
- Track lock requirements found for each callee in TodoWrite

**Error path locking**: For every lock acquired, trace every error path through callees ensuring locks properly released/handed off
- Track each error path traced through callees in TodoWrite

**Resource propagation**: Trace resource ownership through callee boundaries (where does resource end up?)
- Track each resource flow through callees in TodoWrite

**Initialization delegation**: When variables/fields may be uninitialized, check if callees initialize before use
- Track each variable/field and initialization status per callee in TodoWrite

**Note**: Consolidate all findings in single TodoWrite section for callee analysis

#### CS-002: Caller analysis (up the stack)

**Risk**: Various

**When to check**: Functions with modified signatures, return values, or argument constraints

**NULL passing**: Trace callers for NULL passing, especially cleanup paths

**Locking**: track locks held at return time:
- make sure they match caller expectation
- if different from locks held when called or if locks are dropped during the call,
  make sure something has properly revalidated state under the new lock

**Return value propagation**: When return values/types change:
- Step 1: Identify all direct callers, track in TodoWrite
- Step 2: For each caller, verify new return values handled properly
  - differentiate between checking a return value and checking all possible variations.
  - ex: NULL, ERR_PTR(), negative error values vs positive status etc
- Step 3: For callers that propagate return value, add their callers to TodoWrite
- Step 4: Repeat recursively until no more propagation
- Do not skip any callers

**Caller expectations**: Verify callers' expectations about resource state match function behavior

**Note**: Track all caller chains in TodoWrite

#### CS-003: Cross-function data flow

**Risk**: Logic error

**When to check**: Data format changes, encoding changes, or variables passed between functions

**Full lifecycle tracking**: Track variable through ENTIRE lifecycle: set → store → read → use

**Consumer verification**: Track all functions receiving modified variables in TodoWrite

**Format consistency**: Verify ALL consumers updated to match any changes

**Producer/consumer sync**: Check both modified and unmodified code paths

**Note**: Track complete data flow in TodoWrite

**Optimization notes**:
- Perform CS-* patterns in a single pass when tracing call chains
- Load caller/callee context once, apply all CS checks together
- Use TodoWrite to avoid redundant traversals

### 2. Resource Management [RM]

**Principle**: Every resource must have balanced lifecycle: alloc→init→use→cleanup→free

#### RM-001: Resource lifecycle management

**Risk**: Memory leak/corruption

**Common Location**: Error paths between alloc and success

**Requirements**:
- Track ALL resources in TodoWrite (allocations, locks, references, file handles, etc.)
- Verify 1:1 matching: every alloc has corresponding free in ALL paths
- Check cleanup in ALL error paths between acquisition and function return
- For every modified function, list ALL resources acquired
- For every return/goto, verify every previously acquired resource is cleaned up
- Verify function contracts: if function takes resource X to modify, does X end in expected state?
- Track all resource types and state transitions in TodoWrite
- When reporting kmalloc/vmalloc errors, include GFP_FLAGS used

**Note**: For cross-function resource flow, see CS-001 and CS-002

#### RM-002: Init-once enforcement for static resources

**Risk**: Double init

**Common Location**: Static/global initialization

#### RM-004: No access after release/enqueue

**Risk**: Use-after-free

**Common Location**: Async callbacks, after enqueue operations

#### RM-005: Proper refcount handling

**Risk**: Use-after-free/leak

**Details**: refcount_dec_and_test returns true only at zero

#### RM-006: Object state preservation in reassignment

**Risk**: Memory leak

**Common Location**: foo = func(foo) patterns

#### RM-007: List removal with proper handling

**Risk**: Memory leak

**Details**: list_del() without return/use may leak

#### RM-008: Assorted reference counts

**Risk**: Memory leak/Use-after-free

**Details**: load definitions of ref counting functions to make sure you understand them correctly

#### RM-009: Function resource contracts

**Risk**: Resource abandonment

**MANDATORY**: When function accepts resource for modification:
0. Track every resource in the TodoWrite
1. Trace EVERY return path - what happens to the original resource?
2. If function returns different resource, prove original is properly handled
3. Check lock state, reference counts, and ownership of original resource
4. Look for assignment patterns like "original = new" that may abandon original

**Note**: For caller expectation verification, see CS-002

#### RM-010: Object cleanup and reinitialization

**Risk**: Incomplete initialization

**When to check**: When objects are torn down or unregistered:
- Track every object torn down in the TodoWrite
- If they are not freed, but instead returned to a pool or are global variables
  - Check to make sure all fields in the object are fully initialized when the object is setup for reuse
  - When freeing/destroying resources referenced by structure fields, ensure the pointer fields are set to NULL to prevent use-after-free on structure reuse
  - ex: unregister_foo() { foo->dead = 1; free(foo->ptr); add to list}
        register_foo() { pull from list ; skip allocation of foo->ptr; foo->ptr->use_after_free;}
  - Assume [kv]free(); [kv]malloc(); and related APIs handle this properly unless you find proof initialization is skipped

**Note**: For checking if callees initialize variables, see CS-001

#### RM-011: Variable and field initialization

**Risk**: uninit memory usage

**Details**:
- global variables and static variables are zero filled automatically
- Track all other variable/field access from in TodoWrite
- slab and vmalloc APIs have variants that zero fill, and __GFP_ZERO gfp mask does as well
- kmem_cache_create() can use an init_once() function to initialize slab ojbects
  - this only happens on the first allocation, and protects us from garbage in the struct
- trace variable/field access to make sure they are initialized before use
- Writing structure members, or passing to functions that only write without reading, both count as initializing the member.
- special attention for error paths (goto fail)
- if you can't verify fully, check against other similar usage

#### RM-012: memcg accounting

**Risk**: Incorrect memory accounting

**When to check**: skip this pattern unless page, slab or vmalloc APIs are used

**Details**:
- When using __GFP_ACCOUNT, ensure the correct memcg is charged
  - old = set_active_memcg(memcg) ; work ; set_active_memcg(old)
- slabs created with SLAB_ACCOUNT implicitly have __GFP_ACCOUNT on every allocation
- Most usage does not need set_active_memcg(), but:
  - helpers operating in kthreads switching context between many memcgs may need it
  - helpers operating on objects (ex BPF maps) that store an memcg to be charged against at creation time may need it
- by default most usage charges memory to the task's memcg
- Ensure new __GFP_ACCOUNT usage is consistent with the charging model used in the rest of the surrounding code

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
- If you find a type mismatch (using \*foo instead of foo etc), trace the type
  fully and check against the expected type to make sure you're flagging it
  correctly
### 3. Concurrency & Locking [CL]

#### CL-001: Lock type and ordering

**Risk**: Deadlock/sleep bug

**Requirements**:
- Never sleep (mutex/rwsem/schedule/sleeping allocations) in atomic context
- Use _irqsave if lock taken from IRQ context
- Document and verify lock ordering when multiple locks held
- Trylock→lock conversion may introduce deadlock scenarios

#### CL-002: Lock handoff and balance

**Risk**: Missing synchronization

**Requirements**:
- Track lock handoff when returning different locked objects in TodoWrite
- When function returns with different lock than originally held:
  - Verify original locked object's lock state properly handled
  - Check if caller knows which lock to release
  - Trace lock acquisition/release balance for ALL objects involved
- When locks dropped/reacquired, verify protected objects not stale
- Load definitions of locking functions to understand them correctly

**Note**: For lock requirements in callees, see CS-001

#### CL-004: Race window analysis

**Risk**: Data corruption

**When to check**: Check concurrent access:
- Create TodoWrite items to track all concurrent to shared datastructures made
- Verify proper exclusion exists (rcu, locking etc)
- when shared data-structures can be read or written concurrently with other writes
- race windows need hard proof showing that both sides of the race can occurin practice.
- do not worry about theoritical races, only proven races

**To test a race window between two contexts**:
- Add a TodoWrite for every critical section
- Trace normal execution without interruption
- Trace potential races assuming interruptions or concurrency at every point in the critical section
- Think about changes introduced by the patch to potential interruptions or concurrency in the critical section

#### CL-005: Memory ordering for lockless access

**Risk**: Data corruption

**Details**: READ_ONCE/WRITE_ONCE for shared fields

#### CL-007: Cleanup ordering

**Risk**: Use-after-free

**Pattern**: Stop users → wait completion → destroy resources

#### CL-011: Error handling locks

**Risk**: Incorrect locking

**Details**: For every lock acquired in modified functions, check all error paths ensure locks properly released or handed off

**Note**: For tracing error paths through callees, see CS-001

#### CL-012: New concurrent access to shared resources

**Risk**: Race condition

**When to check**: Patch adds new writes to variables/timers/resources already accessed elsewhere

**Process**:
- **Step 1**: Identify all shared resources being written (state vars, timers, flags, etc.)
- **Step 2**: Use grep/semcode to find ALL other write sites for same resources
- **Step 3**: Document execution context for each write site:
  - Process context
  - Workqueue context
  - Softirq context
  - Hardirq context
- **Step 4**: Check if new writes can race with existing writes:
  - Softirq can interrupt: process, workqueue
  - Hardirq can interrupt: everything
  - Workqueues can run concurrent with process context
- **Step 5**: Check for synchronization (locks, atomic ops, memory barriers)
- Track analysis in TodoWrite with resource name, contexts, and values

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

### 4. Error Handling [EH]

#### EH-001: NULL safety verification

**Risk**: NULL deref

**Requirements**:
- Track every pointer access in the TodoWrite
- Don't dereference potentially NULL pointers (including in BUG_ON/WARN_ON statements)
- Trace pointers to ensure they are checked for NULL properly
- If unsure, check to make sure new code maintains similar checks to old code

**Note**: For tracing NULL passing from callers, see CS-002

#### EH-002: ERR_PTR vs NULL consistency

**Risk**: Wrong error check

**Details**: Don't mix IS_ERR with NULL checks

#### EH-003: Error value preservation

**Risk**: Lost errors

**Requirements**:
- Track every error value overwrite in TodoWrite
- Watch for `ret = func(); ... ret = 0;` patterns
- When loops accumulate errors:
  - Trace at least 2 concrete iteration scenarios
  - Scenario 1: [fail, fail] - does final error match last failure?
  - Scenario 2: [fail, success] - is error cleared on success?
  - Scenario 3: [success, fail] - does success get overwritten?
  - Compare to similar patterns in codebase for consistency
  - Ask: Should partial success clear previous recoverable errors?

#### EH-004: Return value changes handled

**Risk**: Wrong returns

**When to check**: When return values or types change:
- Verify ALL return statements in modified function are correct

**Note**: For recursive caller analysis and return value propagation, see CS-002

#### EH-005: Required interface handling

**Risk**: NULL deref

**Details**: Ops structs with required functions per documentation

**Additional Notes**:
- If code checks for a condition via WARN_ON() or BUG_ON() assume that condition will never happen, unless you can provide concrete evidence of that condition existing via code snippets and call traces
- if (WARN_ON(foo)) { return; } might exit a function early, check for incomplete initialization or other mistakes that leave data structures in an inconsistent state

### 5. Bounds & Validation [BV]

#### BV-001: Bounds and validation at point of use

**Risk**: Buffer overflow

**Requirements**:
- Track all index usage in TodoWrite
- Check bounds where data accessed, not just where received
- Revalidate if size can change between check and use
- Validate untrusted data sources only (don't add defensive checks for trusted data)

**Notes on common patterns**:
- strscpy() auto-detects array sizes when compiler can find the type
- char \*s = ""; strlen(s) returns zero, but s[0] is safe to access
- memcpy(dst + (offset & mask), src, size) usually has alignment validation elsewhere
- Global arrays with MAX_FOO: check if impossible to create more than MAX_FOO elements

#### BV-002: Integer overflow/truncation before use

**Risk**: Buffer overflow/logic error

**Requirements**:
- Watch for implicit type conversions when assigning to smaller types (u64 → u32, u32 → u16, etc.)
- Check 16/32-bit arithmetic before array access or calculations
- Check every assignment for truncation issues, tracing types of both sides
- Don't worry about casts between u32 -> int
- if you think a variable can overflow over time, make sure the period of time required is a practical concern
- Add every integer assignment to TodoWrite with type definitions of both sides

#### BV-005: Logic change completeness

**Risk**: Incorrect behavior

**When to check**: When code changes or duplicates existing checks:
- Track every change in the TodoWrite
- Check changes against original condition-by-condition
- Check changes against the intentional changes from the commit message
- Verify ALL boolean conditions are correct
- For flag/constant changes: Trace what values are used in the documented problem case, not all theoretical values
  - theoretical bugs should not be flagged
- Check if A && B became just B (logic weakening without explanation)

**Important**: Never suggest defensive bounds checks unless you can prove the source is untrusted.

### 6. Code Movement [CM]

#### CM-001: Code movement validation

**Risk**: Stale values/missing state

**Requirements**:
- Track all code movement in the TodoWrite
- Verify variable scope valid at new location (variables may be modified between old/new location)
- Check loop bounds still valid: trace 3+ iterations with concrete element names
  - For comparison changes: trace old and new iteration side-by-side
  - for(init; condition; advance) checks condition before executing body
  - Document which elements are included/excluded from processing
  - Verify boundary element handling: is it processed or skipped?
- Verify context dependencies preserved (functions may need locks/state from original location)
- Check for inverted conditionals

#### CM-002: Data format and return value changes

**Risk**: Logic error

**Requirements**:
- When changing how data is encoded/interpreted within a function, verify consistency
- Verify return values used correctly in new location

**Note**: For cross-function data flow and consumer verification, see CS-003

### 7. State Machines & Flags [SM]

#### SM-001: State machine completeness

**Risk**: Invalid state/infinite loop

**Requirements**:
- Track all state/flag changes in TodoWrite
- Verify ALL relevant functions check new flags
- Ensure all paths handle new states/flags
- Check new stop flags in existing loops

### 8. Math [MT]

#### MT-001: Math and rounding correctness

**Risk**: Data loss/logic error

**Requirements**:
- When shifting or rounding, ensure unaligned data not lost
- Verify loop controls with rounding don't stop too soon
- Check alignment of both memory AND size fields
- Use DIV_ROUND_UP when needed, not size >> PAGE_SHIFT for rounding up

### 9. Documentation Enforcement

**Principle**: When commit messages or new comments contain assertions or constraints, validate they are honored in the new code

#### Size Conversion Patterns

**Bytes to pages (round down)**: `size >> PAGE_SHIFT` (only when truncation intended)

**Requirements**:
- Determine the alignment of sizes sent through rounding functions, make sure nothing is lost
- Check for alignment validation of the data represented, not just size validation
- track the alignment not just to the memory allocated, but also of the size field itself. Ensure data is not lost due to size truncation.

#### Common Mistakes

**Watch for**:
- Using `size >> PAGE_SHIFT` when `DIV_ROUND_UP(size, PAGE_SIZE)` needed
- Assuming sizes are page-aligned without verification
- Off-by-one in loops when converting between units

## Special Considerations

### Kernel Context Rules
- **Preemption disabled**: Can use per-cpu vars, may be interrupted by IRQs
- **Migration disabled**: Stay on current CPU but may be preempted
- **typeof() safety**: Can be used with container_of() before init
- **Self-tests**: Memory leaks/FD leaks acceptable unless crash system


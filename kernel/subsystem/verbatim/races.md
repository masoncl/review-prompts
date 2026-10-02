# Race Condition Tracing

This document teaches a systematic method for finding race conditions in
Linux kernel code by tracing parallel execution timelines on shared data. It
is a method, not a description of any tree, so it is maintained by hand and is
not rebuilt from questions. The locking reference needed to verify a timeline
(which contexts each lock may be taken in, nesting, memory ordering, RCU,
PREEMPT_RT, seqlocks) is in `locking.md`; load it alongside this file.

## The Core Mental Model

A race condition is a concrete scenario where two CPUs execute instructions
in a specific interleaved order that produces a wrong outcome. To find
races, build these timelines explicitly.

At every point in one CPU's code path, ask: **"what could the other CPU be
doing right now?"** The answer is: anything in its own code path, at any
point, unless a synchronization mechanism forces an ordering.

## Step-by-Step Tracing Method

### Step 1: Identify the Shared Data

Shared data includes global variables, fields inside globally-reachable
objects (e.g., `inode->i_size`), reference counts, state flags, and list
linkage pointers. Any struct member accessed from more than one code path
is potentially shared.

### Step 2: Enumerate All Code Paths

For each shared variable, list every code path that reads or writes it:
syscall handlers, interrupt handlers (hardirq, softirq), workqueue
callbacks, timer functions, tasklets, module init/exit, network receive
paths (NAPI poll). Each pair of paths is a potential race to analyze.

### Step 3: Build the Timeline

Take two code paths, lay them side by side. Find an interleaving that
produces a wrong outcome.

Example — TOCTOU race on a list:
```
CPU 0 (delete)                    CPU 1 (add)
──────────────                    ──────────
list_empty() returns TRUE
  → decides to skip delete
                                  spin_lock_bh(&lock)
                                  list_add(&rt->rt6i_uncached, &list)
                                  spin_unlock_bh(&lock)
return (skips deletion!)
→ rt is on the list but should have been removed → use-after-free on free
```

The check (`list_empty`) and action (`list_del_init`) are not in the same
atomic region.

### Step 4: Lockset Analysis

For each shared variable V, compute the intersection of locks held across
all accesses by any thread. If the intersection is empty, no single lock
protects V across all accesses — potential race.

```
Path A: spin_lock(&obj->lock); obj->counter++; spin_unlock(&obj->lock);
Path B: obj->counter--;  // no lock held

L(A) = {obj->lock}, L(B) = {}
C(obj->counter) = {obj->lock} ∩ {} = {} → RACE
```

The lock must also be the right *type* for the execution contexts — see
`locking.md`, "Contexts and what excludes what", for where this tree departs
from the usual rules (PREEMPT_RT, local locks, force-threaded handlers).

### Step 5: Check Object Lifetime

At every point where a path releases a lock or drops a reference, ask:
"Could another path still hold a raw pointer to this object?"

```
CPU 0 (lookup)                    CPU 1 (remove)
──────────────                    ──────────────
lock → find item → unlock
                                  lock → list_del → unlock → kfree(item)
item->data ← USE-AFTER-FREE
```

Fix: take a reference count under the lock before releasing it. The
reference has to be taken before the lock or RCU read-side section is dropped
and released only after the last use.

**Build the reference budget before reporting use-after-free.** When the other
side of a suspected use-after-free is asynchronous work, an RCU callback or a
workqueue item, list what keeps the object alive on each side. A pin is a
reference, a held lock, or an open RCU read-side section (see Q4 below). Name
every acquire that pins the shared pointer, who owns it, and every release, up
to the claimed free point.

Report only if the free can happen while the using side still holds a live
pointer with no pin. It is not a use-after-free when:

- the stored pointer is itself counted. Its holder took a reference when it
  saved the pointer, so the free is only deferred until that reference is
  dropped — a deferred free.
- the freeing side waits for the user to finish before it frees.

**Returning storage to a pool is a free.** If storage is permanently mapped or
pooled, return-to-pool and reallocation is a logical free even though the
storage remains addressable and reads do not fault; do not dismiss because the
underlying storage remains mapped. Distinguish read from write after logical
free: a read is reportable only when the stale value drives a decision, a
write is always reportable because it corrupts the next owner's reuse of the
same storage.

Record the result as one line:

```
budget: acquires=[...], releases=[...], refs_live_at_free=..., free_reachable_without_pin=[proof | no]; logical_free=[storage-free | pool-return], use=[read-driving-decision | write]
```

## The Four Questions at Every Access Point

At every line that reads or writes a shared variable:

**Q1: What lock is held?** Trace backward through the call chain. Look for
`lockdep_assert_held()`, `__`-prefixed functions (convention: caller holds
lock), direct lock calls up the stack.

**Q2: What other path could access this data right now?** Another CPU
running the same syscall on a different object, an interrupt on this CPU,
a timer/workqueue, a concurrent `close()` or module unload.

**Q3: Is the lock type strong enough?** A `spin_lock()` protecting data
also accessed from an IRQ handler is insufficient — see `locking.md`, "Contexts and what excludes what".

**Q4: Is the object still alive?** Was the pointer obtained under a lock
or RCU read-side section that is still held? Was a reference count taken?
If neither, the object may have been freed.

## Multi-Variable Races

The most subtle races involve multiple variables that must be updated
atomically together. Each individual access may be locked, but the
relationship between variables is unprotected.

```
CPU 0                                CPU 1
──────                               ──────
lock → set state=ACTIVE → unlock
                                     lock → read state=ACTIVE
                                             call handler → OLD handler!
                                     unlock
lock → set handler=new → unlock
```

Both variables must be updated in the same critical section.

When you find an unlocked access to a shared variable, do not dismiss it
because "the window is tiny." If the ordering violation can occur at all,
it is a bug.

## Interrupt Timelines

Interrupts create concurrency on a single CPU. The handler preempts
whatever was running:

```
CPU 0 (process context)
──────────────────────
spin_lock(&data_lock)        ← acquired, IRQs not disabled
shared_counter++
  ← IRQ fires on THIS CPU
  ├─ IRQ handler: spin_lock(&data_lock) → DEADLOCK
  │   (we hold the lock but can't continue)
  └─ Never returns
```

If the same lock is used from both process and hardirq context, ALL
process-context acquisitions must use `spin_lock_irqsave()`. If shared
with softirq only, process context must use `spin_lock_bh()`.

## Worked Example

```c
static LIST_HEAD(conn_list);
static DEFINE_SPINLOCK(list_lock);

// Path A: add_connection (process context)
//   spin_lock(&list_lock); list_add(&c->list, &conn_list); spin_unlock();
// Path B: receive_data (softirq context)
//   list_for_each_entry(c, &conn_list, list) { ... }  ← NO LOCK
// Path C: remove_connection (process context)
//   spin_lock(&list_lock); list_del(&c->list); spin_unlock(); kfree(c);
```

**Lockset analysis** on Path B vs Path C:
- Path B accesses `conn_list`: L(B) = {} (no lock)
- Path C accesses `conn_list`: L(C) = {list_lock}
- C(conn_list) = {} → RACE

**Timeline (B vs C)**:
```
CPU 0 (Path B: softirq)           CPU 1 (Path C: process)
────────────────────               ────────────────────
c = first entry, no match
next_c = c->list.next
                                   lock → list_del(c) → unlock → kfree(c)
c = next_c ← FREED MEMORY
```

**Four bugs found:**
1. Path B has no list lock → race with Path C on list traversal
2. Path C uses `spin_lock()` but Path B runs in softirq → must use
   `spin_lock_bh()` to prevent softirq preemption on same CPU
3. Path B needs `rcu_read_lock()` + `list_for_each_entry_rcu()`, OR
   `spin_lock_bh(&list_lock)`
4. After fixing with RCU, Path C's `kfree(c)` must become
   `kfree_rcu(c, rcu_head)` or follow `synchronize_rcu()`

## Tracing Algorithm and Quick Checks

### The Algorithm

1. Find all shared data — variables accessed from multiple code paths
2. For each, list every path and its execution context
3. For each pair, compute lockset intersection — empty = potential race
4. Build the interleaved timeline — find a specific wrong outcome
5. Check lock context compatibility (`locking.md`, "Contexts and what excludes what")
6. Check object lifetimes — reference or RCU held after lock release?
7. Check memory ordering — publish patterns need acquire/release
8. Check TOCTOU — condition and action in the same atomic region?

### Quick Checks

- **Lock drop and reacquire**: all prior validation is stale. Re-check
  pointers, refcounts, conditions after reacquiring.
- **Functions returning with different locks**: verify the caller knows
  which lock is held on return and releases the correct one.
- **Naming after a function gains a second lock/mode**: when a patch adds a
  second lock type to a function that previously handled only one (e.g. a
  per-VMA-lock path added to an mmap-lock-only function), check whether an
  existing generic name (`locked`, `flags`, `state`) still reads
  unambiguously, and whether comments referencing "the lock" still resolve
  to one specific lock. Rename to disambiguate (`mmap_locked` vs
  `vma_locked`) rather than writing a comment to work around a name that's
  now ambiguous.
- **Reassigning locked objects**: verify old object's lock is released
  before acquiring the new object's lock.
- **Never dismiss a race because the window is small.** If the ordering
  violation can occur at all, it is a bug.
- **A validation check before the exclusion point is NOT protection.**
  If code checks shared state then acquires exclusion, the check is
  TOCTOU — a concurrent path can modify/free the data between the check
  and exclusion. Do not dismiss because "the check would detect it."
- **A single abort path does not make a race safe.** When evaluating
  whether a race is "handled," you will find one recovery point and
  stop looking. This is wrong. You must trace every instruction between
  the race window and the recovery point. If any intermediate
  instruction dereferences, locks, or depends on the contested resource,
  the race causes a crash before the recovery ever executes.
- **Subsystem guides are authoritative about this tree.** When a guide marks
  something `**Unsafe usage**:` and the code does it, with none of the correct
  forms listed under it, do not override that with your own reasoning. Report
  it. Where it marks something `**Potentially unsafe usage**:`, work out from
  the code which of the two cases it describes this is; only the unsafe case
  is a bug.

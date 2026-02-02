# Locking Subsystem Delta

## Locking Subsystem Patterns [LOCK]

#### LOCK-001: Seqlock critical section

**Risk**: Data corruption

**Details**: ALL code between begin/retry is critical

#### LOCK-002: Sparse annotation compliance

**Risk**: Lock imbalance

**Details**: Honor __must_hold/__acquires/__releases

#### LOCK-003: Write seqcount protection

**Risk**: Data corruption

**Details**: Proper write_seqcount_begin/end pairing

## Preemption vs Migration
- **Preemption disabled**: CPU won't change, but IRQs can occur
- **Migration disabled**: Can be preempted but returns to same CPU
- **IRQs disabled**: No interrupts, implies preemption disabled

## Lock Nesting Classes
- Same lock type needs different classes for nesting
- Use mutex_lock_nested() with nesting level
- Lockdep tracks up to 8 nesting levels

## RCU Specifics
- rcu_read_lock() doesn't prevent preemption (PREEMPT_RCU)
- synchronize_rcu() waits for all readers
- call_rcu() callbacks run after grace period
- SRCU allows sleeping in read sections
- Locking on a spinlock_t and raw_spinlock_t prevents preemption and implicitly
  include rcu_read_lock(). When PREEMPT_RT is on, it does not disable preemption
  on spinlock_t.

## RT (Realtime) Differences
- spinlock_t becomes sleeping locks on RT
- raw_spinlock_t never sleeps (even on RT)
- local_irq_disable() disables IRQs (even on RT)

## _irq and _irqsave variants
- spin_lock_irq and spin_lock_irqsave mask off interrupts.
- spin_lock_irqsave(lock, flags) can be nested again inside spin_lock_irqsave(lock2, flags2)
  as long as the two locks are different and the two flags are different variables
- if locks are taken when irqs are already off:
  - all lock holders need to have irqs masked in order to safely take the lock
  - it is safe to use spin_lock() (without masking interrtupts) from code that is only called when irqs are already off
  - it is safe to spin_lock_irq() and then unlock without re-enabling irqs, as
    long as they are enabled again later, either directly in the same function,
    or elsewhere in the callchain
  - spin_trylock() might be used to avoid the deadlocks.  The deadlock can only happen if spin_lock() is called with interrupts off, without using trylock

## memory barriers
- You're not smart enough to understand smp_mb(), smp_rmb(), or smp_wmb() bugs yet, assume the patch author is correct unless
the usage is wildly wrong.
- smp_mb(): General barrier - ensures all loads/stores before appear to happen before all loads/stores after
- smp_rmb(): Read barrier - ensures all loads before appear to happen before all loads after (no effect on stores)
- smp_wmb(): Write barrier - ensures all stores before appear to happen before all stores after (no effect on loads)
- Barriers prevent CPU/compiler reordering across the barrier point but don't guarantee completion, only ordering appearance
- Usage: Must be paired between CPUs - if CPU A uses smp_wmb() before setting a flag, CPU B needs smp_rmb() after reading that flag
  - This is a guideline, it is sometimes ignored
- Common pattern: Producer uses smp_wmb() after writing data, before setting ready flag; Consumer uses smp_rmb() after reading ready flag, before reading data
- Lockless access: Use barriers around shared data access when not holding locks, especially in RCU read sections or lock-free algorithms

## Quick Checks
- raw_spinlock for IRQ handlers on RT
- Completion variables for event waiting
- Proper memory barriers with lockless algorithms
- atomic_read()/atomic_set() are relaxed on many archs and do NOT imply ordering.
  If ordering matters, look for explicit smp_* barriers or acquire/release
  atomic APIs (e.g., atomic_read_acquire/atomic_set_release).
- percpu-rwsem for frequent read, rare write patterns

## Lock release and reaquire
- Whenever locks are dropped and taken again, verify protected objects are not stale

## When functions return with different locks than originally held
- verify original locked object's locking was properly handled
- verify the callers knows which lock to release

## Complex combinations
- When code reassigns over a previously locked data structure, find if we've properly unlocked that datastructure, or if the lock is mistakenly held forever

## Lock Context Compatibility Matrix

| Lock Type | Process | Softirq | Hardirq | Sleeps |
|-----------|---------|---------|---------|--------|
| spin_lock | ✓ | ✓ | ✓ | ✗ |
| spin_lock_bh | ✓ | ✗ | ✗ | ✗ |
| spin_lock_irqsave | ✓ | ✓ | ✓ | ✗ |
| mutex/rwsem | ✓ | ✗ | ✗ | ✓ |

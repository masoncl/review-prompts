# Locking Subsystem Delta

## Locking Subsystem Patterns [LOCK]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| LOCK-001 | Seqlock critical section | Data corruption | ALL code between begin/retry is critical |
| LOCK-002 | Sparse annotation compliance | Lock imbalance | Honor __must_hold/__acquires/__releases |
| LOCK-003 | Write seqcount protection | Data corruption | Proper write_seqcount_begin/end pairing |

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

## RT (Realtime) Differences
- Spinlocks become sleeping locks on RT
- raw_spinlock_t never sleeps (even on RT)
- local_irq_disable() doesn't disable IRQs on RT

## _irq and _irqsave variants
- spin_lock_irq and spin_lock_irqsave mask off interrupts.
- if locks are taken when irqs are already off:
  - all lock holders need to have irqs masked in order to safely take the lock
  - it is safe to use spin_lock() (without masking interrtupts) from code that is only called when irqs are already off
  - it is safe to spin_lock_irq() and then unlock without re-enabling irqs, as
    long as they are enabled again later, either directly in the same function,
    or elsewhere in the callchain
  - spin_trylock() might be used to avoid the deadlocks.  The deadlock can only happen if spin_lock() is called with interrupts off, without using trylock

## Quick Checks
- raw_spinlock for IRQ handlers on RT
- Completion variables for event waiting
- Proper memory barriers with lockless algorithms
- atomic_read/atomic_write and other calls in this api family provide all of the
  memory barriers needed to atomically read and write atomic_t types on every arch.
  Don't try to find memory barrier or ordering bugs with respect to atomics.
- percpu-rwsem for frequent read, rare write patterns

## Complex combinations
- When code reassigns over a previously locked data structure, find if we've properly unlocked that datastructure, or if the lock is mistakenly held forever

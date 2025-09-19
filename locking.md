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

## Quick Checks
- raw_spinlock for IRQ handlers on RT
- Completion variables for event waiting
- Proper memory barriers with lockless algorithms
- percpu-rwsem for frequent read, rare write patterns

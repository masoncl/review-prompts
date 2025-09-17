# Locking Patterns

## Context Compatibility
| Lock Type | Process | Softirq | Hardirq | Sleeps | Use Case |
|-----------|---------|---------|---------|--------|----------|
| spin_lock | ✓ | ✓ | ✓ | ✗ | Short critical sections |
| spin_lock_bh | ✓ | ✗ | ✗ | ✗ | Block softirqs |
| spin_lock_irq | ✓ | ✓ | ✓ | ✗ | Must restore IRQs |
| spin_lock_irqsave | ✓ | ✓ | ✓ | ✗ | Unknown IRQ state |
| mutex | ✓ | ✗ | ✗ | ✓ | Long sections |
| rwsem | ✓ | ✗ | ✗ | ✓ | Read-heavy |
| seqlock | ✓ | ✓ | ✓ | ✗ | Frequent reads |

## Critical Rules
- Never sleep (mutex/rwsem) in atomic context
- Use _irqsave if lock taken from IRQ context
- Trylock→lock conversion risks deadlock
- Check inode_lock() needs I_MUTEX_PARENT annotation

## sparse annotations
If these are present in the source code, make sure they are honored correctly:
__must_hold(x): The specified lock is held on function entry and exit
__acquires(x): The lock is held on function exit, but not entry
__releases(x): The lock is held on function entry, but not exit
__acquire(x): Code acquires the lock x (used within a function)
__release(x): Code releases the lock x (used within a function)
__cond_lock(x, c): Conditionally acquires lock x if condition c is true

## seqlocks
For seqcount readers, the critical section includes ALL code between:
- read_seqcount_begin(&seqlock)
- read_seqcount_retry(&seqlock, sequence)

Standard pattern:
do {
  seq = read_seqcount_begin(&seqlock);
  // ← EVERYTHING HERE IS IN THE CRITICAL SECTION
  data1 = field1;
  data2 = field2;
  // ← EVERYTHING HERE IS IN THE CRITICAL SECTION
} while (read_seqcount_retry(&seqlock, seq));

write_seqcount_begin/end() create critical sections on the
write side.


# RCU Subsystem Delta

## RCU Read-Side Critical Sections
- No blocking/sleeping in rcu_read_lock() sections
- Can nest rcu_read_lock() calls
- Preemption rules depend on kernel config (PREEMPT_RCU)
- srcu can sleep

## RCU Updates
- rcu_assign_pointer() for publishing
- rcu_dereference() for reading
- synchronize_rcu() is expensive (blocks)
- call_rcu() for asynchronous cleanup

## RCU Variants

| Variant | Sleep in read | Use Case |
|---------|---------------|----------|
| RCU | No | General purpose |
| SRCU | Yes | Sleeping readers |
| Tasks RCU | Yes | Tracing/BPF |

## Memory Ordering
- rcu_dereference() includes read barrier
- rcu_assign_pointer() includes write barrier
- Manual barriers needed for complex patterns

## Quick Checks
- Freed memory accessible until grace period ends
- kfree_rcu() for simple object freeing
- INIT_RCU_HEAD not needed in modern kernels
- rcu_read_lock_held() for debug assertions

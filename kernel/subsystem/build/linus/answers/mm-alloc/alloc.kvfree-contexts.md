- `kvfree_atomic()`: defined in `mm/slub.c`. It calls `vfree_atomic()` for a
  vmalloc address and `kfree()` otherwise.
- `kvfree_atomic()` contexts: any context except NMI, including task context
  with a spinlock held; `vfree_atomic()` has `BUG_ON(in_nmi())` and only
  queues the free to a work item.
- `kvfree()` contexts: preemptible task context, or interrupt context other
  than NMI. It is not limited to process context: `vfree()` hands off to
  `vfree_atomic()` when `in_interrupt()` is true.
- `in_interrupt()`: also true in task context with BH disabled, see
  `irq_count()` in `include/linux/preempt.h`.
- Memory from `kvmalloc()` with `GFP_ATOMIC` or `GFP_NOWAIT`: may be vmalloc
  memory in this tree (see "kvmalloc fallback"), so the allocation context
  does not show that `kfree()` semantics apply.
- **Potentially unsafe usage**: `kvfree()` in atomic context.
  - Unsafe: in task context with preemption off, IRQs off or a spinlock
    held, where `in_interrupt()` is false and the pointer may be a vmalloc
    address; `vfree()` reaches `might_sleep()`.
  - Safe: where `in_interrupt()` is true and not NMI; `vfree()` defers to
    `vfree_atomic()`. For example `bucket_table_free_rcu()` in
    `lib/rhashtable.c`, an RCU callback.
  - Safe: `kvfree_atomic()` instead, as `bucket_table_free_atomic()` in
    `lib/rhashtable.c` does.

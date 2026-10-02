- `rcu_barrier_tasks_trace()`: inline `srcu_barrier()` on
  `rcu_tasks_trace_srcu_struct`.
- `rcu_barrier_tasks()`: defined only under `CONFIG_TASKS_RCU`, with no macro
  fallback. Without that option `call_rcu_tasks` is `call_rcu`, and
  `rcu_barrier()` is the matching barrier.
- `kvfree_rcu_barrier()` in `mm/slab_common.c`: waits for all pending
  `kfree_rcu()` objects; it also calls `rcu_barrier()`, in both
  `CONFIG_KVFREE_RCU_BATCHED` settings.
- `kvfree_rcu_barrier_on_cache()` under `CONFIG_KVFREE_RCU_BATCHED`: flushes
  only the given cache's sheaves, then calls `rcu_barrier()` and drains the
  batches of every CPU.
- `kmem_cache_destroy()`: calls `kvfree_rcu_barrier_on_cache()` first, so it
  runs `rcu_barrier()` for every non-NULL cache, not only for
  `SLAB_TYPESAFE_BY_RCU` ones.
- What `rcu_barrier()` alone misses of `kfree_rcu()`, for example: objects
  still in a per-CPU `rcu_free` sheaf, and objects in `struct kfree_rcu_cpu`
  batches not yet handed to `queue_rcu_work()`.
- `kfree_rcu_mightsleep()` slow path: runs `synchronize_rcu()` and `kvfree()`
  inline before it returns; no barrier covers a call that has not returned.

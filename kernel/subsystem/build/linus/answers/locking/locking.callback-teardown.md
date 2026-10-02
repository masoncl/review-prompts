- `rcu_barrier()` in `kernel/rcu/tree.c`: sleeps on
  `rcu_state.barrier_mutex` and a completion. It does not take
  `cpus_read_lock()`.
- `rcu_barrier()` and `kfree_rcu()`: with `CONFIG_KVFREE_RCU_BATCHED`
  (default y, off with `CONFIG_TINY_RCU`, `CONFIG_SLUB_TINY` or
  `CONFIG_RCU_STRICT_GRACE_PERIOD`) the objects are batched in
  `mm/slab_common.c` and not queued with `call_rcu()` one by one;
  `rcu_barrier()` does not wait for them, `kvfree_rcu_barrier()` and
  `kvfree_rcu_barrier_on_cache()` do. Without it `kvfree_call_rcu()` uses
  `call_rcu()` and `kvfree_rcu_barrier()` calls `rcu_barrier()`.
- `kmem_cache_destroy()`: calls `kvfree_rcu_barrier_on_cache()` itself, so
  pending `kfree_rcu()` objects of that cache need no barrier from the
  caller.
- Callbacks queued with `call_rcu()` that call `kmem_cache_free()`:
  `kvfree_rcu_barrier_on_cache()` also calls `rcu_barrier()` in both
  configurations; in-tree callers still run `rcu_barrier()` themselves before
  `kmem_cache_destroy()`, for example `destroy_inodecache()` in
  `fs/ext4/super.c`.
- `kfree_rcu_mightsleep()`: when it cannot batch the pointer it calls
  `synchronize_rcu()` and `kvfree()` before it returns; no barrier covers a
  call that has not returned yet.

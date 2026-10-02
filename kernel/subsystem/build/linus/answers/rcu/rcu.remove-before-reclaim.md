- **Potentially unsafe usage**: freeing an object with no grace period after
  unlinking it.
  - Unsafe: when the object was ever reachable by an RCU reader and its cache
    is not `SLAB_TYPESAFE_BY_RCU`.
  - Safe: when the object was never made reachable by RCU readers.
    `dentry_free()` in `fs/dcache.c` frees at once only for dentries flagged
    `DCACHE_NORCU`, which `d_alloc_pseudo()` and `d_alloc_cursor()` set at
    allocation; every other dentry goes through `call_rcu()`.
  - Safe: when the cache is `SLAB_TYPESAFE_BY_RCU` and every reader
    revalidates. `__cleanup_sighand()` in `kernel/fork.c` calls
    `kmem_cache_free()` at once; `lock_task_sighand()` rechecks
    `tsk->sighand`.
- **Potentially unsafe usage**: plain `list_del()` on an object that RCU
  readers can reach.
  - Unsafe: on the linkage that readers traverse; it poisons `next`.
  - Safe: on a second linkage that only lock holders walk.
    `audit_del_rule()` in `kernel/auditfilter.c` does `list_del_rcu()` on
    `e->list` and `list_del()` on `e->rule.list`, both under
    `audit_filter_mutex`.
- `audit_del_rule()`: after the unlink it calls `synchronize_rcu()`, tears down
  the rule's watch, tree and mark, and only then `call_rcu()`.
- Polled grace period: a third way to wait. The cookie must be taken after the
  unlink. Under `CONFIG_KVFREE_RCU_BATCHED`, `add_ptr_to_bulk_krc_lock()` in
  `mm/slab_common.c` takes it with `get_state_synchronize_rcu_full()` when the
  pointer is queued; `kvfree_rcu_bulk()` refuses to free, under
  `WARN_ON_ONCE()`, unless `poll_state_synchronize_rcu_full()` says the grace
  period has ended.

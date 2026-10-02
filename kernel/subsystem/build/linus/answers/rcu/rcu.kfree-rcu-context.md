- Caller with a head: may hold a `raw_spinlock_t` with irqs off;
  `set_cpus_allowed_force()` in `kernel/sched/core.c` calls `kfree_rcu()` with
  `p->pi_lock` held.
- NMI, or code that may have interrupted the slab allocator or `call_rcu()`:
  not allowed; `krc_this_cpu_lock()` and the barn lock spin unconditionally.
  `kfree_rcu_nolock()` is the form for those.
- Implementation on `CONFIG_PREEMPT_RT`, call with a head: may take
  `raw_spinlock_t` only, because the caller may hold one; the sheaf path is
  skipped and `krcp->lock` is a `raw_spinlock_t`.
- Implementation without `CONFIG_PREEMPT_RT`, under
  `CONFIG_KVFREE_RCU_BATCHED`: before touching `krcp->lock`,
  `kvfree_call_rcu()` calls `kfree_rcu_sheaf()`. That path takes a
  `local_trylock()` and the `spinlock_t` `lock` of `struct node_barn`, may
  allocate with `GFP_NOWAIT`, may `kfree()`, and may `call_rcu()`.
- Sleeping locks such as a mutex: on no path that a call with a head can
  reach.
- Headless call without `CONFIG_PREEMPT_RT`, under
  `CONFIG_KVFREE_RCU_BATCHED`: the sheaf attempt runs first for it too;
  `might_sleep()` is still asserted on entry.
- Page allocation in `add_ptr_to_bulk_krc_lock()`: only for the headless call,
  after `krcp->lock` is dropped, with
  `GFP_KERNEL | __GFP_NORETRY | __GFP_NOMEMALLOC | __GFP_NOWARN`; never
  `GFP_NOWAIT`.
- No free array slot, with a head: the object is chained on `krcp->head`
  through `head->next`; `call_rcu()` is not used.
- Without `CONFIG_KVFREE_RCU_BATCHED`: `kvfree_call_rcu()` is `call_rcu()` with
  `kvfree_rcu_cb()`, or `synchronize_rcu()` then `kvfree()` when headless.
  There is no `krc` and no sheaf path.

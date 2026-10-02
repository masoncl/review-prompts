- `kvfree_call_rcu()` on `CONFIG_PREEMPT_RT`: never enters the sheaf path; the
  test is `!IS_ENABLED(CONFIG_PREEMPT_RT)`, not the caller's context.
- `__kfree_rcu_sheaf()` on `CONFIG_PREEMPT_RT`: still reached under
  `CONFIG_KVFREE_RCU_BATCHED`, from `kfree_call_rcu_nolock()` with
  `SLAB_FREE_NOLOCK`. It does not bail out; `VM_WARN_ON_ONCE()` fires only if
  it is entered there with spinning allowed.
- Lockdep map: `kfree_rcu_sheaf_map` in `mm/slub.c`, declared with
  `DEFINE_WAIT_OVERRIDE_MAP()` and `LD_WAIT_CONFIG`.
- Scope of the override: the whole of `__kfree_rcu_sheaf()`;
  `lock_map_acquire_try()` at entry, `lock_map_release()` on the success and
  the fail exit.
- Override on `CONFIG_PREEMPT_RT`: not taken, so lockdep still reports a
  `spinlock_t` taken there under a raw lock, unless it is a trylock;
  `check_wait_context()` skips trylocks.
- **Potentially unsafe usage**: a `spinlock_t` or `local_lock()` taken on the
  `kvfree_call_rcu()` path outside `__kfree_rcu_sheaf()`.
  - Unsafe: when a call with a head can reach it; the caller may hold a
    `raw_spinlock_t`, and nothing there overrides the wait type or keeps
    `CONFIG_PREEMPT_RT` out.
  - Safe: inside `__kfree_rcu_sheaf()`, as a trylock or only when spinning is
    allowed, as `barn_get_empty_sheaf()` does; `kfree_rcu_sheaf_map` covers it
    and `kvfree_call_rcu()` keeps RT out.
  - Safe: on the headless path only, where `might_sleep()` is asserted, as the
    `GFP_KERNEL` page allocation in `add_ptr_to_bulk_krc_lock()` under
    `can_alloc`, after `krcp->lock` is dropped.
- With `SLAB_FREE_DEFAULT`: only the per-CPU lock is a trylock;
  `barn_get_empty_sheaf()` uses `spin_lock_irqsave()`, and the empty sheaf is
  allocated with `GFP_NOWAIT`.
- With `SLAB_FREE_NOLOCK`: `spin_trylock_irqsave()`, allocation with
  `SLAB_ALLOC_NOLOCK`, `kfree_nolock()`; a full sheaf goes to `irq_work`
  instead of `call_rcu()` when `irqs_disabled()`.
- Eligibility in `kfree_rcu_sheaf()`: not a vmalloc address, `virt_to_slab()`
  non-NULL, and under `CONFIG_NUMA` `slab_nid(slab) == numa_mem_id()`.
- `cache_has_sheaves()`: tested inside `__kfree_rcu_sheaf()`, and only when
  `pcs->rcu_free` is NULL.

- `cleanup_srcu_struct()` inside a reader of the same domain, Tree SRCU: no
  deadlock; it hits `WARN_ON(srcu_readers_active(ssp))` and returns with
  nothing freed.
- A failed `cleanup_srcu_struct()` in `kernel/rcu/srcutree.c`: leaves
  `ssp->sda`, `ssp->srcu_sup` and any queued work in place; that work reaches
  the domain through `sup->srcu_ssp` and `sdp->ssp`, so the enclosing object
  must not be freed after a WARN.
- **Potentially unsafe usage**: `cleanup_srcu_struct()` with no
  `srcu_barrier()` before it.
  - Unsafe: when a `call_srcu()` callback can still be queued;
    `cleanup_srcu_struct()` in `kernel/rcu/srcutree.c` WARNs on
    `rcu_segcblist_n_cbs()` and returns.
  - Safe: when nothing calls `call_srcu()` on the domain and every
    `synchronize_srcu()` has returned, as `kvm_destroy_vm()` does for
    `kvm->irq_srcu`.
  - Safe: with `srcu_barrier()` after the last `call_srcu()`, as
    `kvm_destroy_vm()` does for `kvm->srcu` and `blk_mq_free_tag_set()` does
    for `set->tags_srcu`.
- `start_poll_synchronize_srcu()`, Tree SRCU: the grace period it requested
  must have ended before `cleanup_srcu_struct()`, which WARNs and returns
  while `srcu_gp_seq` is behind `srcu_gp_seq_needed`; `srcu_barrier()` does
  not wait for it.
- `cleanup_srcu_struct()` from a callback of the same domain: it sleeps, and it
  calls `flush_work()` on the work item that is running the callback.
- Lockdep coverage: only `__synchronize_srcu()`, and `synchronize_srcu()` in
  `kernel/rcu/srcutiny.c`, call `srcu_lock_sync()`; `srcu_barrier()` in
  `kernel/rcu/srcutree.c` and `cleanup_srcu_struct()` have no SRCU annotation.
- `srcu_barrier()` inside a reader of the same domain, Tree SRCU: can deadlock
  when a queued callback still waits for a grace period, and lockdep does not
  report it.
- Configuration: `srcu_lock_sync()` is empty without `CONFIG_DEBUG_LOCK_ALLOC`;
  the `RCU_LOCKDEP_WARN()` for "synchronize_srcu() in same-type SRCU (or in
  RCU) read-side critical section" is empty without `CONFIG_PROVE_RCU`.

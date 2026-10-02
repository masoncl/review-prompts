- Users: search for `DEFINE_WAIT_OVERRIDE_MAP`; there is no put_task_map in
  this tree and no override map under `kernel/rcu/`.
- Wait type: the macro accepts any value; in-tree maps use `LD_WAIT_FREE`,
  `LD_WAIT_CONFIG` and `LD_WAIT_SLEEP`, none uses `LD_WAIT_SPIN`.
- Two opposite uses: raising the limit (`fill_pool_map`, `printk_legacy_map`,
  `vmbus_map`, `kfree_rcu_sheaf_map` at `LD_WAIT_CONFIG`; `tick_freeze_map` at
  `LD_WAIT_SLEEP`) and lowering it so that locks of a higher wait type taken
  inside get reported (`sched_map` in `sched_submit_work()` at
  `LD_WAIT_CONFIG`, in task context; `rv_react_map` in `rv_react()` at
  `LD_WAIT_FREE`).
- `rv_react_map` at `LD_WAIT_FREE`: every checked non-trylock lock taken in a
  reactor is reported, `raw_spinlock_t` included; maps whose outer type is
  `LD_WAIT_FREE` pass, such as the RCU read-side maps.
- Scope of the relaxation: `check_wait_context()` is the only reader of
  `LD_LOCK_WAIT_OVERRIDE`; runtime checks such as `__might_resched()` in
  `rt_spin_lock()` (`kernel/locking/spinlock_rt.c`) are not relaxed.
- Storage: the map must be static; the macro sets no key, so
  `assign_lock_key()` uses the map address and, for a non-static object, prints
  "trying to register non-static key" and turns lockdep off.
- **Potentially unsafe usage**: raising the wait type around a `spinlock_t` or
  sleeping-lock acquisition made under a `raw_spinlock_t` or in hardirq
  context.
  - Unsafe: when the map is taken on PREEMPT_RT in that context and the lock
    can be held by someone else; lockdep stays silent and the RT lock blocks in
    atomic context.
  - Safe: the map is not taken on RT, so lockdep there still checks the
    wrapped code, as in `printk_legacy_allow_spinlock_enter()` (empty under
    `CONFIG_PREEMPT_RT`), `vmbus_isr()` (RT branch wakes a thread instead) and
    `__kfree_rcu_sheaf()` (map taken only if `!IS_ENABLED(CONFIG_PREEMPT_RT)`).
  - Safe: on RT the wrapped call is reached only when `can_fill_pool()` in
    `lib/debugobjects.c` allows it: `preemptible()`, or before
    `SYSTEM_SCHEDULING` outside hardirq; `debug_objects_fill_pool()` does this.
  - Safe: the acquisition cannot block because nothing else runs;
    `tick_freeze()` and `tick_unfreeze()` take the map only when
    `tick_freeze_depth == num_online_cpus()`, on RT too.
- **Unsafe usage**: acquiring an override map with `lock_map_acquire()`; the
  map is then itself checked against the current context and reported as
  invalid wait context when it raises the type.
  - Safe: `lock_map_acquire_try()`, which `check_wait_context()` skips, as
    every in-tree user does.

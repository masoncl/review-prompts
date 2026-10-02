- Bit spinlocks on PREEMPT_RT: stay spinning; `locktypes.rst` ("bit spinlocks")
  applies the `raw_spinlock_t` caveats to them, and says some users switch to
  `spinlock_t` under `#ifdef` at the usage site.
- RT `rwlock_t`: built on `struct rwbase_rt` (`include/linux/rwlock_types.h`);
  there is no struct rt_rwlock in this tree.
- `local_trylock_t`: not listed in `locktypes.rst`; changes category exactly
  like `local_lock_t` (both are `typedef spinlock_t` under `CONFIG_PREEMPT_RT`
  in `include/linux/local_lock_internal.h`).

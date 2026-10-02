- Forced charges in `try_charge_memcg()`, complete list: `PF_MEMALLOC` tasks,
  `__GFP_NOFAIL`, `__GFP_HIGH`.
- `nomem` label: every failure path reaches it, including the ones taken
  before any reclaim, and it returns `-ENOMEM` only when neither
  `__GFP_NOFAIL` nor `__GFP_HIGH` is set.
- `GFP_ATOMIC`: contains `__GFP_HIGH`, so a non-blocking `GFP_ATOMIC` charge
  is forced over the limit and does not fail.
- Dying tasks: not forced. `try_charge_memcg()` does not test `TIF_MEMDIE` or
  a pending fatal signal to let a charge through.
- OOM victim whose `oom_mm` has `MMF_OOM_SKIP`: goes to `nomem` before
  reclaim.
- `consume_stock()` hit: `try_charge_memcg()` returns 0 without touching a
  page counter.
- OOM kill: synchronous, inside the charge. `mem_cgroup_oom()` calls
  `mem_cgroup_out_of_memory()`, which takes `oom_lock`.
- There is no memcg_may_oom field here.
- `mem_cgroup_oom()` is reached only when all of these hold:
  - the charge of `nr_pages` (not the batch) failed
  - the task is not `PF_MEMALLOC` and not `task_in_memcg_oom()`
  - `gfpflags_allow_blocking()` is true
  - the task is not an OOM victim with `MMF_OOM_SKIP`
  - reclaim, then one `drain_all_stock()`, left no margin
  - `__GFP_NORETRY` is clear
  - the last reclaim freed nothing, or `nr_pages` is above
    `1 << PAGE_ALLOC_COSTLY_ORDER`
  - `MAX_RECLAIM_RETRIES` is used up
  - `__GFP_RETRY_MAYFAIL` is clear
  - not (`passed_oom` and `task_is_dying()`)
- `mem_cgroup_oom()` returning false: the charge goes to `nomem`.
- v1 `oom_kill_disable`: `memcg1_oom_prepare()` returns false, no kill. It
  sets `current->memcg_in_oom` only when `current->in_user_fault`.

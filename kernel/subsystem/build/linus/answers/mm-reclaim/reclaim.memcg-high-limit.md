- High check: runs only at `done_restock`. A charge served by
  `consume_stock()` and a forced charge both return before it.
- Inline reclaim: `try_charge_memcg()` calls
  `__mem_cgroup_handle_over_high(gfp_mask)` with the charge's own gfp mask.
- Conditions for the inline call: `current->memcg_nr_pages_over_high` above
  `MEMCG_CHARGE_BATCH`, no `PF_MEMALLOC`, `gfpflags_allow_blocking()`.
- `mem_cgroup_handle_over_high()`: inline wrapper in
  `include/linux/memcontrol.h` that tests the counter;
  `resume_user_mode_work()` calls it with `GFP_KERNEL`.
- Context test: `!in_task()`, not `in_interrupt()`.
- Non-task context: only `memory.high` queues `high_work`; `swap.high` is
  ignored there.
- Memcg used by the handler: `get_mem_cgroup_from_mm(current->mm)`. The memcg
  that was charged is not recorded.
- `__mem_cgroup_handle_over_high()`: skips reclaim and sleep when
  `task_is_dying()`; it has no `__GFP_NOFAIL` test.
- Sleep: skipped when the penalty is at most `HZ / 100`.
- Sleep: happens only once `reclaim_high()` reclaimed nothing and
  `MAX_RECLAIM_RETRIES` is used up.

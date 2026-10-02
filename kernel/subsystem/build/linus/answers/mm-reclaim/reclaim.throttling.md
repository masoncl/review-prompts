- Exempt tasks: `reclaim_throttle()` only calls `cond_resched()` for a task
  with `PF_KTHREAD` or `PF_USER_WORKER` that is not kswapd, whatever the reason.
- kswapd: is throttled, for `VMSCAN_THROTTLE_WRITEBACK`, from `shrink_node()`.
- Fatal signal: `reclaim_throttle()` makes no signal test and sleeps in
  `TASK_UNINTERRUPTIBLE`; only the two `VMSCAN_THROTTLE_ISOLATED` callers test
  `fatal_signal_pending()` after it returns.
- `PF_LOCAL_THROTTLE`: `current_may_throttle()` is tested at the
  `VMSCAN_THROTTLE_CONGESTED` site in `shrink_node()` only.

| Reason | Timeout | Early wake |
|---|---|---|
| `VMSCAN_THROTTLE_WRITEBACK` | `HZ/10` | `__acct_reclaim_writeback()` |
| `VMSCAN_THROTTLE_ISOLATED` | `HZ/50` | `wake_throttle_isolated()` |
| `VMSCAN_THROTTLE_NOPROGRESS` | 1 jiffy | `consider_reclaim_throttle()` |
| `VMSCAN_THROTTLE_CONGESTED` | 1 jiffy | none; no code wakes that queue |

- `VMSCAN_THROTTLE_WRITEBACK` has three call sites:
  - `shrink_node()`: kswapd only, when `sc->nr.immediate` is non-zero.
  - `handle_reclaim_writeback()`: when every folio taken was unqueued dirty
    and `writeback_throttling_sane()` is false, which needs
    `cgroup_reclaim(sc)`.
  - `do_writepages()` in `mm/page-writeback.c`: on `-ENOMEM` with
    `WB_SYNC_ALL`, outside reclaim.
- MGLRU root reclaim, when not `lru_gen_switching()`: `shrink_node()` returns
  after `lru_gen_shrink_node()`, before its WRITEBACK and CONGESTED call
  sites.

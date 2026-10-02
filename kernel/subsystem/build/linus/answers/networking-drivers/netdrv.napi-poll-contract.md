- Return above budget: `__napi_poll()` prints `netdev_err_once()`, there is no
  WARN; the value is then handled like `work == weight`.
- Exactly budget with nothing left: two forms are valid, see the warning in
  `Documentation/networking/napi.rst`.
  - Return `budget` and do not call `napi_complete_done()`.
  - Call `napi_complete_done()` and return `budget - 1`, as `ixgbe_poll()` does
    with `min(work_done, budget - 1)`.
- Returning `budget` after `napi_complete_done()`: `__napi_poll()` sets
  `*repoll` and `napi_poll()` queues an instance the core no longer owns.
- Diagnostics for that case: `pr_warn_once()` only if `n->poll_list` is already
  non-empty; `pr_crit()` in `napi_poll()` only under `CONFIG_DEBUG_NET`.
- Returning `budget` does not guarantee another poll: `__napi_poll()` calls
  `napi_complete()` itself when `napi_disable_pending()`, and
  `napi_complete_done()` when `napi_prefer_busy_poll()`.
- `napi_complete_done()`: never sees the budget; `work_done` is only tested
  for non-zero.
- `napi_complete_done()`: does not test `NAPI_STATE_DISABLE` or
  `NAPI_STATE_PREFER_BUSY_POLL`; it clears the latter.
- `napi_complete_done()` returns false in exactly three cases:

| Case | `NAPI_STATE_SCHED` afterwards |
|---|---|
| `NAPIF_STATE_NPSVC` or `NAPIF_STATE_IN_BUSY_POLL` set | unchanged, nothing done |
| `n->defer_hard_irqs_count > 0` and the gro flush timeout is non-zero | cleared, `n->timer` armed |
| `NAPIF_STATE_MISSED` was set | left set, `__napi_schedule()` called |

- A false return means "do not unmask", not "still owned": in the deferral
  case the instance has been released.

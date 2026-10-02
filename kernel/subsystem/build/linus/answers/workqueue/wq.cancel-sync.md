- There is no WORK_OFFQ_CANCELING here; `__cancel_work_sync()` blocks
  requeueing by raising the disable count (`WORK_CANCEL_DISABLE`), the same
  count `disable_work()` uses.
- `enable_work()` at the end of `__cancel_work_sync()`: skipped when the
  caller passed `WORK_CANCEL_DISABLE` itself, as `disable_work_sync()` and
  `disable_delayed_work_sync()` do; the item then stays disabled.
- Condition of the guarantee: nothing queues the item after the
  `enable_work()` call at the end of `__cancel_work_sync()`, which runs
  before the function returns.
- Item already disabled by another caller: still disabled after
  `cancel_work_sync()` returns, since it undoes only its own increment.

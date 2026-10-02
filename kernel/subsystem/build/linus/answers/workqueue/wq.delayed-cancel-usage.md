- **Potentially unsafe usage**: passing `&dwork->work` to `flush_work()`,
  `cancel_work_sync()`, `disable_work_sync()`, `cancel_work()` or
  `disable_work()`.
  - Unsafe: with `flush_work()` while `dwork->timer` may be armed;
    `start_flush_work()` returns false at once unless an earlier instance is
    running, and the function runs later when the timer fires.
  - Unsafe: with the cancel and disable forms while `dwork->timer` may be
    armed; `work_grab_pending()` busy-waits on `-EAGAIN` until the timer
    expires, then steals the item.
  - Safe: when the timer cannot be armed, as in
    `ip_vs_control_net_cleanup_sysctl()`, which calls `cancel_work_sync()`
    right after `cancel_delayed_work_sync()` on the same item.
  - Safe: the delayed cancel and disable variants, which pass
    `WORK_CANCEL_DELAYED` so that `try_to_grab_pending()` deletes the timer,
    as `blk_mq_cancel_work_sync()` does with `cancel_delayed_work_sync()`.
- `flush_delayed_work()` with a pending timer: queues with
  `__queue_work(dwork->cpu, dwork->wq, &dwork->work)`; it does not call
  `__queue_delayed_work()` or `queue_work_on()`.

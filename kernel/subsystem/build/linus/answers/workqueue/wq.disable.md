- `enable_work()`: does not queue the item, and requests refused while it
  was disabled are lost; `enable_and_queue_work()` in
  `include/linux/workqueue.h` enables and queues when the count reaches 0.
- Maximum depth: 65535, enforced in `work_offqd_disable()`; the kerneldoc of
  `disable_work()` says 65536.
- **Unsafe usage**: `enable_work()` without a matching `disable_work()`.
  - Unsafe: the count is already 0; `enable_work()` takes a pending item off
    its worklist through `work_grab_pending()`, so the function never runs;
    `work_offqd_enable()` warns with `WARN_ONCE()`, and the call returns true.
  - Safe: one `enable_work()` for each earlier `disable_work()` or
    `disable_work_sync()`, as `__cancel_work_sync()` does for its own
    increment.

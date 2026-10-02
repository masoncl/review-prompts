- `queue_limits_commit_update()`: never freezes and does not check for a
  freeze; it only asserts `limits_lock`.
- "No outstanding I/O by other means", in-tree examples: `loop_configure()`
  (device not bound yet), `__loop_clr_fd()` (final release), `nbd_set_size()`
  (zero capacity, no write cache).
- `queue_limits_commit_update_frozen()`: no requirement on outstanding I/O; it
  calls `blk_mq_freeze_queue()` itself around the commit.
- `queue_limits_commit_update_frozen()`: works on bio-based queues too;
  `queue_attr_store()` uses it for every queue.
- Freezes nest by `mq_freeze_depth`, so a second freeze by itself does not
  hang.
- I/O between start and commit: allowed; `sd_revalidate_disk()` issues
  commands to the same queue while it holds `limits_lock`.
- **Unsafe usage**: `queue_limits_start_update()`, `queue_limits_set()` or
  `mutex_lock(&q->limits_lock)` on a queue the caller has frozen.
  - Unsafe: a holder of `limits_lock` such as `sd_revalidate_disk()` blocks in
    `blk_queue_enter()` until the unfreeze, and the freezer blocks on
    `limits_lock`.
  - Safe: start, then `queue_limits_commit_update_frozen()`, as
    `queue_attr_store()` does.
  - Safe: start, `blk_mq_freeze_queue()`, `queue_limits_commit_update()`,
    `blk_mq_unfreeze_queue()`, as `nvme_update_ns_info_generic()` does.
  - Safe: giving up under that freeze with `queue_limits_cancel_update()`
    before the unfreeze, as `disk_update_zone_resources()` does.

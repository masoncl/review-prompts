- Held reference: `blk_mq_freeze_queue_wait()` cannot return. It does not
  mean no freeze has started; `__blk_freeze_queue_start()` kills the counter
  and raises `q->mq_freeze_depth` while references are held.
- `percpu_ref_tryget()` on `q->q_usage_counter`: succeeds on a queue whose
  freeze has started, until the count reaches zero. `blk_mq_timeout_work()`,
  `blk_mq_queue_tag_busy_iter()` and `bio_poll()` enter this way, for example.
- `blk_try_enter_queue()` in `block/blk.h`: the fast path of both
  `blk_queue_enter()` and `bio_queue_enter()`; it is
  `percpu_ref_tryget_live_rcu()` plus a `blk_queue_pm_only()` test.
- `QUEUE_FLAG_DYING` and `GD_DEAD`: tested only after
  `blk_try_enter_queue()` has failed. With a live counter and `q->pm_only`
  zero, both paths succeed without reading either flag.
- Dying queue with `BLK_MQ_REQ_NOWAIT`: `blk_queue_enter()` returns `-EAGAIN`,
  not `-ENODEV`; the NOWAIT test comes before `blk_queue_dying()`.
- Dead disk with `REQ_NOWAIT`: `__bio_queue_enter()` tests `GD_DEAD` first,
  so the bio gets `bio_io_error()` and `-ENODEV`; `bio_wouldblock_error()` is
  only for a disk that is not dead.
- `q->pm_only`: a counter, not `q->rpm_status`; `blk_pre_runtime_suspend()`
  and `scsi_device_quiesce()` raise it.
- `BLK_MQ_REQ_PM` on a pm_only queue: enters unless
  `q->rpm_status == RPM_SUSPENDED`; then it waits like any other caller.
- NOWAIT caller on a pm_only queue: fails with `-EAGAIN` before
  `blk_pm_resume_queue()` runs, so no `pm_request_resume()` is issued.
- After `del_gendisk()` on a disk without `GD_OWNS_QUEUE`: the queue is
  unfrozen, so `bio_queue_enter()` succeeds again despite `GD_DEAD`.
  `__blk_mark_disk_dead()` set the capacity of the whole disk to 0, and
  `bio_check_eod()` in `submit_bio_noacct()` rejects bios to the whole-disk
  bdev that carry sectors and lack `BIO_REMAPPED`; `drop_partition()` does
  not zero a partition's size.
- Lockdep: `blk_queue_enter()` uses `q->q_lockdep_map`; `bio_queue_enter()`
  and `__bio_queue_enter()` use `q->io_lockdep_map`.

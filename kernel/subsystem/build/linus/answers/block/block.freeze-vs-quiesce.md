- After `blk_mq_freeze_queue_wait()` returns: no request exists, so no
  `queue_rq` call can start; each request holds a counter reference until it
  is freed, in `__blk_mq_free_request()` or `blk_mq_flush_tag_batch()`.
- Still running on a frozen queue: dispatch code that has no request,
  from `hctx->run_work` and `q->requeue_work`. It reads the elevator and
  hctx state without a counter reference.
- `elevator_change()` in `block/elevator.c`: uses three steps, freeze, then
  `blk_mq_cancel_work_sync()`, then `blk_mq_quiesce_queue()` inside
  `elevator_switch()`.
- Bio-based queue (`BD_HAS_SUBMIT_BIO`): `__submit_bio()` holds the reference
  only across `->submit_bio()`. Freeze does not wait for bios the driver
  still holds.
- Quiesce and timeouts: `blk_mq_timeout_work()` is not stopped by quiesce. It
  runs under a counter reference and calls `blk_mq_wait_quiesce_done()` itself.
- `__del_gendisk()`: no quiesce call in its body; the only quiesce on its
  path is the one `elevator_switch()` takes and drops in
  `blk_unregister_queue()`. `rq_qos_exit()` runs on a frozen queue that the
  removal path has not quiesced.
- `blk_mq_quiesce_tagset()`: skips queues with
  `BLK_FEAT_SKIP_TAGSET_QUIESCE` in `q->limits.features`. There is no
  QUEUE_FLAG_SKIP_TAGSET_QUIESCE here.

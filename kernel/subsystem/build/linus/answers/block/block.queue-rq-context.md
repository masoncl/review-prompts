- Read-side section: `__blk_mq_run_dispatch_ops()` in `block/blk-mq.h`; the
  SRCU is `srcu` of `struct blk_mq_tag_set`. There is no hctx_lock() and no
  per-hctx SRCU in this tree.
- `__blk_mq_run_dispatch_ops()` with `BLK_MQ_F_BLOCKING`: calls
  `might_sleep_if(check_sleep)`; `blk_mq_run_dispatch_ops()` passes true, so
  direct issue on a blocking queue asserts a sleepable caller.
- Direct issue: adds nothing beyond the RCU or SRCU section; it does not
  disable preemption or interrupts.
- `blk_mq_run_hw_queue()` with `async` false: dispatches inline only when the
  current CPU is in `hctx->cpumask`; otherwise it goes to kblockd through
  `blk_mq_delay_run_hw_queue()`.
- kblockd run: `blk_mq_hctx_next_cpu()` returns `WORK_CPU_UNBOUND` when
  `nr_hw_queues` is 1, the mask is empty, or no mapped CPU is online; then
  `queue_rq` can run on a CPU outside `hctx->cpumask`.
- Plug flush from `schedule()`: `blk_mq_flush_plug_list()` with
  `from_schedule` true skips direct issue and makes every run async;
  `queue_rq` is not called inline there, with or without `BLK_MQ_F_BLOCKING`.
- Atomic callers on a blocking queue: `blk_mq_run_hw_queue()` does not switch
  to async for them; it only has `might_sleep_if()`. The caller must
  pass `async` true, as `blk_mq_start_hw_queue()` and
  `blk_execute_rq_nowait()` do by passing `hctx->flags & BLK_MQ_F_BLOCKING`.
- Interrupt context: the only `in_interrupt()` test is
  `WARN_ON_ONCE(!async && in_interrupt())` in `blk_mq_run_hw_queue()`; the
  direct-issue paths have none of their own.
- NVMe TCP: the flag comes from `NVME_F_BLOCKING` in the controller ops,
  applied in `nvme_alloc_io_tag_set()` and `nvme_alloc_admin_tag_set()`, not
  in `nvme_tcp_queue_rq()`.
- `commit_rqs` and `queue_rqs`: called inside the same section as `queue_rq`,
  so the same sleeping rule applies.

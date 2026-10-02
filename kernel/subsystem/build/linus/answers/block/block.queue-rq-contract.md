- `BLK_STS_OK`: means the driver has taken or already disposed of the request;
  the core checks nothing. In-tree `queue_rq` returns it after ending the
  request (`z2_queue_rq()`), completing it unstarted
  (`nvme_fail_nonready_command()` through `nvme_host_path_error()`), or
  requeueing it with `blk_mq_requeue_request()` (`null_queue_rq()`).
- `blk_mq_start_request()`: the only place that stores a request in
  `tags->rqs[]` and the only writer of `MQ_RQ_IN_FLIGHT`; a request held
  without it has no timeout and is skipped by `blk_mq_tagset_busy_iter()`.
- Non-OK return after `blk_mq_start_request()`: allowed.
  `__blk_mq_requeue_request()` resets a started request to `MQ_RQ_IDLE` on a
  busy status, as `scsi_queue_rq()` relies on; `loop_queue_rq()` starts and
  then returns `BLK_STS_IOERR`.
- BLK_STS_ZONE_RESOURCE: not defined in this tree; there is no zone-busy list
  in `blk_mq_dispatch_rq_list()`.
- Rerun after a busy status in `blk_mq_dispatch_rq_list()` depends only on
  `BLK_MQ_S_SCHED_RESTART`, not on what is in flight:

| `BLK_MQ_S_SCHED_RESTART` | `BLK_STS_RESOURCE` | `BLK_STS_DEV_RESOURCE` |
|---|---|---|
| clear | `blk_mq_run_hw_queue(hctx, true)` at once | same |
| set | `blk_mq_delay_run_hw_queue()` after `BLK_MQ_RESOURCE_DELAY` | no run by the core |

- `BLK_MQ_S_SCHED_RESTART` is set by `__blk_mq_sched_dispatch_requests()` when
  it starts from a non-empty `hctx->dispatch`; `blk_mq_dispatch_rq_list()`
  does not set it for a driver status.
- `BLK_STS_DEV_RESOURCE` with the flag set: the core schedules no run; the
  flag is acted on by `blk_mq_sched_restart()`, called from
  `__blk_mq_free_request()` and `mq_flush_data_end_io()`.
- `blk_mq_mark_tag_wait()`: runs only when `blk_mq_get_driver_tag()` fails,
  not for a status from `queue_rq`.
- Driver tag on requeue: `blk_mq_put_driver_tag()` releases it only when the
  request also has a scheduler tag; with no elevator the request keeps
  `rq->tag`.
- Direct issue (`blk_mq_try_issue_directly()`, `blk_mq_issue_direct()`): both
  busy statuses get `blk_mq_request_bypass_insert()` and
  `blk_mq_run_hw_queue(hctx, false)`; no `BLK_MQ_S_SCHED_RESTART` test, no
  `BLK_MQ_RESOURCE_DELAY`.
- Budget (`get_budget`): once `queue_rq` is called, releasing that request's
  budget is the driver's job. On a non-OK return the driver must release it
  and make `get_rq_budget_token` return a negative value, because
  `blk_mq_release_budgets()` also walks the refused request and puts any
  token that is not negative; `scsi_queue_rq()` sets
  `cmd->budget_token = -1`.
- `bd->last` in `blk_mq_issue_direct()`: computed over the whole list passed
  in, which can span hardware queues; on each switch the previous queue gets
  `commit_rqs` even though every return was `BLK_STS_OK`.
- `commit_rqs` with nothing pending: `queued` counts every `BLK_STS_OK`,
  including requests the driver ended or requeued itself and requests
  `blk_mq_request_issue_directly()` inserted without calling `queue_rq`.

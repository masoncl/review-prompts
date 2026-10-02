- `rq->state`: every state change is a plain `WRITE_ONCE()`; there is no
  `cmpxchg()` on it and no blk_mq_change_rq_state() or blk_mq_set_rq_state()
  in this tree.
- `blk_mq_complete_request()`: returns void and sets `MQ_RQ_COMPLETE`
  unconditionally; it cannot fail or detect an earlier completion.
- `blk_mq_end_request()` and `__blk_mq_end_request()`: never read `rq->state`,
  so a second call is not rejected.
- `MQ_RQ_COMPLETE` writers: `blk_mq_complete_request_remote()`,
  `blk_mq_set_request_complete()`, `blk_mq_complete_request_direct()`.
- A request ended with `blk_mq_end_request()` without a complete call goes
  from `MQ_RQ_IN_FLIGHT` straight to `MQ_RQ_IDLE`;
  `blk_mq_request_completed()` is never true for it.
- `rq->ref`: an `atomic_t`, not a `refcount_t`; helpers are in `block/blk.h`
  and so are not usable from drivers.
- `blk_mq_find_and_get_req()`: takes no lock and does not use `tags->lock`;
  the busy iterators hold `srcu_read_lock()` on `tags_srcu` of
  `struct blk_mq_tag_set`.
- `blk_mq_free_request()`: writes `MQ_RQ_IDLE` before it drops its reference,
  so a timeout handler can see `MQ_RQ_IDLE` or `MQ_RQ_COMPLETE` on a request
  whose tag is released only when `bt_iter()` puts the last reference.
- `blk_mq_put_rq_ref()` on a flush request: calls `rq->end_io`
  (`flush_end_io()` in `block/blk-flush.c`) instead of
  `__blk_mq_free_request()`.
- Handler's reference: `bt_iter()` drops it as soon as the callback returns;
  work the handler defers has no reference of its own.
- `RQF_TIMED_OUT`: set by `blk_mq_rq_timed_out()` before the handler runs;
  while set, `blk_mq_req_expired()` returns false. After `BLK_EH_DONE` the
  core never times that request out again unless `blk_add_timer()` or
  `__blk_mq_requeue_request()` clears the flag.
- `timeout` context: the only caller is `blk_mq_rq_timed_out()`, from
  `q->timeout_work` on kblockd, inside the `tags_srcu` read section; the
  handler may sleep.
- **Potentially unsafe usage**: completing or ending the request from the
  `timeout` handler.
  - Unsafe: while the driver's normal completion path can still reach the same
    request; both sides run `blk_mq_free_request()`, which drops `rq->ref`
    twice.
  - Safe: reap pending completions with the interrupt disabled, then return
    `BLK_EH_DONE` without completing if the state is no longer
    `MQ_RQ_IN_FLIGHT`, as `nvme_timeout()` does with `nvme_poll_irqdisable()`
    on a queue that is not polled.
  - Safe: mark completion and test `blk_mq_request_completed()` under the same
    driver lock, as `null_timeout_rq()` and `null_poll()` do with
    `nq->poll_lock` on a `HCTX_TYPE_POLL` queue.

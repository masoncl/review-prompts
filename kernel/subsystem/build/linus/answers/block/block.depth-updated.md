- At initialisation the core does not call `depth_updated`. Each scheduler's
  `init_sched` calls its own function by name: `dd_init_sched()`,
  `kyber_init_sched()`, `bfq_init_queue()`.
- The comment above `dd_depth_updated()` names `blk_mq_init_sched()` as a
  caller; `blk_mq_init_sched()` has no such call.
- Later callers through the op: `blk_mq_update_nr_requests()` in
  `block/blk-mq.c` and `queue_async_depth_store()` in `block/blk-sysfs.c`.
  Both skip a `NULL` op.
- `q->async_depth`: a member of `struct request_queue`. All three callbacks
  read it; none reads `q->nr_requests`.
- What is written when the callback runs:

  | Caller | `q->nr_requests` | `q->async_depth` | Queue state |
  |---|---|---|---|
  | the scheduler's `init_sched` | set by `blk_mq_init_sched()` from the `struct elevator_tags` | not written by the core; set only if `init_sched` wrote it before the call | frozen, quiesced, `q->elevator_lock` |
  | `blk_mq_update_nr_requests()` | new value | rescaled by new over old `nr_requests`, at least 1, before `q->nr_requests` is written | frozen, quiesced, `q->elevator_lock`, `update_nr_hwq_lock` for write |
  | `queue_async_depth_store()` | unchanged | `min()` of `q->nr_requests` and the stored value | frozen, `q->elevator_lock`; not quiesced, `update_nr_hwq_lock` not taken |

- `queue_async_depth_store()`: returns `-EINVAL` when `q->elevator` is `NULL`.
- `q->elevator`: `blk_mq_init_sched()` never assigns it on success;
  `init_sched` must set `q->elevator = eq`, and `elevator_switch()` reads it
  back into `ctx->new`.
- `eq->elevator_data`: already set by `elevator_alloc()` from `res->data` for a
  type with `alloc_sched_data`; `kyber_init_sched()` does not write it. Other
  types set it in `init_sched`.
- **Unsafe usage**: an `init_sched` that calls its depth function before it
  writes `q->async_depth`.
  - Unsafe: the function computes its limits from the value left from before
    the switch; the core does not write `q->async_depth` before `init_sched`.
  - Safe: write `q->async_depth`, then call, as `dd_init_sched()` and
    `kyber_init_sched()` do; `dd_depth_updated()` passes `q->async_depth` to
    `blk_mq_set_min_shallow_depth()`.

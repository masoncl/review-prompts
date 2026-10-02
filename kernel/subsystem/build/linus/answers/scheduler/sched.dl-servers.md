- `rq->ext_server`: exists under `CONFIG_SCHED_CLASS_EXT`, beside
  `rq->fair_server`; set up by `ext_server_init()`, pick callback
  `ext_server_pick_task()`, both in `kernel/sched/ext/ext.c`.
- `sched_init_dl_servers()`: gives both servers the same parameters, then calls
  `dl_server_detach_bw()` on `ext_server`, so it cannot start until a BPF
  scheduler is enabled.
- sched_ext enable: `dl_server_attach_bw()` on `ext_server` for every CPU; when
  all tasks are switched (`scx_switched_all()`), `dl_server_detach_bw()` on
  `fair_server`. Disable reverses this: `dl_server_swap_bw()` if all tasks
  were switched, otherwise `dl_server_detach_bw()` on `ext_server`.
- Start, complete list of callers of `dl_server_start()`:
  - `enqueue_task_fair()`, when `rq->cfs.h_nr_queued` leaves zero; no other
    call in `kernel/sched/fair.c`
  - the sched_ext enqueue path, when `rq->scx.nr_running` becomes 1
  - `dl_server_attach_bw()` and `dl_server_swap_bw()`, when the CPU is online
  - `sched_server_write_common()`, after applying new parameters
- Stop, complete list of callers of `dl_server_stop()`:
  - `__pick_task_dl()`, at once when `server_pick_task` returns NULL, then it
    picks again; it does not set `dl_yielded`
  - `dl_server_timer()`, when `dl_defer_idle` is set
  - `__dl_server_detach_bw_locked()`, when the server is active
  - `sched_cpu_dying()`, for both servers
  - `sched_server_write_common()`, before applying new parameters
- Last served task dequeued: nothing stops the server. If it is waiting
  throttled it stays `dl_server_active` at least until its timer fires; the
  comment on `dl_server_active` in `include/linux/sched.h` says otherwise.
- `dl_defer_idle`: set by `update_curr_dl_se()` when a charge made while
  `idle_rq()` is true uses up the budget of a waiting server; a charge while
  `idle_rq()` is false, `dl_server_start()` or `dl_server_stop()` clears it.
- There is no dl_server_pick_task() function; the callback is the field
  `server_pick_task`, called from `__pick_task_dl()`.
- `dl_defer`: set to 1 for both servers in `sched_init_dl_servers()`; nothing
  else in the tree sets it, so no in-tree server runs the non-deferred paths.
- `dl_defer` timer: armed for the zero-laxity point by `dl_server_start()`
  itself, not on starvation; `update_curr_dl_se()` cancels it and re-arms it
  for a new period each time served-class runtime uses up the budget of a
  server that waits throttled.
- `dl_defer` also changes:
  - `update_curr_dl_se()` charges a throttled server only if `dl_defer` is set
  - `dl_server_update_idle()` charges idle time only if `dl_defer` is set
  - `update_dl_entity()` uses `update_dl_revised_wakeup()` for a server with
    `dl_defer_running` set, although its deadline equals its period
- After the timer fired (`dl_defer_running` set): the server throttles and
  replenishes like a task and does not defer again until
  `update_curr_dl_se()` or `update_dl_entity()` clears `dl_defer_running`.

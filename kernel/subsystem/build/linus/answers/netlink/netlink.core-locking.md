- Per-socket dump mutex: `nl_cb_mutex`, embedded in `struct netlink_sock`
  in `net/netlink/af_netlink.h`. There is no cb_def_mutex or dump_cb_mutex
  here, and `struct netlink_kernel_cfg` has no mutex member.
- `genl_mutex` in dumps: `genl_start()`, `genl_dumpit()` and `genl_done()`
  take it with `genl_op_lock()` around the family callback only. There is no
  genl_lock_dumpit(), genl_lock_done() or genl_parallel_done() here.
- Non-parallel family, dump callbacks other than `done` at socket close:
  `nl_cb_mutex` and `genl_mutex` are both held; neither replaces the other.
- `genl_family_rcv_msg_dumpit()`: drops `genl_mutex` around
  `__netlink_dump_start()`. The order is `nl_cb_mutex`, then `genl_mutex`.
- `genl_mutex` is released between `start` and the first round, and between
  rounds.

| Callback | `cb_lock` (read) | `nl_cb_mutex` | `genl_mutex` without `parallel_ops` |
|---|---|---|---|
| `pre_doit`, `doit`, `post_doit` | held | no | held |
| `start`, first `dumpit` round | held | held | held |
| later rounds, from `netlink_recvmsg()` | no | held | held |
| `done` at the end of a dump | as the round it ends | held | held |
| `done` at socket close | no | no | held |

- With `parallel_ops`: the `genl_mutex` column is "no" in every row.
- `done` at socket close: `netlink_release()` calls `nlk->cb.done` directly
  when `cb_running` is set. `netlink_sock_destruct()` does not call it, and
  no deferred work is involved.
- `done` at socket close for a `parallel_ops` family: runs with no core lock
  at all.

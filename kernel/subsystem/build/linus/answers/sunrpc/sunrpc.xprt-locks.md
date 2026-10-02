| Lock | Protects | Easy to miss |
|---|---|---|
| `transport_lock` | `snd_task` and hand-off of `XPRT_LOCKED`; `cong`, `cwnd`, `XPRT_CWND_WAIT`; the `XPRT_CLOSE_WAIT` test in `xprt_clear_locked()` against `xprt_schedule_autoclose_locked()`; arming `timer` | not the receive queue or `rq_pin`; `connect_cookie` is bumped without it; `xprt_clear_congestion_window_wait()` clears `XPRT_CWND_WAIT` before it takes the lock |
| `reserve_lock` | `free`, `num_reqs`, the `xid` counter in `xprt_alloc_xid()`, and `XPRT_CONGESTED` against `xprt_free_slot()` | `xprt_rdma_alloc_slot()` and `rpcrdma_req_release()` call the backlog helpers without it |
| `queue_lock` | `recv_queue`, `xmit_queue`, `rq_pin` increments, `RPC_TASK_NEED_RECV`, `RPC_TASK_NEED_XMIT` | `xprt_schedule_autodisconnect()` reads `recv_queue` without it |
| `XPRT_LOCKED` | right to send, connect and close; keeps `transport->sock` stable for a sender | the only assertion is `WARN_ON_ONCE()` on `xprt_lock_connect()` in `xs_connect()` and `xprt_rdma_connect()`; `xs_tcp_send_request()` takes no mutex |
| `recv_mutex` | `sock`, `inet`, `file` of `struct sock_xprt` for code that does not hold `XPRT_LOCKED` | also taken outside the receive workers, for example by `xs_sock_srcport()` and `xs_sock_srcaddr()` |

- All three spinlocks: every acquisition in the tree is plain `spin_lock()`;
  none is in softirq, hard-irq or a timer callback.
- Socket callbacks such as `xs_data_ready()` and `xs_write_space()`: take none
  of them; they set a `sock_state` bit and queue `recv_worker` or
  `error_worker`.
- `xprt_init_autodisconnect()`: a timer callback that takes no spinlock; it
  sets `XPRT_LOCKED` with `test_and_set_bit()` and queues `task_cleanup`.
- RPC/RDMA completions: both client CQs are `IB_POLL_WORKQUEUE` in
  `rpcrdma_ep_create()`, so `rpcrdma_reply_handler()` takes `queue_lock` in
  process context.
- `xprt_write_space()`: its kerneldoc mentions softirq, but its callers are
  `xs_wake_write()` and functions in `net/sunrpc/xprtrdma/verbs.c`, all
  process context.
- Nesting: `xprt_request_enqueue_transmit()` takes `transport_lock` inside
  `queue_lock`; `xs_udp_data_read_skb()` drops `queue_lock` before it takes
  `transport_lock`.
- **Unsafe usage**: taking one of the three spinlocks from a socket callback or
  other softirq code, for example by calling `xprt_force_disconnect()` there.
  - Unsafe: the holders use plain `spin_lock()`, so a softirq on the same CPU
    would spin on a lock that cannot be released.
  - Safe: record the event and queue a worker, as `xs_run_error_worker()`
    does; `xs_error_handle()` then takes the lock in process context.

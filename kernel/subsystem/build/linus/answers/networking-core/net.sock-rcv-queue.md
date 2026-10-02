- `sock_queue_rcv_skb_reason()`: takes `(sk, skb)` and returns
  `enum skb_drop_reason`; there is no reason pointer argument and no errno.
- A caller tests the result for non-zero, never for `< 0`; refusals are
  positive enum values.
- `sock_queue_rcv_skb()` in `include/net/sock.h`: switches on that reason;
  every reason it does not name becomes `-EPERM`.

| Outcome | `sock_queue_rcv_skb_reason()` | `sock_queue_rcv_skb()` |
|---|---|---|
| queued | `SKB_NOT_DROPPED_YET` | 0 |
| pfmemalloc buffer, socket lacks `SOCK_MEMALLOC` | `SKB_DROP_REASON_PFMEMALLOC` | `-EPERM` |
| `BPF_CGROUP_RUN_PROG_INET_INGRESS()` fails, or `sk->sk_filter` returns 0 or the trim fails | `SKB_DROP_REASON_SOCKET_FILTER` | `-EPERM` |
| `security_sock_rcv_skb()` fails | `SKB_DROP_REASON_SECURITY_HOOK` | `-EPERM` |
| `sk_rmem_alloc` `>=` `sk_rcvbuf` | `SKB_DROP_REASON_SOCKET_RCVBUFF` | `-ENOMEM` |
| `sk_rmem_schedule()` fails | `SKB_DROP_REASON_PROTO_MEM` | `-ENOBUFS` |

- The first three refusals come from `sk_filter_trim_cap()` in
  `net/core/filter.c`, reached through `sk_filter_reason()`; the errno that
  the LSM or BPF program returned is discarded.
- `__sock_queue_rcv_skb()` before queueing: `skb->dev = NULL`,
  `skb_set_owner_r()`, `skb_dst_force()`; it does not drop the dst.

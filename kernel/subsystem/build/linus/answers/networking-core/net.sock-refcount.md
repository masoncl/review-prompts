- `skb_set_owner_w()` on a full socket: takes no `sk_refcnt`; it only adds
  `skb->truesize` to `sk_wmem_alloc`.
- `SK_WMEM_ALLOC_BIAS` in `include/net/sock.h`: the name of the initial 1 in
  `sk_wmem_alloc` that `sk_free()` drops.
- Destructors that can drop `sk_wmem_alloc` to zero and so free the socket:

| Destructor | Used for | Final step |
|---|---|---|
| `sock_wfree()` | set by `skb_set_owner_w()` | `__sk_free()` |
| `__sock_wfree()` | TCP pure ACKs | `__sk_free()` |
| `tcp_wfree()` | other TCP tx skbs | keeps one unit, then `sk_free()` |

- `tcp_wfree()` when it queues the socket for TSQ: returns without
  `sk_free()`; `tcp_tsq_workfn()` in `net/ipv4/tcp_output.c` calls `sk_free()`
  later, so the free can come from that work item.
- `sk_destruct()`: uses `call_rcu()` when `SOCK_RCU_FREE` is set or when
  `sk->sk_reuseport_cb` is non-NULL.
- `__sk_free()` with `sk_net_refcnt` set and destroy listeners present: calls
  `sock_diag_broadcast_destroy()` instead of `sk_destruct()`; that queues work
  which calls `sk_destruct()` later.

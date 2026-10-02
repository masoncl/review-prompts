- `skb_set_owner_sk_safe()` in `include/net/sock.h`: tests only that `sk` is
  non-NULL and that `refcount_inc_not_zero(&sk->sk_refcnt)` succeeds; it does
  not call `sk_fullsock()` or `sk_is_refcounted()`.
- `skb_set_owner_sk_safe()` returning false: the buffer is not orphaned and
  keeps its previous owner and destructor; the result is `__must_check`.
  `skb_orphan_partial()` then calls `skb_orphan()`.
- **Unsafe usage**: `skb_set_owner_sk_safe()` on a request or timewait socket;
  its destructor `sock_efree()` calls `sock_put()`, which ends in `sk_free()`.
  - Safe: `skb_set_owner_edemux()`, whose `sock_edemux()` calls
    `sock_gen_put()`, as `tcp_make_synack()` does with a request socket.
  - Safe: a full socket, as `tcp_read_skb()` passes.
- `skb_set_owner_edemux()`: orphans the buffer first, returns void, and on a
  failed `refcount_inc_not_zero()` leaves the buffer unowned.
- `skb_set_owner_w()` on a non-full socket: takes the
  `skb_set_owner_edemux()` path, so `skb->sk` can be NULL afterwards.
- Without `CONFIG_INET`: `skb_set_owner_edemux()` is not defined,
  `sock_edemux` is a macro for `sock_efree`, and `skb_set_owner_w()` has no
  non-full branch.
- `sock_pfree()` in `net/core/sock.c`: destructor for a socket that may be
  attached with no reference; it does nothing when `sk_is_refcounted()` is
  false. `udp_v4_early_demux()` attaches a `SOCK_RCU_FREE` socket this way.
- `bpf_sk_assign()` in `net/core/filter.c`: takes `refcount_inc_not_zero()`
  only when `sk_is_refcounted()`, then installs `sock_pfree()`.
- `skb_set_owner_w()` and `sock_alloc_send_pskb()`: neither takes nor asserts
  the socket lock.
- `skb_set_owner_w()` on a full socket: adds to `sk_wmem_alloc` and cannot
  fail; on a zero count `__refcount_add()` warns and saturates the count.
  `sock_put()` calls `sk_free()`, which drops the bias, only when `sk_refcnt`
  reaches zero.
- `skb_set_owner_r()`: takes no reference of any kind; `sock_rfree()`
  dereferences `skb->sk`, so the socket's destructor has to purge the queue
  first, as `inet_sock_destruct()` does.

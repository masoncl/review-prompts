- Counter field: `__rcuref` (`rcuref_t`) in `struct dst_entry`,
  `include/net/dst.h`; there is no field named __refcnt.
- DST_NOCACHE: not defined in this tree; the name is left only in a comment
  in `net/ipv4/route.c`.
- `dst_hold()` on a dead entry: takes no reference and fires `WARN_ON()`; the
  caller goes on with a pointer it does not own.
- `sk_dst_get()` in `include/net/sock.h`: calls
  `rcuref_get(&dst->__rcuref)` directly, not `dst_hold_safe()`; a search for
  `dst_hold_safe()` callers misses it.
- IPv6 on a failed `dst_hold_safe()`: `ip6_hold_safe()` and
  `ip6_route_output_flags()` in `net/ipv6/route.c` hand back
  `net->ipv6.ip6_null_entry` with `dst_hold()`, not NULL; `ip6_hold_safe()`
  gives NULL only when its `net` argument is NULL.
- IPv4 on a failed `dst_hold_safe()`: `__mkroute_output()` falls through and
  allocates a new route; `inet_sk_rx_dst_set()` and `udp_sk_rx_dst_set()`
  leave `sk->sk_rx_dst` unchanged.
- **Potentially unsafe usage**: `dst_release_immediate()` on an entry that was
  stored where RCU readers look.
  - Unsafe: while a reader that found the entry under `rcu_read_lock()` can
    still be running; `dst_destroy()` frees it with no grace period.
  - Safe: the entry was never published, as in `__ip6_rt_update_pmtu()` and
    `rt6_do_redirect()` when `rt6_insert_exception()` failed.
  - Safe: a grace period has passed since the entry was unpublished, as in
    `rt_fibinfo_free()` in `net/ipv4/fib_semantics.c`, which runs from RCU
    callbacks, for example `free_fib_info_rcu()`.

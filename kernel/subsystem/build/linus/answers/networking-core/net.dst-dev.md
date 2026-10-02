- `dst_dev_put()` in `net/core/dst.c`: also writes `DST_OBSOLETE_DEAD` to
  `dst->obsolete`; it moves the tracked reference with
  `netdev_ref_replace()`, it does not call `netdev_put()`.
- `dst_dev_put()` callers: the code that drops a cached route (nexthop
  exception, per-CPU route, `fib_info` free) and `drivers/net/vrf.c`; no
  netdev notifier calls it directly.
- `rt_flush_dev()` in `net/ipv4/route.c` and `rt6_uncached_list_flush_dev()`
  in `net/ipv6/route.c`: do not call `dst_dev_put()`; they swap the device
  and its tracker and unlink the route from the uncached list.
- Uncached route after the flush: `dst->obsolete`, `dst->input` and
  `dst->output` are unchanged, so the route keeps running its normal handlers
  with `blackhole_netdev` as device.
- `ip6_route_dev_notify()`: acts only on the loopback device and the
  per-netns null, prohibit and blackhole entries (the last two under
  `CONFIG_IPV6_MULTIPLE_TABLES`); it moves no route to `blackhole_netdev`.
- `blackhole_netdev` in `drivers/net/loopback.c`: one global device, never
  registered; `dev_net()` of it is `&init_net` and its MTU is `ETH_MIN_MTU`.
- Netns from a swapped route: `dev_net(dst_dev(dst))` and
  `dst_dev_net_rcu()` return `&init_net`, whatever netns the route was
  created in.
- NULL device: `dst_dev()` and `dst_dev_rcu()` return NULL for an entry
  initialised with no device; neither accessor tests for it.
  - `__metadata_dst_init()` in `net/core/dst.c` passes NULL to `dst_init()`.
  - `xfrm_alloc_dst()` in `net/xfrm/xfrm_policy.c` passes NULL to
    `dst_alloc()`; the bundle code sets the device later.
- `dst_dev()`: a bare `READ_ONCE()`; it asserts no lock and gives no lifetime
  guarantee for the device it returns.
- Direct `dst->dev` reads: nothing in the tree forbids them; `dev` is a plain
  member of the union beside `dev_rcu`, and many files still read it
  directly, for example `rt_flush_dev()` under `ul->lock`, which it also
  holds for its write.

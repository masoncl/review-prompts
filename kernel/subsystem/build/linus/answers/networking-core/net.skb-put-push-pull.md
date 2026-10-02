- `skb_put()` and `__skb_put()`: both run `SKB_LINEAR_ASSERT()`, which is
  `BUG_ON(skb_is_nonlinear(skb))`, unconditional. `__skb_put()` has no other
  check and no `DEBUG_NET_WARN_ON_ONCE()`.
- `__skb_push()`: `DEBUG_NET_WARN_ON_ONCE(len > INT_MAX)` and
  `DEBUG_NET_WARN_ON_ONCE(skb->data < skb->head)`. Both only warn, and only
  under `CONFIG_DEBUG_NET`; the push still happens.
- `__skb_pull()`: `DEBUG_NET_WARN_ON_ONCE(len > INT_MAX)`, then after
  `skb->len -= len` an unconditional `BUG()` when `skb->len < skb->data_len`.
  It does not compare `len` with `skb->len`.
- `__skb_pull()` on a linear skb: `skb->data_len` is 0, so the `BUG()` test
  is never true and an over-long `len` wraps `skb->len` silently.
- `skb_pull()` on a nonlinear skb with `skb_headlen() < len <= skb->len`:
  passes the test in `skb_pull_inline()` and then hits the `BUG()` in
  `__skb_pull()`. NULL is returned only for `len > skb->len`.

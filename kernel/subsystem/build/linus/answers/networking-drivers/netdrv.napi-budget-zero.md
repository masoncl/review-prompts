- Context of the zero-budget call: `__netpoll_send_skb()` in
  `net/core/netpoll.c` asserts IRQs disabled, then reaches `poll_one_napi()`
  through `netpoll_poll_dev()`.
- Non-zero return from a zero-budget call: `WARN_ONCE()` in `poll_one_napi()`.
- `napi_complete_done()` in a zero-budget call from `poll_one_napi()`: returns
  false at its first test, because `poll_one_napi()` holds `NAPI_STATE_NPSVC`.
- `Documentation/networking/napi.rst`: says never to call
  `napi_complete_done()` with budget 0; its example tests `budget &&` first.
- `napi_consume_skb()` with non-zero budget, skb allocated on another CPU:
  goes to `skb_attempt_defer_free()` instead of straight to the local cache,
  unless the skb is shared or `skb_defer_disable_key` is on.
- `napi_consume_skb()` with non-zero budget, fclone skb: freed with
  `__kfree_skb()`, not cached.
- Page pool direct recycling: not controlled by the budget;
  `napi_consume_skb()` does not pass it on, `page_pool_napi_local()` in
  `net/core/page_pool.c` decides.
- **Potentially unsafe usage**: `napi_consume_skb()` with a constant non-zero
  budget.
  - Unsafe: when the caller can run outside softirq or BH-disabled context,
    such as a Tx-clean routine reached from the zero-budget netpoll call;
    `napi_skb_cache_put()` guards the per-CPU cache only with
    `local_lock_nested_bh()`.
  - Safe: when every caller has BH disabled, as `skb_defer_free_flush()` in
    `net/core/dev.c`, which passes 1; `napi_consume_skb()` checks this with
    `DEBUG_NET_WARN_ON_ONCE(!in_softirq())`.
  - Safe: pass the poll function's own `budget` down, as `ixgbe_poll()` does
    to `ixgbe_clean_tx_irq()`; the `!budget` test in `napi_consume_skb()` then
    covers the netpoll call.

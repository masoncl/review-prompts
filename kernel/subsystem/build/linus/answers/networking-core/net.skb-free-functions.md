- `napi_consume_skb()` with a non-zero budget: for a buffer that was allocated
  on another CPU and is not shared, it calls `skb_release_head_state()` at
  once and hands the buffer to `skb_attempt_defer_free()`, which tries to
  queue it for the CPU in `skb->alloc_cpu`. `skb_defer_disable_key` turns that
  path off.
- `dev_kfree_skb()`: a macro for `consume_skb()` in `include/linux/skbuff.h`,
  so it reports consumption, not a drop, and is not for IRQs-disabled callers.
  There is no dev_consume_skb in this tree.
- `sk_skb_reason_drop()`: the tracepoint it fires is `kfree_skb`
  (`trace_kfree_skb()`, which also carries the socket); with `SKB_CONSUMED` it
  fires `consume_skb` instead. `kfree_skb_reason()` is only the inline wrapper
  that passes a NULL socket.
- List of buffers: there is no consume wrapper and no IRQ-safe form of
  `kfree_skb_list_reason()`. To purge a `struct sk_buff_head` without
  reporting drops, pass `SKB_CONSUMED` to `skb_queue_purge_reason()`, as
  `drivers/net/netconsole.c` does.
- Hard interrupt: the rule is stated in the comment above
  `dev_kfree_skb_irq()` in `include/linux/netdevice.h`. The only context check
  on the `kfree_skb()` path in `net/core/skbuff.c` is
  `DEBUG_NET_WARN_ON_ONCE(in_hardirq())` in `skb_release_head_state()`,
  reached only when `skb->destructor` is set.
- `enqueue_to_backlog()` in `net/core/dev.c`: calls `kfree_skb_reason()` on a
  dropped receive buffer in whatever context `netif_rx()` or `__netif_rx()`
  was called from, hard interrupt included.

- `dev_kfree_skb()`: `#define dev_kfree_skb(a) consume_skb(a)` in
  `include/linux/skbuff.h`; it means consumed, and it frees directly whatever
  the IRQ state.
- `napi_consume_skb()` with `budget == 0` or a NULL skb: calls
  `dev_consume_skb_any()`.
- Drop in NAPI Tx completion: `dev_kfree_skb_any()`, because of the budget-0
  call from `poll_one_napi()`; see "Zero budget polls".
- **Potentially unsafe usage**: `kfree_skb()`, `consume_skb()` or
  `dev_kfree_skb()` in code reached from `ndo_start_xmit` or from the Tx
  completion part of a NAPI poll.
  - Unsafe: when netpoll can attach to the device; `__netpoll_send_skb()`
    calls both with hard IRQs disabled, the state in which
    `dev_kfree_skb_any_reason()` defers the free to `net_tx_action()`.
  - Safe: the device sets `IFF_DISABLE_NETPOLL`, which `__netpoll_setup()`
    rejects; `veth_xmit()` calls `kfree_skb()` and `veth_setup()` sets the
    flag.
  - Safe: `dev_kfree_skb_any()` or `dev_consume_skb_any()`, which test
    `in_hardirq() || irqs_disabled()` in `dev_kfree_skb_any_reason()`.

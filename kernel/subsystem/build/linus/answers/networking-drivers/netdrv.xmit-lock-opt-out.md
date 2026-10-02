- Flag: `lltx`, a one-bit field of `struct net_device` beside `priv_flags`;
  there is no NETIF_F_LLTX feature bit in this tree.
- Deprecation wording: in the `struct net_device` kdoc ("Deprecated for real HW
  drivers") and `Documentation/networking/netdevices.rst` ("meant for software
  drivers only"); `Documentation/networking/netdev-features.rst` does not
  mention it.
- Hardware drivers that set `lltx` exist in the tree (search
  `lltx = true` under `drivers/net/ethernet`); for example
  `pasemi_mac_start_tx()` serialises its ring with its own `txring->lock`
  under `spin_lock_irqsave()`.
- Recursion with `lltx`: `dev_xmit_recursion()` in `__dev_queue_xmit()` still
  bounds nesting at `XMIT_RECURSION_LIMIT`; `netif_tx_owned()` does not catch
  it, because `HARD_TX_LOCK()` does not take `_xmit_lock`.
- `netif_tx_lock()` and `netif_tx_disable()` with `lltx`: they still take
  `_xmit_lock`, which the transmit path does not, so they do not wait for a
  transmit routine that is already running.
- `txq_trans_update()` with `lltx`: does nothing, so `netdev_start_xmit()` does
  not update `trans_start`; a driver that needs it calls
  `netif_trans_update()` or `txq_trans_cond_update()` itself.
- `netdev_uses_bql()` in `net/core/net-sysfs.c`: false when `lltx` is set, so
  the queue gets no BQL sysfs group.

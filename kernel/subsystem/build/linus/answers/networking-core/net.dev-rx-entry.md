- `enum gro_result` in `include/linux/netdevice.h`: `GRO_MERGED`,
  `GRO_MERGED_FREE`, `GRO_HELD`, `GRO_NORMAL`, `GRO_CONSUMED`; there is no
  GRO_DROP.
- `napi_gro_receive()`: inline wrapper for `gro_receive_skb(&napi->gro, skb)`.
- `GRO_NORMAL` buffers are batched by `gro_normal_one()` on `rx_list` in
  `struct gro_node` (`napi->gro`), not in `struct napi_struct`;
  `gro_normal_list()` in `include/net/gro.h` passes the batch to
  `netif_receive_skb_list_internal()`.

| Function | Context, where it differs from the name's promise |
|---|---|
| `netif_rx()` | hardirq, softirq, or process context with interrupts enabled; it disables BH itself |
| `__netif_rx()` | hardirq or softirq/BH-disabled only; `lockdep_assert_once()` on `hardirq_count() \| softirq_count()` |
| `dev_forward_skb()` | calls `netif_rx_internal()` directly, so none of the BH handling of `netif_rx()` |
| `netif_receive_skb_core()` | skips RPS, `skb_defer_rx_timestamp()` and the pfmemalloc handling of `__netif_receive_skb()`; generic XDP still runs |
| `gro_cells_receive()` | takes `local_lock_nested_bh()`; see below for where the buffer goes |

- **Potentially unsafe usage**: calling `netif_rx()` with interrupts disabled.
  - Unsafe: in process context with BH enabled; `need_bh_off` is then true,
    `netif_rx()` calls `local_bh_enable()`, and `__local_bh_enable_ip()` in
    `kernel/softirq.c` has `lockdep_assert_irqs_enabled()`.
  - Safe: in hardirq context or with BH already disabled, where
    `hardirq_count() | softirq_count()` makes `need_bh_off` false and BH is
    left alone, as `arcnet_interrupt()` in `drivers/net/arcnet/arcnet.c`
    reaches `netif_rx()` under `spin_lock_irqsave()`.
- `gro_cells_receive()`: hands the buffer to `netif_rx()` instead of the cell
  when `gcells->cells` is NULL, the buffer is `skb_cloned()`, or
  `netif_elide_gro()` is true.
- `gro_cells_receive()` on a device without `IFF_UP`: frees the buffer and
  returns `NET_RX_DROP`.

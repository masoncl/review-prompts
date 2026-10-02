- `sock_queue_rcv_skb_reason()`: `SKB_NOT_DROPPED_YET` means queued, any other
  value means the caller still owns the buffer.
- `sk_add_backlog()`: fails with `-ENOBUFS` over the limit and with `-ENOMEM`
  for a pfmemalloc buffer on a socket without `SOCK_MEMALLOC`; the caller
  frees in both cases.
- `ndo_start_xmit` return values, as `dev_xmit_complete()` in
  `include/linux/netdevice.h` classifies them:

| Return | Buffer |
|---|---|
| `NETDEV_TX_OK` | driver took it |
| negative errno | driver took it |
| `NET_XMIT_DROP`, `NET_XMIT_CN` | driver took it; for example `veth_xmit()` returns `NET_XMIT_DROP` after freeing |
| `NETDEV_TX_BUSY` | still belongs to whoever called the driver |

- `NETDEV_TX_BUSY`, what the caller of the driver then does:

| Caller | Action |
|---|---|
| `sch_direct_xmit()` | requeues with `dev_requeue_skb()` |
| `__dev_queue_xmit()`, device without a queue | frees with `kfree_skb_list_reason()`, returns `-ENETDOWN` for a single buffer |
| `__dev_direct_xmit()` | returns `NETDEV_TX_BUSY` with the buffer not freed |
| `dev_direct_xmit()` | frees with `kfree_skb()` when `dev_xmit_complete()` is false |

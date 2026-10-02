| Callback | Normal driver | Ops-locked driver | Sleep |
|---|---|---|---|
| `ndo_set_rx_mode` | `netif_addr_lock_bh()` of the caller; `rtnl_lock` not guaranteed | from core work: `rtnl_lock`, instance lock, then `netif_addr_lock_bh()` | no |
| `ndo_setup_tc`, `TC_SETUP_BLOCK` or `TC_SETUP_FT` | neither lock guaranteed | instance lock held on some paths, not on others | yes |
| `ndo_tx_timeout` | `tx_global_lock`, queues frozen, timer | same, no instance lock | no |

- `ndo_set_rx_mode` of a normal driver that also has `ndo_change_rx_flags`:
  runs from the core work under `rtnl_lock` and `netif_addr_lock_bh()`, with
  no instance lock; see `__dev_set_rx_mode()` in
  `net/core/dev_addr_lists.c`.
- `TC_SETUP_BLOCK` with the instance lock held: `tc_modify_qdisc()` takes
  `netdev_lock_ops()` and reaches `tcf_block_offload_cmd()` through
  `ingress_init()`.
- `TC_SETUP_BLOCK` without it: `nft_block_offload_cmd()` in
  `net/netfilter/nf_tables_offload.c` takes no netdev lock.
- `TC_SETUP_FT`: `nf_flow_table_offload_cmd()` takes
  `flowtable->flow_block_lock` and no netdev lock.
- An ops-locked driver's `TC_SETUP_BLOCK` handler therefore can neither assert
  the instance lock nor take it.

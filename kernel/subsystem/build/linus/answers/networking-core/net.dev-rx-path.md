- Generic XDP: `do_xdp_generic()` is called inside
  `__netif_receive_skb_core()`, as the first stage after `another_round:`,
  ahead of `skb_vlan_untag()` and the taps.
- Generic XDP on a redirected buffer: `netif_receive_generic_xdp()` returns
  `XDP_PASS` without running the program when `skb_is_redirected()`.
- `skb_vlan_untag()` runs before the taps; `vlan_do_receive()` runs after
  ingress classification and before `rx_handler`.
- `skb_orphan_frags_rx()`: not a stage of the core; on this path it is called
  only inside `deliver_skb()`, so the last handler, handed back through
  `*ppt_prev`, is called without it.
- `pfmemalloc`: skips the taps only (`skip_taps:`); ingress classification and
  `rx_handler` still run, and a protocol that fails
  `skb_pfmemalloc_protocol()` is dropped at `skip_classify:`.
- `skb_skip_tc_classify()`: jumps to `skip_classify:`, so a step placed
  between `skip_taps:` and `skip_classify:` is not run for such a buffer, and
  `skb_reset_redirect()` is skipped too.
- `another_round:` is reached from three kinds of step: `vlan_do_receive()`,
  `RX_HANDLER_ANOTHER`, and `sch_handle_ingress()` setting `*another` (a tc
  redirect for which `skb_do_redirect()` returns `-EAGAIN`).
- `orig_dev`: set once before `another_round:` and passed unchanged to every
  handler on later rounds.
- Protocol delivery order: `ptype_base[]`, then the `ptype_specific` list of
  `dev_net_rcu(skb->dev)`, then `orig_dev->ptype_specific`, then
  `skb->dev->ptype_specific` if the device changed.
- `RX_HANDLER_EXACT`: skips the first two of those lists only; both
  per-device lists are still walked, and the taps have already run.
- No handler matched: counted as `rx_dropped`, or as `rx_nohandler` when
  `deliver_exact` is set.
- `out:` neither frees nor counts; a step that jumps there must already have
  consumed the buffer. `ret` is returned as it stands, `NET_RX_DROP` unless
  something set it.
- `drop:` frees with `drop_reason` and counts; a step that jumps there must
  still own the buffer.

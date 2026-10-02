- `napi_id` argument of `__xdp_rxq_info_reg()`: not stored or used;
  `struct xdp_rxq_info` has no field for it, so the value passed does not
  matter.
- Second way to bind a pool: `xdp_reg_page_pool()` once per pool, then
  `xdp_rxq_info_attach_page_pool()` per queue in place of
  `xdp_rxq_info_reg_mem_model()`; `libeth_rx_fq_create()` does the first
  step.
- **Unsafe usage**: `xdp_rxq_info_unreg()` on a queue whose pool was bound
  with `xdp_rxq_info_attach_page_pool()` and not detached; it calls
  `page_pool_destroy()` and drops a `user_cnt` reference the queue never
  took.
  - Safe: `xdp_rxq_info_detach_mem_model()` first, as
    `__idpf_xdp_rxq_info_deinit()` does; the reference taken by
    `xdp_reg_page_pool()` is dropped by `xdp_unreg_page_pool()`.
  - Safe: no detach when the pool was bound with
    `xdp_rxq_info_reg_mem_model()`, which took the reference that
    `xdp_rxq_info_unreg()` drops, as in `mvneta_create_page_pool()` and
    `mvneta_rxq_drop_pkts()`.
- `xdp_do_check_flushed()`: real only with both `CONFIG_DEBUG_NET` and
  `CONFIG_BPF_SYSCALL`; `__napi_poll()` calls it right after `->poll()`
  returns, and it flushes the leftover lists before it warns.
- `xdp_do_redirect()` failure: the redirect error tracepoint has already
  fired inside it (`_trace_xdp_redirect_map_err()`, called on the error
  paths in `net/core/filter.c`); what the driver still owes is the buffer.
- `trace_xdp_exception()` after a failed redirect: a per-driver addition,
  as in `ixgbe_run_xdp()`; no core code depends on it.
- `bpf_prog_run_xdp()` can hand the driver `XDP_REDIRECT` or `XDP_ABORTED`
  for a program that returned `XDP_TX`: on a bond slave, with
  `bpf_master_redirect_enabled_key` on, it calls `xdp_master_redirect()`.
- The flush duty follows the verdict the driver sees, so a driver that
  handles `XDP_TX` on a bond slave also needs the `XDP_REDIRECT` branch and
  `xdp_do_flush()`.
- `xdp_do_redirect()` and `xdp_do_flush()` dereference
  `current->bpf_net_context`; the NAPI core sets it around `->poll()` with
  `bpf_net_ctx_set()`, but `poll_one_napi()` in `net/core/netpoll.c` does
  not.
- XDP run outside `->poll()` must set the context itself, with BH disabled,
  as `tun_sendmsg()` in `drivers/net/tun.c` does.
- Dropping a multi-buffer frame: every frag must go back as well as the
  head; `xdp_return_buff()` does both, with direct recycling unless
  `xdp_set_return_frame_no_direct()` is in effect, so without that it is
  for the NAPI poll only.

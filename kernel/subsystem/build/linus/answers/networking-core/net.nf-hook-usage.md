- **Potentially unsafe usage**: using the buffer after `NF_HOOK()` returns.
  - Unsafe: when okfn consumes the buffer, as `dst_output()` and
    `ip_rcv_finish()` do. Then no return value of `NF_HOOK()` leaves the
    buffer with the caller.
  - Safe: when okfn leaves the buffer alone and returns 1, and the caller
    continues only on 1. `br_handle_frame()` in `net/bridge/br_input.c` does
    this with `br_handle_local_finish()` and then returns `RX_HANDLER_PASS`.
    `nf_hook_slow()` returns 0 or a negative value for every verdict that took
    the buffer, so 1 can only come from okfn.
- **Unsafe usage**: freeing the buffer on the error path after `NF_HOOK()` or
  `nf_hook()` returned a negative value.
  - Safe: jump past the free, as `raw_send_hdrinc()` in `net/ipv4/raw.c` does:
    its `NF_HOOK()` error goes to `error`, below the `kfree_skb()` at
    `error_free`.
- Direct callers of `nf_hook()`: search for `nf_hook(`. Apart from the
  `NF_HOOK()` and `NF_HOOK_COND()` wrappers they are only in
  `net/ipv4/ip_output.c`, `net/ipv6/output_core.c`, `net/xfrm/xfrm_output.c`
  and `drivers/net/vrf.c`, and none touches the buffer again unless the
  result is 1.
- `__ip_local_out()` and `__ip6_local_out()`: return the `nf_hook()` result
  unchanged, so the test for 1 is their caller's job, as in `ip_local_out()`.
- `ip_rcv()`, `ip_local_deliver()` and `ip_forward()`: use `NF_HOOK()`, not
  `nf_hook()`. `ip_output()` and `ip6_output()` use `NF_HOOK_COND()`.
- `nf_hook_egress()`, `nf_hook_ingress()` and `br_nf_hook_thresh()`: call
  `nf_hook_slow()` directly, not `nf_hook()`.
- `nf_hook_ingress()` in `include/linux/netfilter_netdev.h`: its return
  convention differs. 0 means the device has no hooks and the caller
  continues; a 0 from `nf_hook_slow()` is turned into -1. The caller in
  `__netif_receive_skb_core()` stops only on a negative value.

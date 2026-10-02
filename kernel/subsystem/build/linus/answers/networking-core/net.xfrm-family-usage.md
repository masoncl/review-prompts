- The accessor follows the family of the header at `skb_network_header()` at
  that point, taken from the packet or its dst. `x->props.family` and
  `x->outer_mode.family` describe the outer header only.
- `xfrm_dev_offload_ok()` in `net/xfrm/xfrm_device.c` and
  `xfrm_get_inner_ipproto()` in `net/xfrm/xfrm_output.c`: switch on
  `skb_dst(skb)->ops->family` before `ip_hdr()` or `ipv6_hdr()`.
- `skb_dst(skb)->ops->family` on output is the pre-encapsulation family:
  `xfrm_bundle_create()` allocates each dst with the family in force before
  that state's `props.family` is applied.
- `xfrm_inner_extract_output()`: switches on `skb->protocol`. It does not
  call `xfrm_ip2inner_mode()`.
- `xfrm_inner_mode_encap_remove()` in `net/xfrm/xfrm_input.c`: tunnel mode
  picks by `XFRM_MODE_SKB_CB(skb)->protocol`, BEET by `x->sel.family`.
- `xfrm_ip2inner_mode()` is in `include/net/xfrm.h`. `xfrm_input()` does not
  call it; for example `xfrmi_rcv_cb()` and `xfrm_bundle_create()` do, when
  `x->sel.family == AF_UNSPEC`.
- `XFRM_DEV_OFFLOAD_PACKET`: `xfrm_output_one()` skips
  `xfrm_outer_mode_output()`, so the skb keeps the inner family;
  `xfrm_output()` uses `skb_dst(skb)->ops->family` for such a state.
- **Potentially unsafe usage**: choosing the accessor from `x->props.family`.
  - Unsafe: on output before the outer header is built, or on input after
    decapsulation, in tunnel or BEET mode; the inner packet can be the other
    family.
  - Safe: in transport mode, as `xfrm_inner_mode_input()` does for
    `xfrm4_transport_input()`; `__xfrm_init_state()` rejects a `sel.family`
    that differs from `props.family` unless the mode has
    `XFRM_MODE_FLAG_TUNNEL`.
  - Safe: for the outer header the function has just placed, as
    `xfrm_outer_mode_output()` does for `xfrm4_tunnel_encap_add()`.
  - Safe: on input before decapsulation, as `xfrm_prepare_input()` does; it
    reads the header before `xfrm_inner_mode_encap_remove()` moves the
    network header.

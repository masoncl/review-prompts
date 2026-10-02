# Networking Core: SKB, Sockets, and Packet Flow

## Main structures

### Objects and how they relate

- `skb_frag_t`: holds a `netmem_ref`, not a page pointer; it may refer to a
  `struct net_iov` (`include/net/netmem.h`), memory with no `struct page`.
- `struct dst_entry`: holds no neighbour; `ip_finish_output2()` in
  `net/ipv4/ip_output.c` looks up the `struct neighbour` per packet with
  `ip_neigh_for_gw()`, under `rcu_read_lock()`.
- `sk_backlog` in `struct sock`: not a `struct sk_buff_head`; a bare
  `head`/`tail` pair chained through `skb->next`, with no lock of its own.
  See `__sk_add_backlog()` in `include/net/sock.h`.
- `struct Qdisc` and `struct netdev_queue`: not one-to-one; a root qdisc
  whose ops have no `attach` is grafted onto every Tx queue of the device by
  `qdisc_graft()` in `net/sched/sch_api.c`, so the queues share it.
- `qdisc` and `qdisc_sleeping` in `struct netdev_queue`: both exist;
  `qdisc_sleeping` is the configured qdisc, `qdisc` is the one the transmit
  path uses and is `noop_qdisc` until `transition_one_qdisc()` activates it.
- `struct socket`: not always inside a `struct socket_alloc`;
  `struct tun_file` (`drivers/net/tun.c`) and `struct tap_queue`
  (`include/linux/if_tap.h`) embed one with no inode behind it.
- **Potentially unsafe usage**: `SOCK_INODE()` or `sock_init_data()` on a
  `struct socket`.
  - Unsafe: when the `struct socket` is embedded in a driver structure;
    `SOCK_INODE()` is a `container_of()` on `struct socket_alloc`, and
    `sock_init_data()` in `net/core/sock.c` calls it.
  - Safe: after `sock_from_file()` on `sock->file` returned that same socket,
    as `sock_read_xattr()` in `net/socket.c` tests first; `sock_from_file()`
    returns NULL unless `f_op` is `socket_file_ops`, which rejects tun and
    tap.
- `struct packet_type`: lives on one of five kinds of list, chosen by
  `ptype_head()` in `net/core/dev.c` from `type`, `dev` and `af_packet_net`:
  global `ptype_base[]`, or `ptype_all` / `ptype_specific` in `struct net` or
  in `struct net_device`.
- `list_func` in `struct packet_type`: called for a batch instead of `func`
  when set (`__netif_receive_skb_list_ptype()`); IPv4 and IPv6 set it to
  `ip_list_rcv()` and `ipv6_list_rcv()`, so a check added only to `ip_rcv()`
  misses batched packets.
- `udp4_lib_lookup()`: takes a reference; built only under
  `CONFIG_NF_TPROXY_IPV4` or `CONFIG_NF_SOCKET_IPV4`.
- `SOCK_RCU_FREE`: the flag that makes an unreferenced lookup result usable
  inside the RCU section; `sk_is_refcounted()` in `include/net/sock.h` tests
  it.
- `struct net_device` instance lock: mutex `lock`, taken after RTNL. On
  devices where `netdev_need_ops_lock()` (`include/net/netdev_lock.h`)
  returns true, `netdev_lock_ops()` takes it around driver callbacks; on
  other devices `netdev_lock_ops()` does nothing.
- `__dev_open()` in `net/core/dev.c`: asserts RTNL, then
  `netdev_assert_locked_ops_compat()`, so on an ops-locked device both locks
  are held around `ndo_open`.

## Where to look

**Core files**

| Job | File in this tree |
|---|---|
| Software segmentation | `net/core/gso.c` holds `__skb_gso_segment()` and `skb_mac_gso_segment()`; `skb_segment()` and `skb_segment_list()` are in `net/core/skbuff.c` |
| Helpers that take the device instance lock | `netdev_lock()` and `netdev_unlock()`: `include/linux/netdevice.h`. Conditional and assert forms such as `netdev_lock_ops()`: `include/net/netdev_lock.h`. `dev_` wrappers around `netif_` functions: `net/core/dev_api.c`. There is no net/core/netdev_lock.c |
| What the `net/core/dev_api.c` wrappers lock | Each wrapper around a `netif_` function except `dev_set_threaded()` calls `netdev_lock_ops()`, which takes the lock only when `netdev_need_ops_lock()` is true; `dev_set_threaded()` calls `netdev_lock()` unconditionally |
| Socket system calls | `net/socket.c`; the compat entry points are in `net/compat.c` |
| Datagram helpers | `net/core/datagram.c`; there is no include/net/datagram.h, the prototypes are in `include/linux/skbuff.h`, except `__sk_queue_drop_skb()` in `include/net/sock.h` |
| Drop reason strings | `drop_reasons[]` in `net/core/skbuff.c`, expanded by the preprocessor from `DEFINE_DROP_REASON()` in `include/net/dropreason-core.h`; no file is generated at build time |
| Qdisc drop reasons | separate `enum qdisc_drop_reason` in `include/net/dropreason-qdisc.h`, not part of `enum skb_drop_reason` |

**Netdev conventions**

| Rule | Strength | Where |
|---|---|---|
| Local variable order | Stated as "a convention", given as an imperative; no word of refusal | `Documentation/process/maintainer-netdev.rst` |
| `guard()` | Discouraged in a function longer than 20 lines; plain lock/unlock "(weakly) preferred" | `Documentation/process/maintainer-netdev.rst` |
| `__free()` | Allowed when building APIs and helpers; direct use in core and drivers discouraged | `Documentation/process/maintainer-netdev.rst` |
| `devm_` helpers | Allowed with no condition: "not the preferred style of implementation, merely an acceptable one" | `Documentation/process/maintainer-netdev.rst` |
| Stand-alone clean-up patches | Discouraged, not refused | `Documentation/process/maintainer-netdev.rst` |
| Exports meant only for the core | Allowed under a condition on who uses the symbol | `Documentation/networking/netdevices.rst` |

- None of the `Documentation/process/maintainer-netdev.rst` rules in the table
  is worded as a refusal; where the document objects, its word is
  "discouraged" or "discourages".
- Scope-based cleanup: the document sets no condition about maintainer agreement
  or about code that already uses it.
- Clean-up patches: the discouraged examples are `checkpatch.pl` and trivial
  style fixes, variable-order fixes and `devm_` conversions.
- Spelling and grammar fixes: "not discouraged", so a typo-only patch is not a
  clean-up in this sense.
- `Documentation/process/maintainer-netdev.rst`: has no text on exports, symbol
  namespaces or core-only symbols.
- `NETDEV_INTERNAL` section of `Documentation/networking/netdevices.rst`:
  symbols "can only be used in networking core and drivers which exclusively
  flow via the main networking list and trees".
- `NETDEV_INTERNAL` section: states who may use the symbols and says nothing
  about `MODULE_IMPORT_NS()`.
- EXPORT_IPV6_MOD does not exist in this tree; core-only exports are written
  `EXPORT_SYMBOL_NS_GPL(sym, "NETDEV_INTERNAL")`, for example in
  `net/core/dev.c`.

## Buffer layout

**Linear area and paged data**

- `pskb_may_pull_reason()`: reports `SKB_DROP_REASON_PKT_TOO_SMALL` when
  `len > skb->len`, and `SKB_DROP_REASON_NOMEM` for every
  `__pskb_pull_tail()` failure, whatever its cause.
- **Potentially unsafe usage**: `pskb_may_pull()` on an skb that may be
  shared (`skb->users` above 1).
  - Unsafe: when the head has to be reallocated (not enough tailroom for the
    pulled bytes, or `skb_cloned()`); `pskb_expand_head()` does
    `BUG_ON(skb_shared(skb))`.
  - Safe: after `skb_share_check()`, as `ip_rcv_core()` in
    `net/ipv4/ip_input.c` does before its first `pskb_may_pull()`.
- **Potentially unsafe usage**: `skb_header_pointer()` with an offset that
  can be negative.
  - Unsafe: when nothing limits the offset to the headroom;
    `__skb_header_pointer()` tests only `hlen - offset >= len`, so it returns
    `skb->data + offset` with no test against `skb->head`.
  - Safe: `skb_header_pointer_careful()`, which returns NULL when
    `-offset > skb_headroom(skb)`, as `u32_classify()` in
    `net/sched/cls_u32.c` does.
  - Safe: an offset built from `skb_mac_offset()`, which is
    `skb->head + skb->mac_header - skb->data` and so never points before
    `skb->head`, as `vlan_get_tci()` in `net/packet/af_packet.c` does.
- `skb_pointer_if_linear()`: returns `skb->data + offset` or NULL, with no
  copy and no pull; it rejects a negative offset through its unsigned compare.

**Page fragments**

- `struct skb_frag` in `include/linux/skbuff.h`: `netmem_ref netmem`, then
  `unsigned int len`, then `unsigned int offset`.

| Accessor | On a `struct net_iov` fragment |
|---|---|
| `skb_frag_address()` | NULL |
| `skb_frag_address_safe()` | NULL |
| `skb_frag_net_iov()` | the `struct net_iov *`; NULL on an ordinary page |
| `skb_frag_phys()` | no test; passes NULL to `page_to_phys()` |
| `skb_frag_foreach_page()` | no test; does pointer arithmetic on the NULL from `skb_frag_page()` |
| `netmem_to_page()` | `WARN_ON_ONCE()`, then NULL |
| `__netmem_to_page()` | no test; casts the tagged word |

- `skb_frag_address()` on a highmem page with no mapping: adds the offset to
  the NULL from `page_address()`; only `skb_frag_address_safe()` tests for it.
- `skb_page_unref()` in `include/linux/skbuff_ref.h`: with `recycle` set it
  still calls `put_netmem()` when `napi_pp_put_page()` returns false
  (the netmem is not a page-pool one) or without `CONFIG_PAGE_POOL`.
- `skb_frag_unref()`: does nothing when `skb_zcopy_managed()` is true.

**Unreadable payload**

- There is no skb_frag_set_unreadable here; `__skb_fill_netmem_desc()` in
  `include/linux/skbuff.h` sets `skb->unreadable` when
  `netmem_is_net_iov()` is true, for both `NET_IOV_DMABUF` and
  `NET_IOV_IOURING`.
- `xdp_update_skb_frags_info()` in `include/net/xdp.h`: sets the bit from
  `XDP_FLAGS_FRAGS_UNREADABLE` for skbs built from an XDP buffer.
- `skb_frag_fill_netmem_desc()` and `__skb_fill_netmem_desc_noacc()`: do not
  set the bit; `xdp_buff_add_frag()` marks a net_iov itself with
  `xdp_buff_set_frag_unreadable()`.
- `skb->unreadable`: one bit for the whole skb, inside the `headers` group
  of `struct sk_buff`, so `__copy_skb_header()` carries it to clones and
  copies.
- `___pskb_trim()`: clears the bit once no fragment and no `frag_list`
  remains.
- The test in `skb_copy_bits()` and its siblings sits after the linear part
  and before both the `frags[]` loop and the `frag_list` walk, so the bit on
  the parent blocks the `frag_list` too.
- There is no __skb_checksum() in this tree; `skb_checksum()` holds the
  test.

| Operation | On an unreadable skb |
|---|---|
| `skb_checksum()`, `skb_crc32c()` past the head | `WARN_ON_ONCE()`, return 0 |
| `skb_copy_and_csum_bits()` past the head | returns 0, no warning |
| `skb_checksum_help()` | `-EFAULT`, after its `CHECKSUM_COMPLETE` and GSO tests |
| `pskb_trim_rcsum_slow()`, `CHECKSUM_COMPLETE` | `-EFAULT` if `len > skb_headlen()`, else sets `CHECKSUM_NONE` |
| `pskb_may_pull_reason()` past the head | `SKB_DROP_REASON_NOMEM` |
| `skb_linearize()`, `skb_linearize_cow()` | `-ENOMEM` |
| `skb_cow_data()` with `nr_frags` or cloned | `-ENOMEM` |
| `skb_ensure_writable()` past the head | `-ENOMEM` |
| `skb_copy_ubufs()` | `-EFAULT` |
| `skb_splice_bits()` | splices the linear part, then stops; no error |
| `skb_seq_read()` | returns 0 after the linear part |
| `skb_zerocopy()` | `-EFAULT` if the source head became frag 0 and bytes remain, or if its `skb_copy_bits()` call goes past the head; else shares frags and sets the bit on `to` |
| `skb_condense()` | leaves the frags in place |
| `zerocopy_fill_skb_from_iter()` | `-EFAULT` |
| `tcp_can_collapse()`, `tcp_collapse()` | skip the skb |

- `skb_gro_receive()`, `skb_segment()`, `skb_shift()` and
  `pskb_expand_head()`: have no `skb_frags_readable()` test in their bodies.
- `net/core/filter.c` and `net/core/gro.c`: contain no
  `skb_frags_readable()` test.
- `validate_xmit_unreadable_skb()` in `net/core/dev.c`: `dev->netmem_tx`
  holds an `enum netmem_tx_mode` value; `NETMEM_TX_NO_DMA` passes every skb,
  `NETMEM_TX_NONE` frees an unreadable one, and `NETMEM_TX_DMA` frees it
  only when `frags[0]` is a devmem net_iov bound to another device.
- Outside the core, search for `skb_frags_readable`; for example
  `net/packet/af_packet.c` caps the snap length at `skb_headlen()`.

**Buffer headroom**

- `napi_alloc_skb()`: reserves `NET_SKB_PAD + NET_IP_ALIGN`;
  `__netdev_alloc_skb()` reserves `NET_SKB_PAD` only.
- `NET_SKB_PAD` on s390: 32, set in `arch/s390/include/asm/cache.h`, though
  `L1_CACHE_BYTES` is 256 there.
- `LL_RESERVED_SPACE()`: covers `hard_header_len` and `needed_headroom`
  only; `needed_tailroom` is not in it.
- `LL_RESERVED_SPACE()` is `((sum) & ~(HH_DATA_MOD - 1)) + HH_DATA_MOD`: the
  result is always above the sum, and a sum that is already a multiple of 16
  gains 16.
- `LL_RESERVED_SPACE_EX()`: same formula with the header length supplied by
  the caller; `net/packet/af_packet.c` uses it with a value it read once.
- `__skb_push()`: has no underflow check unless `CONFIG_DEBUG_NET` is set,
  where it only warns; `skb_push()` is the one that calls
  `skb_under_panic()`.
- `skb_cow_head()`: grows the head by the shortfall rounded up to a multiple
  of `NET_SKB_PAD`.
- **Potentially unsafe usage**: `skb_expand_head()` to make room before a
  push.
  - Unsafe: when the headroom is already enough; it does `WARN_ONCE()` and
    returns the skb unchanged, so a cloned header stays shared.
  - Safe: called only under `skb_headroom(skb) < hh_len`, as
    `ip_finish_output2()` in `net/ipv4/ip_output.c` does.
- Metadata: `skb_metadata_len()` bytes ending at `skb_mac_header()` live in
  the headroom, and a header written after `skb_push()` overwrites them.
- To keep the metadata across an inserted header: ask `skb_cow_head()` for
  the metadata length as well, then call `skb_postpush_data_move()` after
  `skb_push()`, as `__vlan_insert_inner_tag()` in `include/linux/if_vlan.h`
  does.
- `skb_data_move()`: clears the metadata with `WARN_ON_ONCE()` when
  `skb->data` was not at `skb_mac_header()` before the push, or when the
  headroom cannot hold the metadata.

## Data pointers and header access

**Put, push and pull**

- `skb_put()` and `__skb_put()`: both run `SKB_LINEAR_ASSERT()`, which is
  `BUG_ON(skb_is_nonlinear(skb))`, unconditional. `__skb_put()` has no other
  check and no `DEBUG_NET_WARN_ON_ONCE()`.
- `__skb_push()`: `DEBUG_NET_WARN_ON_ONCE(len > INT_MAX)` and
  `DEBUG_NET_WARN_ON_ONCE(skb->data < skb->head)`. Both only warn, and only
  under `CONFIG_DEBUG_NET`; the push still happens.
- `__skb_pull()`: `DEBUG_NET_WARN_ON_ONCE(len > INT_MAX)`, then after
  `skb->len -= len` an unconditional `BUG()` when `skb->len < skb->data_len`.
  It does not compare `len` with `skb->len`.
- `__skb_pull()` on a linear skb: `skb->data_len` is 0, so the `BUG()` test
  is never true and an over-long `len` wraps `skb->len` silently.
- `skb_pull()` on a nonlinear skb with `skb_headlen() < len <= skb->len`:
  passes the test in `skb_pull_inline()` and then hits the `BUG()` in
  `__skb_pull()`. NULL is returned only for `len > skb->len`.

**Making headers linear**

- Unreadable frags: `__pskb_pull_tail()` returns NULL first when
  `!skb_frags_readable(skb)`; `pskb_may_pull_reason()` reports this as
  `SKB_DROP_REASON_NOMEM`.
- `SKB_DROP_REASON_NOMEM` covers every NULL from `__pskb_pull_tail()`:
  `pskb_expand_head()` failing (allocation or `skb_orphan_frags()`),
  `skb_clone()` of a shared `frag_list` member, `pskb_pull()` on a
  `frag_list` member.
- Copy from frags: not a failure return. `__pskb_pull_tail()` wraps
  `skb_copy_bits()` in `BUG_ON()`.
- `pskb_inet_may_pull()` with a `skb->protocol` other than `ETH_P_IP` or
  `ETH_P_IPV6`: uses length 0, which still pulls `skb_network_offset(skb)`
  bytes and can fail.
- `pskb_inet_may_pull()` without `CONFIG_IPV6`: the `ETH_P_IPV6` case is
  compiled out, so an IPv6 skb gets length 0.
- `skb_vlan_inet_prepare()` in `include/net/ip_tunnels.h`: the variant for
  skbs that may carry VLAN tags. It pulls MAC plus base IP header from
  `skb->data` and sets the network header itself.

**Lengths from the wire**

- There is no __udp4_lib_rcv() here; `udp_rcv()` in `net/ipv4/udp.c` holds
  the `ulen > skb->len` and `ulen < sizeof(*uh)` checks.
- `ip_rcv_core()`: `ip_fast_csum()` runs after the `iph->ihl*4` pull and the
  reload, not before.
- `__tun_vnet_hdr_get()` in `drivers/net/tun_vnet.h`: where the user-supplied
  `hdr_len` is rejected when larger than `iov_iter_count(from)`.
- **Potentially unsafe usage**: `skb_pull()` or `__skb_pull()` with a wire
  length checked only against `skb->len`.
  - Unsafe: on a skb that may be nonlinear; `len > skb_headlen()` reaches the
    `BUG()` in `__skb_pull()`.
  - Safe: after `pskb_may_pull(skb, len)`, as `xfrm4_remove_beet_encap()` in
    `net/xfrm/xfrm_input.c` does before `__skb_pull(skb, phlen)`.
  - Safe: `pskb_pull()`, which calls `pskb_may_pull()` itself and returns
    NULL on failure.
- **Unsafe usage**: `skb_put()` with a length from a subtraction that can go
  negative.
  - Unsafe: with `NET_SKBUFF_DATA_USES_OFFSET` (`BITS_PER_LONG > 32`)
    `skb->tail` is `unsigned int`; `skb->tail += len` wraps backwards, so for
    a small negative value the `skb->tail > skb->end` test is false and
    `skb_over_panic()` is not called.
  - Safe: compare the operands before subtracting, as `mangle_contents()` in
    `net/netfilter/nf_nat_helper.c` does with `rep_len > match_len` before
    `skb_put(skb, rep_len - match_len)`.

**Dereferencing headers**

- `skb_header_pointer()` in `include/linux/skbuff.h`: read-only alternative.
  Offset counts from `skb->data`; returns a pointer into the head when the
  bytes are linear, else copies to the caller's buffer; NULL when short.
- Transmit paths need the pull too: a tunnel `ndo_start_xmit` handler cannot
  assume the inner IP header is linear. `ipgre_xmit()` in
  `net/ipv4/ip_gre.c` calls `pskb_inet_may_pull()` first.
- **Potentially unsafe usage**: dereferencing `ip_hdr(skb)` with no pull in
  the same function.
  - Unsafe: when some path to this point has no earlier function that pulled
    that header.
  - Safe: when an earlier function on the path pulled it; `udp_rcv()` reads
    `ip_hdr(skb)->saddr` after `ip_rcv_core()` pulled `iph->ihl*4`.

**Pointers after reallocation**

- `CONFIG_FAIL_SKB_REALLOC` (`lib/Kconfig.debug`, needs
  `FAULT_INJECTION_DEBUG_FS`): the debugging aid. `skb_might_realloc()` in
  `net/core/skb_fault_injection.c` calls
  `pskb_expand_head(skb, 0, 0, GFP_ATOMIC)` when the fault attribute fires.
- `skb_might_realloc()` call sites: `pskb_may_pull_reason()`, `pskb_trim()`
  and `pskb_trim_rcsum()`, before their fast-path tests. It is not called
  from `__pskb_pull_tail()`.
- `skb_might_realloc()` controls: debugfs directory `fail_skb_realloc` with a
  `devname` filter file, and the `fail_skb_realloc=` boot parameter.
- `__pskb_pull_tail()`: calls `pskb_expand_head()` when tailroom is short or
  when `skb_cloned()`, even with enough tailroom.
- `pskb_trim()` without the fault injection: reaches `pskb_expand_head()`
  only via `___pskb_trim()`, so only when `skb->data_len` is non-zero and the
  skb is cloned.
- `skb_realloc_headroom()`: reallocates a clone or copy and returns it; the
  head of the skb passed in is untouched.
- Further direct callers of `pskb_expand_head()` that are easy to miss:
  `__skb_grow()`, `__skb_pad()`, `skb_ensure_writable_head_tail()`. Search
  for `pskb_expand_head(` and `__pskb_pull_tail(` for the rest.
- `skb_header_pointer()` result: points into the head when the bytes were
  linear, so it goes stale like any other pointer.

**Header accessors in xfrm**

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

**Alignment of wire headers**

- `struct virtio_net_hdr_v1_hash` in `include/uapi/linux/virtio_net.h`: the
  hash is two `__le16` fields, `hash_value_lo` and `hash_value_hi`. There is
  no `__le32` member, so all three nested structs have 2-byte alignment.
- `virtio_net_hash_value()` in `drivers/net/virtio_net.c`: reassembles the
  two halves.
- Build-time check: two `BUILD_BUG_ON()` lines in `xmit_skb()` require
  `__alignof__(*hdr)` to equal `__alignof__(hdr->hash_hdr)` and
  `__alignof__(hdr->hash_hdr.hdr)`.
- The check covers alignment only. `drivers/net/virtio_net.c` has no
  `BUILD_BUG_ON()` or `static_assert()` on the size of these structs.
- Why equal alignment is required: `xmit_skb()` sets `hdr` to
  `skb->data - vi->hdr_len`, and `vi->hdr_len` is the size of whichever of
  four formats was negotiated, while `can_push` tests the alignment of
  `skb->data` only.
- Casts that rely on it: `virtio_net_hdr_tnl_from_skb()` in
  `include/linux/virtio_net.h` casts the tunnel header to
  `struct virtio_net_hdr`; `tun_xdp_one()` casts the other way.
- **Unsafe usage**: appending a member with alignment above 2 bytes, such as
  a `__le32`, to `struct virtio_net_hdr_v1_hash` or
  `struct virtio_net_hdr_v1_hash_tunnel`.
  - Unsafe: it raises the outer alignment above that of
    `struct virtio_net_hdr_v1`; the `BUILD_BUG_ON()` in `xmit_skb()` fails.
  - Safe: split the value into `__le16` halves, as `hash_value_lo` and
    `hash_value_hi` do; `virtio_net_hash_value()` joins them.

## Sharing and writing

**Shared and cloned**

- `skb_cloned()`: tests `skb->cloned` and that the low half of `dataref` is not
  1. Nothing clears `cloned` on the survivor when its sibling is freed, so the
  bit alone does not say the data is shared.
- `cb[]`: each clone has its own; `__copy_skb_header()` copies the contents at
  clone time.
- `pskb_expand_head()` in `net/core/skbuff.c`: has `BUG_ON(skb_shared(skb))` and
  accepts a clone. Helpers that reallocate the head through it inherit both,
  for example `skb_cow_head()`, `skb_unclone()`, `skb_ensure_writable()` and
  `__pskb_pull_tail()`.
- `CONFIG_FAIL_SKB_REALLOC`: when the fault attribute fires,
  `skb_might_realloc()` calls `pskb_expand_head()` from
  `pskb_may_pull_reason()`, `pskb_trim()` and `pskb_trim_rcsum()` even when the
  bytes are already linear, so the `BUG_ON()` and the stale-pointer cases can
  be reached on any call.

**Clone and copy**

| Function | Headroom bytes | `frag_list` members | `mac_len`, `hdr_len` | Returns NULL also when |
|---|---|---|---|---|
| `skb_clone()` | shared | shared | `mac_len` copied; `hdr_len` is `skb_headroom()` if the original has `nohdr`, else copied | `skb_orphan_frags()` fails |
| `pskb_copy()` | not copied; same size reserved | `skb_get()` on each: shared, not cloned | both 0 | `skb_orphan_frags()` or `skb_zerocopy_clone()` fails |
| `skb_copy()` | copied | data copied into the head | both 0 | `skb_frags_readable()` is false, or `gso_type` has `SKB_GSO_FRAGLIST` |
| `skb_copy_expand()` | the part nearest `data` that fits the new headroom | data copied into the head | both 0 | same as `skb_copy()` |

- `pskb_copy()`: header offsets are copied unchanged, so an offset that points
  before `data`, such as a pulled MAC header, points at bytes that were not
  copied.
- Original after `skb_clone()`: `cloned` is set and `dataref` raised.
- `skb_orphan_frags()`: runs on the original in `skb_clone()` and
  `__pskb_copy_fclone()`, and can replace its zerocopy frags with copies.
- New `struct skb_shared_info` of the three copies: `skb_copy_header()` copies
  only `gso_size`, `gso_segs` and `gso_type`. For example `tx_flags`,
  `hwtstamps`, `tskey` and `meta_len` start at 0, so skb metadata is dropped.
- `pskb_copy()`: also carries `SKBFL_SHARED_FRAG` over from the original.

**Getting a private buffer**

- `skb_unshare()`: copies with `skb_copy()`, not `pskb_copy()`.
- `skb_unshare()` failure: also happens with memory available, when
  `skb_copy()` refuses unreadable frags or `SKB_GSO_FRAGLIST`. The original is
  freed with `kfree_skb()` in that case too.
- `skb_share_check()`: the clone has the same `head` and `data`, so pointers
  into packet data stay valid. Only the `struct sk_buff` pointer changes.
- `skb_unclone()`: makes the head and `struct skb_shared_info` private. Page
  frags stay shared with the former clone by page reference, and each
  `frag_list` member gets `skb_get()`, so it becomes `skb_shared()`.

**Making data writable**

- `skb_cow_head()` success: no other holder counts the header part, so headers
  in front of the payload may be rewritten as well as pushed.
  `__vlan_insert_inner_tag()` in `include/linux/if_vlan.h` moves the MAC header
  after it.
- `skb_cow_head()`: the payload may still be shared with payload-only holders.
  It makes no test against `hdr_len`; `skb_clone_writable()`, used by
  `skb_ensure_writable()`, does.
- `skb_cow_data()`: pulls every page frag into the head whenever
  `nr_frags` is not 0, cloned or not. It fails with `-ENOMEM` when
  `__pskb_pull_tail()` refuses unreadable frags.
- `skb_ensure_writable_head_tail()` in `net/core/skbuff.c`: takes the skb and a
  `struct net_device`, and reallocates when the buffer is cloned or short of
  `needed_headroom` or `needed_tailroom`. It pulls nothing. `dsa_user_xmit()`
  uses it.
- `skb_expand_head()` in `net/core/skbuff.c`: grows headroom on transmit for a
  buffer that may be shared. It clones a shared buffer, keeps `sk` on the
  replacement, and frees the buffer and returns NULL on failure.
  `ip_finish_output2()` uses it.

**Writing to packet data**

- `ip_rcv()`: does not call `skb_share_check()` itself; `ip_rcv_core()` in
  `net/ipv4/ip_input.c` does.
- `iptunnel_handle_offloads()`: calls `skb_header_unclone()`, and only for a GSO
  buffer. It reserves no headroom.
- A queued buffer can be shared: `__skb_try_recv_from_queue()` takes a
  reference for `MSG_PEEK` and leaves the buffer on the queue.
- **Potentially unsafe usage**: changing `struct sk_buff` fields while
  `skb_shared()` is true.
  - Unsafe: when the change is still there after the function returns, or the
    buffer is queued. The other holder sees the new `data` and `len`.
  - Safe: after `skb_share_check()`, on the pointer it returns, as
    `ip_rcv_core()` does.
  - Safe: when `data` and `len` are put back before returning, as `packet_rcv()`
    does. The other holder is the caller of `deliver_skb()`, which does not run
    until the handler returns.
- **Potentially unsafe usage**: writing packet bytes while `skb_cloned()` is
  true.
  - Unsafe: when `skb_clone_writable()` is false for the range. A tap's clone or
    the original in a retransmit queue holds the same bytes.
  - Safe: when `skb_ensure_writable()` has returned 0 for the range. It skips the
    copy if `skb_clone_writable()` holds. `nf_nat_ipv4_manip_pkt()` and
    `__skb_vlan_pop()` do this.
- **Potentially unsafe usage**: writing a GSO field of
  `struct skb_shared_info`, such as `gso_type`, on a clone.
  - Unsafe: when `skb_header_cloned()` is true. The other clone uses the same
    `struct skb_shared_info`.
  - Safe: after `skb_header_unclone()`, as `iptunnel_handle_offloads()` does
    before it sets bits in `gso_type`.
- **Potentially unsafe usage**: writing into page fragments in place.
  - Unsafe: when `skb_cloned()` or `skb_has_shared_frag()` is true. Another
    buffer or user space holds the same pages.
  - Unsafe: when only `skb_cloned()` was tested. `pskb_copy()` and
    `skb_unclone()` leave pages shared by reference with `skb_cloned()` false.
  - Safe: after `skb_cow_data()`, which leaves no page frags and copies
    `frag_list` members that are shared or cloned.

## Per-buffer state

**Checksum state**

| `ip_summed` | Receive: easy to miss | Transmit: easy to miss |
|---|---|---|
| `CHECKSUM_NONE` | after `skb_checksum_init()`, `skb->csum` holds the pseudo-header sum that `__skb_checksum_complete()` adds; `csum_valid` set means already verified | nothing pending |
| `CHECKSUM_UNNECESSARY` | each validated checksum consumes one `csum_level`; at level 0 it becomes `CHECKSUM_NONE` with `csum_valid` set | same as `CHECKSUM_NONE` for a driver; on a GSO buffer accepted like `CHECKSUM_PARTIAL` |
| `CHECKSUM_COMPLETE` | `skb->csum` covers `skb->data` to the end at the moment of validation | `skb_checksum_help()` only sets `CHECKSUM_NONE`, packet untouched |
| `CHECKSUM_PARTIAL` | verified only while `skb_checksum_start_offset(skb) >= 0` | on a GSO buffer the expected state |

- `CHECKSUM_UNNECESSARY` level use: see `__skb_checksum_validate_needed()` and
  `__skb_decr_checksum_unnecessary()` in `include/linux/skbuff.h`.
- `CHECKSUM_PARTIAL` on receive: `skb_csum_unnecessary()` holds the offset
  test; `skb_postpull_rcsum()` sets `CHECKSUM_NONE` once a pull passes
  `csum_start`.
- `__skb_checksum_validate_complete()`: overwrites `skb->csum` with the
  pseudo-header sum unless `ip_summed` is `CHECKSUM_COMPLETE` and the sum
  validated.
- `__skb_checksum_complete()` in `net/core/skbuff.c`: on an unshared buffer it
  stores the full sum in `skb->csum` and sets `CHECKSUM_COMPLETE` with
  `csum_complete_sw`.
- GSO buffer on transmit with `ip_summed` neither `CHECKSUM_PARTIAL` nor
  `CHECKSUM_UNNECESSARY`: `netif_needs_gso()` forces software segmentation;
  `__skb_gso_segment()` calls `skb_warn_bad_offload()` only if that is still
  so after the callbacks returned and the result is neither an error nor the
  original buffer, and `tcp4_gso_segment()` sets `CHECKSUM_PARTIAL` itself.
- `skb_checksum_help()` on unreadable frags (`skb_frags_readable()` false):
  returns `-EFAULT`, `ip_summed` stays `CHECKSUM_PARTIAL`.
- `skb_crc32c_csum_help()`: tests `ip_summed` itself; returns 0 and resolves
  nothing for a non-`CHECKSUM_PARTIAL` or GSO buffer.
- **Unsafe usage**: calling `skb_checksum_help()` or
  `skb_csum_hwoffload_help()` on a buffer whose `ip_summed` is `CHECKSUM_NONE`
  or `CHECKSUM_UNNECESSARY`; neither tests for `CHECKSUM_PARTIAL`, and
  `csum_start` / `csum_offset` share a union with `skb->csum`.
  - Safe: test `skb->ip_summed == CHECKSUM_PARTIAL` first, as
    `ip_do_fragment()` and `validate_xmit_skb()` do.
  - Safe: `CHECKSUM_COMPLETE`, which `skb_checksum_help()` handles before it
    reads the offsets.

**Socket ownership of a buffer**

- `skb_set_owner_sk_safe()` in `include/net/sock.h`: tests only that `sk` is
  non-NULL and that `refcount_inc_not_zero(&sk->sk_refcnt)` succeeds; it does
  not call `sk_fullsock()` or `sk_is_refcounted()`.
- `skb_set_owner_sk_safe()` returning false: the buffer is not orphaned and
  keeps its previous owner and destructor; the result is `__must_check`.
  `skb_orphan_partial()` then calls `skb_orphan()`.
- **Unsafe usage**: `skb_set_owner_sk_safe()` on a request or timewait socket;
  its destructor `sock_efree()` calls `sock_put()`, which ends in `sk_free()`.
  - Safe: `skb_set_owner_edemux()`, whose `sock_edemux()` calls
    `sock_gen_put()`, as `tcp_make_synack()` does with a request socket.
  - Safe: a full socket, as `tcp_read_skb()` passes.
- `skb_set_owner_edemux()`: orphans the buffer first, returns void, and on a
  failed `refcount_inc_not_zero()` leaves the buffer unowned.
- `skb_set_owner_w()` on a non-full socket: takes the
  `skb_set_owner_edemux()` path, so `skb->sk` can be NULL afterwards.
- Without `CONFIG_INET`: `skb_set_owner_edemux()` is not defined,
  `sock_edemux` is a macro for `sock_efree`, and `skb_set_owner_w()` has no
  non-full branch.
- `sock_pfree()` in `net/core/sock.c`: destructor for a socket that may be
  attached with no reference; it does nothing when `sk_is_refcounted()` is
  false. `udp_v4_early_demux()` attaches a `SOCK_RCU_FREE` socket this way.
- `bpf_sk_assign()` in `net/core/filter.c`: takes `refcount_inc_not_zero()`
  only when `sk_is_refcounted()`, then installs `sock_pfree()`.
- `skb_set_owner_w()` and `sock_alloc_send_pskb()`: neither takes nor asserts
  the socket lock.
- `skb_set_owner_w()` on a full socket: adds to `sk_wmem_alloc` and cannot
  fail; on a zero count `__refcount_add()` warns and saturates the count.
  `sock_put()` calls `sk_free()`, which drops the bias, only when `sk_refcnt`
  reaches zero.
- `skb_set_owner_r()`: takes no reference of any kind; `sock_rfree()`
  dereferences `skb->sk`, so the socket's destructor has to purge the queue
  first, as `inet_sock_destruct()` does.

**Segmentation state**

- `SKB_GSO_DODGY` on transmit: enforced by `net_gso_ok()` through
  `skb_gso_ok()` in `netif_needs_gso()`; `gso_features_check()` does not test
  the bit.
- Devices that set `NETIF_F_GSO_ROBUST` (search `drivers/net/`; for example
  `drivers/net/virtio_net.c`): when `netif_needs_gso()` is false they receive
  the buffer with `SKB_GSO_DODGY` still set and no `gso_segment` callback run.
- `qdisc_pkt_len_segs_init()`: called from `__dev_queue_xmit()` for every
  buffer; for `SKB_GSO_DODGY` it recomputes `gso_segs`, and a bad header drops
  the buffer with `SKB_DROP_REASON_SKB_BAD_GSO`.
- NULL return: produced by `tcp_gso_segment()`, `__udp_gso_segment()` and
  `sctp_gso_segment()` when `skb_gso_ok(skb, features | NETIF_F_GSO_ROBUST)`;
  they do not test `SKB_GSO_DODGY`, so a buffer without the bit that passes
  `skb_gso_ok()` also gets NULL and a recomputed `gso_segs`.
- `inet_gso_segment()`: makes no such test; it passes NULL through and
  restores `skb->network_header`.
- Other `SKB_GSO_DODGY` handling, found by searching the name: for example
  `dev_gro_receive()` flushes such a buffer, `tcp4_gso_segment()` refuses
  `skb_segment_list()` for it, and `__pskb_pull_tail()` sets the bit.
- `__skb_gso_segment()`: never frees the original buffer, on any return; the
  caller frees it on error and after a list is returned.
- Returned list: its head can be the original buffer; `skb_segment_list()`
  returns it after `skb_get()`. Release the original with `consume_skb()`,
  as `validate_xmit_skb()` does, never by assuming it is distinct.
- `__skb_gso_segment()`: calls `skb_reset_mac_header()` and
  `skb_reset_mac_len()` itself; the caller does not have to.
- `features` containing `NETIF_F_GSO_PARTIAL`: `__skb_gso_segment()` then
  dereferences `skb->dev`.

**Control block lifetime**

- `skb_orphan()`: does not write `skb->cb`; it runs `skb->destructor` at that
  moment, so a destructor can run long before the buffer is freed and sees
  whatever the current holder has put in `cb`.
- Destructor reading `cb`: done in-tree by `unix_wfree()` in
  `net/unix/af_unix.c`, installed by `unix_scm_to_skb()`; it calls
  `unix_destruct_scm()`, which reads `UNIXCB()`.
- `skb_scrub_packet()`: leaves `cb` alone, and calls `skb_ext_reset()`.
- skb extensions: do not always survive until free; `skb_ext_reset()` drops
  them, for example in `skb_scrub_packet()` and `napi_reuse_skb()`.
- `enum skb_ext_id`: every id is under its own configuration option; there is
  no general-purpose id. Without `CONFIG_SKB_EXTENSIONS` the enum is not
  defined, `skb_ext_reset()`, `skb_ext_del()`, `skb_ext_put()` and
  `skb_ext_copy()` are empty stubs, and `skb_ext_add()` and `skb_ext_find()`
  are not declared.
- `skb->sk` and `skb->destructor`: both cleared by `skb_orphan()`, and by
  `skb_steal_sock()` except in its syncookie request-sock branch.
- `skb_shinfo(skb)->destructor_arg`: lives in `struct skb_shared_info`, so
  every clone sees the same value; it shares a union with `xdp_frags_size`
  and `xdp_frags_truesize`.
- `msg_zerocopy_alloc()` in `net/core/skbuff.c`: keeps
  `struct ubuf_info_msgzc` in the `cb` of a buffer from `sock_omalloc()` that
  is handed to no other layer while the `struct ubuf_info` is referenced;
  `destructor_arg` of the data buffers points into that `cb`.
- `__skb_gso_segment()`: overwrites `cb` from `SKB_GSO_CB_OFFSET` (32) on;
  state carried across segmentation has to fit below it, as the
  `BUILD_BUG_ON()` in `ip_finish_output_gso()` checks.
- `skb_segment()`: copies the original's `cb` into every segment through
  `__copy_skb_header()`.

## Ownership and freeing

**Free functions**

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

**Drop reasons**

- Core reason: written by hand twice in `include/net/dropreason-core.h`, as an
  `FN()` line in `DEFINE_DROP_REASON` and as an entry of
  `enum skb_drop_reason` with its kernel-doc. The macro list generates only
  the names, not the enum.
- Order of the `FN()` list: need not match the enum. `drop_reasons` in
  `net/core/skbuff.c` uses designated initializers and
  `include/trace/events/skb.h` uses value/name pairs, so both key on the enum
  value.
- Enum entry without an `FN()` line: builds, and has no name. An `FN()` line
  without an enum entry does not build.
- Registration: not every subsystem registers. `SKB_DROP_REASON_SUBSYS_QDISC`
  has an entry in `enum skb_drop_reason_subsys` and no call to
  `drop_reasons_register_subsys()`; mac80211 and openvswitch do register.
- Qdisc reasons: a separate `enum qdisc_drop_reason` with its own list
  `DEFINE_QDISC_DROP_REASON` in `include/net/dropreason-qdisc.h`. Their names
  are printed by `trace_qdisc_drop()` (`include/trace/events/qdisc.h`).
- `__tcf_kfree_skb_list()` in `net/sched/sch_generic.c`: recognises a qdisc
  reason by its subsystem bits, fires `trace_qdisc_drop()` with it, and frees
  with `SKB_DROP_REASON_QDISC_DROP`.
- Unregistered or unnamed reason in `net_dm_packet_report_fill()`
  (`net/core/drop_monitor.c`): reported under the name of
  `SKB_DROP_REASON_NOT_SPECIFIED`.
- mac80211 reasons: in `net/mac80211/drop.h`, not in `include/net/mac80211.h`.
  The only mac80211 subsystem is `SKB_DROP_REASON_SUBSYS_MAC80211_UNUSABLE`;
  there is no SKB_DROP_REASON_SUBSYS_MAC80211_MONITOR.
- Values that are not drops, beyond `SKB_NOT_DROPPED_YET`, `SKB_CONSUMED` and
  `SKB_DROP_REASON_MAX`:
  - `SKB_DROP_REASON_SUBSYS_MASK`, a mask inside `enum skb_drop_reason`;
  - each subsystem's base value: `___RX_DROP_UNUSABLE`, `__OVS_DROP_REASON`,
    `__QDISC_DROP_REASON`;
  - the bounds `OVS_DROP_MAX` and `QDISC_DROP_MAX`, and `QDISC_DROP_UNSPEC`
    (0);
  - mac80211's `RX_CONTINUE` and `RX_QUEUED`, which alias `SKB_CONSUMED` and
    `SKB_NOT_DROPPED_YET`.

**Ownership on failure**

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

**Netfilter verdicts and ownership**

- `NF_STOLEN`: `nf_hook_slow()` returns `NF_DROP_GETERR(verdict)`, which is 0
  for a plain steal and a negative errno when the hook used
  `NF_DROP_REASON()`. In the second case the hook has already freed the
  buffer.
- `NF_QUEUE`, queueing failed: `nf_queue()` frees with `kfree_skb()` and
  returns 0, so `nf_hook_slow()` returns 0, not the error.
- `NF_QUEUE`, bypass: continues with the next hook only when `__nf_queue()`
  returned `-ESRCH` and `NF_VERDICT_FLAG_QUEUE_BYPASS` is set. Any other
  queueing error frees the buffer even with the flag.
- `NF_REPEAT` and `NF_STOP`: `nf_hook_slow()` has no case for them. The
  default case does `WARN_ON_ONCE(1)` and returns 0 without freeing the
  buffer.
- `nf_reinject()` in `net/netfilter/nfnetlink_queue.c`: the place that
  handles `NF_REPEAT` (runs the hook again) and `NF_STOP` (calls okfn, like
  `NF_ACCEPT`).
- `NF_HOOK()`: frees nothing itself. On 1 from `nf_hook()` it returns
  whatever okfn returns, so the buffer is gone on accept only if okfn consumes
  it.
- `NF_HOOK_LIST()`: never calls okfn. Buffers that got 1 stay on the list for
  the caller; the others are removed from it.

**After a buffer handoff**

- **Potentially unsafe usage**: reading or freeing the buffer after
  `dev_queue_xmit()` or `netif_rx()` returns.
  - Unsafe: when the caller holds no reference of its own. Every path of
    `__dev_queue_xmit()` and `enqueue_to_backlog()` in `net/core/dev.c`
    consumes the buffer, whatever the return value: it is queued, handed to
    the driver or a hook, or freed.
  - Safe: copy the value before the call and use only the copy, as
    `vlan_dev_hard_start_xmit()` in `net/8021q/vlan_dev.c`,
    `macvlan_start_xmit()` in `drivers/net/macvlan.c` and `loopback_xmit()` in
    `drivers/net/loopback.c` do with `len = skb->len`.
  - Safe: when the caller raised `skb->users` before the call, as
    `pktgen_xmit()` in `net/core/pktgen.c` does under `F_SHARED` around
    `dev_queue_xmit()`, `netif_receive_skb()` and `netdev_start_xmit()`.
    `kfree_skb_reason()` and `consume_skb()` drop one reference through
    `skb_unref()`.
  - Safe: after a callee that can refuse the buffer, when its return value
    says so, as in `veth_xmit()`, which touches the buffer only after
    `veth_forward_skb()` returned `NETDEV_TX_BUSY`; that value comes only from
    `veth_xdp_rx()`, when `ptr_ring_produce()` failed. `dev_queue_xmit()` and
    `netif_rx()` have no such value.
- `macvlan_queue_xmit()`: saves nothing. The saved length is in its caller,
  `macvlan_start_xmit()`, and is `skb->len` with no `ETH_HLEN` added.
- `iptunnel_xmit()` in `net/ipv4/ip_tunnel_core.c` and `ip6tunnel_xmit()` in
  `include/net/ip6_tunnel.h`: compute `pkt_len` themselves before
  `ip_local_out()` or `ip6_local_out()`, so a tunnel driver that calls them
  does not save the length.
- `ip_finish_output2()` and `neigh_resolve_output()`: save no length; they
  return the result of the transmit call and do not touch the buffer again.
- `pktgen_xmit()`: accounts bytes from `pkt_dev->last_pkt_size`, saved when
  the buffer was built.
- pktgen on a device without `IFF_TX_SKB_SHARING`: `clone_skb` above 0, and
  `burst` above 1 in `M_START_XMIT` mode, are refused with `-EOPNOTSUPP`.

**After a netfilter hook**

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

## Receive and transmit paths

**Receive path stages**

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

**Receive entry points**

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

**Packet handler delivery**

- There is no global `ptype_all` list; the only `ptype_all` lists are in
  `struct net_device` and `struct net`.
- `ETH_P_ALL` with neither `pt->dev` nor `pt->af_packet_net`: `ptype_head()`
  returns NULL, `dev_add_pack()` hits `WARN_ON_ONCE()` and registers nothing.
- `ptype_base[]` is the only global list, and holds only handlers with a
  specific type, no device and no `af_packet_net`.
- `ptype_head()` is called before `ptype_lock` is taken, and
  `__dev_remove_pack()` calls it again to find the list.
- **Unsafe usage**: changing `pt->type`, `pt->dev` or `pt->af_packet_net`
  while the handler is registered.
  - Unsafe: when the change makes `ptype_head()` pick another list;
    `__dev_remove_pack()` then searches that list, prints "not found" and
    leaves the entry linked.
  - Safe: remove, change the fields, add again, as `packet_do_bind()` in
    `net/packet/af_packet.c` does with `__unregister_prot_hook()` before it
    writes `po->prot_hook.type` and `po->prot_hook.dev`.
- `deliver_skb()` when `skb_orphan_frags_rx()` fails: returns `-ENOMEM`
  without calling that handler and without freeing; the buffer goes on to the
  later handlers.
- `dev_queue_xmit_nit()`: makes one `skb_clone()` for all transmit taps and
  hands it out through `deliver_skb()` (the last tap is called directly), so
  transmit taps share one buffer just as receive handlers do.

**Transmit path stages**

- No-queue path in `__dev_queue_xmit()`: `dev_xmit_recursion()` check, then
  `validate_xmit_skb()`, then `HARD_TX_LOCK()`; validation is outside the
  transmit lock on this path too.
- Recursion test on the no-queue path: `netif_tx_owned()`, not an open-coded
  compare of `xmit_lock_owner`; under `CONFIG_PREEMPT_RT` it tests the
  rt-mutex owner instead.
- `validate_xmit_skb()` first step: `validate_xmit_unreadable_skb()`, which
  frees a buffer with unreadable frags that the device cannot send.
- `validate_xmit_skb()`: segmentation and the linearize/checksum pair are
  alternatives; a buffer that `netif_needs_gso()` is segmented and skips
  `__skb_linearize()` and `skb_csum_hwoffload_help()` in this function.
- `validate_xmit_skb()` results: the buffer, NULL (freed; `tx_dropped`
  counted on the drop paths of `validate_xmit_skb()` itself), or
  `ERR_PTR(-EINPROGRESS)` when async xfrm crypto took it.
- **Unsafe usage**: testing the result of `validate_xmit_skb()` with `!skb`
  only; `ERR_PTR(-EINPROGRESS)` is then dereferenced.
  - Safe: `IS_ERR_OR_NULL()`, as `validate_xmit_skb_list()` and
    `__dev_queue_xmit()` do; the latter returns `NET_XMIT_SUCCESS` for
    `-EINPROGRESS`.
  - Safe: a NULL test on the result of `validate_xmit_skb_list()`, as
    `sch_direct_xmit()` does; that function skips `IS_ERR_OR_NULL()` entries
    and never returns an error pointer.
- Requeued buffers: `dequeue_skb()` clears `*validate` for `q->gso_skb`
  entries but sets it again when `xfrm_offload()` is non-NULL.
- `qdisc_pkt_len_segs_init()`: runs before `rcu_read_lock_bh()` and both
  egress hooks; on a bad GSO header `__dev_queue_xmit()` frees the buffer and
  returns `-EINVAL`.
- Locked qdisc in `__dev_xmit_skb()`: buffers are pushed on the lockless
  `q->defer_list`; the CPU that found the list empty takes the root lock and
  enqueues the whole list. `struct Qdisc` has no busylock field.
- `xmit_one()` tests `dev_nit_active_rcu()`; `dev_nit_active()` is the wrapper
  that takes `rcu_read_lock()` itself.
- Present in this tree, not gone: `netdev_pick_tx()` (called by
  `netdev_core_pick_tx()` when the driver has no `ndo_select_queue`) and
  `dev_queue_xmit_accel()` (inline in `include/linux/netdevice.h`).

| Name not in this tree | What does the job |
|---|---|
| dev_gso_segment | `skb_gso_segment()` called from `validate_xmit_skb()` |
| qdisc_pkt_len_init | `qdisc_pkt_len_segs_init()` |
| NETIF_F_LLTX | `lltx` bit in `struct net_device`, tested by `HARD_TX_LOCK()` |
| skb->xmit_more | `netdev_xmit_more()` |
| NETDEV_TX_LOCKED | nothing; `enum netdev_tx` has `NETDEV_TX_OK` and `NETDEV_TX_BUSY` |
| Qdisc busylock | `defer_list` and `defer_count` in `struct Qdisc` |

**Transmit return codes**

- Busy on a no-queue device: `__dev_queue_xmit()` returns `-ENETDOWN`, not
  `NET_XMIT_DROP`; it frees with `kfree_skb_list_reason()` and counts
  `tx_dropped`.
- Busy on a no-queue device after segmentation (`is_list`): the unsent
  segments are freed the same way but the return value is `NETDEV_TX_OK`.
- Stopped queue on a no-queue device: same free, count and `-ENETDOWN`,
  without the driver being called (`netif_xmit_stopped()`).
- `-ENETDOWN`: `__dev_queue_xmit()` sets it in two places, both on the
  no-queue path (busy or stopped queue, and recursion).
- Deactivated device: `dev_deactivate_queue()` installs `noop_qdisc`, and
  `noop_enqueue()` drops the buffer and returns `NET_XMIT_CN`.
- NET_XMIT_POLICED is not defined; the qdisc codes are `NET_XMIT_SUCCESS`,
  `NET_XMIT_DROP` and `NET_XMIT_CN`.
- `dev_requeue_skb()`: calls `__netif_schedule()` only for a locked qdisc;
  for `TCQ_F_NOLOCK` it sets `__QDISC_STATE_MISSED` instead.
- A requeue does not prove the driver returned `NETDEV_TX_BUSY`:
  `sch_direct_xmit()` requeues without calling the driver when
  `netif_xmit_frozen_or_stopped()`, and `dev_hard_start_xmit()` sets
  `NETDEV_TX_BUSY` itself when the queue stops with segments left.
- `NET_XMIT_SUCCESS` on a locked qdisc: `__dev_xmit_skb()` returns it as soon
  as the buffer is on a non-empty `q->defer_list`, before any enqueue.
- Enqueue result on a locked qdisc: the CPU that flushes the list returns it
  only when it enqueued exactly one buffer; otherwise `NET_XMIT_SUCCESS`.
- `NET_XMIT_DROP` from `__dev_xmit_skb()` also covers a `defer_list` longer
  than `net_hotdata.qdisc_max_burst` and a qdisc with
  `__QDISC_STATE_DEACTIVATED`.

## Socket references and kinds

**Socket reference counts**

- `skb_set_owner_w()` on a full socket: takes no `sk_refcnt`; it only adds
  `skb->truesize` to `sk_wmem_alloc`.
- `SK_WMEM_ALLOC_BIAS` in `include/net/sock.h`: the name of the initial 1 in
  `sk_wmem_alloc` that `sk_free()` drops.
- Destructors that can drop `sk_wmem_alloc` to zero and so free the socket:

| Destructor | Used for | Final step |
|---|---|---|
| `sock_wfree()` | set by `skb_set_owner_w()` | `__sk_free()` |
| `__sock_wfree()` | TCP pure ACKs | `__sk_free()` |
| `tcp_wfree()` | other TCP tx skbs | keeps one unit, then `sk_free()` |

- `tcp_wfree()` when it queues the socket for TSQ: returns without
  `sk_free()`; `tcp_tsq_workfn()` in `net/ipv4/tcp_output.c` calls `sk_free()`
  later, so the free can come from that work item.
- `sk_destruct()`: uses `call_rcu()` when `SOCK_RCU_FREE` is set or when
  `sk->sk_reuseport_cb` is non-NULL.
- `__sk_free()` with `sk_net_refcnt` set and destroy listeners present: calls
  `sock_diag_broadcast_destroy()` instead of `sk_destruct()`; that queues work
  which calls `sk_destruct()` later.

**References from lookups**

- There is no __udp4_lib_rcv() or __inet_hash() here; UDP receive is
  `udp_rcv()` in `net/ipv4/udp.c` and `udpv6_rcv()` in `net/ipv6/udp.c`, and
  `inet_hash()` sets `SOCK_RCU_FREE` on a TCP listener.
- `udp_rcv()` and `udpv6_rcv()`: `refcounted` covers only the socket from
  `inet_steal_sock()` or `inet6_steal_sock()`; the socket from
  `__udp4_lib_lookup_skb()` or `__udp6_lib_lookup_skb()` is used with no flag
  and no put.
- UDP sockets: not in a `SLAB_TYPESAFE_BY_RCU` cache; under `net/ipv4` and
  `net/ipv6` only the TCP protos set it, so `__udp4_lib_lookup()` and
  `__udp6_lib_lookup()` take no reference and have no key recheck after a
  reference, as `__inet_lookup_established()` has.
- `SOCK_RCU_FREE` is not limited to TCP listeners and UDP; search for
  `sock_set_flag(sk, SOCK_RCU_FREE)`, for example `raw_hash_sk()`.
- Early demux:

| Path | Reference | `skb->destructor` |
|---|---|---|
| `tcp_v4_early_demux()`, `tcp_v6_early_demux()` | always held | `sock_edemux()` |
| `udp_v4_early_demux()`, `udp_v6_early_demux()` | never held | `sock_pfree()` |

- `skb_steal_sock()` in `include/net/request_sock.h` sets `*refcounted`:
  - `skb->sk` NULL: `false`, returns NULL.
  - destructor is not `sock_pfree()`: `true`.
  - destructor is `sock_pfree()` and `sk` is a syncookie request sock
    (`CONFIG_SYN_COOKIES`): `false`, returns `rsk_listener`.
  - destructor is `sock_pfree()`, any other socket: `sk_is_refcounted(sk)`.
- `skb_steal_sock()` syncookie branch: leaves `skb->sk` and `skb->destructor`
  set; `cookie_bpf_check()` in `net/ipv4/syncookies.c` clears them.
- `sock_pfree()`: does nothing when `sk_is_refcounted()` is false; for a
  syncookie request sock it clears `rsk_listener` before `reqsk_free()`,
  because that listener pointer holds no reference.
- `tcp_v4_rcv()` changes `refcounted` after the lookup:
  - `TCP_TW_SYN`: `sk` becomes the `inet_lookup_listener()` result and
    `refcounted = false`.
  - `TCP_NEW_SYN_RECV`, listener still `TCP_LISTEN`: `sock_hold()` on
    `rsk_listener`, `refcounted = true`.
  - `TCP_NEW_SYN_RECV`, listener not `TCP_LISTEN`:
    `reuseport_migrate_sock()` returns a socket already referenced; no
    `sock_hold()`.
- `udp4_lib_lookup()`: compiled only with `CONFIG_NF_TPROXY_IPV4` or
  `CONFIG_NF_SOCKET_IPV4`; `udp6_lib_lookup()` only with the IPv6
  equivalents.
- `sk_lookup()` in `net/core/filter.c` (behind the BPF lookup helpers):
  returns `SOCK_RCU_FREE` sockets unreferenced; `bpf_sk_release()` puts only
  when `sk_is_refcounted()`.

**Request and timewait sockets**

- `sk_to_full_sk()` and `sk_const_to_full_sk()` in `include/net/inet_sock.h`:
  return NULL for a `TCP_TIME_WAIT` socket, not the socket itself.
- `sk_to_full_sk()` on a request sock: returns `rsk_listener`, which is NULL
  when the request sock was allocated with `attach_listener` false, as
  `cookie_tcp_reqsk_alloc()` does.
- Result of `sk_to_full_sk()`: needs a NULL test before any dereference,
  unless the caller has already ruled out a timewait sock and a request sock
  without listener.
- Members of `struct sock_common` that hold other data on a non-full socket:

| `struct sock` name | Request sock holds | Timewait sock holds |
|---|---|---|
| `sk_flags` | `skc_listener` | `skc_tw_dr` |
| `sk_incoming_cpu` | `skc_rcv_wnd` | `skc_tw_rcv_nxt` |
| `sk_rxhash` | `skc_window_clamp` | `skc_tw_snd_nxt` |

- **Potentially unsafe usage**: `sock_flag()`, `sk_incoming_cpu` or
  `sk_rxhash` on a pointer that may be a request or timewait sock.
  - Unsafe: when the value is used as flags, a CPU number or a hash with no
    `sk_fullsock()` test; the storage holds the members in the table above,
    and being in `struct sock_common` does not make them valid.
  - Safe: after `sk_fullsock()` returned true, as `sk_is_refcounted()` tests
    before `sock_flag()`; the unions in `struct sock_common` define the
    overlap.
  - Safe: copying the value unchanged from one request sock to another, as
    `inet_reqsk_clone()` does with `sk_incoming_cpu`.
- `sk_tx_queue_mapping`: is `skc_tx_queue_mapping` in `struct sock_common`
  and valid on all three kinds; `reqsk_alloc_noprof()` clears it,
  `tcp_time_wait()` copies it, and `sk_tx_queue_get()` reads it before its
  `sk_fullsock()` test.

**Sources of non-full sockets**

- Egress `skb->sk` can be a timewait sock, not only a request sock:
  `ip_send_unicast_reply()` and `tcp_v6_send_response()` re-own the RST or
  ACK reply to the original socket with `skb_set_owner_edemux()`.
- Reply sent through the per-cpu control socket (`ipv4_tcp_sk`): the control
  socket builds the skb, but `skb->sk` on the wire path is the original
  timewait or full socket when the caller passed one.
- `sk_listener_or_tw()` in `include/net/sock.h`: tests for a listener,
  request or timewait sock; its one caller is `fq_classify()` in
  `net/sched/sch_fq.c`, on egress `skb->sk`.
- `tcp_make_synack()` by `synack_type`:

| Type | `skb->sk` |
|---|---|
| `TCP_SYNACK_NORMAL`, `TCP_SYNACK_RETRANS` | request sock, `skb_set_owner_edemux()` |
| `TCP_SYNACK_COOKIE` | none |
| `TCP_SYNACK_FASTOPEN` | listener, `skb_set_owner_w()` |

- `bpf_sk_lookup_tcp()`: for a request sock returns its listener; for a
  timewait sock returns NULL; see `bpf_sk_lookup_full_sk()` in
  `net/core/filter.c`.
- `bpf_sk_assign_tcp_reqsk()` in `net/core/filter.c`: puts an unhashed
  syncookie request sock in ingress `skb->sk` with `sock_pfree()`.
- There is no inet_diag_dump_icsk() here; `tcp_diag_dump()` in
  `net/ipv4/tcp_diag.c` walks ehash and puts with `sock_gen_put()`.
- `tcp_v4_early_demux()` is a static function in `net/ipv4/ip_input.c`, and
  `tcp_v6_early_demux()` in `net/ipv6/ip6_input.c`.

**Keeping a socket pointer**

- `sk_stop_timer()`: calls `timer_delete()`; there is no del_timer() timer
  function in this tree.
- `__sock_put()` (used by `sk_stop_timer()` and `sk_stop_timer_sync()`): a
  plain `refcount_dec()` that never calls `sk_free()`.
- **Potentially unsafe usage**: calling `sk_stop_timer()` or
  `sk_stop_timer_sync()`.
  - Unsafe: when the timer's reference may be the last one; `refcount_dec()`
    warns of a leak and nothing frees the socket.
  - Safe: when the caller holds its own reference across the call, as
    `tcp_close()` does: when `sk_net_refcnt` is 0 it calls
    `inet_csk_clear_xmit_timers_sync()` before its own `sock_put()`.
    `__sock_put()` being a bare `refcount_dec()` defines the requirement.
- `inet_csk_clear_xmit_timer()`: does not stop the timer or drop a reference;
  its `sk_stop_timer()` calls are under `#ifdef INET_CSK_CLEAR_TIMERS`, which
  `include/net/inet_connection_sock.h` undefines.
- After `inet_csk_clear_xmit_timer()`: the timer stays armed with its
  reference; the handler runs, finds the pending flag clear, and does
  `sock_put()`.
- `inet_csk_clear_xmit_timers()` and `inet_csk_clear_xmit_timers_sync()`: do
  call `sk_stop_timer()` and `sk_stop_timer_sync()`, on the retransmit,
  delayed-ACK and keepalive timers.
- There is no inet_csk_reset_keepalive_timer() here;
  `tcp_reset_keepalive_timer()` in `net/ipv4/tcp_timer.c` calls
  `sk_reset_timer()`.
- **Potentially unsafe usage**: arming a timer embedded in a socket with
  plain `mod_timer()`.
  - Unsafe: when the handler ends in `sock_put()`, as `tcp_write_timer()`
    does, and nothing took a reference for the timer; the put drops someone
    else's reference.
  - Safe: when the timer's reference is counted another way, as
    `reqsk_queue_hash_req()` does by setting `rsk_refcnt` to 2 + 1 after
    `mod_timer()`; `reqsk_timer_handler()` drops it with `reqsk_put()` when
    it does not re-arm.

## Socket lock, accounting and options

**Socket release versus unlock**

- `__release_sock()`: not private to `release_sock()`; `__sk_flush_backlog()` in
  `net/core/sock.c` and `__tcp_close()` in `net/ipv4/tcp.c` call it too.
- `__sk_flush_backlog()` and `__tcp_close()`: drain the backlog and leave
  `sk->sk_lock.owned` set, so backlog processing can change socket state in the
  middle of an owner's critical section.
- `sk_flush_backlog()` in `include/net/sock.h`: the inline that calls
  `__sk_flush_backlog()` when `sk->sk_backlog.tail` is set.

**Socket lock**

- `lock_sock_nested()` uncontended, under `CONFIG_64BIT` when
  `sizeof(struct slock_owned) == sizeof(long)`: one `try_cmpxchg()` on
  `sk->sk_lock.combined` sets `owned` and returns; it takes no spinlock and
  does not disable BH.
- `lock_sock_nested()` when that `try_cmpxchg()` fails, or in other
  configurations: `spin_lock_bh()` on `slock`, wait in `__lock_sock()` if
  owned, set `owned`, `spin_unlock_bh()`.
- `release_sock()`: has no such shortcut; it takes `slock` with
  `spin_lock_bh()` every time.
- `release_sock()` on a socket whose `release_cb` is `tcp_release_cb()`:
  `tcp_release_cb_cond()` in `include/net/tcp.h` calls it directly, and only
  when `sk->sk_tsq_flags` has a `TCP_DEFERRED_ALL` bit; other protocols that
  set `release_cb` get `sk->sk_prot->release_cb()` on every release.
- `bh_lock_sock()` and `bh_lock_sock_nested()`: plain `spin_lock()`, BH is not
  disabled; process context disables BH first, as `__tcp_close()` does with
  `local_bh_disable()`.

**Queueing to a socket**

- `sock_queue_rcv_skb_reason()`: takes `(sk, skb)` and returns
  `enum skb_drop_reason`; there is no reason pointer argument and no errno.
- A caller tests the result for non-zero, never for `< 0`; refusals are
  positive enum values.
- `sock_queue_rcv_skb()` in `include/net/sock.h`: switches on that reason;
  every reason it does not name becomes `-EPERM`.

| Outcome | `sock_queue_rcv_skb_reason()` | `sock_queue_rcv_skb()` |
|---|---|---|
| queued | `SKB_NOT_DROPPED_YET` | 0 |
| pfmemalloc buffer, socket lacks `SOCK_MEMALLOC` | `SKB_DROP_REASON_PFMEMALLOC` | `-EPERM` |
| `BPF_CGROUP_RUN_PROG_INET_INGRESS()` fails, or `sk->sk_filter` returns 0 or the trim fails | `SKB_DROP_REASON_SOCKET_FILTER` | `-EPERM` |
| `security_sock_rcv_skb()` fails | `SKB_DROP_REASON_SECURITY_HOOK` | `-EPERM` |
| `sk_rmem_alloc` `>=` `sk_rcvbuf` | `SKB_DROP_REASON_SOCKET_RCVBUFF` | `-ENOMEM` |
| `sk_rmem_schedule()` fails | `SKB_DROP_REASON_PROTO_MEM` | `-ENOBUFS` |

- The first three refusals come from `sk_filter_trim_cap()` in
  `net/core/filter.c`, reached through `sk_filter_reason()`; the errno that
  the LSM or BPF program returned is discarded.
- `__sock_queue_rcv_skb()` before queueing: `skb->dev = NULL`,
  `skb_set_owner_r()`, `skb_dst_force()`; it does not drop the dst.

**Memory accounting**

- Unit of forward allocation: `PAGE_SIZE`, rounded by `sk_mem_pages()`; there
  is no SK_MEM_QUANTUM in this tree.
- `sk_bypass_prot_mem` set: `__sk_mem_raise_allocated()` and
  `__sk_mem_reduce_allocated()` leave the protocol's `memory_allocated` alone
  and skip the `sysctl_mem` limits; only the memory cgroup, if enabled for the
  socket, is charged.
- `sk_mem_reclaim()`: acts when `sk_forward_alloc` minus
  `sk_unused_reserved_mem()` is `>= PAGE_SIZE`; `sk_unused_reserved_mem()` is
  `sk_reserved_mem` less `sk_wmem_queued` and `sk_rmem_alloc`, not
  `sk_reserved_mem` itself.
- `__sk_mem_reclaim()`: gives back whole pages only; the remainder under
  `PAGE_SIZE` stays in `sk_forward_alloc`.
- `sk_stream_kill_queues()`: warns on `sk_wmem_queued` and on a non-empty write
  queue, not on `sk_forward_alloc`; `inet_sock_destruct()` warns on
  `sk_rmem_alloc`, `sk_wmem_alloc`, `sk_wmem_queued` and `sk_forward_alloc`.
- Which counters lose `skb->truesize` when a charged buffer is released:

| Released by | Subtracts `truesize` from |
|---|---|
| `sock_rfree()` | `sk_rmem_alloc`, then `sk_mem_uncharge()` |
| `sock_wfree()` | `sk_wmem_alloc` |
| `tcp_wmem_free_skb()` (TCP write and retransmit queues) | `sk_wmem_queued`, then `sk_mem_uncharge()`; for a `skb_zcopy_pure()` buffer the uncharge is `SKB_TRUESIZE(skb_end_offset(skb))` |
| `udp_skb_destructor()` (called at dequeue in `__skb_recv_udp()`) | uses `udp_skb_truesize()`, a copy taken at enqueue, not `skb->truesize` |

- **Potentially unsafe usage**: writing `skb->truesize` of a buffer that is
  charged to a socket.
  - Unsafe: when the counters in the table above are not changed by the same
    delta; the free path subtracts the new value and `inet_sock_destruct()`
    warns on the residue.
  - Safe: same delta applied to the same counters: `tcp_try_coalesce()` for
    `sock_rfree()` buffers, `skb_expand_head()` for `is_skb_wmem()` buffers,
    `tcp_trim_head()` for the TCP write queue.
  - Safe: moving bytes between two buffers charged to the same socket, as
    `tcp_fragment()` does.
  - Safe: before the charge, as `skb_condense()` runs ahead of
    `skb_set_owner_r()` in `tcp_data_queue_ofo()` and ahead of
    `sk_add_backlog()` in `tcp_add_backlog()`.
- `___pskb_trim()` in `net/core/skbuff.c`: calls `skb_condense()` only under
  the test that lets `pskb_expand_head()` change `truesize`, `!skb->sk` or
  destructor `sock_edemux()`.
- `__skb_unclone_keeptruesize()`: restores the saved `truesize` after
  `pskb_expand_head()`; TCP uses it on write-queue buffers.

**Socket option handlers**

- `struct proto_ops` has three option methods: `setsockopt` (`sockptr_t`,
  `unsigned int`), `getsockopt` (`char __user *`, `int __user *`) and
  `getsockopt_iter` (`sockopt_t *`).
- `sockopt_t` is `struct sockopt` in `include/linux/net.h`: `iter_in`,
  `iter_out` over the same buffer, and `optlen` as input size and output
  length.
- `do_sock_getsockopt()` order: `SOL_SOCKET` goes to `sk_getsockopt()`, with no
  `SOCK_CUSTOM_SOCKOPT` test; otherwise `getsockopt_iter` if set; otherwise
  `getsockopt`; otherwise `-EOPNOTSUPP`.
- There is no sock_getsockopt() in this tree; `sk_getsockopt()` in
  `net/core/sock.c` does that job.
- `getsockopt` path: still `__user` only; a kernel `sockptr_t` gets
  `WARN_ONCE()` and `-EOPNOTSUPP`. The `getsockopt_iter` path accepts kernel
  pointers.
- `getsockopt_iter` path, before the handler: `sockptr_to_sockopt()` in
  `net/socket.c` reads the length, returns `-EINVAL` if negative, and bounds
  both iterators to it, so `copy_to_iter()` on `iter_out` cannot write past
  the caller's buffer.
- `getsockopt_iter` path, after the handler: the core writes `opt->optlen`
  back even when the handler failed; `raw_getsockopt()` in `net/can/raw.c`
  relies on that to report the needed size with `-ERANGE`.
- A `getsockopt_iter` handler sets `opt->optlen` to the length returned; it is
  given no pointer to the caller's length, the core copies `opt->optlen` back.
- `struct proto` `getsockopt` still takes `__user` pointers; converted
  protocols wrap with `sockopt_init_user()` and `put_user()` the length only on
  success, as `udp_getsockopt()` does.
- `do_sock_setsockopt()`: returns `-EINVAL` for negative `optlen` before any
  handler; when a cgroup BPF program ran and left a non-zero `optlen`,
  `optval` becomes `KERNEL_SOCKPTR()` of a kernel buffer that can be as small
  as that `optlen` (`__cgroup_bpf_run_filter_setsockopt()` in
  `kernel/bpf/cgroup.c`), so a copy larger than `optlen` reads past a slab
  object.
- `copy_struct_from_sockptr()`: never reads more than the caller's size;
  accepts a shorter value and zero-fills the rest; returns `-E2BIG` when the
  excess bytes are non-zero.
- `copy_safe_from_sockptr()`: rejects a shorter value with `-EINVAL`, and
  ignores excess bytes.

**Softirq access to sockets**

- `sk_add_backlog()`: the bound is the caller's `limit` argument, tested
  against `sk_backlog.len` plus `sk_rmem_alloc`; it has no limit of its own.
- `tcp_add_backlog()` limit: twice `sk_rcvbuf`, plus half of `sk_sndbuf`, plus
  64 KB, capped at `UINT_MAX`.
- `tcp_add_backlog()`: returns `enum skb_drop_reason`; on a non-zero return it
  has already called `bh_unlock_sock()`, so the caller must not unlock again.
- `tcp_add_backlog()` coalescing into `sk->sk_backlog.tail`: runs before the
  limit test and succeeds above the limit; it adds only the delta to
  `sk_backlog.len`.
- `sk_add_backlog()` returns `-ENOMEM`, not `-ENOBUFS`, for a pfmemalloc buffer
  on a socket without `SOCK_MEMALLOC`; `__sk_receive_skb()` and
  `tcp_add_backlog()` map it to `SKB_DROP_REASON_PFMEMALLOC` and `-ENOBUFS` to
  `SKB_DROP_REASON_SOCKET_BACKLOG`.
- `__sk_add_backlog()`: no limit test and no change to `sk_backlog.len`;
  `tcp_child_process()` uses it for an owned child socket.
- `TCP_LISTEN` socket in `tcp_v4_rcv()` and `tcp_v6_rcv()`: handed to
  `tcp_v4_do_rcv()` or `tcp_v6_do_rcv()` without `bh_lock_sock_nested()` and
  without a `sock_owned_by_user()` test.
- UDP receive in `net/ipv4/udp.c`: takes no `bh_lock_sock()` and has no
  backlog; `__udp_enqueue_schedule_skb()` pushes the buffer on the lockless
  `udp_prod_queue` list, and the producer that found that list empty moves the
  batch to `sk_receive_queue` under `sk->sk_receive_queue.lock`.
- Socket reference in softirq: not always held; `__inet_lookup()` returns a
  listener without a reference and sets `*refcounted` to false, and
  `tcp_v4_rcv()` calls `sock_put()` only when `refcounted` is true.
- `tcp_delack_timer()` when the socket is owned: takes `sock_hold()` only if
  it was the one to set `TCP_DELACK_TIMER_DEFERRED`; `tcp_release_cb()` drops
  that reference with `__sock_put()`.

**Lockless socket fields**

- `struct sock` carries no marker for lockless members: `include/net/sock.h`
  does not use `__data_racy`, and the `__cacheline_group_begin()` groups such
  as `sock_write_rx` describe cache layout, not locking.
- The sign is a `READ_ONCE()` of the member somewhere in the tree, or an
  accessor in `include/net/sock.h` that wraps `WRITE_ONCE()`, for example
  `sk_wmem_queued_add()`.
- `sk_flags` has no `WRITE_ONCE()` accessor: `sock_flag()` reads it without
  the lock through `test_bit()`, while `sock_set_flag()` and
  `sock_reset_flag()` are non-atomic `__set_bit()` and `__clear_bit()`.
- **Potentially unsafe usage**: calling `sock_set_flag()` or
  `sock_reset_flag()` on a socket other tasks can reach.
  - Unsafe: when a second writer of `sk_flags` can run at the same time; one
    of the two flag changes is lost.
  - Safe: under `lock_sock()`, as `sock_gettstamp()` in `net/core/sock.c`
    takes the lock only to set one flag.
- Lockless setters in `sk_setsockopt()`: the ones in the first `switch`, before
  `sockopt_lock_sock()`; for example `sock_set_priority()`, which uses
  `WRITE_ONCE()`.

## Routes

**Route entry references**

- Counter field: `__rcuref` (`rcuref_t`) in `struct dst_entry`,
  `include/net/dst.h`; there is no field named __refcnt.
- DST_NOCACHE: not defined in this tree; the name is left only in a comment
  in `net/ipv4/route.c`.
- `dst_hold()` on a dead entry: takes no reference and fires `WARN_ON()`; the
  caller goes on with a pointer it does not own.
- `sk_dst_get()` in `include/net/sock.h`: calls
  `rcuref_get(&dst->__rcuref)` directly, not `dst_hold_safe()`; a search for
  `dst_hold_safe()` callers misses it.
- IPv6 on a failed `dst_hold_safe()`: `ip6_hold_safe()` and
  `ip6_route_output_flags()` in `net/ipv6/route.c` hand back
  `net->ipv6.ip6_null_entry` with `dst_hold()`, not NULL; `ip6_hold_safe()`
  gives NULL only when its `net` argument is NULL.
- IPv4 on a failed `dst_hold_safe()`: `__mkroute_output()` falls through and
  allocates a new route; `inet_sk_rx_dst_set()` and `udp_sk_rx_dst_set()`
  leave `sk->sk_rx_dst` unchanged.
- **Potentially unsafe usage**: `dst_release_immediate()` on an entry that was
  stored where RCU readers look.
  - Unsafe: while a reader that found the entry under `rcu_read_lock()` can
    still be running; `dst_destroy()` frees it with no grace period.
  - Safe: the entry was never published, as in `__ip6_rt_update_pmtu()` and
    `rt6_do_redirect()` when `rt6_insert_exception()` failed.
  - Safe: a grace period has passed since the entry was unpublished, as in
    `rt_fibinfo_free()` in `net/ipv4/fib_semantics.c`, which runs from RCU
    callbacks, for example `free_fib_info_rcu()`.

**Device behind a route**

- `dst_dev_put()` in `net/core/dst.c`: also writes `DST_OBSOLETE_DEAD` to
  `dst->obsolete`; it moves the tracked reference with
  `netdev_ref_replace()`, it does not call `netdev_put()`.
- `dst_dev_put()` callers: the code that drops a cached route (nexthop
  exception, per-CPU route, `fib_info` free) and `drivers/net/vrf.c`; no
  netdev notifier calls it directly.
- `rt_flush_dev()` in `net/ipv4/route.c` and `rt6_uncached_list_flush_dev()`
  in `net/ipv6/route.c`: do not call `dst_dev_put()`; they swap the device
  and its tracker and unlink the route from the uncached list.
- Uncached route after the flush: `dst->obsolete`, `dst->input` and
  `dst->output` are unchanged, so the route keeps running its normal handlers
  with `blackhole_netdev` as device.
- `ip6_route_dev_notify()`: acts only on the loopback device and the
  per-netns null, prohibit and blackhole entries (the last two under
  `CONFIG_IPV6_MULTIPLE_TABLES`); it moves no route to `blackhole_netdev`.
- `blackhole_netdev` in `drivers/net/loopback.c`: one global device, never
  registered; `dev_net()` of it is `&init_net` and its MTU is `ETH_MIN_MTU`.
- Netns from a swapped route: `dev_net(dst_dev(dst))` and
  `dst_dev_net_rcu()` return `&init_net`, whatever netns the route was
  created in.
- NULL device: `dst_dev()` and `dst_dev_rcu()` return NULL for an entry
  initialised with no device; neither accessor tests for it.
  - `__metadata_dst_init()` in `net/core/dst.c` passes NULL to `dst_init()`.
  - `xfrm_alloc_dst()` in `net/xfrm/xfrm_policy.c` passes NULL to
    `dst_alloc()`; the bundle code sets the device later.
- `dst_dev()`: a bare `READ_ONCE()`; it asserts no lock and gives no lifetime
  guarantee for the device it returns.
- Direct `dst->dev` reads: nothing in the tree forbids them; `dev` is a plain
  member of the union beside `dev_rcu`, and many files still read it
  directly, for example `rt_flush_dev()` under `ul->lock`, which it also
  holds for its write.

**Unreferenced routes on a buffer**

- `skb_dst_force()` return value: `skb->_skb_refdst != 0UL`.

| skb state on entry | Returns | skb dst afterwards |
|---|---|---|
| no dst | false | none |
| counted dst | true | unchanged |
| noref dst, `dst_hold_safe()` succeeds | true | counted |
| noref dst, `dst_hold_safe()` fails | false | cleared |

- A false return covers both "no dst" and "hold failed": callers that accept
  an skb with no dst test `skb_dst(skb)` first, as `__nf_queue()` and
  `xfrm_trans_queue_net()` do; callers that need a dst test `skb_dst(skb)`
  afterwards, as `ip_route_input()`, `xfrm_input()` and `xfrm_output_one()`
  do.
- `ip_route_input_noref()`: attaches a noref dst only on a hit in the nexthop
  input cache (`nhc_rth_input`, or `fnhe_rth_input` of a nexthop exception);
  otherwise `ip_route_input_slow()`, `__mkroute_input()` and
  `ip_route_input_mc()` attach a counted dst with `skb_dst_set()`.
- `ip_route_input_noref()`: drops its own `rcu_read_lock()` before it
  returns; the caller's RCU section is what keeps a noref result valid.
- `__copy_skb_header()` in `net/core/skbuff.c`: uses `skb_dst_copy()`, which
  copies the noref bit and takes no reference for a noref dst; a clone or
  copy is not an upgrade.
- Upgrade points: search for `skb_dst_force(`; the tree has under twenty
  callers. Most ignore the return value.
  - `__dev_queue_xmit()`: before the qdisc is looked up, so for queueless
    devices too; with `IFF_XMIT_DST_RELEASE` it calls `skb_dst_drop()`
    instead.
  - `dev_loopback_xmit()` and `loopback_xmit()`: before `netif_rx()` and
    `__netif_rx()`.
  - `__neigh_event_send()`: before the skb goes on `neigh->arp_queue`.
  - `__sock_queue_rcv_skb()`, `sock_queue_err_skb()`, `__sk_add_backlog()`.
  - `__nf_queue()` and `xfrm_trans_queue_net()`: fail with `-ENETDOWN` and
    `-EHOSTUNREACH` when the hold fails.
- TCP receive: `tcp_add_backlog()` calls `tcp_cleanup_skb()`, which calls
  `skb_dst_drop()`; the skb reaches `sk_add_backlog()` with no dst.
- IPv4 UDP and raw receive: `ipv4_pktinfo_prepare()` with `drop_dst` true
  drops the dst; `__udp_enqueue_schedule_skb()` neither drops nor forces.
- `__release_sock()`: has
  `DEBUG_NET_WARN_ON_ONCE(skb_dst_is_noref(skb))` for every backlog skb.
- **Potentially unsafe usage**: dereferencing `skb_dst(skb)` after an upgrade
  point without a NULL test.
  - Unsafe: when the skb could have carried a noref dst into
    `skb_dst_force()` and the caller ignored the return value; a failed hold
    leaves `skb_dst()` NULL.
  - Safe: the dst was counted before the upgrade point (attached with
    `skb_dst_set()`, as `ip_route_input_mc()` does), since `skb_dst_force()`
    acts only when `skb_dst_is_noref()` is true.
  - Safe: the code tests `skb_dst(skb)` after the force, as
    `ip_route_input()` in `include/net/route.h` does.
- **Potentially unsafe usage**: putting an skb on a list that is processed
  after `rcu_read_unlock()` while `skb_dst_is_noref()` is true.
  - Unsafe: when nothing else holds a reference on the dst until the list is
    processed; the last `dst_release()` frees the entry after one grace
    period.
  - Safe: call `skb_dst_force()` inside the RCU section first, as
    `__neigh_event_send()` does before `__skb_queue_tail()`.
  - Safe: call `skb_dst_drop()` first when the consumer needs no route, as
    `tcp_cleanup_skb()` does.
  - Safe: the owner of the dst keeps its own reference for as long as such
    skbs can exist, as `mtk_poll_rx()` in
    `drivers/net/ethernet/mediatek/mtk_eth_soc.c` relies on: the driver holds
    the reference from `metadata_dst_alloc()` until `mtk_free_dev()`.

## Devices and their locks

**Device instance lock**

- Field classes in the comment on `lock` apply to every device, not only
  ops-locked ones: `reg_state`, `up`, `moving_ns`, `nd_net` of a registered
  or unregistering device are written under `netdev_lock()` whether or not
  the device is ops-locked.
- `netif_set_up()` in `net/core/dev.h`: takes `netdev_lock()` itself when the
  device is not ops-locked, so `up` is always written under both locks.
- "Ops protected" fields named by the comment: `cfg`, `cfg_pending`,
  `ethtool`, `hwprov`.
- `flags`, `mtu`, `features`: not in any class of the comment.
- Notifier events and the lock, as asserted by `netdev_debug_event()` in
  `net/core/lock_debug.c` (built with `CONFIG_DEBUG_NET`):

| Event | Instance lock |
|---|---|
| `NETDEV_XDP_FEAT_CHANGE` | held, every device |
| `NETDEV_REGISTER`, `NETDEV_UP`, `NETDEV_DOWN`, `NETDEV_GOING_DOWN`, `NETDEV_CHANGE`, `NETDEV_CHANGENAME` | held if ops-locked |
| `NETDEV_UNREGISTER` | no assertion; `net/core/dev.c` sends it without the lock |
| any other, for example `NETDEV_CHANGEMTU` | no assertion; `register_netdevice()` sends `NETDEV_POST_INIT` without the lock |

- `ndo_init`, `ndo_uninit`, `priv_destructor`: called without the instance
  lock, also on ops-locked devices; see `register_netdevice()`,
  `unregister_netdevice_many_notify()` and `netdev_run_todo()`.
- ethtool ops on an ops-locked device: the default handlers in
  `net/ethtool/netlink.c` and `__dev_ethtool()` call them under the instance
  lock, and take RTNL only if `ethtool_nl_msg_needs_rtnl()` /
  `ethtool_ioctl_needs_rtnl()` (driver's `op_needs_rtnl`) or
  `ethtool_cmd_changes_features()` says so.
- An ethtool op of an ops-locked driver that reaches `ASSERT_RTNL()` code,
  for example `__netdev_update_features()`, needs its bit set in
  `op_needs_rtnl`, for example `ETHTOOL_OP_NEEDS_RTNL_SCHANNELS`.
- Order between two devices: there is no upper-before-lower rule;
  `netdev_lock_cmp_fn()` accepts any order while RTNL is held.
- Queue leasing: the virtual device's lock is taken before the physical
  device's, without RTNL; see `netdev_nl_queue_create_doit()`.

**Locked and unlocked device functions**

- There is no netdev_ops_assert_locked here. The assert helpers in
  `include/net/netdev_lock.h` are:

| Helper | Ops-locked device | Other device |
|---|---|---|
| `netdev_assert_locked()` | lockdep: instance lock | lockdep: instance lock |
| `netdev_assert_locked_ops()` | lockdep: instance lock | no check |
| `netdev_assert_locked_ops_compat()` | lockdep: instance lock | `ASSERT_RTNL()` |

- `netdev_assert_locked_or_invisible()` and
  `netdev_assert_locked_ops_compat_or_invisible()`: same checks, made only in
  `NETREG_REGISTERED` or `NETREG_UNREGISTERING`. There is no
  netdev_ops_assert_locked_or_invisible.
- `netif_` prefix alone does not mean "lock held": `netif_napi_add()`,
  `netif_napi_del()`, `netif_napi_set_irq()` take `netdev_lock()` themselves.
- `_locked` suffix marks the lock-held form for NAPI: `netif_napi_add_locked()`,
  `netif_napi_del_locked()`, `napi_enable_locked()`, `napi_disable_locked()`.
- `netdev_` prefix is mixed: `netdev_state_change()` takes `netdev_lock_ops()`
  and calls `netif_state_change()`; `netdev_update_features()` expects the
  lock held on an ops-locked device.
- `dev_change_flags()`, `dev_set_promiscuity()`, `dev_set_allmulti()`: also
  call `netif_rx_mode_sync()` before unlocking; `netif_change_flags()`,
  `netif_set_promiscuity()` and `netif_set_allmulti()` do not, so an rx-mode
  update that `__dev_set_rx_mode()` queued stays queued.
- `netdev_lock_ops_to_full()` / `netdev_unlock_full_to_ops()`: for a caller
  already inside `netdev_lock_ops()`; lock a non-ops-locked device, only
  assert on an ops-locked one.
- **Unsafe usage**: calling a `dev_` wrapper from `net/core/dev_api.c` on an
  ops-locked device whose instance lock the caller holds; `netdev_lock_ops()`
  takes the same mutex again. `dev_set_threaded()` does so on any device.
  - Safe: call the `netif_` form, as `ipv6_add_dev()` in
    `net/ipv6/addrconf.c` does with `netif_disable_lro()` after
    `netdev_assert_locked_ops_compat()`.
  - Safe: call the `dev_` form from a `NETDEV_UNREGISTER` handler, which
    runs without the lock; `netdev_lock_ops()` then takes it, as
    `__bond_release_one()` does with `dev_close()` when
    `bond_slave_netdev_event()` handles `NETDEV_UNREGISTER`.

**RTNL and per-namespace RTNL**

- `ASSERT_RTNL()`: tests `mutex_is_locked()`, so it passes when any task
  holds RTNL.
- `lockdep_rtnl_is_held()`: constant `true` without `CONFIG_PROVE_LOCKING`,
  so `rtnl_dereference()` and `rcu_dereference_rtnl()` check nothing then.
- RCU-or-per-netns-RTNL dereference: `rcu_dereference_rtnl_net()`. There is
  no rtnl_net_rcu_dereference and no rcu_dereference_bh_rtnl.
- `ASSERT_RTNL_NET()` and `lockdep_rtnl_net_is_held()` with
  `CONFIG_DEBUG_NET_SMALL_RTNL`: require both the global RTNL and
  `net->rtnl_mutex`.
- `CONFIG_DEBUG_NET_SMALL_RTNL`: selects `PROVE_LOCKING`.
- `RTNL_FLAG_DOIT_PERNET` and `RTNL_FLAG_DOIT_PERNET_WIP`: aliases of
  `RTNL_FLAG_DOIT_UNLOCKED` in `include/net/rtnetlink.h`;
  `rtnetlink_rcv_msg()` calls such a handler with no lock held.
- A handler with one of those flags locks for itself, for example with
  `rtnl_net_lock()` or `rtnl_nets_lock()`, which take the global RTNL first;
  no path takes only the per-netns mutex.
- `__rtnl_net_lock()` with `CONFIG_DEBUG_NET_SMALL_RTNL`: for a caller that
  already holds RTNL; it asserts `ASSERT_RTNL()`. Without the option it is an
  empty inline.
- Several namespaces, with `CONFIG_DEBUG_NET_SMALL_RTNL`: `init_net` first,
  then ascending `struct net` address; see `rtnl_net_cmp_locks()`.
- `rtnl_nets_lock()`: static in `net/core/rtnetlink.c`, not available to
  other files.
- `__rtnl_net_unlock()` with `CONFIG_DEBUG_NET_SMALL_RTNL`: calls
  `unregister_netdevice_many_net()` first, so unlocking unregisters devices
  that `unregister_netdevice_queue_net()` queued on `net->dev_unreg_head`.
- `unregister_netdevice_queue_net()` without the option: plain
  `unregister_netdevice_queue()`.

**Device references**

- There is no netdev_get_by_index_rcu and no __dev_get_by_flags in this
  tree.
- `netdev_get_by_flags_rcu()` in `net/core/dev.c`: caller must hold
  `rcu_read_lock()`, yet the device comes back held and tracked
  (`netdev_hold()` with `GFP_ATOMIC`); release with `netdev_put()`.
- `netdev_get_by_index_lock()`: returns with the instance lock held and no
  reference; release with `netdev_unlock()` only.
- `netdev_get_by_index_lock()` returns NULL when `reg_state` is past
  `NETREG_REGISTERED`, `moving_ns` is set, or the device is in another
  namespace; see `netdev_put_lock()`.
- `dev_hold()` with `CONFIG_NET_DEV_REFCNT_TRACKER`: counted in
  `refcnt_tracker.no_tracker`; `dev_put()` decrements the same counter.
- `netdev_tracker_alloc()`: turns an untracked reference into a tracked one
  by decrementing `no_tracker`; valid only on a reference counted there, such
  as one taken by `dev_hold()`, `dev_get_by_index()` or `dev_get_by_name()`.
- `__netdev_tracker_alloc()`: for a reference taken with `__dev_hold()`,
  which touched no tracker counter.
- **Unsafe usage**: releasing a `dev_hold()` reference with `netdev_put()` and
  a tracker, or a `netdev_hold()` reference taken with a tracker with
  `dev_put()`; with `CONFIG_NET_DEV_REFCNT_TRACKER` the `no_tracker` count is
  left unbalanced and `ref_tracker_dir_exit()` warns.
  - Safe: `dev_hold()` then `netdev_tracker_alloc()` then `netdev_put()`
    with that tracker; `netdev_get_by_index()` does the first two for its
    caller.

**Registration and teardown**

- `netdev_wait_allrefs_any()`: waits for `netdev_refcnt_read()` to equal 1,
  not 0; the last count is the one set in `alloc_netdev_mqs()`.
- `netdev_run_todo()`: sets `NETREG_UNREGISTERED` under `netdev_lock()`
  before the wait, right after `rcu_barrier()`.
- Code that runs while references drain sees `NETREG_UNREGISTERED`, not
  `NETREG_UNREGISTERING`.
- Rebroadcast of `NETDEV_UNREGISTER`: every second, under RTNL and
  `__rtnl_net_lock()`, without the instance lock.
- "waiting for %s to become free": every `netdev_unregister_timeout_secs`
  (default 10), followed by `ref_tracker_dir_print()`.
- `free_netdev()`: never calls `priv_destructor`; in the core only
  `register_netdevice()` (error path) and `netdev_run_todo()` do.
- `free_netdev()` on a `NETREG_UNREGISTERING` device: sets
  `needs_free_netdev`, returns; `netdev_run_todo()` frees. It asserts RTNL.
- `needs_free_netdev` set: the device is freed inside the `rtnl_unlock()`
  that follows `unregister_netdevice()`; `netdev_priv()` is gone when
  `rtnl_unlock()` or `unregister_netdev()` returns.
- After a failed `register_netdevice()` the caller has to call
  `free_netdev()`; the driver's `needs_free_netdev` setting is never acted
  on. What the core already ran:

| Failure point | `ndo_uninit` | `priv_destructor` | `reg_state` on return |
|---|---|---|---|
| before `ndo_init`, or `ndo_init` itself | no | no | `NETREG_UNINITIALIZED` |
| after `ndo_init`, through `NETDEV_POST_INIT` | yes | yes | `NETREG_UNINITIALIZED` |
| `netdev_register_kobject()` | yes | yes | `NETREG_UNREGISTERED` |
| `NETDEV_REGISTER` notifier | yes, by full unregister | yes, in `netdev_run_todo()` | `NETREG_UNREGISTERING` until RTNL is dropped |

- `NETDEV_REGISTER` notifier failure: `register_netdevice()` clears
  `needs_free_netdev` and calls `unregister_netdevice_queue()`; a
  `free_netdev()` under the same RTNL hold is deferred as above, as in
  `rtnl_newlink_create()`.
- **Potentially unsafe usage**: freeing in the caller's error path what
  `priv_destructor` frees, after `register_netdevice()` failed later than
  `ndo_init`.
  - Unsafe: when `priv_destructor` was already set when
    `register_netdevice()` ran and the caller frees without testing whether
    it already ran; `register_netdevice()` calls it at `err_uninit`, so the
    state is freed twice.
  - Safe: when the destructor clears `dev->priv_destructor` and the caller
    tests that pointer first, as `ipoib_intf_free()` and
    `__ipoib_vlan_add()` do; `register_netdevice()` and `netdev_run_todo()`
    test the same pointer.
  - Safe: set `priv_destructor` only after registration succeeded, as
    `brcmf_net_attach()` does.
  - Safe: allocate the state in `ndo_init`, leave it to `priv_destructor`
    and call only `free_netdev()`, as `veth_newlink()` does for the peer
    with `veth_dev_init()` and `veth_dev_free()`.

**Device pointer on a buffer**

- `__sock_queue_rcv_skb()` and `__sk_receive_skb()` in `net/core/sock.c`: set
  `skb->dev` to NULL before queueing; `sock_queue_rcv_skb_reason()` goes
  through the first.
- `tcp_v4_rcv()`: sets `skb->dev` to NULL after `process:`, before
  `tcp_v4_do_rcv()` or `tcp_add_backlog()`; TCP does not use `dev_scratch`.
- `dev_scratch`: used only by UDP (`net/ipv4/udp.c`, `include/net/udp.h`); on
  a UDP receive queue the field is not a pointer.
- A fragment on a reassembly queue: `skb->dev` is not cleared; for a fragment
  linked into the rb-tree it is overwritten by `rbnode`, which shares its
  storage, so reading it yields rb-tree data, not a device.
- `ip_frag_queue()`: copies `skb->dev` to a local before
  `inet_frag_queue_insert()` and saves `dev->ifindex` in `qp->iif`.
- `ip_frag_reasm()`: sets `skb->dev` to the device of the fragment that
  completed the datagram; it does no ifindex lookup.
- `ip_expire()`: the only place in `net/ipv4/ip_fragment.c` that uses
  `dev_get_by_index_rcu()` with `qp->iif`; it first takes the head out of the
  tree with `inet_frag_pull_head()`.
- `flush_all_backlogs()`: runs in `unregister_netdevice_many_notify()` after
  `reg_state` becomes `NETREG_UNREGISTERING` and before the first
  `synchronize_net()`.
- `flush_backlog()`: drops only buffers on `input_pkt_queue` and
  `process_queue` whose `skb->dev->reg_state` is `NETREG_UNREGISTERING`; a
  buffer on any other queue is not found by `flush_backlog()`.

## Network namespaces

**Namespace references**

- Main count: `net->ns.__ns_ref`, a `refcount_t` in the embedded
  `struct ns_common`, defined in `include/linux/ns/ns_common_types.h`. Neither
  `struct ns_common` nor `struct net` has a member named `count`.
- `get_net()`, `maybe_get_net()`, `put_net()` and `check_net()`: under
  `CONFIG_NET_NS`, wrappers around `ns_ref_inc()`, `ns_ref_get()`,
  `ns_ref_put()` and `ns_ref_read()` in `include/linux/ns_common.h`.
- `init_net`: `ns_ref_inc()`, `ns_ref_get()` and `ns_ref_put()` return early
  when `is_ns_init_id()` is true, so its count is never changed and
  `maybe_get_net(&init_net)` always succeeds.
- `__ns_ref_active`: a separate counter, in `struct ns_tree`
  (`include/linux/ns/nstree_types.h`), which `struct ns_common` embeds.
  `get_net()` and `put_net()` do not change it, and it is not the passive
  count.
- Last `net_passive_dec()`, under `CONFIG_NET_NS`: frees `net->gen` at once
  but only queues the `struct net` on `defer_free_list`.
  `net_complete_free()` frees it on the next `cleanup_net()` run to reach it,
  after that run's `rcu_barrier()`.
- `get_net_ns_by_pid()`: calls `get_net()`, not `maybe_get_net()`. It reads
  `tsk->nsproxy->net_ns` under `task_lock()`, where the nsproxy holds a
  reference.
- `maybe_get_net()` under `rcu_read_lock()`: see `get_net_ns_by_id()` and
  `psp_nl_multicast_per_ns()`. No `for_each_net_rcu()` walker in this tree
  takes a reference.
- Keeping only the memory past the read section: call `net_passive_inc()`
  inside it, as `rtnl_net_dev_lock()` in `net/core/dev.c` does on the result of
  `dev_net_rcu()`. It then only locks and compares the pointer.

**Kernel sockets**

- Kernel socket: `sk_alloc()` takes a passive reference with
  `net_passive_inc()` and a tracker in `net->notrefcnt_tracker`.
  `__sk_destruct()` drops both.
- Unclosed kernel socket after teardown: `struct net` and `net->gen` stay
  allocated, so `sock_net(sk)` can be dereferenced. Per-net state is gone,
  including the `net_generic()` areas freed by `ops_free_list()`.
- `sk_clone()`: the clone inherits `sk_net_refcnt`. A child of a kernel listener
  takes only `net_passive_inc()`.
- `sk_net_refcnt_upgrade()`: drops the tracker and the passive reference first,
  then calls `get_net_track()` and `sock_inuse_add()`.
- `sk_net_refcnt`: assigned only by `sk_alloc()` and `sk_net_refcnt_upgrade()`.
  `sock_create_kern()` always passes `kern` 1, and `net/socket.c` has no
  creation helper that takes the main count for a kernel socket.
- **Potentially unsafe usage**: calling `sk_net_refcnt_upgrade()` on a kernel
  socket.
  - Unsafe: when nothing guarantees the main count is nonzero. It calls
    `get_net_track()`, which increments without a test.
  - Safe: bracketed by a successful `maybe_get_net()` and a `put_net()`, as
    `rds_tcp_tune()` in `net/rds/tcp.c` does. It returns false on NULL.
  - Safe: when the caller holds a main reference of its own across the call,
    as `generic_ip_connect()` in `fs/smb/client/connect.c` does through the
    `get_net()` that `cifs_get_tcp_session()` stored in the server.
- `sk_net_refcnt_upgrade()` context: it passes `GFP_KERNEL` to the tracker
  allocation, so call it where sleeping is allowed.
- Upgraded socket closed only from a pernet exit handler: its reference keeps
  the main count above zero, so `cleanup_net()` never runs that handler for
  the namespace. `__put_net()` is the only path that queues `cleanup_net()`,
  and it runs only when the main count reaches zero.

**Per-namespace operations**

- RTNL callback: `exit_rtnl` in `struct pernet_operations`. There is no
  exit_batch_rtnl in this tree.
- `exit_rtnl` phase: runs after the grace period and before any `exit`. See
  `ops_exit_rtnl_list()` in `net/core/net_namespace.c`.
- `exit_rtnl` iteration: called once per net per op, with nets in the outer loop
  and ops in reverse inside. `pre_exit` and `exit` iterate the other way round.
- `exit_rtnl` phase is skipped when no op in the walked list sets `exit_rtnl`.
- Per-net RTNL in that phase: `__rtnl_net_lock()` is a real mutex only under
  `CONFIG_DEBUG_NET_SMALL_RTNL`, and an empty stub otherwise.
- `exit` and `exit_batch`: interleaved per op. `ops_exit_list()` runs one op's
  `exit` for every net, then that op's `exit_batch`, then moves to the next op.
- `exit_batch` with its own `rtnl_lock()`: still used, for example by
  `default_device_exit_batch()` in `net/core/dev.c`.
- Core grace period: `synchronize_rcu_expedited()` from `cleanup_net()`. It is
  `synchronize_rcu()` from `setup_net()` unwind and from `ops_undo_single()`.
- Waiting in a handler: no code forbids it in any callback. All run in process
  context, and RTNL is a mutex.
- Cost of a wait: once per net in `pre_exit`, `exit` and `exit_rtnl`, once per
  batch in `exit_batch`.
- Waits under RTNL exist in-tree: `ops_exit_rtnl_list()` ends with
  `unregister_netdevice_many()`, which calls `synchronize_net()` when the kill
  list is not empty. `nexthop_net_exit_rtnl()` also reaches
  `synchronize_net()`, when a removed nexthop is a member of a group.
- `exit_rtnl` is not limited to queueing devices: `fib_net_exit_rtnl()` and
  `nexthop_net_exit_rtnl()` flush tables.
- `synchronize_net()`: expedited when `from_cleanup_net()` or
  `rtnl_is_locked()` is true. A plain `synchronize_rcu()` in a handler is not.
- Final `rcu_barrier()` in `cleanup_net()`: does not cover the
  `net_generic()` areas. `ops_free_list()` has already freed each op's
  `net_generic()` area with `kfree()`.
- **Unsafe usage**: a `call_rcu()` callback queued from an exit handler that
  reads the op's `net_generic()` area; `ops_free_list()` frees the area with
  no wait for callbacks.
  - Safe: unpublish in `pre_exit` and free in `exit`, as
    `iptable_filter_net_pre_exit()` and `iptable_filter_net_exit()` in
    `net/ipv4/netfilter/iptable_filter.c` do. `ops_undo_list()` puts the grace
    period between them.
- Unregistering: `unregister_pernet_subsys()` and `unregister_pernet_device()`
  run the same sequence through `ops_undo_single()`. It covers every live net,
  `init_net` included, with `pernet_ops_rwsem` held for write.

## Protocol statistics

**Protocol MIB counters**

- `__SNMP_INC_STATS64()` on a 32-bit build: defined as
  `SNMP_ADD_STATS64(mib, field, 1)`, so it disables BH itself; it is identical
  to `SNMP_INC_STATS64()`.
- `__IP_INC_STATS()` and `__IP6_INC_STATS()`: self-protecting on 32-bit only;
  on 64-bit they are `__this_cpu_inc()`, so callers still need BH off.
- `__SNMP_ADD_STATS64()` and `__SNMP_UPD_PO_STATS64()` on 32-bit: the only
  64-bit forms that do the bare `syncp` write; reached through
  `__IP_ADD_STATS()` and `__IP_UPD_PO_STATS()`.
- `SNMP_ADD_STATS64()` and `SNMP_UPD_PO_STATS64()` on 32-bit: wrap the `__`
  form in `local_bh_disable()` / `local_bh_enable()`.
- Plain 64-bit forms on 32-bit: not usable in hard-irq context or with IRQs
  off; `__local_bh_enable_ip()` in `kernel/softirq.c` has
  `WARN_ON_ONCE(in_hardirq())` and `lockdep_assert_irqs_enabled()`.
- 32-bit `__SNMP_ADD_STATS64()`: uses `raw_cpu_ptr()`, so
  `CONFIG_DEBUG_PREEMPT` does not check it.
- `u64_stats_update_begin()` on 32-bit: calls `preempt_disable_nested()`, which
  disables preemption itself on `CONFIG_PREEMPT_RT` and otherwise only asserts
  it via `lockdep_assert_preemption_disabled()` (`CONFIG_PROVE_LOCKING`).
- `__this_cpu_preempt_check()`: does not test softirq state; see
  `check_preemption_disabled()` in `lib/smp_processor_id.c`. It passes, for
  example, on nonzero `preempt_count()`, IRQs off, or
  `current->migration_disabled`, so a clean debug run does not show the BH
  requirement is met.
- Users of the 64-bit forms: the `IP_` wrappers in `include/net/ip.h` and
  `_DEVINC()` in `include/net/ipv6.h`.
- `SNMP_DEC_STATS()`: has no double-underscore form; `SNMP_DEC_STATS64()` is
  defined only when `BITS_PER_LONG` is not 32.
- **Potentially unsafe usage**: a double-underscore MIB macro in code that can
  run in process context.
  - Unsafe: when BH is enabled at the call; `raw_cpu_generic_to_op()` in
    `include/asm-generic/percpu.h` is an unprotected read-modify-write, and a
    softirq update of the same counter in between is lost.
  - Unsafe: in a receive handler that is also the socket backlog handler;
    `__release_sock()` in `net/core/sock.c` calls `sk_backlog_rcv()` after
    `spin_unlock_bh()`, in process context with BH enabled.
  - Safe: the plain macro in such a handler, as `tcp_v4_do_rcv()` does with
    `TCP_INC_STATS()`; it is `this_cpu_inc()`, whose generic form
    `this_cpu_generic_to_op()` disables IRQs around the update.
  - Safe: inside the caller's own `local_bh_disable()` section, as
    `tcp_v4_send_reset()` and `__napi_busy_loop()` do.

## Model gaps

### Other mistakes models make

- Models take `__dev_xmit_skb()` to enqueue under the qdisc root lock and
  return the enqueue result. For a qdisc without `TCQ_F_NOLOCK` it frees the
  buffer itself with `SKB_DROP_REASON_QDISC_BURST_DROP` when `q->defer_count`
  goes above `net_hotdata.qdisc_max_burst`.
- Models take an upper device's instance lock to order before a lower's.
  `netdev_lock_cmp_fn()` in `include/net/netdev_lock.h` accepts no order
  when RTNL is not held; lockdep consults it only for two locks of the same
  lock class.
- Models know only `ndo_set_rx_mode`. This tree adds
  `ndo_set_rx_mode_async` and `ndo_work`; `register_netdevice()` warns when
  an ops-locked driver has `ndo_set_rx_mode` without the async one.
- Models name icsk_retransmit_timer. It is not in this tree; the TCP
  retransmit timer is `tcp_retransmit_timer` in `struct sock`.

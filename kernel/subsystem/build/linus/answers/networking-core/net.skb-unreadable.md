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

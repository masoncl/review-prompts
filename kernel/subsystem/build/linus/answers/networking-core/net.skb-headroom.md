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

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

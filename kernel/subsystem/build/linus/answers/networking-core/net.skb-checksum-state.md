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

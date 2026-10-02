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

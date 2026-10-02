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

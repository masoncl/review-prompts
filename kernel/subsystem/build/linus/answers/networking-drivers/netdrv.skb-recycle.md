- Frag free path: `skb_release_data()` calls `__skb_frag_unref()` →
  `skb_page_unref()` in `include/linux/skbuff_ref.h`; there is no
  napi_frag_unref() in this tree.
- Per-page test: `netmem_is_pp()` in `net/core/netmem_priv.h`, applied to
  the compound head and masked with `PP_MAGIC_MASK`, which drops the DMA
  index bits and bits 0-1 of `pp_magic`.
- `page_pool_page_is_pp()` in `include/linux/mm.h` is the same test for the
  page allocator, not the one the skb path calls.
- Unmarked skb: `skb_page_unref()` falls to `put_netmem()` and the head to
  `skb_free_frag()`; nothing on that path unmaps DMA, increments
  `pages_state_release_cnt` or clears `pp_magic`. No page-free hook unmaps.
- Unmarked page, DMA, when `PP_DMA_INDEX_BITS` is non-zero: its entry stays
  in the pool's `dma_mapped` xarray, pointing at a page the pool no longer
  owns.
- Unmarked page reaching the allocator with `check_pages_enabled` on
  (default with `CONFIG_DEBUG_VM`): `free_page_is_bad()` reports
  "page_pool leak" from `page_bad_reason()`, and `__free_pages_prepare()`
  returns false, so the page is not freed.
- Unmarked page with `check_pages_enabled` off: it is freed to the
  allocator with no report.
- Detaching a page: there is no page_pool_release_page() here. The only
  detach is the static `page_pool_return_netmem()`, reached for example
  when `page_pool_put_page()` finds the page refcount is not 1.
- `mlx5e_build_linear_skb()` does not call `skb_mark_for_recycle()`; its
  callers do, for example `mlx5e_skb_from_cqe_linear()`.
- `xdp_build_skb_from_buff()` and `__xdp_build_skb_from_frame()` set the
  mark themselves when the memory type is `MEM_TYPE_PAGE_POOL`;
  `xdp_build_skb_from_zc()` always sets it. A driver using them needs no
  call of its own.

- Reference count: set by `hyp_set_page_refcounted()`, not incremented; it
  does `BUG_ON(p->refcount)`, so a free page with a non-zero count is fatal.
- Tail pages of an order > 0 block: `refcount` stays 0 and `order` stays
  `HYP_NO_ORDER` until `hyp_split_page()`.
- Zeroing: done at free time in `__hyp_attach_page()`, for
  `PAGE_SIZE << order` bytes; `hyp_alloc_pages()` has no `memset()`.
- Callers rely on that zeroing: `hyp_zalloc_hyp_page()` and
  `host_s2_zalloc_page()` return the result of `hyp_alloc_pages()`
  unchanged.
- Free-list node inside the page: cleared by `page_remove_from_list()`, so
  the page is all zero when returned.
- `hyp_pool_init()`: pages below `reserved_pages` are not attached by it, so
  they are not zeroed until their first final `hyp_put_page()`.

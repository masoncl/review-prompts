- Slab page reference count: zero. `alloc_slab_page()` in `mm/slub.c` takes
  frozen pages (for example `alloc_frozen_pages()`), and `__free_slab()`
  returns them with `free_frozen_pages()`, or with
  `free_frozen_pages_nolock()` when `allow_spin` is false.
- Large kmalloc page reference count: also zero; `___kmalloc_large_node()`
  uses `alloc_frozen_pages_noprof()` or `__alloc_frozen_pages_noprof()`. The
  page type is `PGTY_large_kmalloc`.
- `sendpage_ok()`: false for slab memory and for large kmalloc memory, because
  `page_count()` is 0 in both.
- `sendpage_ok()` on a tail page: `PageSlab()` tests only the page given and
  the slab type is set on the head; the `page_count()` test, which goes
  through `page_folio()`, is what rejects it.
- `get_page()` on a slab or large-kmalloc folio: `WARN_ON_ONCE()` and return,
  no reference is taken (`include/linux/mm.h`).
- `put_page()` on a slab or large-kmalloc folio: returns silently, nothing is
  dropped.
- `folio_get()` called directly: no such filter; it hits `VM_BUG_ON_FOLIO()`
  on the zero count, under `CONFIG_DEBUG_VM` only.
- `try_get_page()`: warns once and returns false when the count is 0 or less.
- **Unsafe usage**: giving the `struct page` of a kmalloc buffer to code that
  holds the memory by page reference (`get_page()`, `folio_get()`,
  `MSG_SPLICE_PAGES`). `get_page()` takes no reference and `kfree()` does not
  test the page count, so `kfree()` releases the memory while that code still
  uses it.
  - Safe: test `sendpages_ok()` or `sendpage_ok()` first and clear
    `MSG_SPLICE_PAGES` so the data is copied, as `nvme_tcp_try_send_data()` in
    `drivers/nvme/host/tcp.c` does. `skb_splice_from_iter()` enforces it with
    `WARN_ON_ONCE()` and `-EIO`.
  - Safe: `sg_set_buf()` on a linear-map buffer that is not freed until the
    I/O is complete. It stores page, offset and length and takes no reference;
    `CONFIG_DEBUG_SG` checks the address with `virt_addr_valid()`.

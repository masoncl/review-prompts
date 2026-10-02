- Chain with `CONFIG_NUMA`: `alloc_pages_noprof()` ->
  `alloc_frozen_pages_noprof()` -> `alloc_pages_mpol()` ->
  `__alloc_frozen_pages_noprof()` -> `get_page_from_freelist()` -> `rmqueue()`.
- `alloc_pages_mpol()`: static in `mm/mempolicy.c`, returns a frozen page.
  There is no alloc_pages_mpol_noprof().
- Reference count: set with `set_page_refcounted()` by the wrapper that calls
  the frozen form, for example `alloc_pages_noprof()` (with `CONFIG_NUMA`),
  `folio_alloc_mpol_noprof()`, `__alloc_pages_noprof()`,
  `alloc_pages_nolock_noprof()`.
- Without `CONFIG_NUMA`: no policy layer. `alloc_pages_noprof()` is an inline in
  `include/linux/gfp.h` that calls `alloc_pages_node_noprof()`.
- `__alloc_frozen_pages_noprof()` and `__alloc_pages_noprof()`: take five
  arguments, the last is `alloc_flags`; both are declared in
  `mm/page_alloc.h`.
- `__alloc_pages_noprof()`: has no `EXPORT_SYMBOL()`. There is no
  __alloc_pages_node_noprof(); public entries that take a node are, for
  example, `alloc_pages_node_noprof()` and `__folio_alloc_noprof()`.
- `get_page_from_freelist()` and `rmqueue()`: static in `mm/page_alloc.c`; no
  caller outside that file can enter there.
- `alloc_pages_nolock_noprof()`: goes through
  `alloc_frozen_pages_nolock_noprof()` into `__alloc_frozen_pages_noprof()`
  with `ALLOC_NOLOCK`, not straight to `get_page_from_freelist()`.
- With `ALLOC_NOLOCK` still applied: `current_gfp_context()`,
  `prepare_alloc_pages()` (cpuset), the `__GFP_ACCOUNT` charge.
- With `ALLOC_NOLOCK` skipped: the memory policy, `should_fail_alloc_page()`,
  `alloc_flags_nofragment()`, `__alloc_pages_slowpath()`.

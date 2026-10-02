- `folio_try_get()`: is `folio_ref_add_unless_zero(folio, 1)` in
  `include/linux/page_ref.h`; there is no folio_ref_add_unless() in this
  tree.
- `folio_get()` on a zero count: caught only with `CONFIG_DEBUG_VM`;
  otherwise `VM_BUG_ON_FOLIO()` compiles out and the count goes from 0 to 1.
- `folio_try_get()` context: checks none itself. Page cache lookups hold
  `rcu_read_lock()`; GUP-fast runs with IRQs off, which
  `try_grab_folio_fast()` checks only with `VM_WARN_ON_ONCE()`;
  `page_idle_get_folio()` starts from `pfn_to_online_page()` and holds
  neither.
- **Potentially unsafe usage**: `folio_get()` on a folio the caller took no
  reference on.
  - Unsafe: when the folio was found through something that holds no
    reference, or whose reference nothing held keeps in place: an LRU list,
    the deferred split list, a PFN, the xarray under RCU. The count may be 0,
    freed or frozen.
  - Safe: under the page table lock while a present PTE maps the folio, as
    `copy_present_ptes()` does; `zap_present_folio_ptes()` clears the PTE
    under that lock before the mapping's reference is dropped.
  - Safe: `folio_try_get()` instead, as `isolate_lru_folios()` does under the
    lruvec lock and `deferred_split_isolate()` under the list lock.

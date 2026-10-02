- `folio_has_pincount()`: with `CONFIG_64BIT` true for every large folio;
  otherwise true only for `folio_order(folio) > 1`.
- 32-bit order-1 folio: has no `_pincount`, so a pin adds
  `GUP_PIN_COUNTING_BIAS` to the reference count, as on a small folio.
- Unit: one pin per page, not per call. Pinning n pages of one large folio
  adds n to the reference count and n to `_pincount`.
- Zero folio: a pin changes neither counter. `try_grab_folio()`,
  `try_grab_folio_fast()`, `folio_add_pin()` and `gup_put_folio()` return
  early, so a pin never makes `folio_maybe_dma_pinned()` true for it.
- False while a pin is being taken: GUP-fast takes the plain reference in
  `try_get_folio()` and adds the bias or `_pincount` afterwards.
- Callers that cannot accept that: `folio_needs_cow_for_dma()` asserts, with
  `VM_BUG_ON()`, that `write_protect_seq` is held;
  `__folio_try_share_anon_rmap()` needs the PTE cleared first and issues
  `smp_mb()`.
- Folio without a pin count: any 1024 references read as pinned, `FOLL_GET`
  references included.

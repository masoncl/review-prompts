- `kho_preserve_folio()`: no address or alignment check; its errors are those
  of `kho_radix_add_key()`.
- Scratch overlap: `WARN_ON()` and `-EINVAL` only under
  `CONFIG_KEXEC_HANDOVER_DEBUG`.
- `kho_preserve_folio()`: takes no reference; the caller keeps the folio
  allocated, as `memfd_luo_preserve_folios()` does with `memfd_pin_folios()`.
- `kho_restore_page()`: looks the page up with `pfn_to_online_page()`, not
  `pfn_valid()`; a NULL there returns NULL with no warning.
- Magic mismatch (never preserved, already restored, tail page):
  `WARN_ON_ONCE()` and NULL, nothing written.
- Unaligned `phys`: `PHYS_PFN()` drops the offset, so an address inside the
  head page restores the folio.

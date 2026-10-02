- Sizes: 0 gives `ERR_PTR(-EINVAL)`; `get_order(size) > MAX_PAGE_ORDER` gives
  `ERR_PTR(-E2BIG)`.
- Without `CONFIG_KEXEC_HANDOVER`: the stub returns `ERR_PTR(-EOPNOTSUPP)`.
- Finalize: KHO has no finalize or freeze state here; kho_finalize() is not
  defined, and `kho_unpreserve_free()` has no state check.
- luo_fdt_setup() is not in this tree; `luo_state_setup()` in
  `kernel/liveupdate/luo_core.c` allocates a `struct luo_ser` this way.
- **Unsafe usage**: passing the `ERR_PTR()` result to `kho_unpreserve_free()`
  or `kho_restore_free()`; both filter only NULL.
  - Safe: jump past the free on `IS_ERR()`, as `memfd_luo_preserve()` in
    `mm/memfd_luo.c` does.
- `kho_restore_free()` argument: `phys_to_virt()` of the handed-over physical
  address; the function applies `__pa()` to it.
- One in-tree caller of `kho_restore_free()`: `luo_early_startup()` reads
  `struct luo_ser` through `phys_to_virt()` and, once the size and compatible
  checks pass, calls `kho_restore_free()` on it last. That blob is a
  retrieved subtree, so "Retrieving a subtree" applies: under
  `CONFIG_KEXEC_HANDOVER_DEBUGFS`, `kho_in_debugfs_init()` later points a
  debugfs file at it.
- `kho_restore_free()` on a block already restored: `kho_restore_folio()`
  returns NULL, `WARN_ON()` fires, and no `folio_put()` runs.

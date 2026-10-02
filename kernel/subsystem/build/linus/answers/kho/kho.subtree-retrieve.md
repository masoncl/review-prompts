- `kho_retrieve_subtree()`: takes `(const char *name, phys_addr_t *phys,
  size_t *size)`; `size` may be NULL, as `reserve_mem_kho_retrieve_fdt()`
  passes.
- `-EINVAL`: also returned when `KHO_SUB_TREE_SIZE_PROP_NAME` is missing or
  not 8 bytes long, even if `size` is NULL; `*phys` is already written then.
- `-ENOENT` for no incoming FDT is tested before the NULL test on `phys`.
- `-EOPNOTSUPP`: returned by the stub in `include/linux/kexec_handover.h`
  without `CONFIG_KEXEC_HANDOVER`.
- Mapping: every in-tree consumer uses `phys_to_virt()`; none calls
  `fdt_check_header()` on a sub-blob, only `kho_populate()` does, on the root.
- Struct blobs: check the returned size, then the version, before reading
  fields; see `luo_early_startup()` and `kho_in_kexec_metadata()`.
- FDT blobs: `fdt_node_check_compatible()` then a length test on each
  `fdt_getprop()`; see `reserve_mem_kho_revive()` and `kho_test_restore()`.
- Earliest read: once `kho_populate()` has run; `reserve_mem_kho_revive()`
  reads its blob from the `reserve_mem=` handler, before `kho_memory_init()`.
  `memblock_set_kho_scratch_only()` keeps early allocations off it.
- A consumer need not restore the blob: `reserve_mem_kho_retrieve_fdt()` and
  `kho_in_kexec_metadata()` leave it reserved.
- **Potentially unsafe usage**: freeing a retrieved blob.
  - Unsafe: with `CONFIG_KEXEC_HANDOVER_DEBUGFS`; `kho_in_debugfs_init()`
    creates a file for every incoming subnode that points at the blob, and no
    code removes entries from `kho_in.dbg`.
  - Safe: without `CONFIG_KEXEC_HANDOVER_DEBUGFS`, where
    `kho_in_debugfs_init()` is an empty stub in
    `kernel/liveupdate/kexec_handover_internal.h`.
  - Safe: copying the fields out and leaving the blob reserved, as
    `kho_in_kexec_metadata()` does.

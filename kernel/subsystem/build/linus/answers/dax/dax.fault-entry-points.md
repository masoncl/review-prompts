- `ext4_dax_huge_fault()` in `fs/ext4/file.c`: takes
  `filemap_invalidate_lock_shared()` itself, for reads and writes, before it
  calls `dax_iomap_fault()`.
- `ext4_dax_vm_ops`: all four members reach `ext4_dax_huge_fault()`,
  `.page_mkwrite` included; `ext4_dax_fault()` passes order 0.
- Write test in the handler: `ext4_dax_huge_fault()` and
  `xfs_is_write_fault()` test `FAULT_FLAG_WRITE` and `VM_SHARED`, not
  `vmf->cow_page`, because `cow_page` is unset for a huge fault.
- `vmf->cow_page` is tested in `dax_iomap_pte_fault()` (to set
  `IOMAP_WRITE`) and in `xfs_dax_fault_locked()` (to pick the iomap ops).
- XFS `.map_pages`: there is no xfs_filemap_map_pages() here;
  `xfs_file_vm_ops` installs `filemap_map_pages()`.
- `dax_iomap_pte_fault()` order: i_size test, `grab_mapping_entry()`,
  `pmd_trans_huge()` test, `iomap_iter()` loop around `dax_fault_iter()`,
  store `*iomap_errp`, `dax_unlock_entry()`.
- i_size test: runs before the entry is taken and is not repeated; only the
  caller's lock keeps it true.
- `dax_insert_entry()`: called before every page-table insert of
  `dax_fault_iter()`, `dax_load_hole()` and `dax_pmd_load_hole()`, and before
  the synchronous return; the `cow_page` path and the error returns that come
  before it skip it.
- **Unsafe usage**: reading the `iomap_errp` value after `dax_iomap_fault()`
  without having initialised it.
  - Unsafe: `dax_iomap_pmd_fault()` has no such parameter, and
    `dax_iomap_pte_fault()` returns before the store on the i_size,
    `grab_mapping_entry()` and `pmd_trans_huge()` exits.
  - Safe: set it to 0 before every call, as `__fuse_dax_fault()` does at its
    declaration and again before its retry, or pass NULL, as
    `xfs_dax_fault_locked()` does.

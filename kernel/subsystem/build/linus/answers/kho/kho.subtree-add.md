- `kho_add_subtree()`: takes three arguments, `(const char *name, void *blob,
  size_t size)`; see `kernel/liveupdate/kexec_handover.c`.
- `blob`: any format; nothing checks that it is an FDT. `luo_state_setup()`
  adds a `struct luo_ser`, `kho_out_kexec_metadata()` a
  `struct kho_kexec_metadata`.
- `size`: stored as a `u64` for the next kernel and, under
  `CONFIG_KEXEC_HANDOVER_DEBUGFS`, used as the length of the debugfs file, so
  it must not exceed the preserved allocation.
- `name`: copied by `fdt_add_subnode()` and by `debugfs_create_blob()`; needed
  only for the duration of the call.
- Blob contents: may be rewritten in place until kexec; only the address and
  `size` are captured. `luo_session_serialize()` writes
  `luo_ser->sessions_pa` after the add.
- Return values: 0, `-EEXIST` (name already a child of the root),
  `-ENOMEM` (every other libfdt failure, including either `fdt_setprop()`;
  the new node is deleted first).
- `-EOPNOTSUPP`: returned by the stub in `include/linux/kexec_handover.h`
  without `CONFIG_KEXEC_HANDOVER`.
- No other errno: the body has no test for KHO being enabled and there is no
  finalized state.
- **Unsafe usage**: adding a blob whose pages are not preserved.
  - Unsafe: `kho_add_subtree()` preserves nothing; the next kernel reserves
    only what the radix tree lists, in `kho_mem_retrieve()`.
  - Safe: `kho_alloc_preserve()` first, as `luo_state_setup()` does.
  - Safe: `alloc_page()` then `kho_preserve_pages()`, as `prepare_kho_fdt()`
    does; `kho_preserve_folio()`, as `kho_test_preserve()` does.

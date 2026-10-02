- Required order: `kho_remove_subtree()` before the blob is unpreserved or
  freed, and each unpreserve before its free.
- Blob versus data: no order is required; `kho_test_cleanup()` and
  `memfd_luo_unpreserve()` unpreserve the data first and the blob last.
- Full sequence: `prepare_kho_fdt()` in `mm/memblock.c` preserves the blob,
  adds it, preserves data, and unwinds with `kho_remove_subtree()`,
  `kho_unpreserve_pages()`, `put_page()`.
- Second full sequence, in source only: `kho_test_exit()` in `lib/test_kho.c`
  calls `kho_remove_subtree()`, then `kho_test_cleanup()`. It never runs,
  because `TEST_KEXEC_HANDOVER` is bool and the function is `__exit`, and it
  does not test whether `kho_test_save()` ran, so it does not show how to
  meet the rule in "Calling the API when disabled".
- `kho_test_preserve()` error path: has no `kho_remove_subtree()`, because
  `kho_add_subtree()` is its last step.
- luo_fdt_setup() is not in this tree; `luo_state_setup()` in
  `kernel/liveupdate/luo_core.c` has no `kho_remove_subtree()` either, because
  `kho_add_subtree()` is its last step that can fail.
- Failed `kho_add_subtree()`: it deletes its own node, so the caller only
  unpreserves and frees, as `kho_out_kexec_metadata()` does.
- `kho_remove_subtree()`: finds the node by the blob's physical address;
  returns void and does nothing when no node matches.
- debugfs: `kho_debugfs_blob_add()` keeps the blob pointer only under
  `CONFIG_KEXEC_HANDOVER_DEBUGFS`; otherwise it is a stub that returns 0.

- State when disabled: `kho_init()` returns before creating anything, so
  `kho_out.radix_tree.root` and `kho_out.fdt` are NULL; the same holds before
  `kho_init()` runs and after it fails.
- No function in the table tests `kho_enable`:

| Function | With `kho_out` state NULL |
|---|---|
| `kho_preserve_folio()`, `kho_preserve_pages()` | `-EINVAL` after `WARN_ON_ONCE(!tree->root)` in `kho_radix_add_key()` |
| `kho_preserve_vmalloc()` | `-ENOMEM` for a valid area, because `new_vmalloc_chunk()` fails |
| `kho_alloc_preserve()` | `ERR_PTR(-EINVAL)`; the folio is freed |
| `kho_unpreserve_folio()`, `kho_unpreserve_pages()` | `WARN_ON_ONCE()` in `kho_radix_del_key()`, then return |
| `kho_unpreserve_free()` | same warning, then still drops the folio |
| `kho_add_subtree()`, `kho_remove_subtree()` | NULL pointer dereference in `fdt_open_into()` |
| `kho_retrieve_subtree()`, restore functions | unaffected; work on a handover boot with `kho=off` |

- **Potentially unsafe usage**: calling `kho_add_subtree()` or
  `kho_remove_subtree()`.
  - Unsafe: when nothing on the path proves `kho_init()` set up
    `kho_out.fdt`: `kho=off`, a call before `fs_initcall`, or a
    `kho_is_enabled()` test made before `kho_init()` ran; `fdt_open_into()`
    reads the header through NULL.
  - Safe: after `kho_is_enabled()` read true at `late_initcall` or later, as
    `reserve_mem_init()` in `mm/memblock.c` does; `kho_init()` clears
    `kho_enable` on every failure.
  - Safe: after a preserve call on the same path succeeded, as
    `luo_state_setup()` does with `kho_alloc_preserve()`; `kho_init()` sets the
    radix root and `kho_out.fdt` together and tears both down on failure.
  - Safe: inside `kho_init()` after `kho_out_fdt_setup()` returned 0, as
    `kho_out_kexec_metadata()` does.
  - Safe: `kho_remove_subtree()` for a blob whose `kho_add_subtree()` returned
    0, as the error path of `prepare_kho_fdt()` does.
- `luo_late_startup()`: tests only `liveupdate_enabled()`, decided at
  `early_initcall`; after a later `kho_init()` failure it is the failing
  `kho_alloc_preserve()` that keeps it from `kho_add_subtree()`.
- Unpreserve functions: call only for a preservation that succeeded;
  otherwise, while `kho_out.radix_tree.root` is NULL, they hit
  `WARN_ON_ONCE()`.
- Incoming side: `luo_early_startup()` and `kho_test_init()` skip retrieval
  when `kho_is_enabled()` is false; `reserve_mem_kho_revive()` does not test it.
- `mm/memblock.c`: calls no restore function; `reserve_mem_kho_revive()` only
  re-registers the range with `reserved_mem_add()`.
- Callers of `kho_add_subtree()`: the only one that runs at `fs_initcall` is
  `kho_out_kexec_metadata()`, inside `kho_init()` after `kho_out_fdt_setup()`;
  nothing under `kernel/` outside `kernel/liveupdate/` calls it.

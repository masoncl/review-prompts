- Order; the first three steps run on the boot CPU before any initcall:

| Step | Called from | Runs when |
|---|---|---|
| `kho_populate()` | x86: `add_kho()` from `parse_setup_data()`; DT: `early_init_dt_check_kho()`, last call in `early_init_dt_scan_nodes()` | inside `setup_arch()`, only if the previous kernel passed KHO data |
| `kho_memory_init_early()` | first call in `mm_core_init_early()` in `mm/mm_init.c` | `start_kernel()`, right after `setup_arch()`, before `free_area_init()` |
| `kho_memory_init()` | `mm_core_init()` | immediately before `memblock_free_all()` |
| `kho_init()` | `fs_initcall` | `do_initcalls()` |

- `kho_populate()` on x86: runs before `parse_early_param()`, and neither it nor
  its callers read `kho_enable`.
- `kho_memory_init_early()`: returns at once unless `is_kho_boot()`; otherwise
  sets `kho_scratch`, initialises `kho_in.radix_tree` from the incoming FDT and
  calls `kho_extend_scratch()`.
- `kho_memory_init()`: calls `kho_mem_retrieve()` when `kho_in.scratch_phys` is
  set, else `kho_reserve_scratch()`; there is no kho_release_scratch() here.
- `kho_init()`: the only place that creates outgoing state
  (`kho_out.radix_tree.root`, `kho_out.fdt`).
- First safe call:

| Functions | First usable after | Called earlier |
|---|---|---|
| `kho_retrieve_subtree()` | `kho_populate()`, once `phys_to_virt()` of the FDT is mapped (`kho_populate()` itself uses `early_memremap()`); `reserve_mem()` in `mm/memblock.c` (`__setup`) calls it before `kho_memory_init()` | `-ENOENT` |
| `kho_restore_folio()`, `kho_restore_pages()`, `kho_restore_free()` | `kho_memory_init()`; first in-tree use is `luo_early_startup()` at `early_initcall` | `kho_restore_page()` returns NULL; the magic it tests is written by `kho_preserved_memory_reserve()` |
| `kho_restore_vmalloc()` | as above, plus `vmalloc_init()`, which runs later in `mm_core_init()` | — |
| `kho_preserve_folio()`, `kho_preserve_pages()`, `kho_preserve_vmalloc()`, `kho_alloc_preserve()`, the unpreserve functions | a successful `kho_init()` | `WARN_ON_ONCE(!tree->root)`; preserve fails |
| `kho_add_subtree()`, `kho_remove_subtree()` | a successful `kho_init()` | NULL `kho_out.fdt` is dereferenced in `fdt_open_into()` |

- Outside `kho_init()`, in-tree outgoing users run at `late_initcall`,
  `module_init` or runtime, for example `luo_late_startup()` and
  `reserve_mem_init()`.

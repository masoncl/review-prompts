- `KHO_FDT_COMPATIBLE`: `"kho-v4"`.
- Each subtree: one child node of the root, named by the caller, with two
  properties.

| Macro | Name | Written as | Reader requires |
|---|---|---|---|
| `KHO_SUB_TREE_PROP_NAME` | `"preserved-data"` | `phys_addr_t` | 8 bytes |
| `KHO_SUB_TREE_SIZE_PROP_NAME` | `"blob-size"` | `u64` | 8 bytes |

- `KHO_FDT_MEMORY_MAP_PROP_NAME`: one `u64`, the physical address of
  `kho_out.radix_tree.root`, a `struct kho_radix_node`; written once in
  `kho_out_fdt_setup()`.
- There is no struct khoser_mem_chunk and no KHO_FDT_SUB_TREE_PROP_NAME here.
- Byte order: CPU-native in the root FDT and in both in-tree sub-FDTs; values
  go in as raw bytes through `fdt_property()` and `fdt_setprop()`. None of
  this code calls `cpu_to_fdt64()`.
- Reads: `kho_get_mem_map_phys()` uses `get_unaligned()`;
  `kho_retrieve_subtree()`, `kho_remove_subtree()`, `kho_in_debugfs_init()`
  and `reserve_mem_kho_revive()` dereference the `fdt_getprop()` pointer.
- In-tree sub-FDTs: only `MEMBLOCK_KHO_FDT` (`prepare_kho_fdt()`) and
  `KHO_TEST_FDT` (`lib/test_kho.c`). The `LUO_KHO_ENTRY_NAME` and
  `KHO_METADATA_NODE_NAME` blobs are packed structs, not FDTs.
- memblock sub-FDT: one node per `reserve_mem` entry, named after it, with
  `"start"` and `"size"` written raw from `struct reserve_mem_table`
  (`phys_addr_t`); `include/linux/kho/abi/memblock.h` documents them as u64.
- Size limit: one page, and not only in the core. `setup_kho()` in
  `arch/x86/kernel/kexec-bzimage64.c` and `kho_add_chosen()` in
  `drivers/of/kexec.c` pass `PAGE_SIZE` as the FDT length to the next kernel.
- Root FDT full: `kho_add_subtree()` returns `-ENOMEM`.

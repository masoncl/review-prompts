- Location: core is `kernel/liveupdate/kexec_handover.c`, with
  `kernel/liveupdate/kexec_handover_debugfs.c` and
  `kernel/liveupdate/kho_block.c`; there is no kernel/kexec_handover.c.
  Handed-over layouts are in `include/linux/kho/abi/`.
- No finalize step: there is no kho_finalize(), kho_abort(),
  struct kho_serialization, notifier chain or debugfs finalize file.
- debugfs under `kho/`: read-only blobs plus `scratch_phys` and
  `scratch_len`; it controls nothing.
- Preserved-memory tracker: `struct kho_radix_tree`
  (`include/linux/kho_radix_tree.h`), one tree for all orders; a key
  from `kho_encode_radix_key()` carries both physical address and order.
- There is no struct kho_mem_track, struct khoser_mem_chunk or
  struct kho_mem_phys, and no per-order xarray.
- `struct kho_radix_node` and `struct kho_radix_leaf`: one page each, linked
  by physical address, so the tree is handed over in place with no
  flattening.
- Tracker node pages: not keys in the tracker themselves; they stay intact
  until walked because early allocation is confined to scratch, and
  `kho_extend_scratch()` counts them as busy.
- `struct kho_out` and `struct kho_in`: each embeds its own
  `struct kho_radix_tree`; the incoming one wraps the previous kernel's root
  page (`kho_memory_init_early()`) and is used only by `__init` code.
- `struct kho_out`: `lock` protects the root FDT, not the tracker; each tree
  has its own `lock`; there is no finalized flag.
- `union kho_page_info`: magic plus order, stamped into `page->private` of
  the first page of each preserved block (one tracker key) by
  `kho_preserved_memory_reserve()` during the boot-time walk.
- `kho_restore_folio()` and `kho_restore_pages()`: read only that stamp; they
  do not consult `struct kho_in` or the tracker.
- Order-0 runs: `kho_preserve_pages()` and `kho_restore_pages()`; there is
  no kho_preserve_phys() or kho_restore_phys().
- `struct kho_kexec_metadata`: KHO's own sub-blob, `KHO_METADATA_NODE_NAME`,
  registered in `kho_init()`; the next kernel copies it into `struct kho_in`.
- `struct kho_block_set`: chain of preserved pages, each headed by
  `struct kho_block_header_ser`, holding fixed-size entries; LUO sessions and
  files use it. It is linked into `luo.o`, so it needs `CONFIG_LIVEUPDATE`,
  not only `CONFIG_KEXEC_HANDOVER`.
- Clients: no IOMMU or vfio user in this tree; search callers of
  `kho_add_subtree()` and `kho_preserve_folio()`. `mm/memfd_luo.c` calls the
  preserve functions itself, hands the result to LUO as `serialized_data`,
  and registers no sub-blob of its own.
- Passing to the next kernel: never the command line. `kho_fill_kimage()`
  fills `kho` in `struct kimage`; x86 sends `struct kho_data` as
  `SETUP_KEXEC_KHO` setup data, devicetree arches send `linux,kho-fdt` and
  `linux,kho-scratch` under `/chosen` (`drivers/of/kexec.c`); both reach
  `kho_populate()`.
- Two meanings of scratch on a KHO boot: the `kho_scratch` array of
  `struct kho_scratch`, and memblock regions flagged `MEMBLOCK_KHO_SCRATCH`.
  `kho_extend_scratch()` also flags every range outside the
  `KHO_SCRATCH_EXT_BLKSIZE` blocks that hold preserved memory or tracker
  nodes.
- `kho_scratch` array only: `kho_scratch_overlap()` (hence `MIGRATE_CMA`) and
  kexec image placement in `kho_locate_mem_hole()` ignore the extended
  ranges.

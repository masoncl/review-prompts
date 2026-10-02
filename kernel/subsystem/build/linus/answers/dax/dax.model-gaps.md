- Models take a DAX filesystem's `struct iomap_ops` to be an `iomap_begin` and
  `iomap_end` pair. Here it has a third member `iomap_next`, which
  `iomap_iter()` in `fs/iomap/iter.c` calls when set; for example
  `fuse_iomap_ops` in `fs/fuse/dax.c` sets only `.iomap_next`, built with
  `DEFINE_IOMAP_ITER_NEXT_END()`.
- Models take the loop body of `iomap_iter()` to report progress through a
  processed count. Here the body sets `iter.status` and moves on with
  `iomap_iter_advance()`, which takes a byte count by value; see
  `dax_iomap_pte_fault()` in `fs/dax.c`.
- Models take `.pfn_mkwrite` to be all that `vm_mixed_zeropage_allowed()` in
  `mm/memory.c` needs on a shared mapping that may be written. It also
  requires `vma_is_fsdax()` or `VM_IO`.
- Models take a DAX PTE to be a special devmap pfn mapping. Nothing named
  pte_devmap is in this tree.
- Models take a hmem or CXL `struct dev_dax` to bind to the character device
  driver by default. `dax_hmem_probe()` and `cxl_dax_region_probe()` pass
  `IORESOURCE_DAX_KMEM`, so with `CONFIG_DEV_DAX_KMEM` `dax_match_type()`
  picks kmem; hmem drops the flag only when its `region_idle` parameter is
  set.
- Models take dax_hmem to create a device for every soft-reserved range. With
  `CONFIG_DEV_DAX_CXL`, `hmem_register_device()` in `drivers/dax/hmem/hmem.c`
  skips a range that intersects `IORES_DESC_CXL`; `process_defer_work()` later
  registers it only if `cxl_region_contains_resource()` is false.
- Models do not know `kzalloc_obj()`, `kzalloc_flex()` and `kmalloc_objs()`.
  They are defined in `include/linux/slab.h` and used in
  `drivers/dax/bus.c` and `drivers/dax/kmem.c`.

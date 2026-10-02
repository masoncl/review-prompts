- Without `mem_base`: the cell's `parent` is copied to the child together with
  `start` and `end`; it is not forced to NULL.
- `platform_device_add()`: calls `insert_resource()`, not
  `request_resource()`, for every resource that has a `parent` or whose
  `resource_type()` is `IORESOURCE_MEM` or `IORESOURCE_IO`.
- `insert_resource()` under `mem_base`: does not need `mem_base` itself to be
  in the `iomem_resource` tree.
- Failed insert: happens when the range lies outside `mem_base` or partly
  overlaps a resource already under it; see `__insert_resource()` in
  `kernel/resource.c`.
- Temporary array in `mfd_add_device()`: allocated with `kzalloc_objs()`; the
  function does not call `kcalloc()`.
- **Unsafe usage**: a child requests its range while the parent holds a busy
  region that covers it, including one that encloses the whole `mem_base`;
  the child's request fails with `-EBUSY`.
  - Safe: the parent maps without requesting, as `vexpress_sysreg_probe()` in
    `drivers/mfd/vexpress-sysreg.c` does with `devm_ioremap()`, and each child
    requests its own range. `__request_region_locked()` defines the
    requirement: it descends only through resources without
    `IORESOURCE_BUSY`.

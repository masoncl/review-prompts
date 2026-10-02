- Without `CONFIG_ARCH_HAS_PMEM_API`: `dax_flush()` itself is the empty second
  definition in `drivers/dax/super.c`; it tests no flag and calls nothing.
- `DAXDEV_WRITE_CACHE` clear: `dax_flush()` returns before
  `arch_wb_cache_pmem()`; the flag is written only by `dax_write_cache()`, and
  the enum is private to `drivers/dax/super.c`.
- Callers of `dax_write_cache()`: search for the name; the one that is easy to
  miss is `write_cache_store()` in `drivers/nvdimm/pmem.c`, which lets
  userspace set or clear the flag at run time through sysfs.

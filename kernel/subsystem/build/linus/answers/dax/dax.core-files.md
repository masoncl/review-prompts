| Job | File | Easy to miss |
|---|---|---|
| Third driver on the DAX bus | `drivers/dax/fsdev.c` (`fsdev_dax.o`, `CONFIG_DEV_DAX_FSDEV`) | type `DAXDRV_FSDEV_TYPE` |
| Region glue, persistent memory | `drivers/dax/pmem.c` | a `struct nd_device_driver` on the nvdimm bus, not a DAX-bus driver; its device comes from `drivers/nvdimm/dax_devs.c` |
| Region glue, CXL | `drivers/dax/cxl.c` | a `struct cxl_driver`; its device comes from `drivers/cxl/core/region_dax.c` |
| Region glue, firmware-reserved: driver | `drivers/dax/hmem/hmem.c` (`CONFIG_DEV_DAX_HMEM`) | two `struct platform_driver`, `dax_hmem_platform_driver` and `dax_hmem_driver`; neither calls `dax_driver_register()` |
| Region glue, firmware-reserved: resource list | `drivers/dax/hmem/device.c` (`CONFIG_DEV_DAX_HMEM_DEVICES`) | registers the `hmem_platform` device; `drivers/acpi/numa/hmat.c` feeds it through `hmem_register_resource()` |
| Private header for glue and drivers | `drivers/dax/bus.h` | the only private DAX header the glue files include; none includes `drivers/dax/dax-private.h` |
| Private header for core and bus drivers | `drivers/dax/dax-private.h` | also included by `tools/testing/nvdimm/dax-dev.c` |
| sysfs attribute outside `drivers/dax/bus.c` | `drivers/dax/kmem.c` | `state`, on devices bound to kmem |
| Tracepoints | `include/trace/events/fs_dax.h` | instantiated by `fs/dax.c` only; `drivers/dax/` has no trace events |
| Documentation, sysfs ABI | `Documentation/ABI/testing/sysfs-bus-dax` | |
| Documentation, CXL use of DAX | `Documentation/driver-api/cxl/linux/dax-driver.rst`, `Documentation/driver-api/cxl/allocation/dax.rst` | |
| Test build, nvdimm | `tools/testing/nvdimm/Kbuild` | rebuilds `super.c`, `bus.c`, `device.c` and `pmem.c` from `drivers/dax/`; does not rebuild `kmem.c`, `cxl.c` or `fsdev.c` |
| Test override of a DAX function | `tools/testing/nvdimm/dax-dev.c` | strong `dax_pgoff_to_phys()`; the one in `drivers/dax/bus.c` is `__weak` |
| Test resource and remap wrappers | `tools/testing/nvdimm/test/iomap.c` | targets of the `--wrap=` lines in the `Kbuild`, `devm_memremap_pages()` among them |
| Test build, CXL | `tools/testing/cxl/Kbuild` | rebuilds `drivers/dax/hmem/hmem.c` with `--wrap=walk_hmem_resources` |

- Models take `devm_cxl_add_region()` to hang region removal on a devres
  action. It registers none: a region sits in the `regions` xarray of
  `struct cxl_root_decoder`, and `unregister_region()` in
  `drivers/cxl/core/region.c` removes it under `regions_lock`, for example
  from `delete_region_store()`, `kill_regions()` or
  `endpoint_unregister_region()`.
- Models take `cxld_unregister()` to act on endpoint decoders only. For a root
  decoder it calls `kill_regions()`, which unregisters every region left and
  sets `cxlrd->dead`; `__create_region()` then returns `-ENXIO`.
- Models take every committed region to spawn a pmem or dax child device.
  `cxl_region_probe()` returns 0 with no child when a target memdev has
  `attach` (`cxl_region_has_memdev_attach()`), or when a ram region overlaps
  System RAM.
- Models take `cxl_mem_sanitize()` to hold `cxl_rwsem.region` alone. It takes
  the memdev device lock first, with `guard(device)(&cxlmd->dev)`.
- Models take a trace array to match the size of the hardware data. The
  `header_log` field is `CXL_HEADERLOG_TRACE_SIZE_U32` (128) while hardware
  gives `CXL_HEADERLOG_SIZE_U32` (16); callers pass a zero-filled 128-entry
  buffer, and a `static_assert()` in `drivers/cxl/core/ras.c` pins the size.
- Models gate CXL error handling on PCIEAER_CXL or CXL_RCH_RAS.
  `CONFIG_CXL_RAS` in `drivers/cxl/Kconfig` is the gate, and it depends on
  `ACPI_APEI_GHES` as well as `PCIEAER`.
- Models know only `rwsem_write_kill` and `rwsem_read_intr` as conditional
  guard classes here. `mutex_intr` is also used on `poison.mutex` in
  `cxl_mem_get_poison()`, and `device_intr` on the memdev in
  `drivers/cxl/mem.c`.
- Models take CXL symbols to be exported in namespace `CXL`.
  `devm_cxl_add_endpoint()` (in `drivers/cxl/port.c`) and
  `cxl_memdev_attach_region()` use `EXPORT_SYMBOL_FOR_MODULES()` for `cxl_mem`
  alone.
- Models place the definition of `cxl_rwsem` in `drivers/cxl/core/port.c` or
  `drivers/cxl/core/region.c`. It is in `drivers/cxl/core/hdm.c` and is not
  exported.
- Models name find_cxl_port(). It is not defined; `find_cxl_port_by_dport()`
  and `find_cxl_port_by_uport()` in `drivers/cxl/core/port.c` look a port up.
- Models spell the DVSEC ids and offsets with a CXL_DVSEC prefix. They are
  `PCI_DVSEC_CXL_DEVICE`, `PCI_DVSEC_CXL_RANGE_SIZE_LOW()` and so on in
  `include/uapi/linux/pci_regs.h`; only `CXL_DVSEC_RANGE_MAX` has that
  prefix.

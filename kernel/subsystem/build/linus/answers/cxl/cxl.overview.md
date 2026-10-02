- Scope: besides class-code Type-3 expanders bound by `drivers/cxl/pci.c`,
  the core serves Type-2 (accelerator) drivers outside `drivers/cxl/`, for
  example `drivers/net/ethernet/sfc/efx_cxl.c`, through `include/cxl/cxl.h`.
- `struct cxl_memdev`: not Type-3 only. `devm_cxl_add_classdev()` and
  `devm_cxl_probe_mem()`, both in `drivers/cxl/mem.c`, create it; its parent is
  `cxlds->dev`, whichever driver owns that device.
- `is_cxl_memdev()`: matches two device types, `cxl_class_memdev_type` and
  `cxl_memdev_type`; only the first carries the memdev sysfs groups.
- `struct cxl_dev_state`: allocated devm on the parent device by
  `_devm_cxl_dev_state_create()`; the memdev only points at it, and
  `cxl_memdev_shutdown()` clears `cxlmd->cxlds`.
- `struct cxl_mailbox`: embedded in `struct cxl_dev_state` as `cxl_mbox`, not in
  `struct cxl_memdev_state`.
- `struct cxl_memdev_attach`: set by the memdev creator to say it cannot work
  without the CXL link. With `cxlmd->attach` set:
  - `cxl_mem_probe()` calls `attach->probe()` after the endpoint is added.
- Endpoint `struct cxl_port`: device child of the port that owns
  `parent_dport` (`cxl_port_alloc()` in `drivers/cxl/core/port.c`); the memdev
  is its `uport_dev`, never its parent.
- `struct cxl_dport` of the root port: created up front by
  `add_host_bridge_dport()` in `drivers/cxl/acpi.c`.
- Switch port right after probe: has no dports, no decoders, and no
  `struct cxl_hdm` drvdata; `cxl_port_add_dport()` sets those up when the first
  dport arrives.
- `struct cxl_region_ref`: one per region on every port from the endpoint port
  up to, not including, the root; the decoder it names also gets
  `cxld->region` set, switch decoders included (`cxl_rr_ep_add()` in
  `drivers/cxl/core/region.c`).
- Port reaping: `cxl_detach_ep()` removes a port that lost its last
  `struct cxl_ep` only if its parent is not the root; host-bridge ports stay.
- Partitions: ram or pmem is `enum cxl_partition_mode`; there is no
  enum cxl_decoder_mode. An endpoint decoder names its partition by index
  `part` into `cxlds->part[]` (`struct cxl_dpa_partition`).
- Locks: there is no cxl_region_rwsem or cxl_dpa_rwsem object; the region and
  DPA rwsems are `cxl_rwsem.region` and `cxl_rwsem.dpa` (`struct cxl_rwsem` in
  `drivers/cxl/core/core.h`).
- `port->regions`: changed under `cxl_rwsem.region` held for write, asserted
  in `cxl_port_attach_region()`; an entry is added to `dports` or `endpoints`
  under the port device lock, which `add_dport()` asserts and `add_ep()`
  takes.

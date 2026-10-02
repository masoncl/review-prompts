- There is no devm_cxl_add_memdev() in this tree; a comment in
  `drivers/cxl/core/memdev.c` still names it.
- `__devm_cxl_add_memdev()` in `drivers/cxl/core/memdev.c`: the common helper;
  exported with `EXPORT_SYMBOL_FOR_MODULES()` to `cxl_mem` only, so another
  module cannot call it or pass its own `struct cxl_memdev_attach`.

| Device | Create state | Before registering | Register memdev | In-tree callers |
|---|---|---|---|---|
| class memory | `cxl_memdev_state_create()`; fails with `ERR_PTR(-ENOMEM)` | mailbox, identify, `cxl_dpa_setup()` | `devm_cxl_add_classdev()` (no descriptor) | `cxl_pci_probe()`, `cxl_mock_mem_probe()` |
| accelerator | `devm_cxl_dev_state_create()` with `CXL_DEVTYPE_DEVMEM`; fails with NULL | set `cxlds->media_ready`, `cxl_set_capacity()` | `devm_cxl_probe_mem()` (always a descriptor) | `efx_cxl_init()` in `drivers/net/ethernet/sfc/efx_cxl.c`, `cxl_mock_accel_probe()` in `tools/testing/cxl/test/accel.c` |

- `devm_cxl_add_classdev()` and `devm_cxl_probe_mem()`: both defined in
  `drivers/cxl/mem.c`; both return `ERR_PTR()` on failure, never NULL.
- `cxlds->media_ready`: nothing under `drivers/cxl/core` sets it, so an
  accelerator driver sets it itself; `cxl_mem_probe()` returns `-EBUSY` when
  it is false, which fails `devm_cxl_probe_mem()`.
- `devm_cxl_probe_mem()`: allocates a `struct cxl_attach_region` whose
  `.probe` is `cxl_memdev_attach_region()` in `drivers/cxl/core/region.c`;
  that is the only `struct cxl_memdev_attach` in the tree.
- `cxl_memdev_attach_region()`: creates no region; it fails with `-ENXIO`
  unless an endpoint decoder is already mapped to a committed region with one
  target.
- Without `CONFIG_CXL_REGION`: `cxl_memdev_attach_region()` is a stub that
  returns `-EOPNOTSUPP`, so `devm_cxl_probe_mem()` cannot succeed.
- Bind failure with a descriptor: `cxl_memdev_autoremove()` calls
  `cxl_memdev_unregister()` and returns `ERR_PTR(-ENXIO)` whatever
  `cxl_mem_probe()` returned; the test is `cxl_memdev_attach_failed()`, under
  the memdev device lock.
- `*hpa_range` from `devm_cxl_probe_mem()`: also written when
  `__devm_cxl_add_memdev()` fails, as `{ 0, -1 }` unless the callback reached
  its end; test the returned pointer, not the range.
- Detach with a descriptor: `detach_memdev()` calls
  `device_release_driver(cxlmd->dev.parent)`, which unbinds the accelerator's
  own driver; the memdev is then unregistered by the parent's devm action
  `cxl_memdev_unregister()`.
- Detach trigger: `schedule_detach()` in `drivers/cxl/port.c` is a devm action
  of the endpoint port, added by `cxl_endpoint_port_probe()`; it queues
  `detach_work` on `cxl_bus_wq` whenever that port is unbound, so the parent
  is unbound asynchronously.
- Region on detach: `endpoint_unregister_region()` is a devm action on the
  same endpoint port, so the region behind `hpa_range` is unregistered when
  the port unbinds and does not wait for the parent driver's remove callback.

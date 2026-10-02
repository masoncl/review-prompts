- `port->dports`: keyed by `(unsigned long)dport->dport_dev`; look up with
  `cxl_find_dport_by_dev()`.
- `port_id`: not a key; `find_dport()` scans every dport, and `add_dport()`
  returns `-EBUSY` when the `port_id` is already in use.
- `port->endpoints`: keyed by `(unsigned long)ep->ep`, which is `&cxlmd->dev`;
  look up with `cxl_ep_load()` in `drivers/cxl/cxlmem.h`.
- `struct cxl_ep` entries for a memdev: held by the switch and host bridge
  ports above it, not by its endpoint port; `cxl_add_ep()` is called only from
  the enumeration walk.
- `port->regions`: holds `struct cxl_region_ref`, keyed by the
  `struct cxl_region` pointer; see `cxl_rr_load()` in
  `drivers/cxl/core/region.c`.
- `is_cxl_root()`: tests `port->uport_dev == port->dev.parent`; it does not
  look at what kind of device `uport_dev` is.
- `cxl_device_id()` in `drivers/cxl/core/port.c`: gives the root
  `CXL_DEVICE_ROOT` and every other port `CXL_DEVICE_PORT`.
- Root port: no driver in this tree registers with `CXL_DEVICE_ROOT`, so its
  `dev.driver` stays NULL.

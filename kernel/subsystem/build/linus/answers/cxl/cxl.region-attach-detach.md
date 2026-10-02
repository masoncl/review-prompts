- `check_interleave_cap()` on the endpoint decoder: the first test in
  `cxl_region_attach()`, for auto regions too.
- `cxled->part < 0`: `-ENODEV`, before the mode comparison.
- Size test: `resource_size(cxled->dpa_res) * p->interleave_ways +
  p->cache_size` must equal `resource_size(p->res)`.
- `cxl_region_attach()` does not compare the endpoint decoder's `hpa_range`
  with the region; the user path overwrites it from `p->res`.
- `cxl_region_attach_position()`: the endpoint's host-bridge dport must equal
  `cxlrd->cxlsd.target[pos % iw]`, `iw` being the root decoder's ways.
- Walk in `cxl_region_attach_position()`: starts at the endpoint port itself,
  where `cxl_port_pick_region_decoder()` returns the endpoint decoder.
- `cxl_rr_ep_add()`: sets `cxld->region` and takes a region device reference
  per decoder; `cxl_rr_free_decoder()` drops both when the ref is freed.
- Detach walk: `cxl_port_detach_region()` from the endpoint port up to the
  root.
- Detach from `> CXL_CONFIG_ACTIVE`: resets the decoders of all
  `p->interleave_ways` targets, not only the one leaving.
- Detach with `CXL_REGION_F_LOCK`: no hardware reset; with
  `CXL_REGION_F_AUTO`: `cxl_region_teardown_targets()` does nothing.
- Detach leaves `p->res`, ways, granularity and `cxled->pos` as they were.
- `device_release_driver()`: called whenever `__cxl_decoder_detach()` returns
  a region, whatever the state was.
- Rebind: `__commit()` does not bind the region driver; the only
  `device_attach()` in `drivers/cxl/core/region.c` is in
  `cxl_add_to_region()`, and `cxl_bus_rescan()` in `drivers/cxl/core/port.c`
  calls `device_attach()` on every device on the bus.

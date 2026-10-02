- There is no cxl_decoder_kill_region() here; `cxld_unregister()` in
  `drivers/cxl/core/port.c` is the `DETACH_INVALIDATE` caller, for endpoint
  decoders.
- `cxl_endpoint_decoder_release()`: the device release callback; it does not
  detach.
- Lock: `cxl_decoder_detach()` takes `cxl_rwsem.region` itself in both modes;
  no caller holds it.
- `DETACH_INVALIDATE` invalidates the decoder, not the region: it sets
  `cxled->part = -1` and, apart from the locking, nothing else differs.
- Lookup by decoder with `cxled->cxld.region` NULL: calls
  `cxl_cancel_auto_attach()`, which removes a staged decoder from
  `p->targets[]`; no driver release.
- Return value: 0 also when no target was found.
- Root decoder teardown: `kill_regions()` calls `unregister_region()`, which
  detaches each position through `detach_target()`, so with `DETACH_ONLY`.

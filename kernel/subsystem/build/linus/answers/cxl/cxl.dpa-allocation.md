- There is no cxled_dpa_next() here; `__cxl_dpa_alloc()` in
  `drivers/cxl/core/hdm.c` places the allocation after the last child of the
  partition resource.
- `port->hdm_end`: set to -1 in `cxl_port_alloc()`, then changed only in
  `__cxl_dpa_reserve()` and `__cxl_dpa_release()`, both of which assert
  `cxl_rwsem.dpa` held for write.
- Order test: on the decoder id only; `__cxl_dpa_reserve()` and
  `cxl_dpa_free()` do not look at HPA.
- Skip in `__cxl_dpa_alloc()`: non-zero only for a partition index above 0;
  it runs from the end of the last allocation in the nearest lower partition
  that has one (or from the start of partition 0) to the start of the chosen
  partition.
- Within one partition `__cxl_dpa_alloc()` never produces a skip.
- Skip at enumeration: `init_hdm_decoder()` reads it from the skip registers
  and reserves at a running base that sums the size and skip of the lower
  decoders; no DPA base is read from hardware.
- Skip resource: requested under the decoder's own name and split at
  partition boundaries by `__adjust_skip()`; it lies below `dpa_res->start`.
- Capacity under a skip: a later allocation in that lower partition gets
  `-ENOSPC` until the skipping decoder is freed.
- `-EBUSY` from `__cxl_dpa_alloc()`: `cxled->cxld.region` set,
  `CXL_DECODER_F_ENABLE` set, or `cxled->part` negative.
- `-EBUSY` from `__cxl_dpa_reserve()`: `dpa_res` already set, id not
  `hdm_end + 1`, or the skip or the range conflicts in `cxlds->dpa_res`.
- `__cxl_dpa_reserve()` with zero length: `-EINVAL`.
- `dpa_size_store()` in `drivers/cxl/core/port.c`: rejects a size not aligned
  to `SZ_256M`, then calls `cxl_dpa_free()` before `cxl_dpa_alloc()`, so a
  resize fails with `-EBUSY` on any decoder that is not `hdm_end`.

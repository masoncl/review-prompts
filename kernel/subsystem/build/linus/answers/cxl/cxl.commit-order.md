- `port->commit_end` and `CXL_DECODER_F_ENABLE` in `cxl_decoder_commit()`:
  changed only after `cxld_await_commit()` returns 0; a failed commit leaves
  both as they were and there is no decrement.
- `cxld_await_commit()`: clears `CXL_HDM_DECODER0_CTRL_COMMIT` only when the
  hardware reports `CXL_HDM_DECODER0_CTRL_COMMIT_ERROR` (`-EIO`); on
  `-ETIMEDOUT` it clears nothing.
- `cxl_decoder_reset()` on a decoder with `CXL_DECODER_F_LOCK`: returns before
  touching hardware, flags or `commit_end`.
- `cxl_decoder_reset()` with `id != commit_end`: logs with `dev_dbg()`, clears
  the registers and `CXL_DECODER_F_ENABLE`, leaves `commit_end` unchanged.
- Out-of-order reset record: there is no mask; the hole is a decoder with id
  at or below `commit_end` and `CXL_DECODER_F_ENABLE` clear.
- While a hole exists: `match_free_decoder()` in `drivers/cxl/core/region.c`
  returns no switch decoder for that port, so a region without
  `CXL_REGION_F_AUTO` cannot route through it.
- `cxl_port_commit_reap()`: defined in `drivers/cxl/core/hdm.c`; called
  before the caller clears `CXL_DECODER_F_ENABLE` on the top decoder.
- Lock: `cxl_num_decoders_committed()` asserts `cxl_rwsem.region` held in any
  mode; `cxl_port_commit_reap()` asserts it held for write.
- `cxl_region_decode_reset()`: takes targets last to first; for each target it
  resets from the port below the root down, the endpoint decoder last.
- `cxl_region_decode_commit()`: the opposite, endpoint decoder first.
- `init_hdm_decoder()`: a firmware-committed decoder whose id is not
  `commit_end + 1` fails enumeration with `-ENXIO`.
- Sanitize test in `cxl_decoder_commit()`: skipped when
  `to_cxl_memdev_state()` returns NULL, which is any device that is not
  `CXL_DEVTYPE_CLASSMEM`.
- `cxl_mem_sanitize()` in `drivers/cxl/core/mbox.c`: holds `cxl_rwsem.region`
  for read and returns `-EBUSY` if the endpoint has a committed decoder or
  the memdev has no driver bound.

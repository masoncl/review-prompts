- There is no CXL_REGION_F_INCOHERENT in this tree; `__commit()` and
  `cxl_region_decode_reset()` call `cxl_region_invalidate_memregion()` with no
  flag test other than `CXL_REGION_F_LOCK` in the latter.

| Flag | Stops | Set by | Cleared by |
|---|---|---|---|
| `CXL_REGION_F_AUTO` | attach with an explicit position or a decoder not in `CXL_DECODER_STATE_AUTO` (`-EINVAL`); `cxl_region_teardown_targets()` | `__construct_region()` | nothing |
| `CXL_REGION_F_NEEDS_RESET` | `cxl_region_can_probe()` (`-ENXIO`) | `cxl_region_decode_reset()`, after each decoder | end of the same function; `cxl_region_setup_flags()` for a locked decoder |
| `CXL_REGION_F_LOCK` | write of 0 to `commit`; all of `cxl_region_decode_reset()` | `cxl_region_setup_flags()` | nothing |
| `CXL_REGION_F_NORMALIZED_ADDRESSING` | `cxl_dpa_to_hpa()` (returns `ULLONG_MAX`); `cxl_region_setup_poison()` debugfs files | `cxl_region_setup_flags()` | nothing |

- `cxl_region_setup_flags()`: called from `cxl_region_alloc()` with the root
  decoder, and from `cxl_port_attach_region()` with each port's decoder.
- `CXL_REGION_F_LOCK` sources: `CXL_DECODER_F_LOCK` on any of those decoders,
  or `cxlmd->attach` set on the endpoint decoder's memdev.
- Root decoder with `CXL_DECODER_F_LOCK` (`ACPI_CEDT_CFMWS_RESTRICT_FIXED`):
  every region under it is locked from allocation, user-created ones too.
- `CXL_REGION_F_NORMALIZED_ADDRESSING` source:
  `CXL_DECODER_F_NORMALIZED_ADDRESSING`, which `cxl_prm_setup_root()` in
  `drivers/cxl/core/atl.c` sets on the endpoint decoder together with
  `CXL_DECODER_F_LOCK`.
- Auto region: flags from the endpoint and switch decoders appear only when
  the last target arrives, because `cxl_port_attach_region()` first runs then.
- `CXL_REGION_F_LOCK` does not stop a write of 1 to `commit` or a detach; a
  detach still lowers `p->state` while the hardware stays programmed.
- `CXL_REGION_F_AUTO` stays set after userspace resets the region; `__commit()`
  does not test it and programs the decoders normally.
- `CXL_REGION_F_NEEDS_RESET`: the loop in `cxl_region_decode_reset()` has no
  early exit, and all three callers hold `cxl_rwsem.region` for write, so
  `cxl_region_can_probe()` (read lock) does not see it set.

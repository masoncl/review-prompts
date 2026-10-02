- `struct cxl_endpoint_decoder`: has no mode or size field; the partition is
  the index `part`, the size comes from `cxl_dpa_size()`.
- `struct cxl_root_decoder`: embeds `struct cxl_switch_decoder` as its member
  `cxlsd`.
- `is_switch_decoder()`: also true for a root decoder, so
  `to_cxl_switch_decoder()` accepts one; code that must exclude root decoders
  tests `is_root_decoder()` as well.
- `reset` in `struct cxl_decoder`: returns `void`; only `commit` returns `int`.
- `cxl_decoder_commit()` and `cxl_decoder_reset()`: `static` in
  `drivers/cxl/core/hdm.c`, reachable only through the pointers.
- `init_hdm_decoder()`: the only core code that sets both callbacks to
  functions; `cxl_decoder_init()` in `drivers/cxl/core/port.c` leaves them
  NULL.
- Callbacks stay NULL on: root decoders, the passthrough decoder from
  `devm_cxl_add_passthrough_decoder()`, and DVSEC-emulated endpoint decoders,
  where `cxl_setup_hdm_decoder_from_dvsec()` sets NULL and marks the decoder
  `CXL_DECODER_F_ENABLE | CXL_DECODER_F_LOCK`.
- **Unsafe usage**: calling `cxld->commit` or `cxld->reset` without a NULL
  test on a decoder that may be root, passthrough or DVSEC-emulated.
  - Safe: test first, as `commit_decoder()` in `drivers/cxl/core/region.c`
    does; it accepts a NULL `commit` only for a switch decoder with
    `nr_targets` of at most 1, anything else is a warning and `-ENXIO`.
- Root decoder callbacks: `struct cxl_rd_ops ops`, embedded by value, with
  `hpa_to_spa` and `spa_to_hpa`.
- `__cxl_parse_cfmws()` in `drivers/cxl/acpi.c`: sets both members to
  `cxl_apply_xor_maps()` after `cxl_root_decoder_alloc()`, only for
  `ACPI_CEDT_CFMWS_ARITHMETIC_XOR`; otherwise both stay NULL.
- Callers of the root ops: `cxl_dpa_to_hpa()` and
  `region_offset_to_dpa_result()` in `drivers/cxl/core/region.c`; each tests
  the member for NULL and treats NULL as HPA equal to SPA.
- `qos_class` in `struct cxl_root_decoder`: an `int` copied from the CFMWS,
  not a callback; the `qos_class` callback is in `struct cxl_root_ops` on
  `struct cxl_root`, next to `translation_setup_root`.

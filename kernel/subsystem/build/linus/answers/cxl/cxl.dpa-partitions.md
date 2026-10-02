- `struct cxl_dev_state` and `struct cxl_dpa_partition`: defined in
  `include/cxl/cxl.h`; `struct cxl_dpa_info` with its inner
  `struct cxl_dpa_part_info` is in `drivers/cxl/cxlmem.h`.
- There is no to_ram_res() or to_pmem_res() here; code reads
  `cxlds->part[i].res` directly.
- `cxl_ram_size()`, `to_ram_perf()` and `to_pmem_perf()`: `static` in
  `drivers/cxl/core/memdev.c`; only `cxl_pmem_size()` is shared, in
  `drivers/cxl/cxlmem.h`.
- RAM helpers `cxl_ram_size()` and `to_ram_perf()`: look only at `part[0]`;
  the pmem helpers search every index by mode.
- `add_part()` in `drivers/cxl/core/memdev.c`: drops a zero-size partition, so
  a pmem-only device has pmem at index 0.
- `cxl_mem_dpa_fetch()`: defined in `drivers/cxl/core/memdev.c`.
- `cxl_set_capacity()`: the entry for a device without a mailbox; it builds
  one RAM partition and calls `cxl_dpa_setup()`.
- `cxl_dpa_setup()`: requires each partition to start at the previous end
  plus one, else `-EINVAL`; a gap fails as well as an overlap.
- `cxl_dpa_setup()` called when `cxlds->nr_partitions` is already non-zero:
  returns `-EBUSY`.
- `cxl_dpa_set_part()`: its only busy test is `CXL_DECODER_F_ENABLE`; it does
  not look at `cxled->dpa_res` or `cxled->cxld.region`.
- `cxl_dpa_set_part()` errors: `-EBUSY` enabled, `-EINVAL` no partition of
  that mode, `-ENXIO` partition of zero size.
- `cxled->part` is `-1`: after `cxl_endpoint_decoder_alloc()`, after
  `__cxl_decoder_detach()` with `DETACH_INVALIDATE` on a decoder that had a
  region, and after `__cxl_dpa_reserve()` when no partition contains the
  reserved range.
- **Unsafe usage**: indexing `cxlds->part[cxled->part]` without testing
  `cxled->part >= 0`, including on a decoder that has `dpa_res`.
  - Safe: test first, as `cxl_region_attach()` (`-ENODEV`),
    `construct_region()` (`-EBUSY`), `cxled_get_dpa_perf()` and `mode_show()`
    do; the last reads `part` once with `READ_ONCE()` because it does not
    hold `cxl_rwsem.dpa`.

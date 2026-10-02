- There is no cxl_acpi_set_cache_size() here;
  `cxl_setup_extended_linear_cache()` in `drivers/cxl/acpi.c` is the caller.
- `resource_contains()` in the helper: applied to `target->memregions` itself,
  which `alloc_target()` sets to span 0 to -1; its children are not walked.
- Match: decided by `nid` (through `node_to_pxm()` and `find_mem_target()`),
  the cache address mode and the resource type, not by `start` and `end`.
- **Unsafe usage**: passing a resource with no type flags or with
  `IORESOURCE_UNSET`.
  - Unsafe: `resource_contains()` is false for every cache, the helper returns
    0 with a size of 0, and the cache is lost silently.
  - Safe: `DEFINE_RES_MEM(start, size)`, as
    `cxl_setup_extended_linear_cache()` does; `alloc_target()` gives
    `target->memregions` the type `IORESOURCE_MEM`.
- **Unsafe usage**: reading the `cache_size` output after a non-zero return.
  - Unsafe: on `-ENOENT`, and in the `-EOPNOTSUPP` stub without
    `CONFIG_ACPI_HMAT`, the helper never writes `*cache_size`.
  - Safe: return on a non-zero result before reading the output, as
    `cxl_setup_extended_linear_cache()` does; it presets
    `cxlrd->cache_size = 0`, not the local it passes.
- Any non-zero return: `cxlrd->cache_size` stays 0 with no message.
- Non-zero size: must equal half of the root decoder's range; a mismatch
  warns and stores 0.
- `cxl_setup_extended_linear_cache()` returns void; the root decoder is added
  either way.
- `p->cache_size`: written only by `cxl_extended_linear_cache_resize()`, from
  `__construct_region()`; regions sized through `alloc_hpa()` keep 0.
- `cxl_extended_linear_cache_resize()` failure: `__construct_region()` only
  warns and builds the region with `p->cache_size` 0.
- `extended_linear_cache_size` attribute: hidden by `cxl_region_visible()`
  when `p->cache_size` is 0.
- `cxl_region_probe()`: registers the MCE notifier only when `p->cache_size`
  is non-zero.
- Other users: search `cache_size` under `drivers/cxl/core`; for example
  `spa_maps_hpa()` and `validate_region_offset()`.

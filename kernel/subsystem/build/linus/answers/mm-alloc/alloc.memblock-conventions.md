- `memmap_init_reserved_range()`: `static void __init` in `mm/memblock.c`,
  takes `(phys_addr_t start, phys_addr_t end, int nid)`; `end` is exclusive.
- `memmap_init_reserved_range()` has one caller,
  `memmap_init_reserved_pages()`, which computes
  `end = start + region->size` from the base/size pair in
  `struct memblock_region`.
- There is no reserve_bootmem_region() in this tree.
- `memblock_free()`: takes `(void *ptr, size_t size)`, a virtual address;
  `memblock_phys_free()` takes the physical `base, size`.
- Second parameter name decides the convention: a first parameter named
  `start` is paired with a size in, for example, `reserved_mem_add()` and
  `memblock_double_array()` (`new_area_start`, `new_area_size`).
- Rounding of start/end helpers in `mm/memblock.c` differs:
  `memmap_init_reserved_range()` rounds outward (`PFN_DOWN(start)`,
  `PFN_UP(end)`); `__free_memory_core()` and `__free_reserved_area()` round
  inward (`PFN_UP(start)`, `PFN_DOWN(end)`).
- A start/end pair handed to a base/size function is written `end - start`;
  see `free_memmap()` and `free_reserved_area()` in `mm/memblock.c`.
- **Potentially unsafe usage**: passing a value that looks like an end
  address as the `size` of a base/size function.
  - Unsafe: when `base` is not 0 and the value is a real end address, not
    the all-ones value; the region covers `[base, base + end)`.
  - Safe: the all-ones value (`PHYS_ADDR_MAX`, `-1`, `ULLONG_MAX`) with any
    `base`, to mean "up to the top", as `memblock_clear_hotplug(0, -1)` in
    `free_low_memory_core_early()` and
    `memblock_remove(1ULL << PHYS_MASK_SHIFT, ULLONG_MAX)` in
    `arm64_memblock_init()` do; `memblock_cap_size()` clamps the size to
    `PHYS_ADDR_MAX - base` in `memblock_add_range()` and
    `memblock_isolate_range()`.

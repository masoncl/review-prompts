- Device DAX idle count depends on the driver: `drivers/dax/device.c` uses
  `MEMORY_DEVICE_GENERIC` (idle at 1); `drivers/dax/fsdev.c` uses
  `MEMORY_DEVICE_FS_DAX`, so its pages idle at 0 and take the fsdax wake-up
  path.
- Initial count per type: see `__init_zone_device_page()` in `mm/mm_init.c`.
- Page-table mapping of an fsdax folio: takes one folio reference and one
  mapcount, see `insert_page_into_pte_locked()` in `mm/memory.c`.
- `dax_busy_page()`: does not call `dax_page_is_idle()`; it reports
  `&folio->page` busy when `folio_ref_count(folio) - folio_mapcount(folio)` is
  non-zero.
- `dax_page_is_idle()`: used only as the sleep condition in `wait_page_idle()`
  and `wait_page_idle_uninterruptible()`; it needs the count at 0, so a
  mapping reference keeps a waiter asleep too.
- `free_zone_device_folio()` for `MEMORY_DEVICE_FS_DAX`: leaves
  `folio->mapping` set; the only type-specific step is
  `wake_up_var(&folio->page)`.
- Idle fsdax folio (count 0): can still be large and still carry
  `folio->mapping` or `folio->share`; those go in `dax_folio_put()` when the
  last entry is removed, not at the last put.
- `free_zone_device_folio()` for `MEMORY_DEVICE_GENERIC`: calls no callback and
  leaves `folio->mapping` set; `struct dev_pagemap_ops` has `folio_free`, and
  there is no page_free member.

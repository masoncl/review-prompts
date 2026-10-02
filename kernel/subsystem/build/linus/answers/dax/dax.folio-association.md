- Shared marker: there is no PAGE_MAPPING_DAX_SHARED here; a shared folio has
  `folio->mapping == NULL` and `folio->share != 0`, see `dax_folio_is_shared()`
  in `fs/dax.c`.
- First association of a shared extent: takes the non-shared branch and sets
  `folio->mapping` and `folio->index`; only the second association calls
  `dax_folio_make_shared()`, so a non-NULL `folio->mapping` does not prove a
  single owner.
- Shared branch of `dax_associate_entry()`: increments `folio->share`, which
  counts associations; when the folio still had a mapping it first calls
  `dax_folio_make_shared()`, which clears `folio->mapping` and sets
  `folio->share` to 1. It does not call `dax_folio_init()`, and warns when the
  entry order differs from `folio_order()`.
- Device DAX: `dax_associate_entry()` has no device-DAX test; it skips only
  zero and empty entries. `drivers/dax/device.c` never reaches it and writes
  `folio->mapping` and `folio->index` in `dax_set_mapping()`.
- `dax_folio_reset_order()` in `fs/dax.c`: does the final reset; it also
  zeroes `folio->share`, which is `folio->index`. It is exported, and
  `fsdev_clear_folio_state()` in `drivers/dax/fsdev.c` calls it on probe and
  unbind.
- Shared folio and the generic memory-failure fallback: `dax_lock_folio()`
  returns 0 when `folio->mapping` is NULL, so `mf_generic_kill_procs()` returns
  `-EBUSY`; only the holder's `notify_failure` can find the owners.

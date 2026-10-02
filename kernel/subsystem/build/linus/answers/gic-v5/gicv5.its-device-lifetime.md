- Device ID already in `its_devices`: `gicv5_its_alloc_device()` returns
  `ERR_PTR(-EBUSY)`, so `gicv5_its_msi_prepare()` returns `-EBUSY`.
- `gicv5_its_msi_teardown()`: does no lookup and no NULL test; it uses
  `info->scratchpad[0].ptr` as the `struct gicv5_its_dev`.
- Teardown's only check: `WARN_ON_ONCE(!bitmap_empty(its_dev->event_map,
  its_dev->num_events))`; when it fires the function returns, with the device
  still in `its_devices` and its device table entry still valid.
- Teardown order: `xa_erase()`, `bitmap_free()`,
  `gicv5_its_device_unregister()`, `kfree()`; the unregister return value is
  dropped.
- There is no gicv5_its_free_device() here; the teardown steps are inline in
  `gicv5_its_msi_teardown()`.

- Entry not valid: `gicv5_its_device_unregister()` returns `-EINVAL` after a
  `pr_debug()`; the ITT is not freed.
- Invalidation fails: `gicv5_its_device_unregister()` returns the
  `-ETIMEDOUT`; nothing is restored or retried.
- Callers of `gicv5_its_device_unregister()`: `gicv5_its_msi_teardown()` and
  the `out_unregister` path of `gicv5_its_alloc_device()`; both drop the
  return value and go on to `kfree()` the device.
- **Unsafe usage**: freeing the ITT of a device before the invalidation of
  its cleared device table entry has completed.
  - Unsafe: `kfree()` in `gicv5_its_free_itt()` returns the memory for reuse
    while the ITS may still hold the old entry in its cache and read the
    memory as ITTEs.
  - Safe: freeing tables that no device table entry ever pointed to, as the
    `out_free` path of `gicv5_its_create_itt_two_level()` does.

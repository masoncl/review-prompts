- Models have the order and the lookup rules right; see `mfd_add_devices()` in
  `drivers/mfd/mfd-core.c` and `__device_attach()` in `drivers/base/dd.c`.
- Cell whose `of_compatible` matches only a disabled child node of
  `parent->of_node`: `mfd_add_device()` returns 0 and registers nothing, so a
  consumer may wait for a sibling that never exists.

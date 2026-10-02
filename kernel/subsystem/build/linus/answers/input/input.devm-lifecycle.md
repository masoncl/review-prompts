- Unregistration point in the devres stack: the end of a successful
  `input_register_device()`, not the allocation.
- Managed resource acquired between `devm_input_allocate_device()` and
  `input_register_device()`: released after the device is unregistered and
  before its reference is dropped.
- Managed resource acquired after `input_register_device()`: released before
  the device is unregistered.
- `devm_input_device_release()`: drops one reference; it frees only when that
  is the last one.
- `input_dev_release()` frees on the last put, which can come after unwinding;
  for example `evdev_connect()` takes a reference that only `evdev_free()`
  drops.

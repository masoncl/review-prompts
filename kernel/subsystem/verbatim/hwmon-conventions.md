These are conventions that the maintainers of the hardware monitoring subsystem
ask of new code. Existing code may differ. A kernel tree cannot supply all of
them, so they are kept by hand and inserted as they are.

- Code must follow the guidelines in
  `Documentation/hwmon/submitting-patches.rst`.
- Enum values in this subsystem are traditionally lowercase. Uppercase is
  permitted, but not mandatory.
- Hardware monitoring is an API in Linux, not just a physical layout. Hardware
  monitoring drivers should reside in the `drivers/hwmon/` directory.
- In a new driver, registering hardware monitoring devices from outside
  `drivers/hwmon/` violates layering and increases driver complexity.
- If the main functionality of a chip is not hardware monitoring (such as
  network interface controllers, DRM controllers, or platform specific
  multi-function devices), its hardware monitoring functionality should be
  implemented as an auxiliary device driver, and that hardware monitoring
  driver should reside in `drivers/hwmon/`.
- A hardware monitoring device that supports secondary functionality (such as
  GPIO or LED) should be implemented as a hardware monitoring driver. The
  secondary functionality should be implemented as an auxiliary device, with
  its driver residing in the directory of the appropriate subsystem.
- New drivers must use `hwmon_device_register_with_info()` or
  `devm_hwmon_device_register_with_info()` to register with the hardware
  monitoring subsystem.
- Drivers should use `hwmon_lock()` and `hwmon_unlock()` for the locking that
  the driver itself must implement: the locking for interrupt handling, and
  the locking for attributes registered by any means other than the `info`
  parameter of those two registration functions.

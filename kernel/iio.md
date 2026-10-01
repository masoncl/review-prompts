# IIO Subsystem Delta

## Overview

The Industrial I/O (IIO) subsystem (drivers/iio/) handles sensors and data
acquisition devices including ADCs, DACs, accelerometers, gyroscopes,
magnetometers, light sensors, pressure sensors, and many others. Common
patterns involve channel specification, triggered buffers, regmap-based
register access, and proper scaling/offset handling.

## IIO-Specific Patterns [IIO]

#### IIO-001: Concurrent access locking

**Risk**: Corrupted readings

**Details**: Protect shared state between sysfs and buffer paths
- Claim direct mode for operations that affect the buffers.
- Mutex protection for multi-register transactions

#### IIO-002: Power management sequences

**Risk**: Wrong device state

**Details**: PM operations must match device state requirements
- Ensure register access can be done in sleep state and implementation matches
- Ensure device is active before enabling buffers

## Regmap API

Common patterns with regmap:
- Regmap should be used whenever possible
- Custom bus implementation must be used only if necessary

## Device Tree Bindings

Common DT properties to validate:
- Power supplies are set
- Interrupts are set

## Kernel Version

Always consider the checkout kernel version when reviewing. For example, for
newer kernels must use `PM_RUNTIME_ACQUIRE`, and `devm` whenever possible.

## Quick Checks

- devm_ usage consistent, don't mix manual and devm cleanup
- Proper use of `iio_device_claim_direct_mode()` where needed
- No unneeded 64-bit arithmetics, where gcd could be used.


- `gpiod_to_chip()` and `gpio_device_get_chip()`: take no SRCU lock; they
  return `rcu_dereference_check(gdev->chip, 1)`. The pointer is good only
  while the caller itself keeps `gpiochip_remove()` from running.
- SRCU-protected routes to the chip: `CLASS(gpio_chip_guard, guard)(desc)`
  from a descriptor; `guard(srcu)(&gdev->srcu)` plus `srcu_dereference()`
  from a `struct gpio_device`, as `gpio_device_find()` does.
- `gpio_devices_lock`: a mutex, taken by writers of `gpio_devices` only.
- Line label: `desc->label` is protected by `gdev->desc_srcu`, one SRCU
  domain per `struct gpio_device`, separate from `gdev->srcu`.
- `desc_set_label()`: frees the old label with `call_srcu()` and takes no
  lock of its own.
- `gpiod_get_label()`: the caller holds `gdev->desc_srcu`; chip drivers use
  `gpiochip_dup_line_label()`, which takes it and returns a copy.
- `desc->flags`: not only atomic bitops. `gpiod_get_direction()` and
  `gpiod_free_commit()` read the word with `READ_ONCE()`, change a local
  copy and store it with `WRITE_ONCE()`.
- `struct gpio_device` also holds `can_sleep`, copied from the chip at
  registration, and `data`, the driver pointer behind `gpiochip_get_data()`.

- The core enforces no order, and both orders are in the tree.
- `__uart_start()` with runtime PM disabled on `port->dev`: calls
  `start_tx()` directly, without waiting for `serial_port_runtime_resume()`;
  the driver alone keeps the hardware powered until it enables runtime PM.
- The serial core's runtime PM request on the port device: the asynchronous
  `pm_runtime_get()` in `__uart_start()`; it does not call
  `pm_runtime_get_sync()`.
- Port device resumed while runtime PM on `port->dev` is disabled:
  `rpm_resume()` in `drivers/base/power/runtime.c`, run for the controller
  device between them, does not resume `port->dev` but still increments its
  `child_count`.
- **Potentially unsafe usage**: `pm_runtime_enable()` on `port->dev` after
  `uart_add_one_port()`.
  - Unsafe: when the runtime status of `port->dev` is still `RPM_SUSPENDED` at
    that point; a tty write in between resumes the port device, and
    `pm_runtime_enable()` then warns "Enabling runtime PM for inactive device
    with active children" with the parent recorded as suspended.
  - Safe: when probe has powered the hardware itself and
    `pm_runtime_set_active()` has succeeded before `pm_runtime_enable()`, as
    in `dw8250_probe()`; the status test in `pm_runtime_enable()` then cannot
    match.
  - Safe: enable first and hold a usage reference across the registration, as
    `omap8250_probe()` (`pm_runtime_get_sync()` before,
    `pm_runtime_put_autosuspend()` after) and `stm32_usart_serial_probe()`
    (`pm_runtime_get_noresume()`, `pm_runtime_set_active()`,
    `pm_runtime_enable()`, then `pm_runtime_put_sync()` after) do.

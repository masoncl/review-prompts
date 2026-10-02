- Bus: `serial_base_bus_type` in `drivers/tty/serial/serial_base_bus.c`, static,
  registered under the name "serial-base".
- tty class device, or serdev controller: its parent is the port device
  (`&uport->port_dev->dev`), not `uport->dev`; `uport->dev` is passed only as
  the serdev `host`. See the call in `serial_core_add_one_port()`.
- `uart_add_one_port()` before `serial_base_init()` (an `arch_initcall`) has
  run: `serial_base_device_init()` returns `-EPROBE_DEFER`.
- `UPF_DEAD` writes, in order:
  1. Set at the start of `serial_core_register_port()`, before the port
     device exists.
  2. Cleared in `serial_core_add_one_port()` after `uart_configure_port()` and
     immediately before `tty_port_register_device_attr_serdev()`.
  3. Set again in `serial_core_add_one_port()` if that registration fails.
  4. Set in `serial_core_unregister_port()` before
     `serial_core_remove_one_port()`; removal never clears it.
- `UPF_DEAD` after a non-zero return from `serial_core_register_port()`: still
  set.
- `UPF_DEAD` locking: written under the global `port_mutex` in
  `serial_core.c`, without the port lock; only the writes in
  `serial_core_add_one_port()` also hold `state->port.mutex`.
- `UPF_DEAD` readers: `__uart_start()`, `uart_port_activate()`,
  `serial_port_runtime_resume()` and `serial_port_runtime_suspend()`; no other
  code in the tree tests it.

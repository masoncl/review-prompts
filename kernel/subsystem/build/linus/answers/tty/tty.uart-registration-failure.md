- Return value: 0. `serial_core_add_one_port()` only logs "Cannot register tty
  device on line %u" with `dev_err()`.
- `UPF_DEAD`: set again in the failure branch, so `uart_port_activate()`
  returns `-ENXIO`, `__uart_start()` returns early and the port device's
  runtime PM callbacks skip the port.
- Nothing is unwound: `state->uart_port` stays set, `state->refcount` stays 1,
  the controller and port devices stay, and a console registered by
  `uart_configure_port()` stays registered.
- Driver side: the driver cannot see the failure and its remove path must
  call `uart_remove_one_port()` as for a working port.

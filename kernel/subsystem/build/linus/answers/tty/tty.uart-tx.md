- Buffer: `xmit_fifo` in `struct tty_port`, declared
  `DECLARE_KFIFO_PTR(xmit_fifo, u8)`; reached as `port->state->port.xmit_fifo`.
- `struct uart_state` has no xmit member and no `struct circ_buf`.
- uart_circ_empty() and uart_circ_chars_pending() are not defined here; use
  `kfifo_is_empty()` and `kfifo_len()` on `xmit_fifo`.
- `__uart_start()`: no test for an empty fifo and none for a suspended port.
- `start_tx` with nothing queued: reachable from `__uart_start()`,
  `uart_resume_port()` and `uart_handle_cts_change()`.
- `__uart_start()` runtime PM: `pm_runtime_get()` on `port->port_dev->dev`,
  which queues a resume; it returns without `start_tx` if that fails with
  anything but `-EINPROGRESS`.
- `__uart_start()` calls `start_tx` when `pm_runtime_enabled(port->dev)` is
  false or `pm_runtime_active()` of `port->port_dev->dev` is true; the two
  tests use different devices.
- `__uart_start()` callers: `uart_start()`, `uart_write()`,
  `uart_change_line_settings()` when `hw_stopped` clears.
- `serial_port_runtime_resume()` in `drivers/tty/serial/serial_port.c`: calls
  `start_tx` only if `tx_enabled` is set, the fifo is non-empty and tx is not
  stopped.
- `tx_enabled` of `struct serial_port_device`: set by
  `serial_base_port_startup()`, cleared by `serial_base_port_shutdown()`.
- `serial_port_runtime_suspend()`: returns 0 first when `UPF_DEAD` is set or
  `pm_runtime_enabled()` is false for the port device; otherwise under the
  same three conditions calls `start_tx` and returns `-EBUSY`.
- `__uart_port_tx()`: an `x_char` it sends is counted in `icount.tx` and
  against the count of `uart_port_tx_limited()`.
- `__uart_port_tx()`: `x_char` goes out before the `uart_tx_stopped()` test,
  so it is sent on a stopped port.

- Models take `throttle`, `unthrottle` and `send_xchar` of `struct uart_ops` to
  run under the port lock. A driver that needs the port lock there takes it
  itself, as `pl011_throttle_rx()` and `sunsab_send_xchar()` do.
- Models cite `serial8250_console_write()` as a legacy console `write` that
  uses a trylock under `oops_in_progress`. Here it takes a
  `struct nbcon_write_context *` and does not take the port lock;
  `univ8250_console` sets `write_atomic` and `write_thread` and no `write`.
- `tty_register_driver()`: returns `-ENOMEM` when `alloc_workqueue()` for
  `flip_wq` of `struct tty_driver` fails.
- Models treat `flags` of `struct uart_port` as a 32-bit word. `upf_t` is `u64`
  and `UPF_FULL_PROBE` is bit 32, so a copy into `unsigned int` loses it; see
  `include/linux/serial_core.h`.
- Models take `struct uart_state` to hold an xmit circular buffer, with
  uart_circ_empty and uart_circ_chars_pending as helpers. Drivers take bytes
  from the kfifo with `uart_fifo_get()` and `uart_fifo_out()`, which add to
  `icount.tx` themselves; `uart_xmit_advance()` skips bytes in the kfifo and
  counts them. All three are in `include/linux/serial_core.h`.
- `tty_port_register_device_attr_serdev()`: takes a `host` device before
  `parent`, as do `serdev_tty_port_register()` and
  `serdev_controller_alloc()`.
- Models give no context for `rs485_config` and `iso7816_config` of
  `struct uart_port`. The core calls both with the port lock held and
  interrupts off; see `uart_rs485_config()` and `uart_set_iso7816_config()`.
  `rs485_config` takes three arguments, the middle one a `struct ktermios *`.
- Models expect `kcalloc()` and `kmalloc()` in tty allocation paths. Many
  allocations here use `kzalloc_objs()`, `kzalloc_obj()`, `kmalloc_obj()` and
  `kmalloc_flex()` from `include/linux/slab.h`, for example in
  `uart_register_driver()` and `tty_buffer_alloc()`.

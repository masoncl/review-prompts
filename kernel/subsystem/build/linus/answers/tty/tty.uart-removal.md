- Hangup: `tty_port_tty_vhangup()`, which is synchronous; when it reaches
  `uart_hangup()`, that has finished, including `ops->shutdown()` for an
  active, initialised port, before `release_port()` is called.
- The wait: one `atomic_dec_return(&state->refcount)` drops the initial
  reference, then `wait_event(state->remove_wait,
  !atomic_read(&state->refcount))`; uninterruptible, no timeout.
- Locks held across the wait: the global `port_mutex` and
  `state->port.mutex`.
- **Unsafe usage**: taking `state->port.mutex` while holding a reference from
  `uart_port_ref()`.
  - Unsafe: `serial_core_remove_one_port()` holds that mutex while it waits for
    the reference, so neither side can proceed.
  - Safe: code that needs the mutex uses `uart_port_check()` under it and
    takes no reference, as `uart_set_termios()` does.
  - Safe: taking and dropping the reference with the mutex already held, as
    `uart_alloc_xmit_buf()` does when called from `uart_port_startup()`;
    `serial_core_remove_one_port()` takes the mutex before it waits.
- **Unsafe usage**: calling `uart_remove_one_port()` for a port that is not
  currently registered (never added, already removed, or
  `uart_add_one_port()` returned non-zero).
  - Unsafe: `serial_core_unregister_port()` dereferences `port->port_dev`
    before any check; it is NULL after a removal, and unset or stale after a
    failed add.
  - Safe: exactly one call for each `uart_add_one_port()` that returned 0, as
    `stm32_usart_serial_remove()` does.
- `uart_port` contents after return: `type` is `PORT_UNKNOWN`, `port_dev` is
  NULL, `UPF_DEAD` is set, `name` and `tty_groups` are freed but the pointers
  are not cleared, `state` is not cleared.
- Re-adding the same `uart_port`: `type` stays `PORT_UNKNOWN` unless the
  driver sets it again or `UPF_BOOT_AUTOCONF` makes `config_port()` do it;
  `serial8250_unregister_port()` re-adds its slot as an unknown port when
  `serial8250_isa_devs` is set.

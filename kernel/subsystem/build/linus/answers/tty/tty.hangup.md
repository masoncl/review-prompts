- `TTY_HUPPED`: set at the end of `__tty_hangup()`; cleared by `tty_open()`
  after `open` of `struct tty_operations` succeeds.
- `TTY_HUPPED` already set: `__tty_hangup()` returns at once, so a second
  hangup before a reopen calls no driver callback.
- `TTY_HUPPED` is tested in one other place: `tty_set_ldisc()` fails with
  `-EIO`.
- `TTY_HUPPING`: set after `tty_lock()`, cleared at the end. Its only reader
  is `n_tty_wait_for_input()`, which makes readers return.
- Files replaced: only those whose `write_iter` is `tty_write()`;
  `tty_hung_up_p()` tests for the result.
- `__tty_hangup()` calls no port helper. A driver's `hangup` calls
  `tty_port_hangup()` if it wants the port reset.
- Driver callbacks: `flush_buffer` first, through `tty_ldisc_hangup()` when it
  gets an ldisc reference; then `hangup`, or `close` on the console path.
- After `hangup`, `close` still arrives once for each hung-up file, from
  `tty_release()`. `tty_port_close_start()` returns 0 for such a file and
  leaves the count alone.

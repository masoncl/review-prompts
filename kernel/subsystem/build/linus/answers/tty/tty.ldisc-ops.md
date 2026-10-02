- `receive_buf` with `receive_buf2` also set: still called, by `tiocsti()` in
  `drivers/tty/tty_io.c`, one byte at a time, with no `tty->receive_room`
  clamp.
- Ldisc with only `receive_buf2`: gets no `TIOCSTI` input, and `tiocsti()`
  still returns 0.
- `receive_buf` on the normal path: `tty_ldisc_receive_buf()` in
  `drivers/tty/tty_buffer.c` clamps the count to `tty->receive_room`.
- `tty->receive_room`: `tty_set_termios_ldisc()` zeroes it, and
  `tty->disc_data`, before `open` on every ldisc switch; an ldisc with only
  `receive_buf` that leaves it 0 receives nothing from
  `tty_ldisc_receive_buf()`.
- Short but non-zero return from the receive call: `flush_to_ldisc()` offers
  the rest again at once.
- Return of 0: `flush_to_ldisc()` stops and does not requeue itself; it runs
  again on, for example, the next `tty_flip_buffer_push()` or
  `tty_buffer_unlock_exclusive()`, or when the ldisc restarts it as
  `n_tty_kick_worker()` does.
- `tty_buffer_restart_work()`: declared in `drivers/tty/tty.h` and not
  exported, so an ldisc built as a module cannot call it.
- `lookahead_buf`: called only after a receive call accepted fewer bytes than
  offered, including 0; see `lookahead_bufs()`.
- `lookahead_buf` range: every committed byte not yet looked at, in the
  current buffer and all later ones, not only the remainder of the failed
  call.
- `lookahead_buf` is not called from `tiocsti()` or `paste_selection()`.
- `n_tty_lookahead_flow_ctrl()`: acts only on the START and STOP characters,
  and only under `I_IXON()`; it raises no signals.
- `receive_buf`, `receive_buf2`, `lookahead_buf`: may sleep; every caller is in
  process context with an ldisc reference held.
  - `flush_to_ldisc()` runs in a kworker under the `buf->lock` mutex.
  - `tiocsti()` runs in the ioctl task, `paste_selection()` in the ioctl task
    or in speakup's work item `__speakup_paste_selection()`; both under
    `tty_buffer_lock_exclusive()`.
- Kernel-doc in `include/linux/tty_ldisc.h`: no [DRV] hook carries a sleep
  note; "Can sleep" is on `open`, `close`, `read`, `write`, `hangup` only.
- `dcd_change`: must not sleep; `uart_handle_dcd_change()` calls it and
  asserts `uport->lock`.
- `write_wakeup` call sites: `tty_wakeup()` and, in process context,
  `tty_ldisc_hangup()`; both test `TTY_DO_WRITE_WAKEUP` and hold
  `tty_ldisc_ref()`.
- `write_wakeup` under `tty->flow.lock`: `__start_tty()` calls `tty_wakeup()`
  with that lock held and interrupts off, also when reached from n_tty's
  receive path; a `write_wakeup` that calls `start_tty()` or `stop_tty()`
  deadlocks.
- `write_wakeup` during an ldisc change: silently skipped, because
  `tty_wakeup()` uses the trylock `tty_ldisc_ref()`.
- `tty->write_wait`: woken by `tty_wakeup()` itself, flag or no flag;
  `n_tty_write_wakeup()` only clears `TTY_DO_WRITE_WAKEUP` and sends `SIGIO`.

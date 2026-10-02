- `hangup`: called under a read reference from `tty_ldisc_ref()`, in
  `tty_ldisc_hangup()`, not on the write side.
- `close`: runs on the write side; `tty_ldisc_close()` asserts it.
- `open`: `tty_ldisc_open()` asserts no lock; `tty_ldisc_setup()` opens the
  pty peer without its `ldisc_sem`, because that tty is not yet visible.
- Write-side timeouts: 5 s in `tty_set_ldisc()`, `tty_reopen()` and
  `tty_init_dev()`; `MAX_SCHEDULE_TIMEOUT` in `tty_ldisc_hangup()` and
  `tty_ldisc_release()`.
- `tty_ldisc_release()`: locks through `tty_ldisc_lock_pair()`, which does not
  set `TTY_LDISC_CHANGING` and does not wake `read_wait` or `write_wait`.
- Callbacks that sleep under the caller's reference: keep the write side
  waiting for as long as they sleep; `tty_ldisc_lock()` sets
  `TTY_LDISC_CHANGING` and wakes `read_wait` and `write_wait`, and
  `n_tty_wait_for_input()`, `n_hdlc_tty_read()` and `n_hdlc_tty_write()`
  return once `tty_io_nonblock()` is true.
- Kernel-doc of `tty_ldisc_ref_wait()`: says an existing reference is checked
  for; the code has no check beyond the lockdep annotation in
  `ldsem_down_read()`.
- **Potentially unsafe usage**: taking a second reference on a tty while
  holding one.
  - Unsafe: with `tty_ldisc_ref_wait()`. `ldsem_down_read()` queues behind a
    waiting writer, and that writer waits for the first reference; with
    `tty_ldisc_hangup()` as the writer neither ever returns.
  - Safe: with `tty_ldisc_ref()`, which returns NULL instead of blocking, as
    `tty_set_termios()` does when reached from an ldisc `ioctl`.
  - Safe: use the caller's reference, as `__tty_perform_flush()` does for
    `n_tty_ioctl_helper()`.
- **Unsafe usage**: taking the write side of a tty's `ldisc_sem` while holding
  a reference to that tty.
  - Unsafe: `tty_vhangup()` never returns; `tty_set_ldisc()` stalls 5 s and
    returns `-EBUSY`.
  - Safe: before the reference is taken, as `tty_ioctl()` handles `TIOCSETD`
    and `TIOCVHANGUP`.
  - Safe: `tty_hangup()`, which only queues `tty->hangup_work`.

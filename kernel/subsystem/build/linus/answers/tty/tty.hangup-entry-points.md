- `tty_vhangup_session()`: calls `__tty_hangup()` with `exit_session` 1, which
  also sends `SIGHUP` to the foreground process group.
  `disassociate_ctty()` calls it at exit, for a tty that is not a pty.
- `tty_hangup()`: takes no tty reference for the queued work, and
  `queue_release_one_tty()` reuses the same `hangup_work` for the free.
  `tty_flush_works()` flushes it at the final close; `gsm_dlci_release()`
  uses `tty_vhangup()` for that reason.
- **Potentially unsafe usage**: `tty_vhangup()` from a driver callback.
  - Unsafe: on the tty whose `open`, `close` or `hangup` is running; the
    caller holds `tty_lock()` and `__tty_hangup()` takes it again.
  - Safe: on the slave of a pty pair from the master's `close`, as
    `pty_close()` does; the slave has its own `legacy_mutex`, in subclass
    `TTY_LOCK_SLAVE`, and master then slave is the order `tty_release()`
    uses.
  - Safe: from a removal path that holds no tty lock, through
    `tty_port_tty_vhangup()`, as `serial_core_remove_one_port()` does.
- Console file: a file whose `write_iter` is `redirected_tty_write()`, which
  means it was opened through `console_fops`: `/dev/console`, and with
  `CONFIG_VT` the device `MKDEV(TTY_MAJOR, 0)`.
- With a console file among the open files, `__tty_hangup()`:
  - leaves that file's `f_op` alone and does not count it in `closecount`
  - passes reinit to `tty_ldisc_hangup()`, so the ldisc is reopened instead
    of killed
  - calls `close` with the console file `closecount` times, and does not call
    `hangup`

- `tty_mutex` then `legacy_mutex`: the tty core takes `legacy_mutex` under
  `tty_mutex` only in `tty_init_dev()`, on a tty that was just allocated. On
  reopen `tty_open_by_driver()` drops `tty_mutex` before
  `tty_lock_interruptible()`.
- `tty_lock()` and `tty_lock_interruptible()`: take a tty kref as well as
  `legacy_mutex`; `tty_unlock()` puts it.
- `tty_throttle_safe()` and `tty_unthrottle_safe()`: take `throttle_mutex`,
  not `termios_rwsem`. Only `tty_unthrottle()` takes `termios_rwsem`, for
  write.
- `port->lock`: covers `port->tty`, `count` and `blocked_open`. `iflags` is
  changed with atomic bit operations, without the lock.
- `ldisc_sem` of a pty pair: `tty_ldisc_lock_pair_timeout()` takes the lower
  address first and the other with `LDISC_SEM_OTHER`. It and
  `tty_ldisc_lock_pair()` are static in `drivers/tty/tty_ldisc.c`;
  `tty_ldisc_release()` is the caller.
- Slave pty lock subclasses: `pty_common_install()` puts three slave locks in
  `TTY_LOCK_SLAVE`: `legacy_mutex`, `termios_rwsem` and the port's
  `buf.lock`.
- `buf.lock` then `termios_rwsem`: `flush_to_ldisc()` holds `buf.lock` when
  `n_tty_receive_buf_common()` takes `termios_rwsem`.
- Pty pair, `buf.lock`: slave first, then master. `isig()` on the slave holds
  the slave's `termios_rwsem` for write when `pty_flush_buffer()` takes the
  master's `buf.lock`.
- Master then slave `legacy_mutex`: besides `tty_lock_slave()` in
  `tty_release()`, `pty_close()` on the master calls `tty_vhangup()` on the
  slave with the master locked.

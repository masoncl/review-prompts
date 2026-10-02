| Callback | May sleep | Caller holds |
|---|---|---|
| `open` | yes | `tty_lock()` |
| `close` | yes | `tty_lock()` |
| `write` | no | nothing guaranteed |
| `write_room` | no | nothing guaranteed |
| `set_termios` | yes | `termios_rwsem` for write |
| `throttle` | yes | `throttle_mutex` |
| `unthrottle` | yes | `termios_rwsem` for write, or `throttle_mutex` |
| `hangup` | yes | `tty_lock()` |
| `shutdown` | yes | `tty_mutex`, not `tty_lock()` |
| `cleanup` | yes | nothing |
| `break_ctl` | yes | `atomic_write_lock`, or nothing |
| `wait_until_sent` | yes | nothing guaranteed |

- `open` and `close`: the file pointer is NULL when serdev is the caller, see
  `ttyport_open()` and `ttyport_close()`.
- `write`: called under a spinlock by line disciplines, for example
  `ppp_async_push()` under `xmit_lock`.
- `write_room`: called under the `tx_lock` spinlock in
  `drivers/tty/n_gsm.c`.
- `throttle`: `tty_throttle_safe()` is its only caller; there is no
  tty_throttle() here. n_tty calls it with `termios_rwsem` held for read.
- `unthrottle`: `tty_unthrottle()` holds `termios_rwsem` for write;
  `tty_unthrottle_safe()` holds `throttle_mutex`.
- `shutdown`: runs in `release_tty()`, in the context of the final close or of
  a failed `tty_init_dev()`. `release_tty()` warns if `tty_mutex` is not
  locked.
- `cleanup`: the only callback of the twelve that runs in the
  `release_one_tty()` worker.
- `break_ctl`: `send_break()` holds `atomic_write_lock` only without
  `TTY_DRIVER_HARDWARE_BREAK`. `TIOCSBRK` and `TIOCCBRK` call it with no
  lock.
- `wait_until_sent`: no lock from `tty_wait_until_sent()` in an ioctl;
  `tty_lock()` from `tty_port_close_start()`; `atomic_write_lock` from
  `set_termios()` in `drivers/tty/tty_ioctl.c`.
- Kernel-doc, `shutdown`: says "called under the tty lock"; the caller holds
  `tty_mutex` and has already dropped `tty_lock()`.
- Kernel-doc, `cleanup`: calls it the part of shutdown "for routines that
  might sleep"; `shutdown` runs under a mutex and may sleep too.
- Kernel-doc, `throttle` and `unthrottle`: says called under
  `termios_rwsem`; the safe helpers take only `throttle_mutex`, and the rwsem
  is held only if the line discipline holds it.
- Kernel-doc, `unthrottle`: says always invoke via `tty_unthrottle()`; n_tty
  uses `tty_unthrottle_safe()`.
- Kernel-doc, `close`: says required; `tty_release()` and `__tty_hangup()`
  test it for NULL.
- Kernel-doc, `break_ctl`: says only "May sleep" and names no lock.

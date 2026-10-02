- `__tty_alloc_driver()` arrays: `ttys` and `termios` are skipped with
  `TTY_DRIVER_DEVPTS_MEM`; `ports` is skipped with
  `TTY_DRIVER_DYNAMIC_ALLOC`; `cdevs` has one slot with
  `TTY_DRIVER_DYNAMIC_ALLOC`, else one per line.
- `cdevs`: only the pointer array is allocated there; each cdev is made by
  `tty_cdev_add()`, per line from `tty_register_device_attr()`, or once from
  `tty_register_driver()` with `TTY_DRIVER_DYNAMIC_ALLOC`.
- There is no put_tty_driver() or alloc_tty_driver() here;
  `tty_alloc_driver()` and `tty_driver_kref_put()` are the pair.
- `tty_standard_install()` does not read `driver->ports`; `tty_init_dev()`
  falls back to `driver->ports[idx]` after the install step if `tty->port` is
  still NULL.
- With `TTY_DRIVER_DYNAMIC_ALLOC`, `driver->ports` is NULL, so `install` has
  to set `tty->port`, as `pty_common_install()` does.
- Open on a line with no port: `tty_init_dev()` warns with
  `WARN_RATELIMIT()`, fails with `-EINVAL` and calls `release_tty()`.
- That failure runs `shutdown`, `remove` and later `cleanup` of
  `struct tty_operations` on a tty that never reached `open`.

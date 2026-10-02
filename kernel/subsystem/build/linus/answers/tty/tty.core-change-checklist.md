- Serial core baseline, for comparison: `uart_ops` in
  `drivers/tty/serial/serial_core.c` has no `lookup`, `remove`, `shutdown`,
  `cleanup`, `resize` or `ldisc_ok`; its driver flags are
  `TTY_DRIVER_REAL_RAW | TTY_DRIVER_DYNAMIC_DEV`; its ports are never
  refcounted (`tty_port_destroy()`, no `tty_port_put()`).
- Serial core does take the hangup-while-open path:
  `serial_core_remove_one_port()` calls `tty_port_tty_vhangup()`.

| User | Paths in the core that a serial port does not take |
|---|---|
| pty, `drivers/tty/pty.c` | every `tty->link` / `o_tty` branch; `ops->lookup` and `ops->remove`; `TTY_DRIVER_DEVPTS_MEM` and `TTY_DRIVER_DYNAMIC_ALLOC` branches of `__tty_alloc_driver()`, `tty_release_checks()`, `tty_register_device_attr()`; `tty_reopen()` returning `-EIO` for a master; `tty_pair_get_tty()` in `tty_ioctl()`; `tty_insert_flip_string_and_push_buffer()`; `tty_buffer_set_limit()` |
| VT, `drivers/tty/vt/vt.c` | `tty_port_install()` (sets `tty->port` before `tty_init_dev()` looks at `driver->ports[]`); `ops->shutdown`, `ops->cleanup`, `ops->resize`, `ops->ldisc_ok`; `tty_port_put()` with a `destruct` op; `paste_selection()` |
| `/dev/console`, `/dev/tty0`; a serial console opened through `/dev/console` takes these too | `console_fops`: `redirected_tty_write()`, the `redirected_tty_write` branch of `tioccons()`, the `cons_filp` branch of `__tty_hangup()` |
| serdev, `drivers/tty/serdev/serdev-ttyport.c` | `port->client_ops` other than `tty_port_default_client_ops`; `tty_init_dev()` and `tty_release_struct()` with no `struct file` |
| speakup, `drivers/accessibility/speakup/spk_ttyio.c` | `tty_kopen_exclusive()`, `tty_kclose()`, `TTY_PORT_KOPENED`, in-kernel `tty_set_ldisc()` |
| `drivers/leds/trigger/ledtrig-tty.c` | `tty_kopen_shared()` |
| refcounted ports, for example `drivers/usb/class/cdc-acm.c`, `net/bluetooth/rfcomm/tty.c`, `drivers/tty/n_gsm.c` | `tty_port_destructor()` and the `destruct` op |
| drivers whose `hangup` op calls it, for example `drivers/tty/ttynull.c` | `tty_port_hangup()` |

- `ptmx_open()`: in `drivers/tty/pty.c`, not `tty_io.c`; it calls
  `tty_init_dev()` and `tty_add_file()` itself and bypasses `tty_open()`.
- `TIOCPKT`, `TIOCSPTLCK`, `TIOCGPTN`: handled in `pty_unix98_ioctl()` and
  `pty_bsd_ioctl()` through `tty->ops->ioctl`; only `TIOCGPTPEER` is a case in
  `tty_ioctl()`.
- Flip work queue: `tty_buffer_queue_work()` uses `port->buf.flip_wq`, else
  `system_dfl_wq`. `tty_register_driver()` allocates `driver->flip_wq` only
  without `TTY_DRIVER_NO_WORKQUEUE` and with `driver_name` set. All four pty
  drivers set the flag and the VT driver sets no `driver_name`, so both run
  `flush_to_ldisc()` on `system_dfl_wq`; a serial port whose
  `struct uart_driver` has a `driver_name` runs it on its driver's queue.
- `__tty_hangup()`: the files it hangs up are switched to `hung_up_tty_fops`;
  a `console_fops` file is not switched.
- `TTY_DRIVER_RESET_TERMIOS` (for example pty, VT, `ttynull`; not serial
  core): `tty_ldisc_hangup()` calls `tty_reset_termios()` and
  `tty_save_termios()` returns early.
- Without `TTY_DRIVER_DYNAMIC_DEV` (for example VT, legacy pty, `ttynull`):
  `tty_register_driver()` registers every device itself. Serial core sets the
  flag.
- `con_ldisc_ok()`: rejects every discipline but `N_TTY`, so `tty_set_ldisc()`
  switching cannot be exercised on a VT.
- serdev: `ttyport_open()` calls `tty_init_dev()` directly, not
  `tty_kopen_exclusive()`, and does not set `TTY_PORT_KOPENED`.
- Under serdev the tty driver's `open` and `close` get `filp == NULL`;
  `tty_port_block_til_ready()` and `tty_hung_up_p()` accept that.
- serdev `client_ops`: has no `lookahead_buf`; `lookahead_bufs()` tests for
  NULL, `tty_port_tty_wakeup()` calls `write_wakeup` without a test.
- There is no tty_port_register_device_serdev() here; serial core calls
  `tty_port_register_device_attr_serdev()`, which creates no cdev when a
  serdev controller was registered.
- `tty_kopen()`: passes a NULL file to `tty_driver_lookup_tty()`, which returns
  `-EIO` for a driver with `ops->lookup`, so a devpts pty cannot be
  kernel-opened.
- `tty_kopen_shared()`: returns the already-open tty with a reference and
  without `tty_lock()`, NULL if none is open, or an `ERR_PTR()`; it never
  calls `tty_init_dev()`.
- `tty_buffer_lock_exclusive()`: callers are `tiocsti()` and
  `paste_selection()` in `drivers/tty/vt/selection.c`; `tty_buffer_flush()`,
  which `tty_ldisc_flush()` calls, raises `priority` and takes `buf->lock`
  itself.
- Line disciplines other than `N_TTY`: search for `tty_register_ldisc(`; the
  list includes non-network users such as `drivers/input/serio/serport.c`,
  `drivers/pps/clients/pps-ldisc.c` and `sound/soc/ti/ams-delta.c`. There is no
  n_tracesink or n_tracerouter driver in this tree.

| Selftest | Reaches | Skips when |
|---|---|---|
| `tools/testing/selftests/tty/tty_tiocsti_test.c` | `tiocsti()` on a pty slave, `TIOCSCTTY`, sysctl `dev.tty.legacy_tiocsti` | sysctl missing, no pty, `CAP_SYS_ADMIN` missing for the variant, or the sysctl cannot be set to the variant's value |
| `tools/testing/selftests/tty/tty_tstamp_update.c` | `tty_open_current_tty()`, `tty_update_time()` | stdin is not a `/dev/tty*` or `/dev/pts*` path |
| `tools/testing/selftests/filesystems/devpts_pts.c` | `ptmx_open()`, `ptm_open_peer()` | stdin is not a terminal |

- Selftest coverage: all three run on a pty or the caller's own terminal; none
  switches a line discipline or reaches serdev or the `tty_kopen_exclusive()`
  path. The only hangup they cause is `tty_vhangup()` of the slave from
  `pty_close()` when the master closes. `tools/testing/selftests/pidfd` has no
  ptmx test.
- `TTY_PARANOIA_CHECK` and `CHECK_TTY_COUNT`: `#define`d to 1 in
  `drivers/tty/tty_io.c`, so `tty_release_checks()` and `check_tty_count()` are
  always built; neither has a Kconfig symbol.
- `TTY_DEBUG_HANGUP` (`tty_io.c`, `pty.c`) and `LDISC_DEBUG_HANGUP`
  (`tty_ldisc.c`): `#undef`ed in source; enabling needs a source edit.
- `tty_debug()`: is `pr_debug`, so `tty_release_checks()` failures, and the
  hangup traces once they are enabled, print only with dynamic debug or
  `DEBUG`.
- Lockdep names: there is no TTY_LDISC_NORMAL; the ldisc semaphore subclasses
  are `LDISC_SEM_NORMAL` and `LDISC_SEM_OTHER` in `drivers/tty/tty_ldisc.c`,
  and `TTY_LOCK_NORMAL` / `TTY_LOCK_SLAVE` in `drivers/tty/tty.h` cover
  `legacy_mutex`, `termios_rwsem` and the buffer lock.
- `CONFIG_DEBUG_LOCK_ALLOC`: without it `ldsem_down_write_nested()` is a macro
  in `include/linux/tty_ldisc.h` and the pty pair ordering in
  `tty_ldisc_lock_pair_timeout()` is unchecked.
- `lockdep_assert_held_write(&tty->ldisc_sem)`: in `tty_ldisc_close()`,
  `tty_ldisc_failto()`, `tty_ldisc_kill()` and `tty_ldisc_reinit()`; these
  are reached from release, hangup and ldisc change of any tty, but check
  only with lockdep on.

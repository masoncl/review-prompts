# TTY and Serial Subsystem

## Main structures

### Objects and how they relate

- Default receive path: `tty_port_default_receive_buf()` reads `port->itty`,
  not `port->tty`, so data can still reach the ldisc while `port->tty` is
  NULL.
- `port->itty`: set and cleared with no kref taken or put.
- `release_tty()`: unhooks the tty from the driver as well as from the port;
  `tty_driver_remove_tty()` calls `remove` of `struct tty_operations`, or
  clears the `driver->ttys[]` slot when there is none.
- `struct tty_port` lifetime depends on the driver:

  | Owner | Port memory | Freed by |
  |---|---|---|
  | serial core | `struct uart_state` array of the `struct uart_driver` | `uart_unregister_driver()`; kref unused, `uart_port_ops` has no `destruct` |
  | pty | one per end, both allocated in `pty_common_install()` | `tty_port_put()` in `pty_cleanup()`, so it dies with its tty |

- `TTY_DRIVER_DEVPTS_MEM` and `TTY_DRIVER_DYNAMIC_ALLOC`: Unix98 ptys set
  both, in `unix98_pty_init()`.
- `tty_kopen_exclusive()`: gives a tty with no `struct file`.
- `tty->ldisc`: NULL after a hangup that does not reinit (`tty_ldisc_kill()` in
  `tty_ldisc_hangup()`), until `tty_reopen()` reinstates it. `tty_ldisc_ref()`
  returns NULL then, and also while a writer holds or waits for `ldisc_sem`.
- `xmit_buf` of a serial core port: exists only between
  `uart_alloc_xmit_buf()` and `uart_free_xmit_buf()`; the write paths test it
  for NULL.
- `state->uart_port`: `uart_port_ref()` with `uart_port_deref()` pins it
  through `state->refcount`. `uart_port_check()` asserts `port.mutex` instead.
- `serial_core_remove_one_port()`: waits on `remove_wait` for the refcount to
  drain before it clears `state->uart_port`.
- `struct serial_ctrl_device`, `struct serial_port_device`
  (`drivers/tty/serial/serial_base.h`): devices on the `serial-base` bus that
  `uart_add_one_port()` creates between the hardware device and the tty device.
- Device chain: `uport->dev`, then ctrl, then port (`uport->port_dev`), then
  the tty device. `__uart_start()` does runtime PM on `port_dev`.
- `struct console` and the open path: `/dev/console` resolves in
  `tty_lookup_driver()` through `console_device()` and the console's `device`
  hook. For serial that is `uart_console_device()`, where `co->data` is the
  `struct uart_driver`.
- `uart_port_lock()` and its variants: also take nbcon ownership of
  `uport->cons` when `uart_console()` is true for the port and the console is
  registered, `CON_NBCON`, with `write_atomic`. A bare
  `spin_lock(&uport->lock)` does not.

## Where to look

**Core files**

| Job | File, and what is easy to get wrong |
|---|---|
| flip buffers | `drivers/tty/tty_buffer.c` holds `__tty_insert_flip_string_flags()`; `tty_insert_flip_string_fixed_flag()` is a static inline wrapper in `include/linux/tty_flip.h` |
| termios ioctls | `drivers/tty/tty_ioctl.c`; `user_termios_to_kernel_termios()` and `kernel_termios_to_user_termios()` are `__weak` there, with a strong definition in, for example, `arch/sparc/kernel/termios.c`; `drivers/tty/tty_baudrate.c` holds only baud-rate encode and decode |
| ptys | `drivers/tty/pty.c`; `ptmx_open()` and `ptmx_fops` are in it, inside `#ifdef CONFIG_UNIX98_PTYS` |
| serial core | `drivers/tty/serial/serial_core.c`; `uart_add_one_port()` is not in it but in `drivers/tty/serial/serial_port.c`, and reaches `serial_core_register_port()` in `serial_core.c` through `serial_ctrl_register_port()` |
| bus the serial core puts its own devices on | `drivers/tty/serial/serial_base_bus.c`: `serial_base_bus_type`, whose `.name` is `"serial-base"`; `serial_core.c`, `serial_base_bus.c`, `serial_ctrl.c` and `serial_port.c` link into one module, `serial_base.o` |
| shared parts of the 8250 driver | two objects in `drivers/tty/serial/8250/Makefile`: `8250_base.o` is `8250_port.c` plus the optional lib files listed there; `8250.o` is `8250_core.c` plus `8250_platform.c` (and `8250_pnp.c`) |
| 8250 module init | `drivers/tty/serial/8250/8250_platform.c`: `serial8250_init()`, its `uart_register_driver()` call, `nr_uarts`, `serial8250_isa_init_ports()`; `serial8250_reg` and `serial8250_register_8250_port()` are in `8250_core.c` |
| selftests | `tools/testing/selftests/tty/` builds two programs: `tty_tstamp_update.c` and `tty_tiocsti_test.c`; a pty test is in `tools/testing/selftests/filesystems/devpts_pts.c` |
| serial and serdev selftests, KUnit tests | no file: `tools/testing/selftests/` has no serial or serdev directory, and nothing under `drivers/tty/` mentions KUnit |
| the other jobs (file operations, line discipline switching, default line discipline, tty ports, job control, serdev) | the files are the objects listed in `drivers/tty/Makefile` and `drivers/tty/serdev/Makefile` |

## Tty drivers and ports

**Registering a tty driver**

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

**Driver setup before registration**

- `init_termios`: there is no default; `__tty_alloc_driver()` zero-fills the
  driver, so the driver copies `tty_std_termios` itself.
- `write_room` missing while `write` is set: `file_tty_write()` logs
  "missing write_room method" on each write and goes on; `tty_write_room()`
  returns 2048.
- After a failed `tty_register_driver()`: a `driver->flip_wq` that was
  allocated is already destroyed, and ports that were in `driver->ports`
  still point at it until `tty_port_destroy()` clears `buf.flip_wq`;
  `uart_register_driver()` shows the cleanup order.

**Driver, port and tty lifetimes**

- `release_one_tty()`: puts no port and frees no termios. It calls `cleanup`,
  puts the driver and the module, drops the pids and frees the tty.
- The tty core takes no reference on `tty->port`; only drivers call
  `tty_port_get()` and `tty_port_put()`, for example `pty_cleanup()`.
- `struct tty_struct` kref: an open raises `tty->count`, not the kref. The
  initial reference from `alloc_tty_struct()` is dropped by `release_tty()`
  at the final close.
- Other tty references, for example: `port->tty`, `signal->tty` of session
  members, and `tty_lock()` for as long as the lock is held.
- `release_tty()`: runs at the final close under `tty_mutex`, before the last
  kref goes; it calls `shutdown`, saves termios, clears `itty` and cancels
  the buffer work. `cleanup` runs later, in `release_one_tty()`.
- `tty_port_destructor()`: if `port->itty` is still set it warns and returns
  without freeing, so the port leaks. A final `tty_port_put()` from `cleanup`
  is after `release_tty()` cleared `itty`.
- Last `tty_port_put()`: may sleep, since `tty_port_destroy()` cancels the
  buffer work synchronously.
- Last `tty_driver_kref_put()`: may sleep when `TTY_DRIVER_INSTALLED` is set,
  since `destruct_tty_driver()` then removes the proc entry and, without
  `TTY_DRIVER_DYNAMIC_DEV`, the line devices.
- `destruct` in `struct tty_port_operations`: usb-serial does not set one, it
  calls `tty_port_destroy()` itself; `acm_port_destruct()` in
  `drivers/usb/class/cdc-acm.c` is an example of one.
- `driver->flip_wq`: destroyed by `tty_unregister_driver()`, not by
  `destruct_tty_driver()`; a port keeps its pointer in `buf.flip_wq` until
  `tty_port_unregister_device()` or `tty_port_destroy()` clears it.
  `tty_unregister_device()` does not clear it.

**Locks and their order**

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

**Context of driver callbacks**

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

**Port open and close helpers**

- `tty_port_open()`: sets `TTY_PORT_INITIALIZED` after `activate`, not
  `TTY_PORT_ACTIVE`. `TTY_PORT_ACTIVE` is set in
  `tty_port_block_til_ready()`.
- `activate` is optional: with none, `tty_port_open()` still sets
  initialized.
- `activate` returning nonzero, positive too: `tty_port_open()` returns the
  value at once, leaves initialized clear and skips
  `tty_port_block_til_ready()`. `uart_open()` maps a positive value to 0.
- `tty_port_close()`: does nothing more when `tty_port_close_start()` returns
  0, which is every close but the last, and every close of a hung-up file.
- `tty_port_shutdown()` on a port with `port->console` set: returns before it
  tests or clears initialized, so `tty_port_close()` and `tty_port_hangup()`
  never call `shutdown` and leave initialized set; the next
  `tty_port_open()` then skips `activate`.
- `tty_port_close()` does not set `TTY_IO_ERROR` on a console port.
- `tty_port_hangup()`: also sets `TTY_IO_ERROR` on the tty, under
  `port->lock`.
- `TTY_PORT_ACTIVE`: the helpers in `drivers/tty/tty_port.c` only write it.
  `uart_hangup()` is the only reader in this tree.
- `tty_port_block_til_ready()` returns 0 without waiting in two cases:
  - `tty_io_error()` is true: it sets active and does not touch DTR/RTS.
  - the file is NULL or has `O_NONBLOCK`: it raises DTR/RTS only if `C_BAUD`
    is nonzero, then sets active.

**Hangup sequence**

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

**Hangup entry points**

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

**Port to tty pointers**

- `tty_port_install()` sets `tty->port`, not `port->tty`.
- `port->tty` is set by `tty_port_tty_set()`, which `tty_port_open()` calls
  before `activate`. The open path in `drivers/tty/tty_io.c` never sets it.
- A driver that uses neither `tty_port_open()` nor `tty_port_tty_set()` has
  `port->tty` NULL all the time, for example pty; `tty_port_tty_get()` and
  `tty_port_tty_wakeup()` then find no tty.
- `port->tty` is cleared by `tty_port_close()` on the last close and by
  `tty_port_hangup()`, which clears it under `port->lock` and puts the
  reference after the port `shutdown`.
- `scoped_guard(tty_port_tty, port)` with `scoped_tty()`, from
  `include/linux/tty_port.h`: gets the tty, skips the body if it is NULL, and
  puts it at the end; see `__tty_port_tty_hangup()`.
- `port->itty` is set in `tty_init_dev()` after `tty_ldisc_lock()` succeeds,
  and for the pty slave in `pty_common_install()`.
- `port->itty` is cleared in `release_tty()`, for the tty and its link, just
  before `tty_buffer_cancel_work()`.
- `port->itty` readers on the receive path: `tty_port_default_receive_buf()`
  and `tty_port_default_lookahead_buf()`, with `READ_ONCE()` and no
  reference; they run from the buffer work that `release_tty()` cancels.

**Pairing of open and close**

- `tty_open()`: when `open` fails or is NULL, it drops `tty_lock()` and calls
  `tty_release()`, which calls `close` with the same file.
- `ptmx_open()` does the same through `tty_release()`; `ttyport_open()` calls
  `close` directly, with a NULL file.
- If that was the only open, `tty_release()` goes on to `release_tty()`, so
  `shutdown` and later `cleanup` of `struct tty_operations` run too.
- `tty_port_close_start()`: drops `port->count` for any file that is not hung
  up. The initialized bit gates only the drain there, and `shutdown` in
  `tty_port_shutdown()`.
- After a failed `activate`: the port `shutdown` is not called, since
  initialized was never set; `port->tty` stays set until `tty_port_close()`
  clears it.
- A blocking open that fails because of a hangup:
  `tty_port_block_til_ready()` does not restore `port->count`, and
  `tty_port_close_start()` skips the hung-up file, so the count stays
  balanced.
- `uart_install()` sets `tty->driver_data` before `open` can run, so
  `uart_close()` can find its state after any failure in `uart_open()`.

## Line disciplines

**Line discipline callbacks**

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

**Changing the line discipline**

- Fallback order in `tty_ldisc_restore()`: the old ldisc number, then `N_TTY`,
  then `N_NULL`, then `panic()`.
- Restored old ldisc: a new `struct tty_ldisc` from `tty_ldisc_get()`, opened
  again after its `close` already ran, with `tty->disc_data` NULL and
  `tty->receive_room` 0; the previous ldisc state is gone.
- `tty_set_ldisc()` return value after a successful restore: still the error
  from the new ldisc's `open`.
- Console test in `__tty_hangup()`: an open file whose `write_iter` is
  `redirected_tty_write()`.

| open files at hangup | `tty_ldisc_hangup()` does | `tty->ldisc` after |
|---|---|---|
| console among them | `tty_ldisc_reinit()`: `tty->termios.c_line`, then `N_TTY`, then `N_NULL` | new instance |
| no console | `tty_ldisc_kill()` | NULL |

- Hangup callbacks: `flush_buffer`, `write_wakeup` and `hangup` run first,
  under `tty_ldisc_ref()`, before the write side is taken.
- Hangup while the trylock fails: all three callbacks are skipped; the kill or
  reinit still happens.
- `tty_ldisc_setup()`: never sets `tty->ldisc` to NULL, also when `open`
  fails.
- `tty_ldisc_reinit()`: sets `tty->ldisc` to NULL only when the new `open`
  fails; it stays NULL until a later `tty_ldisc_reinit()` succeeds.
- Changes of `tty->ldisc` in `tty_ldisc_reinit()`: made on the write side of
  `tty->ldisc_sem`, so a reference holder never sees one.
- `tty_reopen()` after a hangup without console: tries only
  `tty->termios.c_line`, with no `N_TTY` fallback; on failure the open fails
  and `tty->ldisc` stays NULL.

**Line discipline references**

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

## Received data

**Workqueue for received data**

- `tty_buffer_queue_work()` in `drivers/tty/tty_buffer.c`: queues `buf->work`
  on `port->buf.flip_wq`, and on `system_dfl_wq` when that pointer is NULL.
- A NULL `port->buf.flip_wq` is a valid state: nothing crashes and the data is
  still delivered.
- `system_unbound_wq` is not used in `drivers/tty/tty_buffer.c`.
- `tty_register_driver()` in `drivers/tty/tty_io.c`: allocates
  `driver->flip_wq` with `alloc_workqueue()`, flags `WQ_UNBOUND | WQ_SYSFS`,
  named from `driver->name` and `driver->driver_name`; it is not `WQ_HIGHPRI`.
- The allocation is the default: it is skipped only when
  `TTY_DRIVER_NO_WORKQUEUE` is set or `driver->driver_name` is NULL.
- `driver->flip_wq` is destroyed by `tty_unregister_driver()` and by the error
  path of `tty_register_driver()`.
- `tty_port_link_driver_wq()` in `include/linux/tty_port.h`: copies
  `driver->flip_wq` into the port only if `port->buf.flip_wq` is NULL.
- `tty_port_link_driver_wq()` is called by `tty_port_register_device_attr()`,
  `tty_port_register_device_attr_serdev()`, `tty_port_install()`, and by
  `tty_register_driver()` for each port already in `driver->ports[]`.
- `tty_port_link_device()`: only sets `driver->ports[index]`; it links no
  workqueue itself.
- `tty_port_link_wq()` in `drivers/tty/tty_port.c`: stores the pointer
  unconditionally and does not test `TTY_DRIVER_NO_WORKQUEUE`; the flag only
  stops the per-driver allocation.
- A workqueue that a driver itself passes to `tty_port_link_wq()` is never
  destroyed by the tty core, which destroys only `driver->flip_wq`; destroying
  it is left to the driver.
- No driver in this tree calls `tty_port_link_wq()` directly; the pty drivers
  set `TTY_DRIVER_NO_WORKQUEUE` and so run on `system_dfl_wq`.
- `tty_port_unregister_device()` and `tty_port_destroy()`: set
  `port->buf.flip_wq` to NULL, a driver-chosen workqueue included, so it has to
  be linked again before the port is reused.
- **Unsafe usage**: `TTY_DRIVER_DYNAMIC_ALLOC` with a `driver_name` and without
  `TTY_DRIVER_NO_WORKQUEUE`.
  - Unsafe: `__tty_alloc_driver()` leaves `driver->ports` NULL, and
    `tty_register_driver()` reads `driver->ports[i]` after it allocates the
    workqueue.
  - Safe: set both flags, as `legacy_pty_init()` and `unix98_pty_init()` in
    `drivers/tty/pty.c` do.

**Flip buffer structure**

- `next` is a second release/acquire pair, besides `commit`:
  `__tty_buffer_request_room()` stores `commit` and then `next`;
  `flush_to_ldisc()` and `lookahead_bufs()` load `next` before `commit`.
- `__tty_buffer_request_room()`: moves `buf->tail` to the new buffer first,
  then does the two release stores on the old tail.
- `tty_buffer_alloc()`: its limit test refuses only when `mem_used` is already
  above `mem_limit`; the requested size is added after the test, so one
  allocation can overshoot the limit.
- `tty_buffer_alloc()` with a size of at most `MIN_TTYB_SIZE`: takes a buffer
  from `buf->free` first, and that path skips the limit test.
- `tty_buffer_alloc()` with a size of at most `MIN_TTYB_SIZE` and `buf->free`
  empty: goes through the limit test and `kmalloc_flex()` like any other size.
- `mem_used`: counts `size` rounded up to a multiple of 256, while each buffer
  allocates `2 * size` data bytes plus the header; buffers parked on
  `buf->free` are not counted.
- There is no TTYB_MIN_SIZE here; the recycle threshold is `MIN_TTYB_SIZE` in
  `drivers/tty/tty_buffer.c`.
- `tty_buffer_lock_exclusive()` and `tty_buffer_flush()`: exclude only the
  consumer; the insert functions and `tty_flip_buffer_push()` neither take
  `buf->lock` nor test `buf->priority`, so the driver keeps appending.

**Inserting received data**

- **Potentially unsafe usage**: inserting into, or pushing, one
  `struct tty_port` from more than one context.
  - Unsafe: when two of the contexts can run at the same time and share no
    lock; `__tty_buffer_request_room()` and `__tty_insert_flip_string_flags()`
    update `port->buf.tail` and `tail->used` with plain stores and take no
    lock.
  - Safe: one lock held across the insert and the commit, as
    `tty_insert_flip_string_and_push_buffer()` does with `port->lock`.
  - Safe: a single context that cannot run concurrently with itself and holds
    no lock, as `max310x_handle_rx()` in `drivers/tty/serial/max310x.c`,
    reached only from the threaded handler `max310x_ist()`.
- `uart_insert_char()` in `drivers/tty/serial/serial_core.c`: neither takes nor
  asserts the `struct uart_port` lock; the caller supplies the serialisation.
- `tty_insert_flip_string_and_push_buffer()`: `port->lock` covers the insert
  and the commit only; the work is queued after the unlock, also when nothing
  was inserted.
- `tty_insert_flip_string_and_push_buffer()` is declared in
  `drivers/tty/tty.h` and not exported, so modules cannot call it.
- `tty_buffer_request_room()` and `tty_insert_flip_string_and_push_buffer()`
  return `int`, never negative; the other insert functions return `size_t`.
- `__tty_buffer_request_room()` when allocation fails: returns the room left
  in the current tail, but 0 if the caller needs flag bytes and the tail has
  none.
- When allocation fails and the tail has no flag bytes, a character with a
  flag other than `TTY_NORMAL` is dropped while `TTY_NORMAL` bytes still fit
  in the room the tail has left, except through
  `tty_insert_flip_string_flags()`, which always needs flag bytes.
- `tty_prepare_flip_string()`: adds the returned length to `tail->used` before
  the driver has written the bytes; the next commit publishes all of them,
  written or not.
- `buf_overrun` is a field of `struct uart_icount` in `struct uart_port`;
  `struct tty_port` has no counter and the tty core counts nothing for a short
  insert.

## Serial core ports

**Serial core structures**

- Transmit buffer: `xmit_buf` and `xmit_fifo` live in the `struct tty_port`
  embedded in `struct uart_state`; `struct uart_state` itself has no buffer.
- State array: allocated with `kzalloc_objs()` in `uart_register_driver()`.
- 8250 sub-drivers: do not own the registered `struct uart_port`.
  `serial8250_register_8250_port()` copies selected fields of the caller's
  `struct uart_8250_port` into a slot of the static `serial8250_ports[]` in
  `drivers/tty/serial/8250/8250_core.c` and registers that slot; the caller's
  struct is only a template and is often on the stack.
- `uart_port_ref()`: takes no lock; `atomic_add_unless(&state->refcount, 1, 0)`
  then returns `state->uart_port`.
- `uart_port_check()`: tests nothing; it asserts `state->port.mutex` with
  lockdep and returns `state->uart_port`. It does not look at `UPF_DEAD`.
- Reference plus port lock: `uart_port_ref_lock()` and
  `uart_port_unlock_deref()`, static inlines in
  `drivers/tty/serial/serial_core.c`; `uart_port_unlock_deref()` accepts NULL.
- `uart_port_lock()` and `uart_port_unlock()` in
  `include/linux/serial_core.h`: take a `struct uart_port *` and only the port
  spinlock (and the nbcon ownership for a registered nbcon console); they take
  no reference.

**Registering a UART port**

- Bus: `serial_base_bus_type` in `drivers/tty/serial/serial_base_bus.c`, static,
  registered under the name "serial-base".
- tty class device, or serdev controller: its parent is the port device
  (`&uport->port_dev->dev`), not `uport->dev`; `uport->dev` is passed only as
  the serdev `host`. See the call in `serial_core_add_one_port()`.
- `uart_add_one_port()` before `serial_base_init()` (an `arch_initcall`) has
  run: `serial_base_device_init()` returns `-EPROBE_DEFER`.
- `UPF_DEAD` writes, in order:
  1. Set at the start of `serial_core_register_port()`, before the port
     device exists.
  2. Cleared in `serial_core_add_one_port()` after `uart_configure_port()` and
     immediately before `tty_port_register_device_attr_serdev()`.
  3. Set again in `serial_core_add_one_port()` if that registration fails.
  4. Set in `serial_core_unregister_port()` before
     `serial_core_remove_one_port()`; removal never clears it.
- `UPF_DEAD` after a non-zero return from `serial_core_register_port()`: still
  set.
- `UPF_DEAD` locking: written under the global `port_mutex` in
  `serial_core.c`, without the port lock; only the writes in
  `serial_core_add_one_port()` also hold `state->port.mutex`.
- `UPF_DEAD` readers: `__uart_start()`, `uart_port_activate()`,
  `serial_port_runtime_resume()` and `serial_port_runtime_suspend()`; no other
  code in the tree tests it.

**Failed tty device registration**

- Return value: 0. `serial_core_add_one_port()` only logs "Cannot register tty
  device on line %u" with `dev_err()`.
- `UPF_DEAD`: set again in the failure branch, so `uart_port_activate()`
  returns `-ENXIO`, `__uart_start()` returns early and the port device's
  runtime PM callbacks skip the port.
- Nothing is unwound: `state->uart_port` stays set, `state->refcount` stays 1,
  the controller and port devices stay, and a console registered by
  `uart_configure_port()` stays registered.
- Driver side: the driver cannot see the failure and its remove path must
  call `uart_remove_one_port()` as for a working port.

**Callbacks during port registration**

- `uart_configure_port()` early return: only when `uart_iotype_mmio()` or
  `uart_iotype_io()` is true for `port->iotype` and `iobase`, `mapbase` and
  `membase` are all zero. A `UPIO_BUS` port with no base address goes on.
- Gate for everything after `config_port()`: `port->type != PORT_UNKNOWN`.

| Callback | Made when | NULL test |
|---|---|---|
| `ops->config_port()` | `UPF_BOOT_AUTOCONF` set | none |
| `ops->type()` | type known | yes |
| `ops->pm()` | type known; ON, then OFF unless `uart_console()` | yes |
| `ops->set_mctrl()` | type known and `SER_RS485_ENABLED` clear | none |
| `port->rs485_config()` | type known and `SER_RS485_ENABLED` set | none |
| console `setup()` and write | from `register_console()`, called when type known, `port->cons` set and not registered | - |

- `config_port()` flags: `port->type` is reset to `PORT_UNKNOWN` and
  `UART_CONFIG_TYPE` is passed only when `UPF_FIXED_TYPE` is clear.
- `set_mctrl()`: also called for a console port; `port->mctrl` is masked to
  `TIOCM_DTR`, plus `TIOCM_RTS` when `uart_console_hwflow_active()` is true.
- `port->rs485_config()`: called from `uart_rs485_config()` under the port
  lock with a NULL termios.
- `register_console()`: the test is on `port->cons`, which
  `serial_core_add_one_port()` has just set to `drv->cons`; it does not test
  `uart_console(port)`, so adding any line of a driver with a console can
  register that console.
- 8250 sub-drivers: `serial8250_register_8250_port()` ORs in
  `UPF_BOOT_AUTOCONF`, so `config_port()` runs on every registration that
  passes the early return.
- `startup()` and the other open-time callbacks: not made by the registering
  task, except `set_termios()` when the driver's console `setup()` calls
  `uart_set_options()`. An open from another task blocks in `tty_port_open()`
  on `state->port.mutex`, which `serial_core_add_one_port()` holds until it
  returns; the open can then run before the driver executes its next
  statement after `uart_add_one_port()`.
- **Unsafe usage**: setting up, after `uart_add_one_port()`, anything that
  `startup()`, `set_termios()` or `start_tx()` dereference.
  - Safe: set driver data and private pointers before the call, as
    `stm32_usart_serial_probe()` does with `platform_set_drvdata()`;
    `tty_port_open()` is what can call `uart_port_activate()` at once.

**Removing a UART port**

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

**Runtime PM and port registration**

- The core enforces no order, and both orders are in the tree.
- `__uart_start()` with runtime PM disabled on `port->dev`: calls
  `start_tx()` directly, without waiting for `serial_port_runtime_resume()`;
  the driver alone keeps the hardware powered until it enables runtime PM.
- The serial core's runtime PM request on the port device: the asynchronous
  `pm_runtime_get()` in `__uart_start()`; it does not call
  `pm_runtime_get_sync()`.
- Port device resumed while runtime PM on `port->dev` is disabled:
  `rpm_resume()` in `drivers/base/power/runtime.c`, run for the controller
  device between them, does not resume `port->dev` but still increments its
  `child_count`.
- **Potentially unsafe usage**: `pm_runtime_enable()` on `port->dev` after
  `uart_add_one_port()`.
  - Unsafe: when the runtime status of `port->dev` is still `RPM_SUSPENDED` at
    that point; a tty write in between resumes the port device, and
    `pm_runtime_enable()` then warns "Enabling runtime PM for inactive device
    with active children" with the parent recorded as suspended.
  - Safe: when probe has powered the hardware itself and
    `pm_runtime_set_active()` has succeeded before `pm_runtime_enable()`, as
    in `dw8250_probe()`; the status test in `pm_runtime_enable()` then cannot
    match.
  - Safe: enable first and hold a usage reference across the registration, as
    `omap8250_probe()` (`pm_runtime_get_sync()` before,
    `pm_runtime_put_autosuspend()` after) and `stm32_usart_serial_probe()`
    (`pm_runtime_get_noresume()`, `pm_runtime_set_active()`,
    `pm_runtime_enable()`, then `pm_runtime_put_sync()` after) do.

## Serial core callbacks and data path

**Context of UART callbacks**

- Callers in `drivers/tty/serial/serial_core.c`, where the context is not
  simply "port lock" or "port mutex":

| Callback | Held by the caller |
|---|---|
| `throttle`, `unthrottle` | nothing; only a port reference |
| `send_xchar` | nothing; only a port reference |
| `tx_empty` | never the port lock; port mutex in `uart_get_lsr_info()` and `uart_suspend_port()`, nothing in `uart_wait_until_sent()` |
| `type` | port mutex, in `uart_line_info()` and `uart_report_port()` |
| `set_termios` | port mutex, never the port lock; `uart_set_options()` takes neither |
| `release_port` | port mutex; in `serial_core_remove_one_port()` only the file-local `port_mutex` |
| `config_port` | port mutex; `uart_configure_port()` adds `console_lock()` when `uart_console()` |

- "Port mutex" is `mutex` in `struct tty_port`; `uart_port_check()` asserts it.
- `tx_empty`, `break_ctl`, `set_termios`: a driver that needs the port lock
  takes it inside, as `serial8250_tx_empty()` does.
- `struct uart_ops` has no `set_wake` member.
- Callbacks reached under the port lock cannot sleep; for the rest, callers in
  `drivers/tty/serial/serial_core.c` hold no spinlock.
- Kernel-doc in `include/linux/serial_core.h` against those callers:

| Callback | Kernel-doc says | Callers do |
|---|---|---|
| `startup` | "port_sem taken", "Interrupts: globally disabled" | port mutex, interrupts on |
| `shutdown` | "port_sem taken" | port mutex |
| `pm`, `type`, `ioctl`, `verify_port`, `request_port`, `config_port` | "Locking: none" | port mutex |
| `release_port` | "Locking: none" | port mutex, except at port removal |
| `tx_empty` | "Locking: none", "must not sleep" | port mutex in two of three callers |
| `set_termios` | "caller holds tty_port->mutex", "must not sleep" | `uart_set_options()` does not take it |

- port_sem is defined nowhere in this tree.

**Transmit path**

- Buffer: `xmit_fifo` in `struct tty_port`, declared
  `DECLARE_KFIFO_PTR(xmit_fifo, u8)`; reached as `port->state->port.xmit_fifo`.
- `struct uart_state` has no xmit member and no `struct circ_buf`.
- uart_circ_empty() and uart_circ_chars_pending() are not defined here; use
  `kfifo_is_empty()` and `kfifo_len()` on `xmit_fifo`.
- `__uart_start()`: no test for an empty fifo and none for a suspended port.
- `start_tx` with nothing queued: reachable from `__uart_start()`,
  `uart_resume_port()` and `uart_handle_cts_change()`.
- `__uart_start()` runtime PM: `pm_runtime_get()` on `port->port_dev->dev`,
  which queues a resume; it returns without `start_tx` if that fails with
  anything but `-EINPROGRESS`.
- `__uart_start()` calls `start_tx` when `pm_runtime_enabled(port->dev)` is
  false or `pm_runtime_active()` of `port->port_dev->dev` is true; the two
  tests use different devices.
- `__uart_start()` callers: `uart_start()`, `uart_write()`,
  `uart_change_line_settings()` when `hw_stopped` clears.
- `serial_port_runtime_resume()` in `drivers/tty/serial/serial_port.c`: calls
  `start_tx` only if `tx_enabled` is set, the fifo is non-empty and tx is not
  stopped.
- `tx_enabled` of `struct serial_port_device`: set by
  `serial_base_port_startup()`, cleared by `serial_base_port_shutdown()`.
- `serial_port_runtime_suspend()`: returns 0 first when `UPF_DEAD` is set or
  `pm_runtime_enabled()` is false for the port device; otherwise under the
  same three conditions calls `start_tx` and returns `-EBUSY`.
- `__uart_port_tx()`: an `x_char` it sends is counted in `icount.tx` and
  against the count of `uart_port_tx_limited()`.
- `__uart_port_tx()`: `x_char` goes out before the `uart_tx_stopped()` test,
  so it is sent on a stopped port.

**Port startup and shutdown**

- There is no uart_change_speed() here; `uart_change_line_settings()` calls
  `set_termios`.
- First open: `uart_port_activate()` passes `init_hw` false, so
  `uart_port_startup()` does not raise DTR/RTS.
- First open, DTR/RTS: raised after `set_termios` by
  `tty_port_block_til_ready()` through `uart_dtr_rts()`, when `C_BAUD()`.
- `init_hw` true: only from `uart_set_info()` and `uart_do_autoconfig()`.
- `serial_base_port_startup()`: last step of `uart_startup()`, after
  `set_termios`; calls no driver callback.
- `set_mctrl` from `uart_update_mctrl()`: skipped when `mctrl` does not change
  or `SER_RS485_ENABLED` is set.
- `pm` from `uart_change_pm()`: skipped when the state does not change;
  `uart_configure_port()` leaves a console port at `UART_PM_STATE_ON`.
- Last close, in order: `tx_empty` polling in `uart_wait_until_sent()`;
  `set_mctrl` dropping DTR/RTS if `HUPCL`; `stop_rx`; `shutdown`; `pm` OFF.
- Last close, DTR/RTS: dropped by `tty_port_shutdown()` before it calls
  `uart_tty_port_shutdown()`.
- `uart_tty_port_shutdown()`: does not call `uart_shutdown()`.
- `uart_hangup()`: does not call `tty_port_hangup()`; it runs
  `uart_flush_buffer()` then `uart_shutdown()` itself, only when
  `tty_port_active()`.
- Hangup of an active, initialised port, in order: `flush_buffer`; `set_mctrl`
  if `HUPCL`; `shutdown`; `pm` OFF. No `stop_rx`.
- Console, last close: `tty_port_shutdown()` returns at its `console` test;
  after the `tx_empty` polling no callback runs and the port stays
  initialised.
- Console, next open after such a close: `tty_port_open()` skips
  `uart_port_activate()`, so no `startup` or `set_termios`.
- Console, hangup: `shutdown` is still called and DTR/RTS still dropped under
  `HUPCL`; only `pm` OFF is skipped.
- Console, hangup: `uart_shutdown()` saves cflag and speeds into
  `struct console`; the next `uart_port_startup()` restores them.
- Console test differs: close uses `console` in `struct tty_port`, written
  once in `serial_core_add_one_port()`; hangup uses `uart_console()` live.

**Serial consoles**

- `uart_console()`: under `CONFIG_SERIAL_CORE_CONSOLE`, tests only `cons`
  non-NULL and `cons->index == line`; no `CON_ENABLED` and no registration
  test. Without that option it is constant 0.
- `index` of `struct console`: `drivers/tty/serial/serial_core.c` never writes
  it.
- `cons` of `struct uart_port`: every port of a driver gets the same pointer
  from `serial_core_add_one_port()`; only the `index` compare tells them apart.
- `uart_port_set_cons()`: the only way to write `cons` of `struct uart_port`;
  `__uart_port_using_nbcon()` relies on it changing under the port lock.
- `device_lock`, `device_unlock`: take the port lock with
  `__uart_port_lock_irqsave()` and `__uart_port_unlock_irqrestore()`, not the
  `uart_port_lock_irqsave()` wrapper.
- `nbcon_emit_one()` in `kernel/printk/nbcon.c`, when `use_atomic` is false:
  calls `device_lock`, then acquires nbcon ownership itself, then calls
  `write_thread`.
- `write_atomic`: called with no `device_lock`; nbcon ownership is its only
  serialisation against the driver.
- `register_console()` and `unregister_console_locked()`: hold `device_lock`
  while changing the console list, when `CON_NBCON` and `write_atomic` are set.
- `nbcon_alloc()`: fails with a warning unless `write_thread`, `device_lock`
  and `device_unlock` are all set.
- Driver: `univ8250_console` in `drivers/tty/serial/8250/8250_core.c`, writing
  through `serial8250_console_write()`.
- Other nbcon serial consoles: search `CON_NBCON` under `drivers/tty/serial`;
  for example `pl011_console_write_atomic()`.

**The port lock**

- Wrappers: call `spin_lock()` or its irq variant on `lock`, then
  `__uart_port_nbcon_acquire()`; unlock calls `__uart_port_nbcon_release()`
  first.
- `__uart_port_lock_irqsave()`: the raw lock with no nbcon step; for
  `device_lock` callbacks and `uart_port_set_cons()` only.
- nbcon_locked_port: no such field in this tree.
- `uart_port_unlock()` and its irq variants: do not look at `sysrq_ch`.
- Guards: `uart_port_lock`, `uart_port_lock_irq`, `uart_port_lock_irqsave`,
  `uart_port_lock_check_sysrq_irqsave`; conditional `_try` variants of
  `uart_port_lock` and `uart_port_lock_irqsave` only, from
  `DEFINE_GUARD_COND()` and `DEFINE_LOCK_GUARD_1_COND()`.
- Initialised in `uart_port_spin_lock_init()`: `spin_lock_init()` plus one
  lockdep class, `port_lock_key`, for every port.
- `serial_core_add_one_port()`: initialises the lock unless
  `uart_console_registered()`.
- `uart_set_options()`: initialises the lock unless
  `uart_console_registered_locked()` or `console_reinit` is set; its caller
  must hold `console_list_lock()`.
- Earlycon: `register_earlycon()` and `of_setup_earlycon()` initialise the
  lock of their own port.
- Drivers also call `spin_lock_init()` themselves, for example
  `serial8250_init_port()`.
- **Unsafe usage**: `spin_lock()` or a variant directly on `lock` of
  `struct uart_port`.
  - Unsafe: on a port that can be an nbcon console; `write_atomic` runs
    without the port lock and is kept out only by nbcon ownership.
  - Safe: `__uart_port_lock_irqsave()` inside `device_lock`, as
    `univ8250_console_device_lock()` does; `nbcon_emit_one()` acquires
    ownership itself afterwards.
  - Safe: any `uart_port_lock()` wrapper or guard.

**Receive path and SysRq**

- Guard: `uart_port_lock_check_sysrq_irqsave`; it unlocks with
  `uart_unlock_and_check_sysrq_irqrestore()`. See `serial8250_handle_irq()`.
- No guard exists for `uart_unlock_and_check_sysrq()`, and no conditional
  variant.
- `serial8250_handle_irq_locked()`: its caller must release the lock with that
  guard or with `uart_unlock_and_check_sysrq_irqrestore()`.
- `uart_handle_sysrq_char()`: defined here and used by many drivers; with
  `CONFIG_MAGIC_SYSRQ_SERIAL` it calls `handle_sysrq()` at once, under the
  port lock; without it, a stub that returns 0.
- `uart_prepare_sysrq_char()`: does not test `has_sysrq`; in
  `include/linux/serial_core.h` only `uart_handle_break()` and the two unlock
  helpers do.
- `has_sysrq` clear: the unlock helpers skip `sysrq_ch` entirely.
- `uart_handle_break()`: a second break disarms `sysrq` whenever it is
  non-zero; there is no time test.
- **Unsafe usage**: `uart_prepare_sysrq_char()` followed by
  `uart_port_unlock()`, an irq variant of it, or a plain port-lock guard.
  - Unsafe: `sysrq_ch` stays set and `handle_sysrq()` does not run until some
    later check_sysrq unlock.
  - Safe: `uart_unlock_and_check_sysrq()` or
    `uart_unlock_and_check_sysrq_irqrestore()` on every exit path.
  - Safe: `guard(uart_port_lock_check_sysrq_irqsave)`, as
    `serial8250_handle_irq()` does.
- **Potentially unsafe usage**: `uart_handle_sysrq_char()` under the port
  lock.
  - Unsafe: when the console `write` of that port takes the port lock while
    `sysrq` is non-zero.
  - Safe: when `write` skips the lock if `sysrq` is set, as
    `s3c24xx_serial_console_write()` does; `uart_handle_sysrq_char()` clears
    `sysrq` only after `handle_sysrq()` returns.

## serdev

**Serdev controllers and devices**

- `tty_port_register_device_attr_serdev()`: the test is
  `PTR_ERR(dev) != -ENODEV` on the `struct device *` from
  `serdev_tty_port_register()`; success and every other error skip the cdev.
- `tty_port_register_device_attr_serdev()` tests no driver flag or type; its
  only caller is `serial_core_add_one_port()` in
  `drivers/tty/serial/serial_core.c`.
- `serial_core_add_one_port()` when `tty_port_register_device_attr_serdev()`
  returns an error: the port has neither cdev nor serdev controller;
  `serdev_tty_port_register()` puts its controller on its error path.
- Controller with no child: `serdev_controller_add()` succeeds, and the cdev
  is suppressed, in two cases where no client was enumerated from firmware:
  - `of_serdev_register_devices()` returns 0 when the controller node has a
    graph (`of_graph_is_present()`).
  - `acpi_serdev_register_devices()` returns 0 when
    `acpi_quirk_skip_serdev_enumeration()` sets `skip`.
- `ctrl->serdev` is NULL in those cases until other code calls
  `serdev_device_alloc()` and `serdev_device_add()`, for example
  `drivers/power/sequencing/pwrseq-pcie-m2.c`.
- `port->client_ops` is not saved: the error path of
  `serdev_tty_port_register()`, and `serdev_tty_port_unregister()`, both
  write `&tty_port_default_client_ops`.
- RX entry: `receive_buf()` in `drivers/tty/tty_buffer.c`, called from
  `flush_to_ldisc()`, calls `port->client_ops->receive_buf`; the tty's line
  discipline is not consulted.
- Line discipline: `tty_init_dev()` still opens one with `tty_ldisc_setup()`,
  and `tty_set_termios()` still calls its `set_termios`; RX and write wakeup
  bypass it.
- `ttyport_receive_buf()`: gated on `SERPORT_ACTIVE`, not on `serdev->ops`;
  the flag bytes `fp` are dropped, so the client sees no break, parity or
  framing marks.
- Short return from the client: `flush_to_ldisc()` offers the remainder again
  at once if the return was non-zero; on 0 it stops, and the bytes wait until
  the work is queued again, which nothing under `drivers/tty/serdev/` does.
- `ttyport_write_wakeup()`: calls the client only if `TTY_DO_WRITE_WAKEUP`
  was set and `SERPORT_ACTIVE` is set; `ttyport_write_buf()` is the only
  serdev code that sets `TTY_DO_WRITE_WAKEUP`.
- `serdev_controller_write_wakeup()` with a NULL `write_wakeup` member:
  returns without calling anything; there is no default, and
  `serdev->write_comp` is not completed.

**Controller termios settings**

- `ttyport_open()` `c_cflag`: clears `CSIZE` and `PARENB`; sets `CS8`,
  `CRTSCTS` and `CLOCAL`; does not touch `CREAD`, `PARODD`, `CMSPAR` or
  `CSTOPB`.
- `CRTSCTS` is requested on every open; a client without RTS/CTS wiring calls
  `serdev_device_set_flow_control()` with `false`, as `gnss_serial_open()` in
  `drivers/gnss/serial.c` does.
- Starting termios: `tty_init_termios()` takes `driver->termios[idx]` if
  `release_tty()` saved one with `tty_save_termios()`, else `init_termios`.
- Serial core's tty driver does not set `TTY_DRIVER_RESET_TERMIOS`, so speed
  and the untouched bits survive `serdev_device_close()` into the next open.
- `ttyport_open()` calls `tty_init_dev()`, `tty->ops->open()` with a NULL
  file, `tty_unlock()` and `tty_set_termios()`; it ignores the
  `tty_set_termios()` return value.
- Setters in `drivers/tty/serdev/serdev-ttyport.c`: each copies
  `tty->termios` with no lock held, edits the copy, then calls
  `tty_set_termios()`, which takes `termios_rwsem` itself; two concurrent
  setters can lose one change.
- `ttyport_set_parity()`: clears `CMSPAR` as well as `PARENB` and `PARODD`
  before applying the request.

**Serdev client drivers**

- `serdev_device_write_buf()`: exported function in
  `drivers/tty/serdev/core.c`, not a wrapper; one call to
  `ctrl->ops->write_buf`, no `write_lock`, no wait, no need for
  `write_wakeup`.
- `serdev_device_write()`: returns `-EINVAL` whenever
  `serdev->ops->write_wakeup` is NULL, for any timeout.
- `serdev_device_write()` return: `-ETIMEDOUT` or `-ERESTARTSYS` only when
  nothing was written, else the short count; a negative `write_buf` return is
  passed back even after earlier chunks were accepted.
- `serdev_device_write()` with a `write_wakeup` that never calls
  `serdev_device_write_wakeup()`: a partial write waits until the timeout or
  a signal; a timeout of 0 becomes `MAX_SCHEDULE_TIMEOUT`.
- There is no serdev_device_write_room() in this tree.
- `receive_buf`: may sleep; it runs in `flush_to_ldisc()` work with the
  `buf->lock` mutex held, so `serdev_device_write()` is allowed there.
- Callbacks can run before `serdev_device_open()` returns: `ttyport_open()`
  sets `SERPORT_ACTIVE`, then `serdev_device_open()` still calls
  `pm_runtime_get_sync()`.
- `serdev->ops`: dereferenced with no NULL test in
  `serdev_controller_receive_buf()`, `serdev_controller_write_wakeup()` and
  `serdev_device_write()`; only the two members are NULL-tested.
- **Unsafe usage**: `serdev_device_open()` before
  `serdev_device_set_client_ops()`.
  - Unsafe: `serdev_controller_receive_buf()` in `include/linux/serdev.h`
    dereferences `serdev->ops`, which is still NULL.
  - Safe: set the ops, then open, as `hci_uart_register_device_priv()` in
    `drivers/bluetooth/hci_serdev.c` does.
- **Potentially unsafe usage**: `serdev_device_open()` before
  `serdev_device_set_drvdata()`.
  - Unsafe: when `receive_buf` or `write_wakeup` dereferences the driver data
    with no NULL test; `ttyport_open()` sets `SERPORT_ACTIVE`, and
    `ttyport_receive_buf()` calls the client from then on.
  - Safe: when the callback returns on NULL driver data, as
    `scd30_serdev_receive_buf()` in `drivers/iio/chemical/scd30_serial.c`
    does.
  - Safe: set the driver data, then open, as `w1_uart_probe()` in
    `drivers/w1/masters/w1-uart.c` does.
- **Unsafe usage**: calling `serdev_device_write_buf()` or
  `serdev_device_write()` from `write_wakeup`.
  - Unsafe: on a serial core port `uart_write()` takes the port lock, which
    the caller of `uart_write_wakeup()` already holds, for example under
    `serial8250_handle_irq()`.
  - Safe: schedule work from `write_wakeup` and write from the work item, as
    `snd_serial_generic_write_wakeup()` and `snd_serial_generic_tx_work()` in
    `sound/drivers/serial-generic.c` do.
  - Safe: call only `serdev_device_write_wakeup()`, which is one
    `complete()`.
- **Unsafe usage**: calling `serdev_device_close()` from `receive_buf`.
  - Unsafe: `uart_close()` reaches `tty_buffer_flush()` through
    `tty_port_close_start()`, and that takes the `buf->lock` mutex which
    `flush_to_ldisc()` holds while it runs `receive_buf`; after it,
    `release_tty()` calls `tty_buffer_cancel_work()`, which is
    `cancel_work_sync()` on that same work.
  - Safe: close from `remove()` or another task, as
    `hci_uart_unregister_device()` does; `receive_buf` is not running once
    `serdev_device_close()` has returned.
- **Unsafe usage**: calling a termios, tiocm, break, flush or
  wait-until-sent function before a successful `serdev_device_open()` or
  after `serdev_device_close()`.
  - Unsafe: those ops in `drivers/tty/serdev/serdev-ttyport.c` dereference
    `serport->tty`, which is NULL before the first open and is left pointing
    at the released tty by `ttyport_close()` and by a failed
    `ttyport_open()`.
  - Safe: open, then configure, as `gnss_serial_open()` in
    `drivers/gnss/serial.c` does.
- `ttyport_write_buf()` is the only controller op that tests
  `SERPORT_ACTIVE`: on a closed device it returns 0, so
  `serdev_device_write_buf()` reports 0 bytes and `serdev_device_write()`
  waits for its timeout.

## The 8250 driver modules

**8250 module split**

- `8250.o` and `8250_base.o`: both are `obj-$(CONFIG_SERIAL_8250)`; there is no
  separate Kconfig symbol for the base module.
- `8250_rsa.o`: part of `8250_base` (`8250_base-$(CONFIG_SERIAL_8250_RSA)`),
  not of `8250`.
- 8250_alpha.o: not in this tree; `8250` holds only `8250_core.o`,
  `8250_platform.o` and `8250_pnp.o`.
- `drivers/tty/serial/8250/8250.h`: declares unexported symbols of both
  modules, so a prototype there does not show that a cross-module call links.
  - In `8250.ko`, for example `nr_uarts`, `serial8250_reg`,
    `serial8250_setup_port()`, `serial8250_isa_config`.
  - In `8250_base.ko`, for example `rsa_enable()`, `fintek_8250_probe()`,
    `serial8250_tx_dma()`.
- Function moved so that its caller is in the other module: check for an
  `EXPORT_SYMBOL` line next to each `8250_base` symbol that `8250.ko` code
  then uses; the header alone tells nothing.
- Export in `8250.ko`, for example `serial8250_get_port()`: no `8250_base`
  source file uses one; `8250.ko` already needs `8250_base` exports, so with
  `CONFIG_SERIAL_8250=m` neither module could then load first.
- Exports of `8250_base`: most are plain `EXPORT_SYMBOL_GPL()`.
  - `"SERIAL_8250"` namespace: only `serial8250_clear_fifos()`,
    `serial8250_handle_irq_locked()`, `serial8250_fifo_wait_for_lsr_thre()`.
  - `"SERIAL_8250_PCI"` namespace: the two exports of `8250_pcilib.c`.
  - Import form is the quoted string, `MODULE_IMPORT_NS("SERIAL_8250")`.
  - No source file of `8250.ko` imports a namespace; code moved into `8250.ko`
    that calls one of the namespaced functions needs the import added.
- `univ8250_rsa_support()` in `8250_rsa.c`: exported with
  `EXPORT_SYMBOL_FOR_MODULES(univ8250_rsa_support, "8250")`, so only the module
  named `8250` may use it; `kernel/module/main.c` rejects an explicit import
  of a `module:` namespace.
- `serial8250_console_write()`, `serial8250_console_setup()`,
  `serial8250_console_exit()`: defined in `8250_port.c`, called from
  `8250_core.c`, not exported.
  - These three calls link because both sides sit under
    `#ifdef CONFIG_SERIAL_8250_CONSOLE`, and that option
    `depends on SERIAL_8250=y`.
- **Potentially unsafe usage**: a call between `8250.ko` and `8250_base.ko`
  files to a function that has no export.
  - Unsafe: when the code can be built with `CONFIG_SERIAL_8250=m`; modpost
    reports the symbol undefined.
  - Safe: when caller and callee are both inside
    `#ifdef CONFIG_SERIAL_8250_CONSOLE`, as `univ8250_console_setup()` calling
    `serial8250_console_setup()`; `drivers/tty/serial/8250/Kconfig` makes the
    option depend on `SERIAL_8250=y`.
- `struct uart_8250_ops`: has three hooks, `setup_irq`, `release_irq` and
  `setup_timer`; `serial8250_do_startup()` also calls
  `up->ops->setup_timer()`.
- `up->ops`: set only in `serial8250_setup_port()` in `8250_core.c`; these
  three hooks are the only `8250.ko` functions that the `8250_base` source
  files call.
- `univ8250_port_ops`: the variable lives in `8250_core.c`, but every function
  in it belongs to `8250_base`: a copy of the base ops, plus, with
  `CONFIG_SERIAL_8250_RSA`, the three overrides from `8250_rsa.c`. It is not a
  route from base into `8250.ko`.
- `serial8250_isa_config`: set by `serial8250_set_isa_configurator()` and
  called from `8250_platform.c` and `8250_core.c`, all inside `8250.ko`;
  `8250_port.c` does not reference it.
- `dl_read`, `dl_write`: defaults are installed in `8250_port.c`;
  `serial8250_register_8250_port()` only copies what the registering driver
  supplied.
- Base code that needs data owned by `8250.ko`: gets it as a pointer argument
  to an exported base function that `8250.ko` calls. See
  `univ8250_rsa_support()`: `__serial8250_isa_init_ports()` passes
  `&univ8250_port_ops` and `univ8250_port_base_ops`, and `8250_rsa.c` keeps
  the second in its static `core_port_base_ops`.

## Other users of the tty core

**Changing the tty core**

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

## Model gaps

### Other mistakes models make

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

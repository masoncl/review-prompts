# What the tty measurement found

Three models were asked the 36 questions in `tty-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Readers A and C were current (both
assumed kernels from 6.12 to 6.18) and reader B older (6.10 to 6.12). For
reader A the check of the "Buffers and flow control" group returned nothing the
first time, so those five questions were run again for that reader alone and
the numbers below are from the second run. The hand-written guide was never
checked against current sources, so differences between it and the built guide
are expected and are noted near the end.

Readers A and C know the three objects and how long each lives, the locks and
their order, how a line discipline reference is taken, how the flip buffers
are laid out, that the serial core has its own bus with controller and port
devices, that the transmit buffer is a kfifo and that the port lock has
wrappers which also take ownership of an nbcon console. Reader B knows the
older shape of all of this and has names from before each of those changes.
What every reader gets wrong is narrower: the context the driver callbacks run
in, the pieces added in the last few releases (the receive workqueue, the
SysRq-aware guard, which consoles are nbcon), and order and conditions inside
functions whose outline they know.

## What all three readers got wrong

- **The workqueue that feeds the line discipline.** `tty_register_driver()`
  allocates a workqueue per driver, `driver->flip_wq`, unless the driver passed
  `TTY_DRIVER_NO_WORKQUEUE` or has no `driver_name`; ports are linked to it by
  `tty_port_link_driver_wq()`; `tty_unregister_driver()` destroys it; a port
  with none falls back to `system_dfl_wq`. Reader A knew the per-driver queue
  but named a flag that does not exist (TTY_DRIVER_CUSTOM_WORKQUEUE) and the
  wrong fallback. Reader B described a single global workqueue called tty_wq,
  which is not in the tree. Reader C said the tty layer creates no workqueue
  at all. `TTY_DRIVER_NO_WORKQUEUE` was missing from every reader's table of
  driver flags; only pty sets it.
- **The SysRq-aware guard.** Every reader said it knew of no scope-based guard
  that goes with `uart_prepare_sysrq_char()`. `include/linux/serial_core.h`
  defines `uart_port_lock_check_sysrq_irqsave`, the 8250 interrupt handlers use
  it, and the comment above it says the plain `uart_port_lock_irqsave` guard
  silently drops the captured character. The lists of guards were also short
  of the conditional try forms.
- **Context of the `struct tty_operations` callbacks.** All three had `write`
  called under `atomic_write_lock`. Nothing is guaranteed: echo from the
  receive path holds only the line discipline's output lock, slip, PPP and
  n_gsm call it under their own spinlocks, and serdev holds nothing; that, not
  echo, is why it may not sleep. `shutdown` runs from `release_tty()` under
  `tty_mutex` after the tty lock has been dropped, although the kernel-doc says
  "under the tty lock". `break_ctl` is called with no lock for TIOCSBRK and
  TIOCCBRK. `unthrottle` comes under `termios_rwsem` from `tty_unthrottle()`
  and under `throttle_mutex` from the safe variants; `throttle` only the
  latter. `wait_until_sent` can run under the tty lock (close) or under
  `atomic_write_lock` (a termios change that waits).
- **Context of the `struct uart_ops` callbacks.** Each reader's table had three
  or four rows wrong, and not the same ones. `tx_empty` and `send_xchar` are
  called without the port lock. `set_termios` is documented as not sleeping and
  `uart_set_options()` calls it without the port mutex. `poll_init`, `type`,
  `verify_port` and `ioctl` run under the port mutex. The kernel-doc still
  speaks of port_sem and says startup runs with interrupts globally disabled.
- **The port lock.** Beyond the guard list: the lock is initialised in
  `serial_core_add_one_port()` only if the port is not already a registered
  console, and also in `uart_set_options()`, there too only when the console
  is not registered and `console_reinit` is clear; the raw
  `__uart_port_lock_irqsave()` is correct in a console's `device_lock`
  callback; the wrappers take nbcon ownership only when the console is
  registered, has `CON_NBCON` and has a `write_atomic` callback.
- **Which serial consoles are nbcon.** Reader A said none in mainline, reader C
  only pl011, reader B only 8250 and in the wrong file. Six drivers set
  `write_atomic` and `write_thread`: the 8250 core, pl011, imx, qcom_geni,
  sifive and tegra-utc.
- **`__uart_start()`** calls `start_tx` when runtime PM is not enabled on the
  hardware device as well as when the serial core's port device is active. All
  three gave only the second condition. The transmit buffer is an anonymous
  kfifo of `u8` declared with `DECLARE_KFIFO_PTR()` in `struct tty_port`, not a
  `struct kfifo` (readers A and C) and not a circ_buf (reader B).
- **Serdev and the character device.** `tty_port_register_device_attr_serdev()`
  skips the character device for every result other than `-ENODEV`, errors
  included, and a controller with no child still registers when the node has
  an OF graph. Every reader said "a child was found: no character device".
- **`tty_port_block_til_ready()`**: CLOCAL only skips the wait for carrier; the
  counts and DTR/RTS are still handled. It returns at once only for a NULL or
  non-blocking file or a tty in the I/O error state.
- The selftests: `tools/testing/selftests/tty/` holds two tests. Reader B
  doubted the directory exists; A and C named one.

## What only some readers got wrong

Readers A and B:

- **The line discipline at hangup.** Both said it is reset to N_TTY.
  `tty_ldisc_hangup()` kills it, leaving `tty->ldisc` NULL until
  `tty_reopen()`, unless a file opened through /dev/console is on the tty; only
  then is it reinitialised, to `termios.c_line`, then N_TTY, then N_NULL.
- **A port whose tty device cannot be registered.** `serial_core_add_one_port()`
  sets `UPF_DEAD` again, logs, and still returns 0. `UPF_DEAD` is set at the
  start of `serial_core_register_port()` and cleared before the tty or serdev
  device is registered. Reader A had it cleared afterwards and the failure only
  logged; reader B was unsure of the flag's name.
- **Order inside `uart_configure_port()`**: power on, `set_mctrl` (skipped when
  RS485 is enabled), `uart_rs485_config()`, console registration, power off
  for a port that is not the console, all only when the port type is known,
  and nothing at all for an I/O or MMIO port with no address. Reader A had the
  order wrong, reader B the conditions.
- `uart_suspend_port()` calls `console_suspend()` and `console_resume()`, not
  console_stop() and console_start(). `ttyport_open()` sets CS8, CRTSCTS and
  CLOCAL and never CREAD or HUPCL.
- `tty_operations` `close` after a failed `open`: both described the wrong
  thing `uart_close()` tolerates. With no `driver_data` it decrements the
  port's count and returns.

Reader C alone: `TTY_BUFFER_PAGE` does not bound a buffer's size; tty_throttle()
does not exist; the safe throttle variants return false when skipped;
`8250_pcilib.o` is part of `8250_base` and 8250_alpha.o does not exist; its
runtime PM examples were reversed (`dw8250_probe()` calls
`pm_runtime_set_active()` before registering and `pm_runtime_enable()` after;
`omap8250_probe()` enables first).

Reader B alone, mostly names from before a rework:

- alloc_tty_driver() and put_tty_driver(), which are gone;
  `tty_alloc_driver()` and `tty_driver_kref_put()` replaced them.
- The transmit buffer as `state->xmit`, a circ_buf, with uart_circ_empty() and
  uart_circ_chars_pending(); a wake_peer callback. None exists.
- The port lock wrappers as "thin spinlock calls", and guards called
  guard(uart_port).
- A dedicated serdev line discipline. There is none: serdev replaces
  `port->client_ops`, and `flush_to_ldisc()` calls those directly.
- The serial core's bus: a file serial_base.c, one controller device per
  driver, device links. The bus is `serial_base_bus_type` in
  `serial_base_bus.c`, there is one controller per hardware device and
  `ctrl_id`, and power is parent and child runtime PM.
- The [TTY] and [DRV] halves of `struct tty_ldisc_ops` swapped, the receive
  callbacks as unable to sleep, and `read` taking an iov_iter.
- The driver's `write` called with `port->lock` held; `set_termios` under the
  tty lock; a TTY_STOPPED bit; the flip buffer lock as a spinlock; a
  CONFIG_DEBUG_TTY_LOCK option.
- The 8250 split entirely: it put `8250_core.o` and `8250_pnp.o` in the base
  module, left out `8250_platform.o` and made `8250_fintek` and `8250_dwlib`
  separate modules.

## What the readers already knew

Readers A and C needed little or nothing on the file map and entry points, the
lock table and order, line discipline references and switching, the flip
buffer's structure and the insert functions, the serial core's structures and
reference counting, port removal, startup and shutdown order, and (reader A)
the 8250 module split. Reader B was right about the outline of most of these
and wrong in the details listed above. These are dropped from the build set.

## Where the hand-written guide is stale

`tty.md` has two topics. What it says about the 8250 modules matches
`drivers/tty/serial/8250/Makefile` object for object, and its list of ways out
of a reverse dependency is what the tree does: the comment above
`univ8250_rsa_support()` in `8250_rsa.c` describes passing pointers from
`8250.ko` for exactly this reason. It does not say that the per-platform
drivers are separate modules that use exports of both, or that
`8250_early.o` can only be built in.

The registration topic is one fix written as a rule:

- The call chain and the four callbacks it lists are right, but it leaves out
  the conditions. Everything after `config_port` happens only when the port
  type is known; `set_mctrl` is skipped when RS485 is enabled; nothing happens
  for an I/O or MMIO port with no address. It also leaves out `type`, called
  from `uart_report_port()`, the console's `setup` when `register_console()`
  runs there, and that a serdev client may open the port.
- "`pm_runtime_enable()` must be called BEFORE `uart_add_one_port()`" is stated
  as an absolute. `8250_dw.c` and `8250_mtk.c` both have a `pm` callback that
  calls `pm_runtime_get_sync()`, both call `pm_runtime_enable()` after
  `serial8250_register_8250_port()`, and both work, because the calls fail
  fast with the usage count kept balanced and their clocks are already on.
  The rule needs its precondition: the callback's runtime PM call is what
  powers the hardware it then touches.
- "blocks indefinitely", "circular wait conditions" and "hung worker threads"
  are not what the runtime PM core does with a device that is not enabled:
  `pm_runtime_resume_and_get()` and `pm_runtime_put_sync()` return `-EACCES` at
  once. What goes wrong afterwards depends on what the callback then does to
  hardware that nothing powered.
- It has nothing on the rest of the subject: the tty core, line disciplines,
  ports and buffers, the port lock, the callbacks' context, serdev.

## Left out of the build set

The hand-written guide is 580 words, so the build set is sized to the 600-word
floor, within twenty percent: 10 of the 36 questions and 490 words of budget,
none under 40. Both of the old guide's topics are kept: the callbacks made
while a port is registered, with the runtime PM rule that rests on them, and
the module split of the 8250 driver. The rest are the questions where all
three readers were wrong about something a reviewer would act on: the two
callback-context tables, the port lock, the transmit path, the receive
workqueue, plus the file map and a checklist for core changes that carries the
serdev, pty and console paths in a few lines.

The first build set held eleven questions in 465 words, five of them under 40,
and those five came out as fragments that meant nothing without the question
beside them. With every budget at 40 or more, eleven no longer fit, and
`tty.8250-code-motion-usage` is the one that went. It had the lowest
relevance, readers A and C needed one and two corrections on it, and the fact
its rule rests on, which way the dependency between the two modules runs, is
asked for by `tty.8250-modules`. What it added is that a reverse dependency
breaks the build only with `CONFIG_SERIAL_8250=m`, when the two are separate
modules, and the ways out of one, which the section on the hand-written guide
above records. The words it freed went to the workqueue, the transmit path,
the port lock and the checklist, whose answers each have five or six things
to say.

Left out although a reader got them wrong: the hangup sequence, line
discipline switching and the port helpers (readers A and C know the outline;
the two facts that matter, the line discipline being killed and what CLOCAL
skips, are recorded above); registering a UART port and removing one
(`UPF_DEAD` and the return of 0); receive and SysRq (the guard is asked for by
the port lock question); suspend, consoles, startup and shutdown; the serdev
model and client interface; throttling and the write path; the driver flags
table and driver registration. Left out because readers A and C already knew
them: entry points, lifetimes, the port's two tty pointers, locks, line
discipline references and callbacks, flip buffer structure and usage, the
serial core's structures.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 104 corrections, 34% rewritten on average
reader B: 161 corrections, 73% rewritten on average
reader C: 88 corrections, 24% rewritten on average

question                            reader A      reader B      reader C
tty.core-files                       6% ( 4)      28% ( 6)       5% ( 2)
tty.entry-points                    12% ( 3)      23% ( 3)       8% ( 1)
tty.struct-lifetimes                30% ( 3)      74% ( 3)      35% ( 2)
tty.port-tty-pointers               43% ( 1)      80% ( 3)      35% ( 2)
tty.locks                           28% ( 3)      65% ( 6)       4% ( 1)
tty.driver-registration             51% ( 6)      62% ( 9)      21% ( 1)
tty.driver-flags                    34% ( 4)      68% ( 5)       8% ( 1)
tty.ops-context                     20% ( 5)      49% ( 8)      30% ( 4)
tty.open-close-usage                56% ( 1)      79% ( 3)      12% ( 1)
tty.hangup                          50% ( 2)      84% ( 7)      36% ( 3)
tty.port-helpers                    45% ( 2)      71% ( 4)      34% ( 3)
tty.ldisc-refs                      15% ( 1)      62% ( 2)      12% ( 2)
tty.ldisc-change                    33% ( 2)      74% ( 3)      11% ( 2)
tty.ldisc-ops                       32% ( 3)      74% ( 5)      19% ( 2)
tty.flip-buffer                     48% ( 3)      76% ( 4)      17% ( 6)
tty.flip-usage                      23% ( 3)      70% ( 3)      22% ( 1)
tty.flip-workqueue                  57% ( 2)      88% ( 3)      94% ( 1)
tty.throttle                        46% ( 4)      86% ( 5)      55% ( 2)
tty.write-path                      17% ( 3)      82% ( 4)      32% ( 1)
tty.uart-structs                    15% ( 1)      62% ( 5)      11% ( 3)
tty.uart-registration               65% ( 2)      86% ( 5)       8% ( 1)
tty.uart-registration-callbacks     45% ( 1)      81% ( 4)       8% ( 2)
tty.uart-runtime-pm-usage           15% ( 1)      82% ( 3)      41% ( 4)
tty.uart-removal                    32% ( 1)      82% ( 4)      15% ( 1)
tty.uart-port-lock                  68% ( 8)      77% ( 6)      39% ( 5)
tty.uart-ops-context                45% ( 4)      43% ( 9)      20% ( 4)
tty.uart-tx                         36% ( 5)      89% ( 4)      24% ( 4)
tty.uart-rx-sysrq                   35% ( 3)      85% ( 2)      14% ( 2)
tty.uart-startup-shutdown           32% ( 4)      78% ( 3)       9% ( 1)
tty.uart-suspend                    44% ( 3)      90% ( 2)      14% ( 1)
tty.uart-console                    37% ( 4)      76% ( 3)      33% ( 2)
tty.8250-modules                     9% ( 1)      90% ( 6)      30% ( 5)
tty.8250-code-motion-usage          20% ( 1)      82% ( 2)      14% ( 2)
tty.serdev-model                    35% ( 3)      86% ( 5)      14% ( 3)
tty.serdev-client-usage             32% ( 2)      74% ( 4)      25% ( 3)
tty.core-change-checklist           22% ( 5)      78% ( 8)      37% ( 7)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `tty.port-tty-pointers`, `tty.driver-registration`, `tty.open-close-usage`, `tty.hangup`, `tty.uart-registration`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `tty.struct-lifetimes`, `tty.locks`, `tty.port-helpers`, `tty.ldisc-refs`, `tty.ldisc-change`, `tty.ldisc-ops`, `tty.flip-buffer`, `tty.flip-usage`, `tty.uart-structs`, `tty.uart-removal`, `tty.uart-rx-sysrq`, `tty.uart-startup-shutdown`, `tty.uart-console`, `tty.serdev-client-usage`.
Put back because a guide has to say what each main structure is before anything else: `tty.serdev-model`.

## Questions reorganised

- Subjects now: tty drivers and ports; line disciplines; received data; serial core ports; serial
  core callbacks and data path; serdev; the 8250 driver modules; other users of the tty core.
  32 questions before and after; ids kept, none merged whole.
- Asked twice, now once: what a hangup does to the line discipline (`tty.ldisc-change`, out of
  `tty.hangup`); the SysRq-aware guard (`tty.uart-rx-sysrq`, out of `tty.uart-port-lock`).
- `tty.8250-modules` asks what code motion breaks the build, not which objects are in each module.
- Dropped from inside questions: order of steps within a function, the lock table, the list of
  guards, which drivers are nbcon consoles, the signature of the line discipline read.

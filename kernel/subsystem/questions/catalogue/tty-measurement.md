# Questions: TTY and serial (measurement set)

- guide: tty.md
- title: TTY and Serial Subsystem

A wide set of questions about `drivers/tty/`: the tty core, line disciplines,
tty ports and flip buffers, the serial core with its 8250 driver, and serdev.
It is used to measure what a model already knows before deciding what the
built guide should spend its words on. The hand-written guide it will replace
is 580 words and covers only two topics, callbacks made while a UART port is
registered and the module split of the 8250 driver. The virtual terminal, the
individual line disciplines other than the default one, and the hardware
drivers are left out. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## tty.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

Which files hold the tty core's file operations, line discipline switching,
the default line discipline, tty ports, the flip buffers, job control, termios
ioctls and ptys; the serial core and the bus it puts its own devices on; the
8250 driver's shared parts; serdev; the public headers for each; and the
documentation and selftests? A table. Start from `drivers/tty/Makefile` and
`drivers/tty/serial/Makefile`.

## tty.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

For each job (opening a tty, the final close, a hangup, moving received bytes
from a driver to the line discipline, a write from user space, changing
termios, changing the line discipline, registering a UART port, opening a
serdev device), which function do you start reading from? A table.

# Objects and their lifetimes

## tty.struct-lifetimes: Driver, port and tty lifetimes

- section: Objects and lifetimes
- relevance: 5 - the three objects die at different times and bugs live in the gap
- words: 100

How long do a `struct tty_driver`, a `struct tty_port` and a
`struct tty_struct` each live, what reference count does each have, and what
runs when the last reference to each goes, in which context? Start from
`tty_kref_put()`, `tty_port_put()` and `tty_driver_kref_put()`.

## tty.port-tty-pointers: From a port to its tty

- section: Objects and lifetimes
- relevance: 5 - interrupt handlers reach the tty through the port
- words: 90

A `struct tty_port` has two pointers to a tty, `tty` and `itty`. When is each
set and cleared, who may read each, and what usage of them from a driver's
interrupt handler or work item is unsafe, and what that looks similar is
correct? Start from `tty_port_tty_get()` and `include/linux/tty_port.h`.

## tty.locks: Locks and their order

- section: Objects and lifetimes
- relevance: 5 - most tty fixes are lock order or missing-lock fixes
- words: 140

Which locks does the tty core have (global, per tty and per port), what does
each protect, and in what order are they taken where more than one is held?
A table, then the order. Start from `struct tty_struct`, `struct tty_port`,
`drivers/tty/tty_mutex.c` and the lock subclasses in `drivers/tty/tty.h`.

## tty.driver-registration: Registering a tty driver

- section: Drivers and ports
- relevance: 4 - every non-UART tty driver does this by hand
- words: 110

What sequence of calls allocates, sets up, registers and later tears down a
`struct tty_driver`, which fields must be set before registering, how does
each line get its `struct tty_port`, and what happens at open if a line has
none? Start from `__tty_alloc_driver()`, `tty_register_driver()` and
`tty_port_register_device()`.

## tty.driver-flags: Driver flags

- section: Drivers and ports
- relevance: 3 - a wrong flag changes who creates the device nodes
- words: 90

Give a table of the flags in `enum tty_driver_flag` and what each makes the
core do. Which may a driver set and which belongs to the core?

## tty.ops-context: Context of driver callbacks

- section: Drivers and ports
- relevance: 5 - sleeping in the wrong callback is the classic tty driver bug
- words: 120

For the callbacks in `struct tty_operations` that a driver is most likely to
implement (open, close, write, write_room, set_termios, throttle and
unthrottle, hangup, shutdown and cleanup, break_ctl, wait_until_sent), which
may sleep, which may not, and which lock is each called under? A table. Start
from the kernel-doc in `include/linux/tty_driver.h` and check it against the
callers.

## tty.open-close-usage: Pairing of open and close

- section: Drivers and ports
- relevance: 4 - drivers that assume a successful open leak or underflow counts
- words: 70

If a driver's `open` in `struct tty_operations` returns an error, is its
`close` called for that file, and what must `close` therefore tolerate? What
usage is unsafe, and what does an in-tree driver do that is correct? Start
from `tty_open()` and `uart_close()`.

## tty.hangup: Hangup sequence

- section: Drivers and ports
- relevance: 5 - hangup races with open, close, read and write
- words: 120

What does a hangup do, step by step, to the open files, the session, the line
discipline, the tty's flags and the driver, and how do the asynchronous and
the synchronous entry points differ? What is different when one of the open
files is the console? Start from `__tty_hangup()`.

## tty.port-helpers: Port open and close helpers

- section: Drivers and ports
- relevance: 4 - most drivers should be built on these and many get the pairing wrong
- words: 110

What do `tty_port_open()`, `tty_port_close()`, `tty_port_hangup()` and
`tty_port_block_til_ready()` do for a driver, when are the `activate` and
`shutdown` callbacks of `struct tty_port_operations` called and under which
lock, and what do the initialized and active bits in `iflags` each mean?

# Line disciplines

## tty.ldisc-refs: Line discipline references

- section: Line disciplines
- relevance: 5 - calling into a line discipline without a reference is a use after free
- words: 90

How does code get a safe reference to a tty's current line discipline, which
of the functions may be called from interrupt context, what does a NULL return
mean, and what lock is behind it? What usage is unsafe? Start from
`tty_ldisc_ref()`, `tty_ldisc_ref_wait()` and `drivers/tty/tty_ldsem.c`.

## tty.ldisc-change: Changing the line discipline

- section: Line disciplines
- relevance: 4 - the fallback paths are where the bugs have been
- words: 100

What are the steps of `tty_set_ldisc()`, what happens if the new line
discipline's open fails, what does a hangup do to the line discipline, and
when can `tty->ldisc` be NULL? Start from `drivers/tty/tty_ldisc.c`.

## tty.ldisc-ops: Line discipline callbacks

- section: Line disciplines
- relevance: 4 - the receive side has three entry points with different contracts
- words: 110

For `struct tty_ldisc_ops`, which callbacks come from the tty core and which
from the driver side, which may sleep, how do `receive_buf`, `receive_buf2`
and `lookahead_buf` differ, and what may `write_wakeup` not do? What is the
signature of `read`? Start from `include/linux/tty_ldisc.h`.

# Buffers and flow control

## tty.flip-buffer: Flip buffer structure

- section: Buffers and flow control
- relevance: 4 - the producer and consumer are lockless and the barriers matter
- words: 110

How is received data queued between a driver and the line discipline: what
are `struct tty_bufhead` and `struct tty_buffer`, which fields does the
producer own and which the consumer, what orders them, what bounds the memory
used, and how does other code get exclusive access? Start from
`drivers/tty/tty_buffer.c`.

## tty.flip-usage: Inserting received data

- section: Buffers and flow control
- relevance: 4 - what a driver's receive path must get right
- words: 90

Which functions does a driver call to queue received bytes and flags and to
push them, from which contexts, what do they return when memory runs out, and
may two contexts insert into the same port at once? What usage is unsafe, and
what is correct? Start from `include/linux/tty_flip.h`.

## tty.flip-workqueue: Workqueue for received data

- section: Buffers and flow control
- relevance: 4 - decides which workqueue a port's receive work runs on
- words: 80

On which workqueue does the work that feeds the line discipline run: a system
workqueue or one the tty layer creates, and if the latter who creates and
destroys it and how does a port come to use it? What can a driver do to choose
differently? Start from `tty_buffer_queue_work()`, `tty_register_driver()` and
`tty_port_link_wq()`.

## tty.throttle: Throttling and stopping

- section: Buffers and flow control
- relevance: 3 - two separate flow-control states that are easy to mix up
- words: 100

How does the line discipline tell a driver to stop and resume receiving, what
are `receive_room` and the throttled bit, why are there "safe" variants of
throttle and unthrottle, and how is that different from the stopped state set
by `stop_tty()`, and which lock covers each?

## tty.write-path: Write path

- section: Buffers and flow control
- relevance: 3 - explains who may call a driver's write and when
- words: 90

How does a write from user space reach a driver's `write` callback, which lock
serialises writers, how is the data chunked, and how does a driver that has
drained its buffer get more (which flag, which function)? Start from
`file_tty_write()` and `tty_wakeup()`.

# The serial core

## tty.uart-structs: Serial core structures

- section: Serial core objects
- relevance: 4 - the mapping from a uart_port to the tty objects
- words: 100

How do `struct uart_driver`, `struct uart_state` and `struct uart_port` relate
to each other and to the tty driver, port and tty, who allocates each, and how
does the serial core keep a `uart_port` from being removed while it is in use?
Start from `uart_port_ref()` and `uart_port_check()` in
`drivers/tty/serial/serial_core.c`.

## tty.uart-registration: Registering a UART port

- section: Serial core objects
- relevance: 5 - the devices and the call chain changed when the serial base bus arrived
- words: 110

What does `uart_add_one_port()` do, through which functions, which struct
devices does it create and on which bus, what is the dead flag in the port's
flags for, and what does it return when the tty device itself cannot be
registered? Start from `drivers/tty/serial/serial_port.c` and
`serial_core_register_port()`.

## tty.uart-registration-callbacks: Callbacks during port registration

- section: Serial core objects
- relevance: 5 - a driver must be ready for callbacks before registration returns
- words: 100

Does registering a port with `uart_add_one_port()` call back into the driver
before it returns? If it does, list each callback, the condition under which
it is made and the function that makes it. Start from `uart_configure_port()`.

## tty.uart-runtime-pm-usage: Runtime PM and port registration

- section: Serial core objects
- relevance: 4 - a probe that hangs only on some configurations
- words: 80

Does the order of `pm_runtime_enable()` and `uart_add_one_port()` in a serial
driver's probe matter? If so, what usage is unsafe and for which drivers, and
what that looks similar is correct? Name an in-tree driver for each side if
there is one.

## tty.uart-removal: Removing a UART port

- section: Serial core objects
- relevance: 4 - the port structure belongs to the driver and is freed right after
- words: 90

What does `uart_remove_one_port()` do, in what order, how does it wait for
users of the port, and what may the low-level driver do with its `uart_port`
and its hardware resources before and after the call? Start from
`serial_core_remove_one_port()`.

## tty.uart-port-lock: The port lock

- section: Serial core locking
- relevance: 5 - taking the spinlock directly is wrong for a console port
- words: 100

How must a serial driver take and release the lock in `struct uart_port`, what
do the wrappers do beyond taking the spinlock, which scope-based guards exist,
and where is the lock initialised? What usage is unsafe, and what that looks
similar is correct? Start from `uart_port_lock_irqsave()` in
`include/linux/serial_core.h`.

## tty.uart-ops-context: Context of UART callbacks

- section: Serial core locking
- relevance: 5 - half the callbacks run under the port lock with interrupts off
- words: 120

For the callbacks in `struct uart_ops`, which are called with the port lock
held and interrupts disabled, which with only the port mutex, which with
nothing, and which may sleep? A table. Start from the kernel-doc in
`include/linux/serial_core.h` and check it against the callers in
`drivers/tty/serial/serial_core.c`.

## tty.uart-tx: Transmit path

- section: Serial core data path
- relevance: 4 - the transmit buffer's type and helpers have changed
- words: 110

Where does the serial core keep bytes waiting to be transmitted, what type is
that buffer, which helpers should a driver's transmit interrupt use to take
bytes from it and account for them, when must it call `uart_write_wakeup()`,
and what does the core do before calling `start_tx`? Start from
`__uart_start()` and the transmit helper macros in
`include/linux/serial_core.h`.

## tty.uart-rx-sysrq: Receive path and SysRq

- section: Serial core data path
- relevance: 4 - handling SysRq under the port lock deadlocks with the console
- words: 100

How should a serial driver's receive interrupt pass characters, flags and
overruns up, how should it handle a break and a SysRq character on a console
port, and which unlock helpers or guards go with that? What usage is unsafe?
Start from `uart_insert_char()`, `uart_prepare_sysrq_char()` and
`uart_handle_break()`.

## tty.uart-startup-shutdown: Port startup and shutdown

- section: Serial core data path
- relevance: 4 - which of the driver's startup and shutdown run on open, close and hangup
- words: 110

On the first open, the last close and a hangup of a serial port, which
functions in the serial core run, in what order do they call the driver's
`startup`, `shutdown`, `set_termios`, `pm` and modem-control callbacks, and
what is different for a port that is the console? Start from
`uart_port_activate()`, `uart_tty_port_shutdown()` and `uart_hangup()`.

## tty.uart-suspend: System suspend of a port

- section: Serial core data path
- relevance: 3 - every serial driver's suspend calls it
- words: 90

What do `uart_suspend_port()` and `uart_resume_port()` do to an open port, to
a port that can wake the system, and to the console when console suspend is
disabled, and which driver callbacks do they call?

## tty.uart-console: Serial consoles

- section: Serial core data path
- relevance: 4 - console and tty share the port and its lock
- words: 100

How does a serial driver provide a console: how the console is tied to the
`uart_driver`, when it is registered, how `uart_console()` decides, what
`uart_set_options()` and `uart_console_write()` are for, and which serial
drivers in this tree implement the atomic and threaded console write
callbacks?

# The 8250 driver

## tty.8250-modules: Module split of the 8250 driver

- section: 8250
- relevance: 4 - decides where a function may live
- words: 90

Into which modules are the common parts of the 8250 driver built, which object
files go into each, which way does the dependency between them run, and how
are the per-platform drivers built? Start from
`drivers/tty/serial/8250/Makefile`.

## tty.8250-code-motion-usage: Moving code between 8250 files

- section: 8250
- relevance: 3 - fails only in a modular build
- words: 70

When a function is moved between files under `drivers/tty/serial/8250/`, what
move is unsafe and what that looks similar is fine, in which configuration
does the failure show, and what are the usual ways out?

# serdev

## tty.serdev-model: Serdev controllers and devices

- section: serdev
- relevance: 4 - decides whether a port gets a character device at all
- words: 110

What are a serdev controller and a serdev device, how does a tty port become a
controller, when is the character device not created, how does the controller
open the underlying tty and with what termios, and how are received bytes and
write wakeups routed to the client instead of a line discipline? Start from
`tty_port_register_device_attr_serdev()` and
`drivers/tty/serdev/serdev-ttyport.c`.

## tty.serdev-client-usage: Serdev client drivers

- section: serdev
- relevance: 4 - the client callbacks have different sleeping rules
- words: 100

What must a serdev client driver do to open, configure, write to and close its
device, how do `serdev_device_write()` and `serdev_device_write_buf()` differ,
which of the callbacks in `struct serdev_device_ops` may sleep, and what does
the bus do at probe and shutdown? What usage is unsafe?

# Changing the implementation

## tty.core-change-checklist: Changing the tty core

- section: What a change must preserve
- relevance: 4 - a core change is exercised by ptys, consoles, serdev and every driver
- words: 100

What must a change to the tty core (`drivers/tty/tty_io.c`,
`drivers/tty/tty_ldisc.c`, `drivers/tty/tty_port.c`,
`drivers/tty/tty_buffer.c`) keep working besides an ordinary serial port:
which other users take different paths through the same code, which
invariants do they rely on, and which tests or debug options exercise them?

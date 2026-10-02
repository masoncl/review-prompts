# Questions: TTY and Serial Subsystem

- guide: tty.md
- title: TTY and Serial Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/tty-measurement.md` is the wider
set the readers were measured on and `catalogue/tty-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## tty.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## tty.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: the tty core's file operations; line discipline switching;
the default line discipline; tty ports; the flip buffers; job control; termios ioctls; ptys; the
serial core; the bus the serial core puts its own devices on; the shared parts of the 8250 driver;
serdev; the selftests. If the tree has no file for a job, say so in the row. Start from
`drivers/tty/Makefile` and `drivers/tty/serial/Makefile`.

# Tty drivers and ports

## tty.driver-registration: Registering a tty driver

- section: Tty drivers and ports
- relevance: 4 - every non-UART tty driver does this by hand

Which functions allocate and release a `struct tty_driver` in this tree? How does each line of a
driver get its `struct tty_port`, and what does an open do on a line that has none? Start from
`__tty_alloc_driver()` and `tty_port_register_device()`.

## tty.driver-setup: Driver setup before registration

- section: Tty drivers and ports
- relevance: 4 - a driver that registers before it is set up can be opened in that state

What are the requirements for a `struct tty_driver` that is passed into `tty_register_driver()` in
order to assure safe usage? Start from `__tty_alloc_driver()`.

## tty.struct-lifetimes: Driver, port and tty lifetimes

- section: Tty drivers and ports
- relevance: 5 - the three objects die at different times and bugs live in the gap

How long do a `struct tty_driver`, a `struct tty_port` and a `struct tty_struct` each live, and
what runs when the last reference to each goes, in which context? Start from `tty_kref_put()`,
`tty_port_put()` and `tty_driver_kref_put()`.

## tty.locks: Locks and their order

- section: Tty drivers and ports
- relevance: 5 - most tty fixes are lock order or missing-lock fixes

What do `tty_mutex`, the `legacy_mutex` that `tty_lock()` takes, `ldisc_sem` and `termios_rwsem`
of `struct tty_struct`, and `mutex` and `lock` of `struct tty_port` each protect? In what order
are they taken where more than one is held, including the two ttys of a pty pair? Start from
`drivers/tty/tty_mutex.c` and the lock subclasses in `drivers/tty/tty.h`.

## tty.ops-context: Context of driver callbacks

- section: Tty drivers and ports
- relevance: 5 - sleeping in the wrong callback is the classic tty driver bug

For the callbacks in `struct tty_operations` that a driver is most likely to implement (open,
close, write, write_room, set_termios, throttle and unthrottle, hangup, shutdown and cleanup,
break_ctl, wait_until_sent), a table: may it sleep, and what, if anything, is the caller
guaranteed to hold? Go by the callers, and say where the kernel-doc in
`include/linux/tty_driver.h` disagrees with them.

## tty.port-helpers: Port open and close helpers

- section: Tty drivers and ports
- relevance: 4 - most drivers should be built on these and many get the pairing wrong

When do `tty_port_open()`, `tty_port_close()` and `tty_port_hangup()` call the `activate` and
`shutdown` callbacks of `struct tty_port_operations`, and under which lock? What do the
initialized and active bits in `iflags` of `struct tty_port` each mean? What does
`tty_port_block_til_ready()` do for an open that does not wait for carrier?

## tty.hangup: Hangup sequence

- section: Tty drivers and ports
- relevance: 5 - hangup races with open, close, read and write

What does `__tty_hangup()` replace the file operations of the open files with, which flag does it
set on the tty and when is that flag cleared, and which driver callbacks does it call? Start from
`__tty_hangup()`.

## tty.hangup-entry-points: Hangup entry points

- section: Tty drivers and ports
- relevance: 5 - the entry point decides in which context the hangup runs

How do `tty_hangup()` and `tty_vhangup()` differ, and from which contexts may each be called? What
does `__tty_hangup()` do differently when one of the open files is the console? Start from
`__tty_hangup()`.

## tty.port-tty-pointers: Port to tty pointers

- section: Tty drivers and ports
- relevance: 5 - interrupt handlers reach the tty through the port

When are the `tty` and `itty` members of `struct tty_port` each set and cleared? What are the
requirements for reading each of them from a driver's interrupt handler or work item in order to
assure safe usage? Start from `tty_port_tty_get()` and `include/linux/tty_port.h`.

## tty.open-close-usage: Pairing of open and close

- section: Tty drivers and ports
- relevance: 4 - drivers that assume a successful open leak or underflow counts

If a driver's `open` in `struct tty_operations` returns an error, is its `close` called for that
file? What are the requirements for a driver's `close` in order to assure safe usage after an
`open` that failed? Name an in-tree driver that shows it. Start from `tty_open()` and
`uart_close()`.

# Line disciplines

## tty.ldisc-ops: Line discipline callbacks

- section: Line disciplines
- relevance: 4 - the receive side has three entry points with different contracts

How do `receive_buf`, `receive_buf2` and `lookahead_buf` in `struct tty_ldisc_ops` differ in when
they are called and what they return? Which of the callbacks that are called from the driver side
may sleep? From which context is `write_wakeup` called, and what does that require of it? Start
from `include/linux/tty_ldisc.h`.

## tty.ldisc-change: Changing the line discipline

- section: Line disciplines
- relevance: 4 - the fallback paths are where the bugs have been

What does `tty_set_ldisc()` fall back to if the new line discipline's open fails, what does a
hangup do to the line discipline, with and without the console among the open files, and when
can `tty->ldisc` therefore be NULL? Start from `drivers/tty/tty_ldisc.c`.

## tty.ldisc-refs: Line discipline references

- section: Line disciplines
- relevance: 5 - calling into a line discipline without a reference is a use after free

Which of the functions that take a reference to a tty's current line discipline may be called from
interrupt context, and what does a NULL return mean? What are the requirements for reading
`tty->ldisc` and for calling a line discipline's callbacks in order to assure safe usage? Start
from `tty_ldisc_ref()`, `tty_ldisc_ref_wait()` and `drivers/tty/tty_ldsem.c`.

# Received data

## tty.flip-workqueue: Workqueue for received data

- section: Received data
- relevance: 4 - no reader named the flag or the fallback correctly

On which workqueue does `tty_buffer_queue_work()` queue the work that feeds the line discipline,
and who creates and destroys that workqueue? How can a driver choose a different workqueue? Start
from `tty_buffer_queue_work()`, `tty_register_driver()` and `tty_port_link_wq()`.

## tty.flip-buffer: Flip buffer structure

- section: Received data
- relevance: 4 - the producer and consumer are lockless and the barriers matter

In `drivers/tty/tty_buffer.c`, what orders a driver's writes of received data against the reads of
the work that feeds the line discipline? What bounds the memory that a port may queue? How does
code that needs the buffers to itself, such as a flush, get exclusive access? Start from
`drivers/tty/tty_buffer.c`.

## tty.flip-usage: Inserting received data

- section: Received data
- relevance: 4 - what a driver's receive path must get right

From which contexts may a driver call the insert functions and `tty_flip_buffer_push()`, and what
do the insert functions return when memory runs out? What are the requirements for inserting
received bytes into one `struct tty_port` from more than one context, in order to assure safe
usage? Start from `include/linux/tty_flip.h`.

# Serial core ports

## tty.uart-structs: Serial core structures

- section: Serial core ports
- relevance: 4 - the mapping from a uart_port to the tty objects

How do `struct uart_driver`, `struct uart_state` and `struct uart_port` relate to each other and
to the tty driver, port and tty, and who allocates each? How does the serial core keep a
`uart_port` from being removed while it is in use? Start from `uart_port_ref()` and
`uart_port_check()` in `drivers/tty/serial/serial_core.c`.

## tty.uart-registration: Registering a UART port

- section: Serial core ports
- relevance: 5 - the devices and the call chain changed when the serial base bus arrived

Which struct devices does `uart_add_one_port()` create, and on which bus? What is `UPF_DEAD` in
the flags of `struct uart_port` for, and when is it set and cleared? Start from
`drivers/tty/serial/serial_port.c` and `serial_core_register_port()`.

## tty.uart-registration-failure: Failed tty device registration

- section: Serial core ports
- relevance: 5 - the return value decides what a driver's probe does next

What does `uart_add_one_port()` return when the tty device cannot be registered, and in what state
does it leave the port? Start from `serial_core_register_port()`.

## tty.uart-registration-callbacks: Callbacks during port registration

- section: Serial core ports
- relevance: 5 - a driver must be ready for callbacks before registration returns

Which of the driver's callbacks can `uart_add_one_port()` make before it returns, and under what
condition is each made or skipped? What must the driver therefore have ready before the call?
Start from `uart_configure_port()`.

## tty.uart-removal: Removing a UART port

- section: Serial core ports
- relevance: 4 - the port structure belongs to the driver and is freed right after

How does `uart_remove_one_port()` wait for users of the port, and what may the low-level driver
do with its `uart_port` and its hardware resources before the call and after it returns? Start
from `serial_core_remove_one_port()`.

## tty.uart-runtime-pm-usage: Runtime PM and port registration

- section: Serial core ports
- relevance: 4 - a probe that hangs only on some configurations

What are the requirements for the order of `pm_runtime_enable()` and `uart_add_one_port()` in a
serial driver's probe in order to assure safe usage, and to which drivers do they apply? Name an
in-tree driver that shows it.

# Serial core callbacks and data path

## tty.uart-ops-context: Context of UART callbacks

- section: Serial core callbacks and data path
- relevance: 5 - half the callbacks run under the port lock with interrupts off

For the callbacks in `struct uart_ops`, a table: which are called with the port lock held and
interrupts disabled, which with only the port mutex, which with nothing, and which may sleep?
Go by the callers in `drivers/tty/serial/serial_core.c`, and say where the kernel-doc in
`include/linux/serial_core.h` disagrees with them.

## tty.uart-tx: Transmit path

- section: Serial core callbacks and data path
- relevance: 4 - the transmit buffer's type and helpers have changed

Where does the serial core keep bytes that wait to be transmitted, and what type is that buffer?
Which helpers should a driver's transmit interrupt use to take bytes from it and account for them?
Under what conditions does the core call `start_tx`? Start from `__uart_start()` and the transmit
helper macros in `include/linux/serial_core.h`.

## tty.uart-startup-shutdown: Port startup and shutdown

- section: Serial core callbacks and data path
- relevance: 4 - which of the driver's startup and shutdown run on open, close and hangup

On the first open, the last close and a hangup of a serial port, which of the driver's
`startup`, `shutdown`, `set_termios`, `pm` and modem-control callbacks are called and in what
order, and what is different for a port that is the console? Start from `uart_port_activate()`,
`uart_tty_port_shutdown()` and `uart_hangup()`.

## tty.uart-console: Serial consoles

- section: Serial core callbacks and data path
- relevance: 4 - console and tty share the port and its lock

How is a serial console tied to its `struct uart_driver`, and how does `uart_console()` decide?
What does the serial core require of a driver whose console implements the atomic and threaded
write callbacks of `struct console`? Name one driver that does.

## tty.uart-port-lock: The port lock

- section: Serial core callbacks and data path
- relevance: 5 - taking the spinlock directly is wrong for a console port

What are the requirements for taking and releasing the lock in `struct uart_port`, in a driver and
in a console callback, in order to assure safe usage? What do the wrappers do beyond taking the
spinlock? Where is the lock initialised? Start from `uart_port_lock_irqsave()` in
`include/linux/serial_core.h`.

## tty.uart-rx-sysrq: Receive path and SysRq

- section: Serial core callbacks and data path
- relevance: 4 - handling SysRq under the port lock deadlocks with the console

What are the requirements for handling a break and a SysRq character in a serial driver's receive
interrupt on a console port, in order to assure safe usage? Which unlock helper or scope-based
guard has to go with `uart_prepare_sysrq_char()`? Start from `uart_prepare_sysrq_char()`,
`uart_handle_break()` and the guards in `include/linux/serial_core.h`.

# serdev

## tty.serdev-model: Serdev controllers and devices

- section: serdev
- relevance: 4 - decides whether a port gets a character device at all

How does a tty port become a serdev controller, and under what condition is the character device
not created? How are received bytes and write wakeups routed to the serdev client? Start from
`tty_port_register_device_attr_serdev()` and `drivers/tty/serdev/serdev-ttyport.c`.

## tty.serdev-termios: Controller termios settings

- section: serdev
- relevance: 4 - a client driver starts from the settings that the controller chose

With which termios settings does the serdev controller open the underlying tty, and which
functions does a client call to change them? Start from `drivers/tty/serdev/serdev-ttyport.c`.

## tty.serdev-client-usage: Serdev client drivers

- section: serdev
- relevance: 4 - the client callbacks have different sleeping rules

How do `serdev_device_write()` and `serdev_device_write_buf()` differ, and which of the callbacks
in `struct serdev_device_ops` may sleep? What are the requirements for a client driver's calls
into serdev, between `serdev_device_open()` and `serdev_device_close()` and from its callbacks, in
order to assure safe usage?

# The 8250 driver modules

## tty.8250-modules: 8250 module split

- section: The 8250 driver modules
- relevance: 4 - decides where a function may live

Into which modules are the common parts of the 8250 driver built, and which module may call into
which? What does that require of a function that is moved from one of their source files to
another? How does in-tree code call from the module that is depended on into the module that
depends on it? Start from `drivers/tty/serial/8250/Makefile`.

# Other users of the tty core

## tty.core-change-checklist: Changing the tty core

- section: Other users of the tty core
- relevance: 4 - a core change is exercised by ptys, consoles, serdev and every driver

Which users of the tty core, other than a serial port driver, take paths through
`drivers/tty/tty_io.c`, `drivers/tty/tty_ldisc.c`, `drivers/tty/tty_port.c` and
`drivers/tty/tty_buffer.c` that a serial port does not take? Which selftests and which debug
options exercise those paths?

# Model gaps

## tty.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.

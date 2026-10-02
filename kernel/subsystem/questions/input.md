# Questions: Input Subsystem

- guide: input.md
- title: Input Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/input-measurement.md` is the
wider set the readers were measured on and `catalogue/input-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## input.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## input.core-files: Core files

- relevance: 4 - the core is a dozen small files and three headers

A table and nothing else, job to file: the input core; the event, joystick and mouse character
device handlers; the multitouch library; the poller; the force-feedback core and its memoryless
helper; the keymap libraries; the touchscreen property helpers; the user-space input device and
its structures; the serio bus and the PS/2 library; `struct input_device_id`; the event codes.
Where a reader is likely to look for a file that does not exist in this tree, say so in the row.
Start from `drivers/input/Makefile` and `include/linux/input.h`.

# Open, close, inhibit and readiness

## input.ready-state: Output events and readiness

- section: Open, close, inhibit and readiness
- relevance: 5 - when event() may run has changed and nothing in a diff shows it

When may the core call a device's `event()` callback relative to its `open()` and `close()`,
what gates it, and what state is pushed to the driver when the gate opens and when it shuts?
Start from `input_event_dispose()` and `input_dev_toggle()`.

## input.open-close: Open and close callbacks

- section: Open, close, inhibit and readiness
- relevance: 4 - where drivers start and stop the hardware

When does the core call a device's `open()` and `close()`, given that users are counted, and what
serialises the two callbacks? What does the core do when `open()` returns an error? Start from
`input_open_device()` and `input_close_device()`.

## input.flush-callback: Flush callback

- section: Open, close, inhibit and readiness
- relevance: 4 - a driver that sets it must know when it runs

When does the core call a device's `flush()` callback, and under which lock? Start from
`input_flush_device()`.

## input.inhibit: Inhibiting a device

- section: Open, close, inhibit and readiness
- relevance: 4 - close() and open() run without any handler asking

Which driver callbacks do inhibiting and uninhibiting an input device call, and under which
lock? What happens to pressed keys, active contacts and incoming events while inhibited, and
what do the two operations return on a device that is being unregistered? Start from
`input_inhibit_device()`.

## input.mutex-scope: Device mutex

- section: Open, close, inhibit and readiness
- relevance: 4 - drivers that take it themselves must know what already holds it

What does the mutex inside `struct input_dev` protect, which driver callbacks run with it
already held, and when does a driver need to take it itself?

## input.polling: Polled devices

- section: Open, close, inhibit and readiness
- relevance: 4 - the old separate polled-device structure is what people remember

How does a driver make an input device polled in this tree, where a reader's memory offers a
separate polled-device structure and its own allocation call? When does the poll function start
and stop relative to `open()`, `close()`, inhibit and suspend, and what bounds the interval user
space can set? Start from `input_setup_polling()`.

## input.device-enabled-usage: Checking for an active device

- section: Open, close, inhibit and readiness
- relevance: 4 - drivers read users directly or without the lock

How should a driver test whether its device currently has users and is not inhibited, and which
lock must it hold? What are the requirements for a suspend or resume callback that calls
`input_device_enabled()` in order to assure safe usage? Start from `input_device_enabled()`.

# Registering and unregistering a device

## input.register-setup: Setup before registration

- section: Registering and unregistering a device
- relevance: 4 - decides which driver lines are redundant and which are needed

What does `input_allocate_device()` already initialise, and what does `input_register_device()`
itself set or clear in a device's capability bitmaps? What must a driver have set before it calls
`input_register_device()`?

## input.absinfo: Absolute axis information

- section: Registering and unregistering a device
- relevance: 4 - old code and the prose guide use fields that are gone

Where do the minimum, maximum, fuzz, flat and resolution of an absolute axis live, where a
reader's memory offers other fields, and when is that storage allocated? What does registration
do if an absolute device has none?

## input.register-visible: Callbacks during registration

- section: Registering and unregistering a device
- relevance: 5 - a callback can run before the registering call returns

At what point inside `input_register_device()` can the driver's `open()`, `event()` and keymap
callbacks first be called, by whom, and what does that require of the order of initialisation in
a probe function? Name an in-tree handler that opens a device from its connect callback.

## input.register-failure: Registration failure

- section: Registering and unregistering a device
- relevance: 4 - who frees after a failed register differs by kind of device

When `input_register_device()` fails, what has the core already undone, and what must the caller
still do for an unmanaged device and for a managed one?

## input.unregister-sequence: Unregistration steps

- section: Registering and unregistering a device
- relevance: 5 - what is and is not stopped when it returns

In what order does `input_unregister_device()` carry out its steps, and which callback of `struct
ff_device` does it call? What is guaranteed to have stopped when it returns? Start from
`__input_unregister_device()` and `input_disconnect_device()`.

## input.unregister-callbacks: Callbacks after unregistration

- section: Registering and unregistering a device
- relevance: 5 - decides whether callbacks need guards against unbind

Once `input_unregister_device()` has returned, which of the driver's callbacks can still be
invoked through a handler? By what path is the driver's `close()` called during unregistration,
and when is it not called? What does the core do with an `input_event()` the driver makes
afterwards? Start from `evdev_disconnect()` and `evdev_mark_dead()`.

## input.evdev-after-disconnect: Event device after disconnect

- section: Registering and unregistering a device
- relevance: 5 - decides whether callbacks need guards against calls from user space after unbind

After `evdev_disconnect()` has run, what does a system call on an event character device that is
still open return, and what stops it from reaching the driver? Start from `evdev_mark_dead()`.

## input.refcount-lifetime: Reference counting

- section: Registering and unregistering a device
- relevance: 4 - the device outlives the driver's private data

What keeps a `struct input_dev` alive after `input_unregister_device()` returns, who drops the
last reference, and what is freed when it goes? Start from `input_dev_release()`.

## input.free-unregister-usage: Freeing and unregistering

- section: Registering and unregistering a device
- relevance: 5 - the classic double free, and a pattern that only looks like one

What are the requirements for calling `input_free_device()` and `input_unregister_device()` on the
same device in order to assure safe usage? What does `input_free_device()` do with a NULL pointer?

## input.async-teardown-usage: Timers and work at teardown

- section: Registering and unregistering a device
- relevance: 5 - the recurring use-after-free in input drivers

What are the requirements for stopping a driver's own timers, work items and interrupt handlers
relative to `input_unregister_device()` and to the freeing of private data, in order to assure
safe usage?

## input.serio-teardown-usage: Serio teardown

- section: Registering and unregistering a device
- relevance: 4 - the interrupt can still run while disconnect frees things

What are the requirements for the order of `serio_close()`, `input_unregister_device()`, stopping
work and freeing private data in a serio driver's `disconnect()` in order to assure safe usage?
What does `serio_pause_rx()` guarantee? Name in-tree code that shows the order.

# Managed devices

## input.devm-lifecycle: Managed allocation and teardown

- section: Managed devices
- relevance: 5 - when each half runs decides every ordering question

At what point is each devres entry of a device from `devm_input_allocate_device()` added to the
parent device? Where in the unwinding of a driver's managed resources is the device therefore
unregistered, and where is it freed? Start from `devm_input_device_unregister()` and
`devm_input_device_release()`.

## input.devm-manual-calls: Manual calls on managed devices

- section: Managed devices
- relevance: 4 - reviewers flag safe code as a double free

What happens when `input_free_device()` or `input_unregister_device()` is called by hand on a
device from `devm_input_allocate_device()`: is either a double free or a double unregister, and
what does the core do to the devres entries?

## input.devm-parent: Parent of a managed device

- section: Managed devices
- relevance: 3 - a common redundant line, and one helper depends on it

What sets `dev.parent` of an input device, may a driver override it for a managed device, and
what do the library helpers that need a parent do when it is not set?

## input.devm-ordering-usage: Mixing managed and unmanaged resources

- section: Managed devices
- relevance: 5 - the release order is what breaks

What are the requirements for the order in which a driver acquires and releases its other
resources around a device from `devm_input_allocate_device()`, in order to assure safe usage? When
is an explicit `input_unregister_device()` in `remove()` required for such a device, and when is
it redundant?

# Reporting events

## input.event-path: Path of an event

- section: Reporting events
- relevance: 4 - the map for everything else in this part

Between a driver's call to `input_event()` and a handler, where is it decided what to do with
the event, where are values queued and what flushes them, and what do a filter and a grab change
about which handles see them? Name the functions to start reading from.

## input.event-filtering: Events the core drops

- section: Reporting events
- relevance: 5 - explains events that never reach user space

A table by event type of the conditions under which `input_get_disposition()` discards an event a
driver reports. Which event types does it pass on when the value has not changed, and what does a
value of two mean for a key? Start from `input_get_disposition()`.

## input.sync-frames: Frames and synchronisation

- section: Reporting events
- relevance: 4 - a missing sync is the commonest driver bug

What does the core do with a frame that holds nothing but the sync, what happens when a driver
never syncs and the queue fills, and how can a handler tell a synthetic sync from a driver's?

## input.pre-register-events: Events before registration

- section: Reporting events
- relevance: 3 - allows a simpler probe order than reviewers expect

Is it safe to call `input_event()` on a device that has been allocated but not yet registered,
what happens to the event, and what is that good for?

## input.output-event-context: Events sent to the device

- section: Reporting events
- relevance: 4 - the callback runs in atomic context

Which event types does the core pass down to a device's `event()` callback, in what context and
under which lock is it called, and how do drivers that must sleep to program the hardware cope?

## input.event-context: Reporting context and locks

- section: Reporting events
- relevance: 5 - the lock is a spinlock with interrupts off

Which lock does `input_event()` take and how, and from which contexts may it be called? What are
the requirements for a driver that holds its own lock while it calls `input_event()` in order to
assure safe usage?

# Multitouch

## input.mt-init: Initialising slots

- section: Multitouch
- relevance: 4 - flags and call order decide what the core does for the driver

A table of the flags `input_mt_init_slots()` takes and what each makes the core do for the
driver. Where must the call come relative to setting the multitouch axis parameters, and what
does it return for zero slots, for too many, and for a second call?

## input.mt-frame: Reporting a frame of contacts

- section: Multitouch
- relevance: 4 - the sequence is easy to get subtly wrong

In what sequence does a slotted multitouch driver report one frame of contacts, what does
`input_mt_report_slot_state()` return and when does it assign a new tracking id, and what does
`input_mt_sync_frame()` do beyond closing the frame?

## input.mt-release: Releasing contacts

- section: Multitouch
- relevance: 3 - the core does it at some points and not at others

At which points does the core lift all active contacts by itself, which function does it and is
it available to drivers, and when must a driver release contacts itself?

## input.mt-slot-index-usage: Slot numbers from the device

- section: Multitouch
- relevance: 5 - the index comes from hardware

What does the core do with a slot number outside the range the driver declared? What are the
requirements for a driver that uses a contact or slot number reported by the hardware in its own
code, in order to assure safe usage? Start from `input_handle_abs_event()`.

# Force feedback

## input.ff-create: Creating a force-feedback device

- section: Force feedback
- relevance: 4 - the order of calls is fixed and the limits are checked

What must a driver set on the input device before it calls `input_ff_create()`, and what must it
set on the resulting `struct ff_device` afterwards? Which limits does `input_ff_create()` enforce?
Start from `drivers/input/ff-core.c`.

## input.ff-destroy: Freeing the ff device

- section: Force feedback
- relevance: 4 - decides what a driver's error path and remove may free

Who frees the `struct ff_device` that `input_ff_create()` installed and the private data attached
to it, and at which point in the life of the input device? What are the requirements for a driver
that calls `input_ff_destroy()` itself in order to assure safe usage?

## input.ff-memless-timer: Memoryless helper timer

- section: Force feedback
- relevance: 5 - the timer calls into the driver

What stops the timer that the memoryless force-feedback helper runs, at which points in the
device's life and through which callbacks of `struct ff_device`, and what does that leave for
the driver to stop itself?

## input.ff-memless-ownership: Memoryless helper data

- section: Force feedback
- relevance: 5 - ownership passes on success only

Who owns the data pointer passed to `input_ff_create_memless()` after the call succeeds and after
it fails, and what frees it? What are the requirements for a driver's later use of that pointer in
order to assure safe usage? Name an in-tree caller that handles the failure case.

## input.ff-play-effect-usage: Deferred effect playback

- section: Force feedback
- relevance: 4 - the callback is atomic, so drivers defer, and the deferral leaks

In what context does the memoryless helper call the driver's `play_effect` callback? What are the
requirements for work that a driver defers from `play_effect`, at close, suspend and unbind, in
order to assure safe usage?

# Handlers

## input.handler-methods: Handler event methods

- section: Handlers
- relevance: 4 - the three methods are exclusive and one has a return contract

Which of the methods by which an input handler receives events is used when, may a handler
define more than one, and what must each return? In what context are they called? Start from
`input_handle_setup_event_handler()`.

## input.handler-connect: Connect and disconnect

- section: Handlers
- relevance: 4 - the core serialises these and relies on what they do

What must a handler's `connect()` and `disconnect()` do, and in what order, what serialises them
against device and handler registration, and what does a non-zero return from `connect()` mean
to the core?

## input.handler-start: Start callback

- section: Handlers
- relevance: 3 - the points at which it is called have changed

What is a handler's `start()` for, at which points does the core call it, and under which lock?

# Core locking and other users

## input.lock-order: Lock order

- section: Core locking and other users
- relevance: 4 - five locks nest and lockdep has caught inversions here

In what order do the global input mutex, a device's mutex, its event spinlock, the
force-feedback mutex and a handler's own locks nest, and which paths establish that order?

## input.core-change-checklist: Changing the core

- section: Core locking and other users
- relevance: 4 - a core change reaches every handler and the user ABI

What do the RCU list walks in the event path of `drivers/input/input.c` rely on? Which compat
paths and which tests depend on the layout of `struct input_event` and `struct ff_effect`?

# Maintainer conventions

## input.style: Error variables and cleanup guards

- section: Maintainer conventions
- relevance: 3 - reviewers enforce them and the tree does not write them down

Which conventions for input drivers does the tree write down, and where? For the naming of error
variables and the use of scope-based cleanup and lock guards, what do the files of the input core
under `drivers/input/` do?

# Model gaps

## input.model-gaps: Other mistakes models make

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

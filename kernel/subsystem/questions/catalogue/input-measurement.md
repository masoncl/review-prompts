# Questions: Input Subsystem (measurement set)

- guide: input.md
- title: Input Subsystem

A wide set of questions about the input core and what it owes to, and expects
from, the drivers under `drivers/input/`: the life of an input device, managed
devices, open, close and inhibit, the path of an event, keymaps, the multitouch
library, polling, force feedback, handlers and the event character device, the
user-space device, and the serio bus with its PS/2 library. It is used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 1,685 words and
covers device lifetime, managed devices, force-feedback memory and the
maintainer's style. HID has its own set. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## input.core-files: Core files

- section: Finding your way
- relevance: 4 - the core is a dozen small files and three headers
- words: 110

Which files hold the input core, the event, joystick and mouse character
device handlers, the multitouch library, the poller, the force-feedback core
and its memoryless helper, the keymap libraries, the touchscreen property
helpers, the user-space input device, the serio bus and PS/2 library, the
structure definitions, `struct input_device_id` and the event codes? A table.
Start from `drivers/input/Makefile` and `include/linux/input.h`.

## input.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - the prose guide and the code have drifted apart
- words: 80

Which files under `Documentation/input/` and `Documentation/driver-api/` are
the authority on writing an input driver, on event codes, on the multitouch
protocol and on force feedback, and does the driver-writing guide name any
structure fields or functions that this tree no longer has? Start from
`Documentation/input/input-programming.rst`.

## input.tests: Tests

- section: Finding your way
- relevance: 2 - small, but a core change is expected to keep it passing
- words: 50

What tests does the tree carry for the input core, how are they built and
run, and what do they cover? Start from `drivers/input/tests/`.

## input.kconfig-libraries: Library configuration symbols

- section: Finding your way
- relevance: 3 - a missing select is a link failure in some configurations
- words: 60

Which helper libraries under `drivers/input/` have their own configuration
symbol that a driver has to select, which are always part of the core module,
and what is each symbol called? Start from `drivers/input/Kconfig` and
`drivers/input/Makefile`.

# The structures

## input.dev-struct: Device structure

- section: Structures
- relevance: 4 - every driver fills it and every question below names its fields
- words: 110

What are the groups of fields in `struct input_dev`: identity, capability
bitmaps, current-state bitmaps, keymap, callbacks, locks, user counting and
the flags that track unregistration, inhibition and readiness? Say in a phrase
what each group is for and who writes it, the driver or the core.

## input.handler-handle: Handlers and handles

- section: Structures
- relevance: 4 - the three-way split is what the unregister guarantees rest on
- words: 90

What are `struct input_handler` and `struct input_handle`, how do they relate
to a `struct input_dev`, which lists link them, and which handlers does this
tree register outside `drivers/input/`?

## input.registration-bitmaps: Bitmaps at registration

- section: Structures
- relevance: 4 - decides which driver lines are redundant and which are needed
- words: 60

What does `input_register_device()` itself set, clear or wipe in a device's
capability bitmaps, and what does that make redundant in a driver?

## input.set-capability: Declaring capabilities

- section: Structures
- relevance: 3 - the helpers differ in what else they set up
- words: 70

What do `input_set_capability()` and `input_set_abs_params()` do beyond
setting one bit, what happens when the type or code is out of range, and what
does plain `__set_bit()` on a capability bitmap leave undone?

## input.absinfo: Absolute axis information

- section: Structures
- relevance: 4 - old code and the prose guide use fields that are gone
- words: 70

Where do the minimum, maximum, fuzz, flat and resolution of an absolute axis
live, when is that storage allocated, how do drivers read and write it, and
what does registration do if an absolute device has none?

## input.identity-fields: Identity fields

- section: Structures
- relevance: 3 - reviewers ask for these and the core requires none of them
- words: 60

Which of `name`, `phys`, `uniq`, `id` and `dev.parent` does the core require
before registration, which does it merely print or export, and where does
each show up for user space?

# Device lifetime

## input.alloc-register: Allocation and registration

- section: Lifetime of an input device
- relevance: 4 - the sequence every driver follows
- words: 80

Which calls allocate, register, unregister and free a `struct input_dev`, what
does allocation already initialise, and what must a driver have set up before
it registers? Start from `input_allocate_device()`.

## input.register-visible: Visibility at registration

- section: Lifetime of an input device
- relevance: 5 - a callback can run before the registering call returns
- words: 80

At what point inside `input_register_device()` can the driver's `open()`,
`event()` and keymap callbacks first be called, by whom, and what does that
require of the order of initialisation in a probe function? Name an in-tree
handler that opens a device from its connect callback.

## input.register-failure: Registration failure

- section: Lifetime of an input device
- relevance: 4 - who frees after a failed register differs by kind of device
- words: 60

When `input_register_device()` fails, what has the core already undone, and
what must the caller still do for an unmanaged device and for a managed one?

## input.free-unregister-usage: Freeing and unregistering

- section: Lifetime of an input device
- relevance: 5 - the classic double free, and a pattern that only looks like one
- words: 90

What usage of `input_free_device()` and `input_unregister_device()` on the
same device is unsafe, and what usage that looks similar is correct, including
a shared error path that handles both the registered and the unregistered
case? Say what `input_free_device()` does with a NULL pointer.

## input.refcount-lifetime: Reference counting

- section: Lifetime of an input device
- relevance: 4 - the device outlives the driver's private data
- words: 70

What keeps a `struct input_dev` alive after `input_unregister_device()`
returns, who drops the last reference, and what is freed when it goes? Start
from `input_dev_release()`.

## input.unregister-sequence: Unregistration steps

- section: Lifetime of an input device
- relevance: 5 - what is and is not stopped when it returns
- words: 110

List in order what `input_unregister_device()` does: the flag it sets, what it
does to pressed keys, how handlers are detached and under which lock, which
timers it stops, which force-feedback hook it calls and when the device
leaves sysfs. Start from `__input_unregister_device()` and
`input_disconnect_device()`.

## input.after-unregister-calls: Callbacks after unregistration

- section: Lifetime of an input device
- relevance: 5 - decides whether callbacks need guards against unbind
- words: 90

Once `input_unregister_device()` has returned, which of the driver's callbacks
can still be invoked through a handler, is the driver's `close()` called
during unregistration and by what path, and what happens to an `input_event()`
the driver makes afterwards? Start from `evdev_disconnect()`.

## input.async-teardown-usage: Timers and work at teardown

- section: Lifetime of an input device
- relevance: 5 - the recurring use-after-free in input drivers
- words: 90

What usage of a driver's own timers, work items and interrupt handlers around
`input_unregister_device()` and the freeing of private data is unsafe, and
what that looks similar is correct? Say which asynchronous sources the core
stops by itself and which it cannot know about.

# Managed devices

## input.devm-alloc: Managed allocation

- section: Managed devices
- relevance: 4 - which calls have a managed form and which do not
- words: 70

What does `devm_input_allocate_device()` set up that `input_allocate_device()`
does not, is there a managed form of registration, and how is a managed device
registered?

## input.devm-two-step: Managed teardown

- section: Managed devices
- relevance: 5 - when each half runs decides every ordering question
- words: 80

Which devres entries does a managed input device have, at what point is each
added to the parent device, and so where in the unwinding of a driver's
managed resources is the device unregistered and where is it freed? Start
from `devm_input_device_unregister()` and `devm_input_device_release()`.

## input.devm-manual-calls: Manual calls on managed devices

- section: Managed devices
- relevance: 4 - reviewers flag safe code as a double free
- words: 70

What happens when `input_free_device()` or `input_unregister_device()` is
called by hand on a device from `devm_input_allocate_device()`: is either a
double free or a double unregister, and what does the core do to the devres
entries?

## input.devm-ordering-usage: Mixing managed and unmanaged resources

- section: Managed devices
- relevance: 5 - the release order is what breaks
- words: 90

What usage that mixes a managed input device with resources released by hand
in `remove()`, or with managed resources acquired in the wrong order, is
unsafe, and what that looks similar is correct? Say when an explicit
`input_unregister_device()` in `remove()` is required for a managed device and
when it is redundant.

## input.devm-parent: Parent of a managed device

- section: Managed devices
- relevance: 3 - a common redundant line, and one helper depends on it
- words: 50

What sets `dev.parent` of an input device, may a driver override it for a
managed device, and which library helpers refuse to work or misbehave when the
parent is not set?

# Open, close and inhibit

## input.open-close: Open and close callbacks

- section: Open, close and inhibit
- relevance: 4 - where drivers start and stop the hardware
- words: 80

When does the core call a device's `open()` and `close()`, how are users
counted, what serialises the two callbacks, what happens when `open()` returns
an error, and what is `flush()` for? Start from `input_open_device()` and
`input_close_device()`.

## input.ready-state: Output events and readiness

- section: Open, close and inhibit
- relevance: 5 - when event() may run has changed and nothing in a diff shows it
- words: 80

When may the core call a device's `event()` callback relative to its `open()`
and `close()`, which field gates it, and what state is pushed to the driver
when the gate opens and when it shuts? Start from `input_event_dispose()` and
`input_dev_toggle()`.

## input.inhibit: Inhibiting a device

- section: Open, close and inhibit
- relevance: 4 - close() and open() run without any handler asking
- words: 80

How is an input device inhibited and uninhibited, which driver callbacks does
that call and under which lock, what happens to pressed keys, active contacts
and incoming events while inhibited, and what do the two operations return on
a device that is being unregistered? Start from `input_inhibit_device()`.

## input.device-enabled-usage: Checking for an active device

- section: Open, close and inhibit
- relevance: 4 - drivers read users directly or without the lock
- words: 70

How should a driver test whether its device currently has users and is not
inhibited, which lock must it hold, and what usage in suspend and resume
callbacks is unsafe and what that looks similar is correct? Start from
`input_device_enabled()`.

## input.mutex-scope: Device mutex

- section: Open, close and inhibit
- relevance: 4 - drivers that take it themselves must know what already holds it
- words: 70

What does the mutex inside `struct input_dev` protect, which driver callbacks
and core operations run with it held, and when does a driver need to take it
itself?

## input.pm-core: Core suspend and resume

- section: Open, close and inhibit
- relevance: 3 - the core already does part of what drivers reimplement
- words: 70

What does the input core do by itself to every input device on suspend,
resume, freeze and poweroff, and what does `input_reset_device()` do and for
whom? Start from `input_dev_pm_ops`.

# Events

## input.event-path: Path of an event

- section: Reporting events
- relevance: 4 - the map for everything else in this part
- words: 110

Trace a call to `input_event()` from a driver to a handler: the capability
check, the lock, the function that decides what to do with the event, where
values are queued, what flushes them, and how they reach each handle,
including filters and a grab. Name the functions.

## input.event-filtering: Events the core drops

- section: Reporting events
- relevance: 5 - explains events that never reach user space
- words: 100

For each event type, under what conditions does the core discard an event a
driver reports: unsupported code, unchanged value, zero value, fuzz, an
inhibited device? Say which types are never filtered for duplicates and what a
key value of two means. A table. Start from `input_get_disposition()`.

## input.sync-frames: Frames and synchronisation

- section: Reporting events
- relevance: 4 - a missing sync is the commonest driver bug
- words: 80

What does `input_sync()` do to the queued values, what does the core do with
a frame that holds nothing but the sync, what happens when a driver never
syncs and the queue fills, and how can a handler tell a synthetic sync from a
driver's?

## input.event-context: Reporting context and locks

- section: Reporting events
- relevance: 5 - the lock is a spinlock with interrupts off
- words: 80

Which lock does `input_event()` take and how, from which contexts may it be
called, and what usage of a driver's own lock around event reporting is
unsafe, given that the core calls back into the driver under the same lock,
and what that looks similar is correct?

## input.pre-register-events: Events before registration

- section: Reporting events
- relevance: 3 - allows a simpler probe order than reviewers expect
- words: 60

Is it safe to call `input_event()` on a device that has been allocated but
not yet registered, what happens to the event, and what is that good for?

## input.report-helpers: Report helpers

- section: Reporting events
- relevance: 2 - one of them changes the value
- words: 50

What do the `input_report_*()` helpers and `input_sync()` expand to, which of
them alter the value they are given, and how does a driver report a hardware
autorepeat?

## input.timestamps: Event timestamps

- section: Reporting events
- relevance: 3 - a driver can supply its own, and it is reset per frame
- words: 60

How does a driver give the core a hardware timestamp for a frame, which clocks
are kept, when is the timestamp taken if the driver gives none, and when is it
cleared? Start from `input_set_timestamp()`.

## input.events-per-packet: Packet size hint

- section: Reporting events
- relevance: 3 - sizes both the core's queue and each reader's buffer
- words: 60

What is `hint_events_per_packet`, how does the core estimate it at
registration, what is sized from it, and when should a driver set it by hand?
Start from `input_estimate_events_per_packet()`.

## input.autorepeat: Software autorepeat

- section: Reporting events
- relevance: 3 - the defaults apply only when the driver leaves fields zero
- words: 70

How does a driver get software key autorepeat, what defaults does
registration install and under what condition, how does a driver that repeats
in hardware opt out, and which timer and lock does the repeat use? Start from
`input_enable_softrepeat()`.

## input.output-event-context: Events sent to the device

- section: Reporting events
- relevance: 4 - the callback runs in atomic context
- words: 70

Which event types does the core pass down to a device's `event()` callback, in
what context and under which lock is it called, and how do drivers that must
sleep to program the hardware cope?

## input.inject: Injected events

- section: Reporting events
- relevance: 3 - the path a write to the character device takes
- words: 60

How does an event written by a handler or by user space enter the core, how
does that differ from `input_event()`, and how does a grab affect it? Start
from `input_inject_event()`.

# Keymaps

## input.keymap-default: Default keymap handling

- section: Keymaps
- relevance: 3 - three fields switch the default on
- words: 70

Which fields make the core's default get and set keycode work, what does the
default set do to the key capability bitmap and to a key that is currently
pressed, and may a driver call the default from its own callback? Start from
`input_default_setkeycode()` and `input_set_keycode()`.

## input.keymap-callback-context: Keymap callback context

- section: Keymaps
- relevance: 3 - the callbacks must not sleep
- words: 50

In what context and under which lock are a device's `getkeycode()` and
`setkeycode()` called, and what does that forbid?

## input.sparse-keymap: Sparse keymaps

- section: Keymaps
- relevance: 3 - who owns the copy of the map has changed over time
- words: 70

What does `sparse_keymap_setup()` allocate and against which device's
lifetime, does the driver free it, which capability bits does it set, and how
is an unknown scancode reported? Start from `drivers/input/sparse-keymap.c`.

## input.matrix-keymap: Matrix keymaps

- section: Keymaps
- relevance: 3 - it depends on the parent being set first
- words: 70

What does `matrix_keypad_build_keymap()` need to be set on the input device
before it is called, where does the keymap memory come from when none is
passed, how is a scancode formed from row and column, and what does it return
for an out-of-range entry?

# Multitouch

## input.mt-init: Initialising slots

- section: Multitouch
- relevance: 4 - flags and call order decide what the core does for the driver
- words: 100

What does `input_mt_init_slots()` set up, what does each of its flags make the
core do, where must it come relative to setting the multitouch axis
parameters, what are its limits on the slot count, and what does it return
for zero slots or a second call? A table of flags.

## input.mt-frame: Reporting a frame of contacts

- section: Multitouch
- relevance: 4 - the sequence is easy to get subtly wrong
- words: 90

List the calls a slotted multitouch driver makes for one frame of contacts,
say what `input_mt_report_slot_state()` returns and when it assigns a new
tracking id, and what `input_mt_sync_frame()` does beyond closing the frame.

## input.mt-slot-index-usage: Slot numbers from the device

- section: Multitouch
- relevance: 5 - the index comes from hardware
- words: 70

What does the core do with a slot number outside the range the driver
declared, and what usage of a contact or slot number reported by the hardware
is unsafe in the driver's own code, and what that looks similar is correct?
Start from `input_handle_abs_event()`.

## input.mt-tracking: In-kernel tracking

- section: Multitouch
- relevance: 3 - the helpers fail in ways callers do not check
- words: 70

What do `input_mt_assign_slots()` and `input_mt_get_slot_by_key()` need in
order to work, what do they return when they cannot assign a slot, and what
must the driver call every frame for them to stay correct?

## input.mt-release: Releasing contacts

- section: Multitouch
- relevance: 3 - the core does it at some points and not at others
- words: 60

At which points does the core lift all active contacts by itself, which
function does it and is it available to drivers, and when must a driver
release contacts itself?

## input.touchscreen-props: Touchscreen property helper

- section: Multitouch
- relevance: 3 - it rewrites axis parameters the driver set earlier
- words: 70

What does `touchscreen_parse_properties()` read and change, where must it be
called relative to setting axis parameters and initialising slots, and how
are the swap and invert settings applied when positions are reported?

# Polling

## input.polling: Polled devices

- section: Polling
- relevance: 4 - the old separate polled-device structure is what people remember
- words: 80

How does a driver make an input device polled in this tree, does a separate
polled-device structure and its allocation call still exist, when does the
poll function run relative to `open()` and `close()`, on which workqueue, and
what is exposed in sysfs? Start from `input_setup_polling()`.

# Force feedback

## input.ff-create: Creating a force-feedback device

- section: Force feedback
- relevance: 4 - the order of calls is fixed and the limits are checked
- words: 80

What does `input_ff_create()` allocate and install on the input device, what
must be set before and after it, which callbacks are mandatory, what limits
does it enforce, and who frees it all? Start from `drivers/input/ff-core.c`.

## input.ff-callback-context: Force-feedback callback context

- section: Force feedback
- relevance: 4 - half of them may sleep and half may not
- words: 80

For each callback in `struct ff_device`, in what context and under which lock
is it called, and which of them may sleep? A table.

## input.ff-memless-ownership: Memoryless helper data

- section: Force feedback
- relevance: 5 - ownership passes on success only
- words: 80

Who owns the data pointer passed to `input_ff_create_memless()` after it
succeeds and after it fails, how is it eventually freed, and so what usage of
that pointer by a driver is unsafe and what that looks similar is correct?
Name an in-tree caller that handles the failure case.

## input.ff-memless-timer: Memoryless helper timer

- section: Force feedback
- relevance: 5 - the timer calls into the driver
- words: 70

What stops the timer that the memoryless force-feedback helper runs, at which
points in the device's life, through which callbacks of `struct ff_device`,
and what does that leave for the driver to stop itself?

## input.ff-play-effect-usage: Deferred effect playback

- section: Force feedback
- relevance: 4 - the callback is atomic, so drivers defer, and the deferral leaks
- words: 70

In what context does the memoryless helper call the driver's `play_effect`,
what do drivers on sleeping buses do about it, and what usage of that deferred
work at close, suspend and unbind is unsafe and what that looks similar is
correct?

## input.ff-effect-range: Effect type range

- section: Force feedback
- relevance: 2 - the bounds moved when a new effect type was added
- words: 50

Which effect types and waveforms does this tree define, what are the lowest
and highest valid effect type, and where does the core check an uploaded
effect against them? Start from `include/uapi/linux/input.h`.

# Handlers

## input.handler-methods: Handler event methods

- section: Handlers
- relevance: 4 - the three methods are exclusive and one has a return contract
- words: 80

Which methods can an input handler use to receive events, may it define more
than one, what must each return, in what context are they called, and how
does the core turn the handler's choice into what it calls per handle? Start
from `input_handle_setup_event_handler()`.

## input.handler-connect: Connect and disconnect

- section: Handlers
- relevance: 4 - the core serialises these and relies on what they do
- words: 80

What must a handler's `connect()` and `disconnect()` do, in what order, what
serialises them against device and handler registration, and what does a
non-zero return from `connect()` mean to the core?

## input.handler-match: Matching devices to handlers

- section: Handlers
- relevance: 3 - the match flags cover less than the table suggests
- words: 60

How does the core decide a handler matches a device: which fields of
`struct input_device_id` are gated by flags and which are always compared,
what ends the table, and what is the `match()` callback for?

## input.handler-start: Start callback

- section: Handlers
- relevance: 3 - the points at which it is called have changed
- words: 60

What is a handler's `start()` for, at which points does the core call it, and
under which lock?

## input.grab: Grabbing a device

- section: Handlers
- relevance: 3 - one handle takes all events
- words: 60

What does grabbing an input device do to event delivery and to injected
events, how is the grab pointer protected, and what happens to it when the
grabbing handle closes?

## input.passive-observer: Passive observers

- section: Handlers
- relevance: 2 - a handler that must not power the hardware up
- words: 50

What does marking a handler as a passive observer change about opening and
closing a device through its handles, and does any handler in this tree set
it?

## input.evdev-client: Event device clients

- section: Handlers
- relevance: 3 - the per-reader buffer and its overflow rule
- words: 80

What does the event character device keep per open file, how is the buffer
sized, what happens when it overflows, and what do the event mask, the clock
selection and revocation do? Start from `struct evdev_client`.

## input.evdev-dead: Event device after disconnect

- section: Handlers
- relevance: 4 - this is what keeps user space out of a driver that has gone
- words: 70

After its input device is unregistered, what stops reads, writes, ioctls and
new opens on an event character device from reaching the driver, and which
lock makes that reliable? Start from `evdev_mark_dead()`.

# User-space devices

## input.uinput-lifecycle: User-space input devices

- section: User-space devices
- relevance: 3 - a state machine around the ordinary registration calls
- words: 80

What states does a user-space input device go through between opening the
control node and destroying the device, which ioctls move it along, what
validation is applied to what user space supplies, and where did its
structure definitions go? Start from `drivers/input/misc/uinput.c`.

# The serio bus and PS/2

## input.serio-ports: Serio port lifetime

- section: Serio and PS/2
- relevance: 3 - registration is asynchronous and the core frees the port
- words: 80

How is a `struct serio` port allocated, registered and unregistered, which of
those is asynchronous, who frees the structure, and how are child ports
removed? Start from `__serio_register_port()`.

## input.serio-driver: Serio driver callbacks

- section: Serio and PS/2
- relevance: 3 - the interrupt callback runs under a spinlock
- words: 80

What are the callbacks of `struct serio_driver`, when is each called, in what
context does `interrupt()` run, and what do `serio_open()` and `serio_close()`
do and where may they be called from?

## input.serio-teardown-usage: Serio teardown

- section: Serio and PS/2
- relevance: 4 - the interrupt can still run while disconnect frees things
- words: 80

In a serio driver's `disconnect()`, what ordering of closing the port,
unregistering the input device, stopping work and freeing private data is
unsafe, and what that looks similar is correct? Say what pausing receive on a
port does.

## input.libps2: PS/2 command library

- section: Serio and PS/2
- relevance: 3 - the receive path was reworked around one handler
- words: 80

How does a PS/2 driver send a command and receive bytes through the library:
what does it pass at initialisation, which function does it install as the
serio interrupt handler, what serialises commands, and how are acknowledge
and response bytes told from ordinary data? Start from `ps2_init()`.

# Changing the implementation

## input.lock-order: Lock order

- section: What a change must preserve
- relevance: 4 - five locks nest and lockdep has caught inversions here
- words: 80

In what order do the global input mutex, a device's mutex, its event
spinlock, the force-feedback mutex and a handler's own locks nest, and which
paths establish that order?

## input.core-change-checklist: Changing the core

- section: What a change must preserve
- relevance: 4 - a core change reaches every handler and the user ABI
- words: 90

What must a change to the input core keep working besides the core itself:
the handlers inside and outside `drivers/input/`, the RCU list walks in the
event path, the compat paths for event and effect structures, the procfs,
sysfs and uevent output, the module alias format and the tests?

## input.uapi-codes: Event codes and device ids

- section: What a change must preserve
- relevance: 3 - the maxima are baked into module aliases
- words: 70

What has to be kept in step when an event code or a maximum is added: which
header holds `struct input_device_id` and the matching maxima, what fails to
build when they disagree, and what is user-visible ABI?

# Conventions

## input.style: Maintainer conventions

- section: Conventions
- relevance: 3 - reviewers enforce them and the tree does not write them down
- words: 80

What conventions do input patches follow for the subject line, comment style,
naming of error variables, returning from a function with several failure
points, and the use of scope-based cleanup and lock guards, and is any of it
written down in the tree?

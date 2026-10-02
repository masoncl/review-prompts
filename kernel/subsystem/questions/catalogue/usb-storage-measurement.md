# Questions: USB Storage (measurement set)

- guide: usb-storage.md
- title: USB Storage Subsystem

A wide set of questions about `drivers/usb/storage/`: the usb-storage core
(transport, protocol and SCSI glue layers, the control thread), the unusual
devices tables and their quirk flags, the sub-drivers built on the core, and
the uas driver that shares the directory. It is used to measure what a model
already knows before deciding what the built guide should spend its words on.
The hand-written guide it will replace is 414 words and covers only redundant
subclass and protocol overrides in `UNUSUAL_DEV()` entries. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## usbstor.files: Files and layers

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

Which files under `drivers/usb/storage/` and which headers under `include/`
hold: probing and the control thread, the transport layer, the protocol layer,
the SCSI host template and error handlers, the device tables, the quirk flag
definitions, the subclass and protocol codes, the device initialisers, the
debug helpers, and the uas driver and its detection logic? A table.

## usbstor.command-path: Path of a command

- section: Finding your way
- relevance: 4 - every other rule hangs off this path
- words: 100

Trace one SCSI command through usb-storage from the host template's queue
callback to the call that completes it back to the SCSI core: name each
function on the way, say which thread or context each runs in, and say how many
commands can be in flight at once. Start from `usb_stor_control_thread()`.

## usbstor.us-data: Per-device structure

- section: Core structures
- relevance: 4 - lifetime of everything else follows from it
- words: 90

Where does a `struct us_data` live in memory, which call allocates it and which
call finally frees it, and how does code get from it to the SCSI host and back?
What are the two flag words in it for, and what types are they?

## usbstor.locks: Locks and what they cover

- section: Core structures
- relevance: 5 - a transfer outside the right lock collides with the running command
- words: 100

Which lock in `struct us_data` serialises use of the device and of the single
URB and I/O buffer, who takes it, and for how long? Which lock protects the
current command pointer, and through which macros is it taken? For each state
bit in `dflags`, named in full, say whether every place that sets or clears it
holds that lock: look at all of them, since a bit set under the lock in one
function and without it in another is not protected by it. Start from
`usb_stor_control_thread()`, `command_abort_matching()` and
`quiesce_and_remove_host()`.

## usbstor.dflags: Dynamic state bits

- section: Core structures
- relevance: 3 - the names a reviewer meets in every error path
- words: 100

List the `US_FLIDX_` bits kept in the dynamic flag word, and for each say what
it means, who sets it and who clears it. A table. Start from
`drivers/usb/storage/usb.h`.

## usbstor.probe-sequence: Probe in two halves

- section: Probe and disconnect
- relevance: 4 - sub-drivers depend on what is set when
- words: 110

What does `usb_stor_probe1()` set up, what may a caller change between it and
`usb_stor_probe2()`, and what does the second half do, in order? What does
each do with its resources when it fails, and what must the caller not do
after a failure?

## usbstor.disconnect: Disconnect order

- section: Probe and disconnect
- relevance: 4 - the order is what prevents use after free
- words: 100

List the steps of `usb_stor_disconnect()` in the order they happen, placing
each of these: the sub-driver's destructor, refusing new commands, removing the
SCSI host, stopping the control thread, cancelling the scan, freeing the
buffers, dropping the last host reference. How is the control thread told to
exit, and what has to be true first? Start from `quiesce_and_remove_host()`
and `release_everything()`.

## usbstor.scan-delay: Delayed scanning

- section: Probe and disconnect
- relevance: 3 - the parameter's units and the power-management reference are easy to get wrong
- words: 90

How is the SCSI scan of a newly probed device scheduled, which module parameter
delays it and in what units and syntax is that parameter written, what else
does the scan routine do before scanning, and how are the runtime-PM reference
and the pending bit balanced if the device goes away first?

## usbstor.pm: Suspend, resume and reset hooks

- section: Probe and disconnect
- relevance: 3 - the reset callbacks take a lock the caller may already hold
- words: 90

What do the driver's suspend, resume, reset-resume, pre-reset and post-reset
callbacks each do, which of them take or release a lock, and what hook does a
sub-driver have into suspend and resume? What does that imply for code that
wants to reset the port? Start from `usb_stor_pre_reset()`.

# The transport layer

## usbstor.transport-returns: Transfer and transport result codes

- section: Transport layer
- relevance: 5 - the two families are both small integers and are easy to mix up
- words: 120

What are the two families of result codes used below the protocol layer, what
does each value mean, which functions return which family, and what does
`usb_stor_invoke_transport()` do for each value a transport can return? Which
helpers return a negative errno instead? Start from
`drivers/usb/storage/transport.h`.

## usbstor.urb-submission: Submitting URBs for a command

- section: Transport layer
- relevance: 5 - an URB the abort path cannot see hangs error handling
- words: 110

Which paths cancel the transfer that is in progress for a queued command, how
do they find it, and is disconnect one of them? What way of doing USB I/O from
a transport or sub-driver while a queued command is being handled is unsafe,
which helpers are the correct way, and which in-tree code that does its own
USB I/O is correct? Start from `usb_stor_msg_common()` and
`usb_stor_stop_transport()`.

## usbstor.iobuf: Small transfer buffer

- section: Transport layer
- relevance: 4 - DMA from the wrong memory is silent on most machines
- words: 80

What is `us->iobuf`, how big is it, how is it allocated, and how does the
submission code treat a transfer that uses it differently from one that does
not? What kind of buffer is unsafe to hand to the bulk and control helpers,
and what do the in-tree transports do with a command block that may be on the
stack?

## usbstor.bulk-transport: Bulk-only quirks handling

- section: Transport layer
- relevance: 4 - each tolerance is there for real devices and a cleanup can remove it
- words: 130

In the Bulk-only transport, what does the driver check in the status wrapper
(tag, signature, status, residue), and what deviations by devices does it
tolerate: a wrong signature, a bogus residue, a skipped data phase, a
zero-length or stalled status read, a device that sends too much? Start from
`usb_stor_Bulk_transport()`.

## usbstor.autosense: Automatic sense requests

- section: Transport layer
- relevance: 4 - decides what result the SCSI core sees
- words: 120

When does `usb_stor_invoke_transport()` issue a REQUEST SENSE on its own, how
does it choose how many sense bytes to ask for, what does it do when the sense
data comes back empty, and which results does it turn into an immediate retry
or a hard error instead?

## usbstor.error-recovery: Recovery after a transport error

- section: Errors and resets
- relevance: 4 - the lock is dropped in the middle of a command
- words: 100

After a transport error or an abort, what does `usb_stor_invoke_transport()`
do to resynchronise with the device, in what order are the kinds of reset
tried, which lock is released around which of them and why, and which state
bits are set and cleared on the way? When is a port reset refused outright?

## usbstor.eh-handlers: SCSI error handlers

- section: Errors and resets
- relevance: 4 - the abort handler waits on the control thread
- words: 110

What do the usb-storage host template's abort, device-reset and bus-reset
handlers each do, what does the abort handler wait for and who signals it, what
does it return when no command or a different command is pending, and how does
the control thread treat a command that timed out before it was picked up?
Start from `command_abort_matching()`.

# The protocol layer and SCSI glue

## usbstor.protocols: Subclass to protocol handler

- section: Protocol and SCSI glue
- relevance: 3 - the mapping has holes that probe turns into an error
- words: 100

Which protocol handler and which transport does the core choose for each
subclass and protocol code, what does each protocol handler change in the
command before passing it on, and what happens at probe when the code is one
the core has no case for? Start from `get_protocol()` and `get_transport()`.

## usbstor.host-template: Host template

- section: Protocol and SCSI glue
- relevance: 4 - callback names and limits have changed with the SCSI core
- words: 110

What does the usb-storage SCSI host template set for queue depth, maximum
sectors, scatter-gather table size and DMA alignment, what are its per-device
and per-target callbacks called in this tree and what arguments do they take,
and how does each module that uses the core get its own copy of the template?
Start from `usb_stor_host_template_init()`.

## usbstor.sdev-configure: Per-device SCSI settings

- section: Protocol and SCSI glue
- relevance: 4 - most quirk flags end here, and some settings are not flags at all
- words: 140

In usb-storage's device-configure callback, how is the maximum transfer size
chosen, which SCSI device settings are forced on for every disk regardless of
flags, which are set only by a quirk flag, and what is done for devices that
are not disks? Which of this could equally be done in the earlier init
callback, and which could not? Start from `sdev_configure()` in
`drivers/usb/storage/scsiglue.c`.

## usbstor.max-lun: Number of logical units

- section: Protocol and SCSI glue
- relevance: 3 - several places override it and the last one wins
- words: 100

How does usb-storage decide the highest LUN a device has: which transports
and subclasses start with which value, when is the device asked, what bounds
are put on its answer, which flags override it, and which later callback can
reset it? What is done for a device that reports eight or more?

## usbstor.capacity-hacks: Capacity and last-sector workarounds

- section: Protocol and SCSI glue
- relevance: 3 - three flags and a heuristic interact
- words: 100

What do `US_FL_FIX_CAPACITY`, `US_FL_CAPACITY_HEURISTICS` and
`US_FL_CAPACITY_OK` each make the SCSI disk driver or usb-storage do, which
vendors get one of them without a table entry, and when does usb-storage's own
last-sector logic run and what does it change in a failed command? Start from
`last_sector_hacks()`.

# The unusual devices tables

## usbstor.unusual-macro: Entry macro arguments

- section: Unusual devices table
- relevance: 5 - ten positional arguments and two misleading field names
- words: 110

List the arguments of `UNUSUAL_DEV()` in order and say what each is. Which
structure fields do the subclass and protocol arguments end up in, what are
those fields called, and what kind of code does each actually hold? Which
values mean "use what the device reports", and where are they defined?

## usbstor.table-expansion: Expanding the table

- section: Unusual devices table
- relevance: 4 - two arrays indexed by the same position
- words: 120

In which source files is `drivers/usb/storage/unusual_devs.h` included, under
which macro definitions, and what array does each inclusion produce? How does
the probe routine get from the matched id to the entry's names, overrides and
init function, and what does it use for an id that was added at run time? What
else is in that header besides `UNUSUAL_DEV()` lines?

## usbstor.entry-match: Entry matching rules

- section: Unusual devices table
- relevance: 4 - decides which interfaces and which revisions an entry captures
- words: 100

Which descriptor fields does an `UNUSUAL_DEV()` entry match on and which does
it not look at, what follows for a device with several interfaces, which entry
wins when two entries or an entry and a generic class entry both match, and
what does a wide or narrow revision range mean for other devices that reuse
the same ids?

## usbstor.override-notice: Redundant overrides

- section: Unusual devices table
- relevance: 5 - the subject of the hand-written guide
- words: 100

Does the driver check whether a subclass or protocol override in a table entry
is the same as what the device reports itself, and if so where, for which
entries, what does it log and at what level, and what suppresses it? What does
a correct entry for a device whose descriptors are right but which needs a
quirk flag look like, and when is an explicit override correct? Start from
`get_device_info()`.

## usbstor.entry-conventions: Conventions for new entries

- section: Unusual devices table
- relevance: 4 - what maintainers ask for on every such patch
- words: 110

What do the comments at the top of `drivers/usb/storage/unusual_devs.h` and
`drivers/usb/storage/unusual_uas.h` ask of someone adding an entry: ordering,
what goes above the entry, what information accompanies the patch and where it
is sent? When is `COMPLIANT_DEV()` used instead, and what does the header say
about entries whose only purpose is mode switching?

## usbstor.descriptor-crosscheck: Checking an entry against descriptors

- section: Unusual devices table
- relevance: 3 - how a reviewer tells a needed override from a redundant one
- words: 80

Given the text a submitter pastes from `/sys/kernel/debug/usb/devices` or from
lsusb, which fields show the interface's self-reported subclass and protocol,
which numeric values correspond to the common `USB_SC_` and `USB_PR_` codes,
and which arguments of the entry are they compared with?

# Quirk flags

## usbstor.flag-definitions: Defining a flag

- section: Quirk flags
- relevance: 4 - the flag space and its carrier have different widths
- words: 110

Where and by what mechanism are the `US_FL_` flags defined, where else does
that definition get expanded, how wide is the flag word in `struct us_data`
and in the uas driver compared with the field of `struct usb_device_id` that
carries the flags from the table, and how many values are still free? What
follows for someone adding a flag?

## usbstor.flags-by-driver: Flags each driver honours

- section: Quirk flags
- relevance: 5 - an entry can set a flag the driver that binds never reads
- words: 140

Which `US_FL_` flags are acted on only by usb-storage, which only by uas, and
which by both, and for the ones usb-storage ignores, what does usb-storage do
unconditionally instead? A table. Start from `sdev_configure()` in
`drivers/usb/storage/scsiglue.c` and `uas_sdev_configure()`.

## usbstor.quirks-param: Quirks module parameter

- section: Quirk flags
- relevance: 4 - a new letter needs three places changed
- words: 110

What is the syntax of the usb-storage `quirks` module parameter, does an entry
in it add to or replace the flags from the built-in table and for which flags,
which drivers consult it, and which places have to be updated together when a
new flag letter is added? What goes wrong if one is missed? Start from
`usb_stor_adjust_quirks()`.

## usbstor.runtime-flag-changes: Flags changed at run time

- section: Quirk flags
- relevance: 3 - the table value is not the last word
- words: 100

Which quirk flags does the driver itself set or clear after probe, on what
evidence, and where? Include flags dropped because of the connection speed,
learnt from a device's responses, and turned on by vendor id.

# UAS

## usbstor.uas-selection: Choosing between uas and usb-storage

- section: UAS
- relevance: 5 - both drivers match the same devices
- words: 130

When a device offers both Bulk-only and UAS, how is it decided which driver
binds: which function makes the decision, who calls it, what conditions on the
device, the quirk flags and the host controller make it choose usb-storage,
and which device-specific checks are coded there instead of in a table? Where
is `drivers/usb/storage/unusual_uas.h` included, and if in more than one
place, why? Start from `uas_use_uas_driver()`.

## usbstor.uas-command-state: UAS command bookkeeping

- section: UAS
- relevance: 4 - completion depends on several URBs finishing in any order
- words: 120

How does the uas driver track a command: where is its private state kept, what
are the state bits, how are tags assigned and looked up, which lock covers all
of this, and what has to be true before the command is completed to the SCSI
core? What happens when URB allocation or submission fails in the queue
callback? Start from `uas_submit_urbs()` and `uas_try_complete()`.

## usbstor.uas-error-handling: UAS error handling and reset

- section: UAS
- relevance: 4 - the abort handler does not abort
- words: 110

What do the uas abort and reset handlers do and return, what does the driver do
with outstanding commands and URBs around a device reset, what do its pre-reset
and post-reset callbacks do and return on failure, and what does disconnect do
before removing the host? Start from `uas_eh_abort_handler()`.

## usbstor.uas-queue-depth: UAS queue depth and streams

- section: UAS
- relevance: 3 - the numbers come from the bus, not from a constant
- words: 80

How does uas choose its queue depth with and without streams, how does that
become the host's and each device's queue depth, and what host limits
(command length, LUNs, scatter-gather) does it set? Start from
`uas_configure_endpoints()`.

# Sub-drivers

## usbstor.subdriver-structure: Anatomy of a sub-driver

- section: Sub-drivers
- relevance: 4 - the pieces are spread over four files
- words: 130

How is a `ums-*` sub-driver put together: where are its device entries kept,
which arrays does it build from them, how does it find the entry for a matched
id and what does that require of the `struct usb_driver`, what does it set
between the two probe halves, how does the main driver know to leave its
devices alone, and which macro and namespace import does it need? Use
`drivers/usb/storage/karma.c` as the example.

## usbstor.extra-data: Sub-driver private data

- section: Sub-drivers
- relevance: 4 - the destructor is where timers and work outlive the device
- words: 100

How does a sub-driver attach private data to `struct us_data`, who frees it,
when does its destructor run relative to the control thread stopping and the
host being removed, and can it run when initialisation failed part of the way?
What usage of timers or work items in that data is unsafe, and what does a
correct destructor do? Start from `usb_stor_release_resources()`.

## usbstor.init-function: Device init functions

- section: Sub-drivers
- relevance: 3 - runs before the control thread and the host exist
- words: 90

When in probe does an entry's init function run, what exists and what does not
exist yet at that point, which transfer helpers can it use and what locking
does it need, and what happens to the probe when it returns non-zero? If
a sub-driver talks to the device after the second probe half has returned,
what must it hold? Start from `usb_stor_acquire_resources()`.

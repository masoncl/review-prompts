# Questions: USB Storage Subsystem

- guide: usb-storage.md
- title: USB Storage Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/usb-storage-measurement.md` is
the wider set the readers were measured on and `catalogue/usb-storage-measurement-results.md` says
what they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## usbstor.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Unusual device entries

## usbstor.unusual-macro: Entry macro arguments

- section: Unusual device entries
- relevance: 5 - ten positional arguments and two misleading field names

In an `UNUSUAL_DEV()` entry, in what order do the arguments come, and which positions hold the
subclass and the protocol override? What are the structure fields those two end up in called,
and what kind of code does each actually hold? Which values mean "use what the device
reports", and where are the codes defined?

## usbstor.table-expansion: Expanding the table

- section: Unusual device entries
- relevance: 4 - two arrays indexed by the same position

How does `storage_probe()` get from the matched `struct usb_device_id` to the entry's names,
overrides and init function? What does that require of the arrays that are built from
`drivers/usb/storage/unusual_devs.h`? What does probe use for an id that was added at run time?

## usbstor.entry-match: Entry matching rules

- section: Unusual device entries
- relevance: 4 - decides which interfaces and which revisions an entry captures

Which descriptor fields does an `UNUSUAL_DEV()` entry match on and which does it not look at, and
to which interfaces of a matching device does the entry apply? Which entry wins when two entries,
or an entry and a generic class entry, both match? Which devices does the revision range of an
entry include?

## usbstor.override-notice: Redundant override notice

- section: Unusual device entries
- relevance: 5 - the subject of the hand-written guide

Does the driver check whether a subclass or protocol override in a table entry is the same as
what the device reports itself, and if so where, for which entries, what does it log and at what
level, and what suppresses it? What does a correct entry for a device whose descriptors are
right but which needs a quirk flag look like, and when is an explicit override correct? Start
from `get_device_info()`.

## usbstor.entry-conventions: Conventions for new entries

- section: Unusual device entries
- relevance: 4 - what maintainers ask for on every such patch

What do the comments at the top of `drivers/usb/storage/unusual_devs.h` and
`drivers/usb/storage/unusual_uas.h` each ask of someone adding an entry: where it goes and what
is written above it, and what information accompanies the patch and to whom it is sent? When is
`COMPLIANT_DEV()` used instead, and what does the header say about entries whose only purpose
is mode switching?

# Quirk flags, uas and usb-storage

## usbstor.quirk-flags: Flag word and quirks parameter

- section: Quirk flags, uas and usb-storage
- relevance: 4 - the flag space and its carrier have different widths, and a new letter needs several places changed

How wide is the flag word in `struct us_data` and in the uas driver, compared with the field of
`struct usb_device_id` that carries the flags from the table? Does an entry in the `quirks` module
parameter add to or replace the flags from the built-in table, and for which flags? Start from
`usb_stor_adjust_quirks()`.

## usbstor.new-flag: Flag and letter definitions

- section: Quirk flags, uas and usb-storage
- relevance: 4 - a new flag and its letter need several places changed, and the diff shows only the ones the patch touched

What does adding a `US_FL_` flag and a letter for it in the `quirks` module parameter require:
where is the flag defined, and which other places must change with it? Start from
`usb_stor_adjust_quirks()`.

## usbstor.flags-by-driver: Flags each driver honours

- section: Quirk flags, uas and usb-storage
- relevance: 5 - an entry can set a flag the driver that binds never reads

A table of the `US_FL_` flags the uas driver acts on, in two groups: those usb-storage acts on as
well, and those only uas reads. For the second group, say whether usb-storage does the same
thing for every device without testing a flag, and where. Write every flag name in full. Then
one sentence on which driver reads the remaining flags, and whether any is read by neither.
Start from `uas_sdev_configure()` and from `sdev_configure()` in
`drivers/usb/storage/scsiglue.c`.

## usbstor.uas-selection: Choosing between uas and usb-storage

- section: Quirk flags, uas and usb-storage
- relevance: 5 - both drivers match the same devices

When a device offers both Bulk-only and UAS, how does the result of `uas_use_uas_driver()` decide
which of usb-storage and uas binds? Which conditions make the function choose usb-storage, and
which of them are coded in the function and not in a table? Where is
`drivers/usb/storage/unusual_uas.h` included, and how does that reach both drivers? Start from
`uas_use_uas_driver()`.

## usbstor.sdev-configure: Per-device SCSI settings

- section: Quirk flags, uas and usb-storage
- relevance: 4 - most quirk flags end here, and some settings are not flags at all

In `sdev_configure()`, which SCSI device settings are forced on for every device regardless of
flags and which are set only by a quirk flag, and how is the maximum transfer size chosen? Which
of these settings does the code say cannot be made in `sdev_init()`, and what reason does it give?
Start from `sdev_configure()` in `drivers/usb/storage/scsiglue.c`.

## usbstor.host-template: Host template

- section: Quirk flags, uas and usb-storage
- relevance: 4 - callback names and limits have changed with the SCSI core

Which per-device and per-target callbacks does `usb_stor_host_template` set, and what arguments
does each take? Which limits does the template fix for every device? How does each module that
uses the core get its own copy of the template? Start from `usb_stor_host_template_init()`.

# The command path and its locks

## usbstor.command-path: Queuecommand and the control thread

- section: The command path and its locks
- relevance: 4 - every other rule hangs off this path

Between the host template's queue callback and the call that completes a command back to the
SCSI core, which thread or context runs each stage, and how many commands can be in flight at
once? Which call completes the command, and which locks have been released by then? Start from
`usb_stor_control_thread()`.

## usbstor.us-data: us_data lifetime and flag words

- section: The command path and its locks
- relevance: 4 - lifetime of everything else follows from it

Where does a `struct us_data` live in memory, which call allocates it and which call finally frees
it? What are the requirements for code that holds a pointer to it after `usb_stor_disconnect()`
has run, in order to assure safe usage? What are the two flag words in it for, and how wide is
each?

## usbstor.locks: Locks and what they cover

- section: The command path and its locks
- relevance: 5 - a transfer outside the right lock collides with the running command

Which lock in `struct us_data` serialises use of the device and of the single URB and I/O
buffer, who takes it, and for how long? Which lock protects the current command pointer, and
through which macros is it taken? For each state bit in `dflags`, named in full, say whether
every place that sets or clears it holds that lock: look at all of them, since a bit set under
the lock in one function and without it in another is not protected by it. Start from
`usb_stor_control_thread()`, `command_abort_matching()` and `quiesce_and_remove_host()`.

## usbstor.urb-submission: Submitting URBs for a command

- section: The command path and its locks
- relevance: 5 - an URB the abort path cannot see hangs error handling

Which paths cancel the transfer that is in progress for a queued command, how do they find it, and
is disconnect one of them? What are the requirements for USB I/O that a transport or sub-driver
does while a queued command is being handled, in order to assure safe usage? Name in-tree code
that does its own USB I/O and meets them. Start from `usb_stor_msg_common()` and
`usb_stor_stop_transport()`.

## usbstor.iobuf: iobuf and DMA-safe buffers

- section: The command path and its locks
- relevance: 4 - DMA from the wrong memory is silent on most machines

What are the requirements for a buffer passed to `usb_stor_bulk_transfer_buf()`,
`usb_stor_control_msg()` or `usb_stor_ctrl_transfer()` in order to assure safe usage, and how do
the in-tree transports meet them for a command block that may be on the stack? What is `us->iobuf`
for, how big is it, and how does `usb_stor_msg_common()` treat a transfer that uses it differently
from one that does not?

## usbstor.transport-returns: Transfer and transport result codes

- section: The command path and its locks
- relevance: 5 - the two families are both small integers and are easy to mix up

What are the two families of result codes used below the protocol layer, and which functions
return which family? What does `usb_stor_invoke_transport()` do for each value a transport can
return, and which helpers return a negative errno instead? A table for each family. Start from
`drivers/usb/storage/transport.h`.

# Sense, Bulk-only and recovery

## usbstor.autosense: Automatic sense requests

- section: Sense, Bulk-only and recovery
- relevance: 4 - decides what result the SCSI core sees

When does `usb_stor_invoke_transport()` issue a REQUEST SENSE on its own and how does it choose
how many sense bytes to ask for, what does it do when the sense data comes back empty, and which
results does it turn into an immediate retry or a hard error instead?

## usbstor.bulk-transport: Bulk-only CSW tolerances

- section: Sense, Bulk-only and recovery
- relevance: 4 - each tolerance is there for real devices and a cleanup can remove it

In `usb_stor_Bulk_transport()`, which fields of the command status wrapper does the driver check,
and what does it do when a check fails? Which deviations from the Bulk-only specification does the
code accept on purpose, and what reason does the code give for each? Start from
`usb_stor_Bulk_transport()`.

## usbstor.error-recovery: Recovery after a transport error

- section: Sense, Bulk-only and recovery
- relevance: 4 - the lock is dropped in the middle of a command

After a transport error or an abort, which resets does `usb_stor_invoke_transport()` try in order
to resynchronise with the device, and in what order? Which lock does it release around which of
them, and why? When does `usb_stor_port_reset()` refuse to reset the port?

## usbstor.eh-handlers: SCSI error handlers

- section: Sense, Bulk-only and recovery
- relevance: 4 - the abort handler waits on the control thread

What do the usb-storage host template's abort, device-reset and bus-reset handlers each do, and
which of them aborts the running command first? What does the abort handler wait for, who
signals it, and what does it return when no command or a different command is pending? How does
the control thread treat a command that timed out before it was picked up? Start from
`command_abort_matching()`.

# Probe, disconnect and sub-drivers

## usbstor.probe-sequence: Probe in two halves

- section: Probe, disconnect and sub-drivers
- relevance: 4 - sub-drivers depend on what is set when

What may a caller change between `usb_stor_probe1()` and `usb_stor_probe2()`, and in what order
does the second half start the control thread, take its runtime power management reference and
add the SCSI host? What does each half do with its resources when it fails, and what must the
caller not do after a failure?

## usbstor.disconnect: Disconnect order

- section: Probe, disconnect and sub-drivers
- relevance: 4 - the order is what prevents use after free

What does `usb_stor_disconnect()` do, in order, from its first call to dropping the last reference
on the SCSI host, and where in that order does the sub-driver's destructor run? How is the control
thread told to exit, and what has to be true first? Start from `quiesce_and_remove_host()` and
`release_everything()`.

## usbstor.extra-data: Sub-driver private data

- section: Probe, disconnect and sub-drivers
- relevance: 4 - the destructor is where timers and work outlive the device

Who frees the private data a sub-driver attaches to `us->extra`, and when does
`us->extra_destructor` run relative to the control thread stopping and the host being removed? Can
the destructor run when initialisation failed part of the way, and with what in the pointer? What
are the requirements for a timer or a work item kept in that data, in order to assure safe usage?
Start from `usb_stor_release_resources()`.

## usbstor.subdriver-structure: Sub-driver tables and registration

- section: Probe, disconnect and sub-drivers
- relevance: 4 - the pieces are spread over four files

In a `ums-*` sub-driver, what must be true of the arrays it builds from its device entries and of
its `struct usb_driver` for a matched id to find the right entry? How does the main driver know to
leave the sub-driver's devices alone? What does the sub-driver's source need in order to build and
load as a module? Use `drivers/usb/storage/karma.c` as the example.

# UAS

## usbstor.uas-command-state: UAS command bookkeeping

- section: UAS
- relevance: 4 - completion depends on several URBs finishing in any order

In the uas driver, which lock covers a command's private state and the table of tags, and what
has to be true before a command is completed to the SCSI core, given that its URBs finish in any
order? What happens when URB allocation or submission fails in the queue callback? Start from
`uas_submit_urbs()` and `uas_try_complete()`.

## usbstor.uas-error-handling: UAS error handling and reset

- section: UAS
- relevance: 4 - the abort handler does not abort

Which error handlers does the uas host template install, and what does each do and return? What
does the driver do with outstanding commands and URBs around a device reset, including what its
pre-reset and post-reset callbacks return on failure, and what does disconnect do before
removing the host? Start from `uas_eh_abort_handler()`.

# Model gaps

## usbstor.model-gaps: Other mistakes models make

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

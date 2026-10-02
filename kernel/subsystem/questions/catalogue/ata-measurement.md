# Questions: ATA (measurement set)

- guide: ata.md
- title: ATA Subsystem

A wide set of questions about libata (`drivers/ata/`), used to measure what a
model already knows before deciding what the built guide should spend its
words on. The hand-written guide it will replace is 432 words and is about one
thing only, how strictly device-reported data may be checked while a device is
being configured; the questions cover that and the rest of the library: the
objects, configuring a device, quirks, the command path, error handling and
what a controller driver supplies. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## ata.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files under `drivers/ata/` hold the libata core, error handling, the SCSI
translation, the SATA-only helpers, SFF and BMDMA support, port multipliers,
the transport classes and sysfs, ACPI, tracing and the shared AHCI code, and
which headers hold the libata API and the ATA command and IDENTIFY
definitions? A table. Start from `drivers/ata/Makefile`.

## ata.objects: Host, port, link and device

- section: Finding your way
- relevance: 4 - every function takes one of these
- words: 100

What are the objects libata is built from, from the host down to a queued
command, how does each point to the others, and where are instances of each
allocated? Start from `struct ata_host`, `struct ata_port`, `struct ata_link`,
`struct ata_device` and `struct ata_queued_cmd` in `include/linux/libata.h`.

## ata.docs: Documentation

- section: Finding your way
- relevance: 2 - parts of it describe interfaces that are gone
- words: 70

Which files under `Documentation/` describe libata, its sysfs attributes and
its kernel parameters, and which parts of `Documentation/driver-api/libata.rst`
no longer match `struct ata_port_operations`?

# Configuring a device

## ata.config-path: Configuration path

- section: Probing and configuring
- relevance: 5 - where every capability check lives
- words: 110

In what order is a newly found device identified and configured, from the reset
that classifies it to the point where a SCSI device is attached, and in which
context does all of that run? Name the function for each step. Start from
`ata_eh_revalidate_and_attach()` and `ata_dev_configure()`.

## ata.config-reruns: Reconfiguration

- section: Probing and configuring
- relevance: 4 - a check added for probe also runs on every resume
- words: 90

When is `ata_dev_configure()` run again for a device that is already attached,
what state is reset at its start, and what is compared afterwards to decide
whether it is still the same device? Start from `ata_dev_revalidate()`.

## ata.config-failure: Configuration failure

- section: Probing and configuring
- relevance: 5 - what a new error return costs
- words: 110

What happens to a device when `ata_dev_read_id()`, `ata_dev_configure()` or
`ata_dev_revalidate()` returns an error: how many attempts does it get, what
does each errno value mean to the caller, and what is the final outcome? Start
from `ata_eh_handle_dev_fail()`.

## ata.optional-features: Optional feature setup

- section: Probing and configuring
- relevance: 4 - the pattern new feature code is expected to follow
- words: 100

How do the helpers that `ata_dev_configure()` calls for optional features (NCQ,
FUA, device sleep, sense reporting, zoned, trusted, positioning ranges,
duration limits, depopulation) behave when the device lacks a log, a read
fails or a field has an unexpected value? Which of them can fail the
configuration as a whole?

## ata.log-directory: Log directory

- section: Logs and device-reported data
- relevance: 5 - gates every feature that is read from a log
- words: 100

How is the general purpose log directory read and cached, what does the code do
when the version word is not what the standard says, when is the cache thrown
away, and what does a caller get when it asks whether a log is supported?
Start from `ata_log_supported()`.

## ata.log-page-reads: Log page reads

- section: Logs and device-reported data
- relevance: 4 - the return value is not an errno
- words: 100

What does `ata_read_log_page()` return, when does it use DMA and what does it
do when the DMA form fails, which port flag and which quirks stop it issuing a
command at all, and which buffer do callers normally pass?

## ata.validation-usage: Checking device-reported data

- section: Logs and device-reported data
- relevance: 5 - a check that is too strict takes away a working disk
- words: 120

When code in the identify and configure paths finds that device-reported data
does not match the standard (a version word, reserved bits, an optional
field), which responses does the tree use (warn and go on, turn one feature
off, fail the device) and for which kinds of mismatch? What usage is unsafe,
and what that looks similar is correct? Name in-tree code that shows each.

## ata.message-helpers: Message helpers

- section: Logs and device-reported data
- relevance: 2 - the once-only form is not per device
- words: 60

Which macros print a message for a port, a link or a device, what prefix do
they give, and what exactly does the once-only device warning limit: once per
device, or once per call site? Start from `ata_dev_printk` in
`include/linux/libata.h`.

# Quirks

## ata.quirk-names: Quirk flags

- section: Quirks
- relevance: 4 - the names have changed
- words: 70

What does this tree call the per-device flags for broken features, what type
holds them in `struct ata_device`, how is each flag defined, and what is the
limit on their number? Start from `include/linux/libata.h`.

## ata.quirk-table: Quirk table matching

- section: Quirks
- relevance: 4 - an entry placed after a wider pattern never applies
- words: 100

How is a device matched against the static table of per-model quirks: what is
compared, with what kind of pattern, and what happens when a device matches
more than one entry? How does a quirk that carries a value get it? Start from
`ata_dev_quirks()`.

## ata.quirk-runtime: Quirks set at run time

- section: Quirks
- relevance: 5 - a bit set in response to a device's reply can outlive its cause
- words: 120

Which code sets or clears a device's quirk bits outside the static table, and
for how long does a bit set that way last across revalidation, reset and
detach? What usage of setting a quirk bit in response to something the device
reported is unsafe, and what that looks similar is correct?

## ata.quirk-add: Adding a quirk

- section: Quirks
- relevance: 3 - five places, and two of them are user-visible
- words: 80

What are all the places that have to change when a new per-device quirk flag
is added, including what users see in the log and can type on the command
line? Start from `enum ata_quirks`.

## ata.force-param: Force parameter

- section: Quirks
- relevance: 3 - how users work around a bad check without a rebuild
- words: 90

What can the `libata.force` parameter override, how is an entry matched to a
port, link or device, at which points is it applied, and where is it
documented? Start from `force_tbl` in `drivers/ata/libata-core.c`.

# Commands

## ata.command-path: Command path

- section: Issuing and completing commands
- relevance: 4 - turns a search into a lookup
- words: 100

List in order the functions a SCSI command passes through from the host
template's queuecommand to the controller driver's issue callback, and say
which lock is held. Start from `ata_scsi_queuecmd()`.

## ata.qc-defer: Deferring a command

- section: Issuing and completing commands
- relevance: 4 - who holds a command that cannot go now
- words: 110

What may a driver's `qc_defer` callback return, what does the core do for each
value, and what happens to a command that cannot be issued now: is it handed
back to the SCSI layer or held by libata? Start from `ata_scsi_qc_issue()`.

## ata.completion: Command completion

- section: Issuing and completing commands
- relevance: 4 - the rule that keeps the normal path and error handling apart
- words: 110

What does `ata_qc_complete()` do with a command whose `err_mask` is set, which
flag marks a command as owned by error handling and what does that do to
`ata_qc_from_tag()`, and when is the result taskfile read back?

## ata.internal-commands: Internal commands

- section: Issuing and completing commands
- relevance: 4 - the signature and the return type are easy to get wrong
- words: 100

What are the arguments of `ata_exec_internal()`, what does it return, what
context must the caller be in, what does it do if the port is frozen, and what
happens when the command times out?

## ata.return-conventions: Error masks and errnos

- section: Issuing and completing commands
- relevance: 4 - testing one kind as if it were the other compiles
- words: 100

Which of the functions used while configuring a device and handling errors
return a mask of bits from `enum ata_completion_errors` and which return a
negative errno, and what usage that mixes the two is unsafe? Give the common
ones in a table.

# Error handling

## ata.eh-entry: Entering error handling

- section: Error handling
- relevance: 4 - probing, hotplug and power management all run here too
- words: 110

How does libata error handling get to run: who schedules it, which thread runs
it, what is copied and cleared on entry, and what serialises it between the
ports of one host? Is a driver's `error_handler` optional? Start from
`ata_scsi_port_error_handler()`.

## ata.eh-reporting: Reporting from interrupt handlers

- section: Error handling
- relevance: 4 - what every controller driver has to get right
- words: 110

How does a controller driver's interrupt handler hand an error to error
handling: where does it record the error mask, the requested action and a
description, and how does it choose between freezing the port, aborting the
port and aborting one link? Start from `ahci_error_intr()`.

## ata.reset-ops: Reset callbacks

- section: Error handling
- relevance: 4 - the layout in the operations structure has changed
- words: 120

Where in `struct ata_port_operations` do the prereset, softreset, hardreset and
postreset callbacks live, which is preferred when several are set, in what
order does a reset call them and freeze and thaw the port, and what do
`-ENOENT` and `-EAGAIN` from them mean? Start from `ata_eh_reset()`.

## ata.locking: Locks

- section: Error handling
- relevance: 4 - two flag words in the port have different rules
- words: 100

Which locks does libata have, what does each protect (which flag words in
`struct ata_port` in particular), and which may be held when a driver callback
is called? Start from the `lock` pointer in `struct ata_port` and `eh_mutex` in
`struct ata_host`.

# Controller drivers

## ata.port-ops-inheritance: Operations inheritance

- section: What a driver supplies
- relevance: 3 - explains why operations structures are writable
- words: 90

How does one `struct ata_port_operations` inherit from another, when is the
inheritance resolved, how is a method removed in a child, and what does that
mean for declaring an operations structure `const`? Start from
`ata_finalize_port_ops()`.

## ata.sht-macros: Host template macros

- section: What a driver supplies
- relevance: 3 - the callback names follow the SCSI layer's renames
- words: 90

Which macros fill in a driver's `struct scsi_host_template`, what do they set,
and what are the per-device init, configure and destroy callbacks called in
this tree? Start from `__ATA_BASE_SHT` in `include/linux/libata.h`.

## ata.lpm: Link power management

- section: What a driver supplies
- relevance: 3 - one device's quirk changes the whole port's policy
- words: 110

What are the link power management policies, where does a port's initial
policy come from, which port flags, link flags, host flags and quirks turn it
off, and what happens to the port's target policy when an attached device has
the quirk? Start from `enum ata_lpm_policy` and `ata_dev_config_lpm()`.

# Changing the implementation

## ata.config-symbols: Configuration options

- section: What a change must preserve
- relevance: 3 - a core change has to build with each part left out
- words: 90

Which Kconfig symbols compile parts of libata in or out (SFF, BMDMA, SATA
hosts, port multipliers, ACPI, the force parameter, zero-power optical
drives), which source files does each control, and how does
`include/linux/libata.h` cope when one is off? Start from `drivers/ata/Kconfig`
and `drivers/ata/Makefile`.

## ata.change-checklist: Changing the core

- section: What a change must preserve
- relevance: 4 - the library has users outside its own directory
- words: 100

What must a change to the libata core or its headers keep working besides the
AHCI driver on a PC: the other users of the library inside and outside
`drivers/ata/`, the builds with parts configured out, the tracepoints, and the
user-visible attributes and parameters?

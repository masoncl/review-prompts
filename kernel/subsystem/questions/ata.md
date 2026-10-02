# Questions: ATA Subsystem

- guide: ata.md
- title: ATA Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/ata-measurement.md` is the wider
set the readers were measured on and `catalogue/ata-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## ata.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## ata.config-path: Configuration path

- relevance: 5 - where every capability check lives

A table and nothing else: the steps by which a newly found device is identified and configured,
from the reset that classifies it to the point where a SCSI device is attached, each with the
function to start reading from and the context it runs in. Say which steps do not run in the
error handling thread. Start from `ata_eh_revalidate_and_attach()` and `ata_dev_configure()`.

# Configuring a device

## ata.config-reruns: Revalidation and configure reruns

- section: Configuring a device
- relevance: 4 - a check added for probe also runs on every resume

When is `ata_dev_configure()` run again for a device that is already attached, what per-device
state does it reset on each run, and what is compared, before or after it runs, to decide
whether it is still the same device? Start from `ata_dev_revalidate()`.

## ata.config-failure: Configuration failure

- section: Configuring a device
- relevance: 5 - what a new error return costs

What happens to a device when `ata_dev_read_id()`, `ata_dev_configure()` or
`ata_dev_revalidate()` returns an error: how many attempts does it get, what does each errno
value mean to the caller, and what is the final outcome? Start from
`ata_eh_handle_dev_fail()`.

## ata.optional-features: Optional feature setup

- section: Configuring a device
- relevance: 4 - the pattern new feature code is expected to follow

What do the helpers that `ata_dev_configure()` calls to set up an optional feature, such as
`ata_dev_config_ncq()` or `ata_dev_config_cdl()`, do when the data that the device reports for the
feature is missing or is not valid? Can the return value of any of them make `ata_dev_configure()`
fail, and on what condition?

## ata.validation-usage: Checking device-reported data

- section: Configuring a device
- relevance: 5 - a check that is too strict takes away a working disk

What are the requirements for code reached from `ata_dev_read_id()` or `ata_dev_configure()` that
checks device-reported data against the standard, in order to assure safe usage: what may it do on
a mismatch, and when may it fail the device? Name in-tree code that shows it.

## ata.log-directory: Log directory

- section: Configuring a device
- relevance: 5 - gates every feature that is read from a log

Where does `ata_log_supported()` get the general purpose log directory from, and when is the
directory read from the device again? What does `ata_read_log_directory()` do when the version
word is not what the standard says? Start from `ata_log_supported()`.

## ata.log-supported-result: Log support check result

- section: Configuring a device
- relevance: 5 - a caller that treats the result as an errno or as a plain yes or no handles a failed read wrongly

What does `ata_log_supported()` return for a log that the device supports, and what does it return
when the log directory cannot be read?

## ata.log-page-reads: Log page reads

- section: Configuring a device
- relevance: 4 - the return value is not an errno

What does `ata_read_log_page()` return, and if it can read a log with DMA, what does it do when
that read fails? Which port flags and quirks stop it reading a log, and is each tested inside the
function or by its callers? Give flag and quirk names in full.

# Quirks

## ata.quirk-flags: Quirk flags

- section: Quirks
- relevance: 4 - the names and the type have changed, and adding one touches user-visible places

What type holds the flags of `enum ata_quirks` in `struct ata_device`, and what enforces the limit
on their number? When a new flag is added, what besides the enumerator has to change for it to be
printed in the log and settable from the command line? Start from `enum ata_quirks` in
`include/linux/libata.h`.

## ata.quirk-table: Quirk table matching

- section: Quirks
- relevance: 4 - an entry placed after a wider pattern never applies

How is a device matched against the static table of per-model quirks: what is compared, with
what kind of pattern, and what happens when a device matches more than one entry? If a quirk
can carry a value, where does the value come from? Start from `ata_dev_quirks()`.

## ata.quirk-runtime: Quirks set at run time

- section: Quirks
- relevance: 5 - a bit set in response to a device's reply can outlive its cause

For how long does a bit last that code other than `ata_dev_quirks()` sets in the `quirks` member
of `struct ata_device`, and what clears it? What are the requirements for code that sets a quirk
bit in response to something the device reported, in order to assure safe usage? Name in-tree code
that shows it.

# Issuing and completing commands

## ata.command-path: Command path

- section: Issuing and completing commands
- relevance: 4 - turns a search into a lookup

On the way from `ata_scsi_queuecmd()` to the controller driver's `qc_issue` callback, which lock
is held and who takes it, where does the `struct ata_queued_cmd` for the command come from, and at
which step can a command be refused or deferred? Start from `ata_scsi_queuecmd()`.

## ata.qc-defer: Deferring a command

- section: Issuing and completing commands
- relevance: 4 - who holds a command that cannot go now

What may a driver's `qc_defer` callback return, what does the core do for each value, and what
happens to a command that cannot be issued now: is it handed back to the SCSI layer or held by
libata, and if held, where and who sends it later? Start from `ata_scsi_qc_issue()`.

## ata.completion: Command completion

- section: Issuing and completing commands
- relevance: 4 - the rule that keeps the normal path and error handling apart

What does `ata_qc_complete()` do with a command whose `err_mask` is set, which flag marks a
command as owned by error handling and what does that do to `ata_qc_from_tag()`, and when is
the result taskfile read back?

## ata.internal-commands: Internal commands

- section: Issuing and completing commands
- relevance: 4 - the signature and the return type are easy to get wrong

What does `ata_exec_internal()` return, and what does it require of its caller: the context and
the locks held?

## ata.internal-command-failure: Frozen ports and timeouts

- section: Issuing and completing commands
- relevance: 4 - a caller has to know what state the port is in after an internal command fails

What does `ata_exec_internal()` do when the port is frozen, and what does it do to the port and to
the command when the command times out?

## ata.internal-command-buffer: Data buffers

- section: Issuing and completing commands
- relevance: 4 - new feature code hands a buffer to these functions for every log it reads

What are the requirements for the buffer passed into `ata_exec_internal()` or
`ata_read_log_page()` in order to assure safe usage? Name in-tree code that shows it.

## ata.return-conventions: Error masks and errnos

- section: Issuing and completing commands
- relevance: 4 - testing one kind as if it were the other compiles

Which of `ata_exec_internal()`, `ata_read_log_page()`, `ata_dev_set_feature()`,
`ata_dev_read_id()`, `ata_dev_reread_id()`, `ata_dev_configure()` and `ata_dev_revalidate()`
return a mask of bits from `enum ata_completion_errors` and which return a negative errno? Give
the answer as a table. What are the requirements for a caller that tests or passes on either kind
of value, in order to assure safe usage?

# Error handling and locks

## ata.eh-entry: Entering error handling

- section: Error handling and locks
- relevance: 4 - probing, hotplug and power management all run here too

Do `ata_port_freeze()` and `ata_port_abort()` schedule libata error handling by themselves? What
does error handling copy and clear on entry, and what serialises error handling between the ports
of one host? Start from `ata_scsi_port_error_handler()`.

## ata.eh-ownership-release: Ownership release during sleeps

- section: Error handling and locks
- relevance: 4 - state that error handling read before a sleep may have changed after it

What do `ata_eh_release()` and `ata_eh_acquire()` give up and take back, and what are the
requirements for a function that sleeps between the two, in order to assure safe usage?

## ata.driver-error-handler: Driver error handler

- section: Error handling and locks
- relevance: 4 - decides whether a test for a missing callback is needed or is dead code

Must a controller driver set `error_handler` in `struct ata_port_operations`, and what does
`ata_scsi_port_error_handler()` do for a port whose driver did not set it?

## ata.eh-reporting: Reporting from interrupt handlers

- section: Error handling and locks
- relevance: 4 - what every controller driver has to get right

How does a controller driver's interrupt handler hand an error to error handling: where does it
record the error mask, the requested action and a description, and how does it choose between
freezing the port, aborting the port and aborting one link? Start from `ahci_error_intr()`.

## ata.reset-ops: Reset callbacks

- section: Error handling and locks
- relevance: 4 - the layout in the operations structure has changed

Where in `struct ata_port_operations` are the prereset, softreset, hardreset and postreset
callbacks declared? In what order does `ata_eh_reset()` call them and freeze and thaw the port,
and what do `-ENOENT` and `-EAGAIN` from them mean? Start from `ata_eh_reset()`.

## ata.reset-method-choice: Choice of reset method

- section: Error handling and locks
- relevance: 4 - a driver that sets both callbacks has to know which one runs

When a driver sets both the softreset and the hardreset callback, which does `ata_eh_reset()` use
first, and on what condition does it use the other?

## ata.locking: Locks and flag words

- section: Error handling and locks
- relevance: 4 - two flag words in the port have different rules

Which lock protects `flags` and which protects `pflags` in `struct ata_port`, and does either rule
depend on the state of the port? Which libata locks may be held when a driver callback is called?
Start from the `lock` pointer in `struct ata_port` and `eh_mutex` in `struct ata_host`.

# Other users and builds

## ata.change-checklist: Outside callers and Kconfig guards

- section: Other users and builds
- relevance: 4 - the library has users outside its own directory

What are the requirements for a change to the libata core in order that it builds when a Kconfig
option compiles part of the core out, and that callers outside `drivers/ata/` still work? What
else has to change when a patch changes a libata structure or flag name that a tracepoint or a
user-visible attribute shows?

# Model gaps

## ata.model-gaps: Other mistakes models make

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

# Questions: PCI Subsystem

- guide: pci.md
- title: PCI Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/pci-measurement.md` is the wider
set the readers were measured on and `catalogue/pci-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## pci.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## pci.newer-facilities: Newer facilities

- section: Finding your way
- relevance: 4 - a reader cannot review what it does not recognise

A table and nothing else, job to file under `drivers/pci/`: powering a device before it can be
enumerated; link bandwidth control and notification; data object exchange; link encryption and
device security; steering hints for memory writes; enclosure LEDs; resizable BARs. Where a
controller driver or another subsystem calls the code, and the PCI core does not, say so in the
row. If this tree has no code for a job, say so in the row.

# Configuration space

## pci.config-access-returns: Configuration accessor results

- section: Configuration space
- relevance: 5 - callers mix two error conventions and test the wrong thing

What do `pci_read_config_dword()` and the other configuration space read and write functions
guarantee about their return value, including whether a failure is always a positive code, and
about the output after a failed read? What are the requirements for a caller that tests the return
value, or uses the value read, in order to assure safe usage? Before saying whether a failure is
always positive, read what the accessor passes back from the bus's `read` op, the first test in
`pcibios_err_to_errno()`, and one such op, `raw_pci_read()`. Where the answer names a return code,
give its full name. Start from `pci_read_config_dword()` in `drivers/pci/access.c`.

## pci.pcie-capability-accessors: PCI Express capability accessors

- section: Configuration space
- relevance: 4 - they differ from the plain accessors in ways callers trip on

What do `pcie_capability_read_word()` and `pcie_capability_read_dword()` return, and leave in the
output, for a register the device does not implement and after a failed read? What are the
requirements for a read-modify-write of a PCI Express capability register in order to assure safe
usage: for which registers does `pcie_capability_clear_and_set_word()` take a lock, and which
lock? Start from `pcie_capability_read_word()` and `pcie_capability_clear_and_set_word()`.

## pci.save-restore-state: Saved configuration state

- section: Configuration space
- relevance: 5 - reset and resume paths depend on when state was saved

When does the core itself save a device's configuration state, what does the restore function do
when no state has been saved, and what does the flag that records a save mean to the power
management code? Start from `pci_save_state()` and `pci_restore_state()` in `drivers/pci/pci.c`.

# Devices and their drivers

## pci.device-lifecycle: Device lifecycle

- section: Devices and their drivers
- relevance: 4 - a change has to go in the right step

Between a device being found on a bus and a driver being able to bind to it, which step makes it
visible to lookups and which to drivers, and what gates binding, so where must a change go that
has to run before any driver can probe? On removal, what is guaranteed to have happened by the
time the driver's remove callback returns and by the time the structure is freed? What does this
tree use to record that a device has been added or removed, where a reader remembers a structure
member? Start from `pci_scan_single_device()`, `pci_bus_add_device()` and
`pci_stop_and_remove_bus_device()`.

## pci.driver-binding: Probe and remove

- section: Devices and their drivers
- relevance: 4 - what the core has done before probe runs is not in the driver

What has the core already done for a device when a driver's probe callback is entered, and what
does it undo after the remove callback returns? Which thread runs the probe callback, and on which
CPU? How does the core treat probe's return value, including a positive one? Start from
`pci_device_probe()` and `pci_device_remove()` in `drivers/pci/pci-driver.c`.

## pci.locks: Core locks

- section: Devices and their drivers
- relevance: 4 - which lock a caller must already hold is rarely in the diff

What does each of `pci_bus_sem`, `pci_rescan_remove_lock` and `pci_lock` protect? Which functions
require the caller to hold one of them already, and is the requirement asserted or only
documented?

## pci.device-references: Lookups and references

- section: Devices and their drivers
- relevance: 4 - leaks and extra puts both come from here

What are the requirements for the reference on a device returned by `pci_get_device()` or by
another lookup function, and on the loop variable of `for_each_pci_dev`, in order to assure safe
usage? What does a lookup do with the reference on the device passed in as its starting point? Is
there an automatic cleanup form of `pci_dev_put()`? Start from `pci_get_device()`,
`for_each_pci_dev` and `pci_dev_put()`.

# Interrupt vectors and managed devices

## pci.irq-vector-api: Allocating interrupt vectors

- section: Interrupt vectors and managed devices
- relevance: 4 - flag names and fallback conditions are quoted from memory

What does the interrupt vector allocation function guarantee: in what order does it try the
interrupt types and when does it fall back to a pin interrupt, what does it return on success and
which error on failure, and how does a driver then get the Linux interrupt number and find out
which type it was given? Give the flag names this tree defines where a reader remembers others.
Start from `pci_alloc_irq_vectors_affinity()` in `drivers/pci/msi/api.c`.

## pci.legacy-msi-api: Older MSI functions

- section: Interrupt vectors and managed devices
- relevance: 3 - the old guide's topic; the list may be longer than it says

Besides the vector allocation interface, which functions for enabling MSI and MSI-X does this
tree still export, which of them does the source or the documentation call legacy or deprecated,
and what does a driver lose by using one of them? Start from `drivers/pci/msi/api.c` and
`Documentation/PCI/msi-howto.rst`.

## pci.managed-functions: Managed functions

- section: Interrupt vectors and managed devices
- relevance: 5 - which plain calls become managed has changed and decides what cleanup is a bug

On a device that was enabled with `pcim_enable_device()`, which plain PCI calls become managed and
which do not? What are the requirements for cleanup in an error path and in remove on such a
device, in order to assure safe usage? Which managed functions does the source mark deprecated,
and what replaces them? Start from `drivers/pci/devres.c`, `pcim_enable_device()` and
`pcim_setup_msi_release()`.

## pci.irq-vector-cleanup: Freeing interrupt vectors

- section: Interrupt vectors and managed devices
- relevance: 5 - the rule depends on how the device was enabled

What are the requirements for freeing interrupt vectors allocated in probe, on an error path and
in remove, in order to assure safe usage, for a device enabled with `pci_enable_device()` and for
one enabled with `pcim_enable_device()`? What does the documentation say about the second case?
What does `pci_free_irq_vectors()` do when it runs a second time? Start from
`pci_free_irq_vectors()` and `pcim_msi_release()`.

# Removal, reset and recovery

## pci.surprise-removal: Surprise removal

- section: Removal, reset and recovery
- relevance: 4 - remove callbacks run against hardware that is gone

How does the core mark a device that has been physically removed, and what do the configuration
accessors do for it afterwards? Which accesses to the device does the core not intercept? What are
the requirements for a driver's remove callback and interrupt handler that may run after the
device is gone, in order to assure safe usage? Start from `pci_dev_is_disconnected()` and
`pciehp_unconfigure_device()`.

## pci.function-reset: Function reset

- section: Removal, reset and recovery
- relevance: 4 - the lock and the method list both changed

Which of `pci_reset_function()`, `pci_reset_function_locked()`, `pci_try_reset_function()` and
`__pci_reset_function_locked()` is used when: which locks does each take, on which devices, and
what do the ones that expect the caller to hold locks check? Start from `pci_reset_function()` and
`pci_dev_lock()` in `drivers/pci/pci.c`.

## pci.reset-methods: Reset methods and callbacks

- section: Removal, reset and recovery
- relevance: 4 - a driver's callbacks run around some reset entry points only, and the method order decides which reset a device gets

Which driver callbacks run around a function reset, and which of the function reset entry points
call them? In what order are the reset methods tried for a device, and what makes the core stop
before it has tried them all? Give the order as one line. Start from `pci_reset_function()`,
`__pci_reset_function_locked()` and `pci_reset_fn_methods` in `drivers/pci/pci.c`.

## pci.error-recovery: Error recovery sequence

- section: Removal, reset and recovery
- relevance: 4 - the order of callbacks and when the reset happens have been reworked

When an error is reported, when is the link or slot reset relative to the driver's error
callbacks, and for which errors? How are the votes of several devices under the port combined,
including a device that has no handler? What is done to the devices and their drivers when
recovery fails? Give result codes and channel states by their full constant names. Start from
`pcie_do_recovery()` in `drivers/pci/pcie/err.c`.

# Controller drivers

## pci.host-bridge-api: Registering a host bridge

- section: Controller drivers
- relevance: 4 - every controller driver repeats this sequence

What does `pci_host_probe()` require of the `struct pci_host_bridge` it is given, and of the
driver's runtime power management state, before the call? Which locks does it take, and around
which of its steps? What undoes it on remove, or when a later step of the driver's probe fails?
Start from `devm_pci_alloc_host_bridge()` and `pci_host_probe()`.

## pci.config-ops-locking: Configuration callbacks and locking

- section: Controller drivers
- relevance: 4 - a callback that assumes it is serialised is wrong in some builds

What does the core guarantee about locking to the `read` and `write` callbacks in a controller's
`struct pci_ops`, and in which configurations or call paths is a callback entered without
`pci_lock` held? Does a callback have to set the output itself when it fails? What are the
requirements for a callback's own locking in order to assure safe usage? Start from
`pci_lock_config()` in `drivers/pci/access.c` and `CONFIG_PCI_LOCKLESS_CONFIG`.

# Endpoint framework

## pci.endpoint-objects: Endpoint objects

- section: Endpoint framework
- relevance: 4 - the vocabulary the rest depends on

How do `struct pci_epc`, `struct pci_epf` and the drivers of each relate? Which call binds a
function to a controller, and which call starts the link? Under which lock do calls into the
controller driver's `struct pci_epc_ops` run? Start from `include/linux/pci-epc.h`,
`include/linux/pci-epf.h` and `drivers/pci/endpoint/pci-ep-cfs.c`.

## pci.endpoint-error-returns: Endpoint error returns

- section: Endpoint framework
- relevance: 5 - the wrong test on a returned pointer crashes or hides a failure

A table of the endpoint framework functions that hand back a pointer: whether each reports
failure with an error pointer or with NULL, and so which test its caller must make. Start from
`pci_epc_get()`, `pci_epf_create()`, `pci_epc_get_features()`, `pci_epf_alloc_space()` and
`pci_epc_mem_alloc_addr()`, and the create functions in `drivers/pci/endpoint/pci-epc-core.c`.

## pci.endpoint-teardown-usage: Endpoint teardown

- section: Endpoint framework
- relevance: 4 - which release functions tolerate a failed pointer is not uniform

What are the requirements for the pointer passed to `pci_epc_put()`, `pci_epf_destroy()`,
`pci_epf_free_space()` and the endpoint framework's other put, destroy and free functions, in
order to assure safe usage? Which of them check their argument, and for which values, so that a
caller may pass them the result of a failed call? Start from `pci_epc_put()`, `pci_epf_destroy()`
and `pci_epf_free_space()`.

# Model gaps

## pci.model-gaps: Other mistakes models make

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

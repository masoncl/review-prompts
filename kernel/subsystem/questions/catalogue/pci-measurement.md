# Questions: PCI (measurement set)

- guide: pci.md
- title: PCI Subsystem

A wide set of questions about the PCI core, the driver interface, the host
bridge interface and the endpoint framework, used to measure what a model
already knows before deciding what the built guide should spend its words on.
The hand-written guide it will replace is 493 words and covers four things
only: error returns in the endpoint framework, the older MSI functions, freeing
interrupt vectors, and device naming. Power management and device tree parsing
have their own guides. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## pci.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

Which files under `drivers/pci/` hold enumeration, the driver model glue,
removal, configuration space access, resource assignment, the managed
(devres) functions, interrupt vector allocation, reset, error recovery, native
hotplug, SR-IOV, quirks, the sysfs files and the endpoint framework? A table.

## pci.entry-points: Entry points

- section: Finding your way
- relevance: 4 - where to start reading for each job
- words: 100

For each job (scan one device, bind a driver to it, stop and remove it, reset a
function, recover from a reported error, allocate interrupt vectors, register a
host bridge), which function do you start reading from? A table.

## pci.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several driver rules are written down only there
- words: 60

Which files under `Documentation/PCI/` are the authority on the driver
interface, on MSI, on error recovery and on the endpoint framework?

## pci.newer-facilities: Newer facilities

- section: Finding your way
- relevance: 3 - a reader cannot review what it does not recognise
- words: 110

Which parts of `drivers/pci/` handle powering a device before it can be
enumerated, link bandwidth control and notification, data object exchange,
link encryption and device security, steering hints for memory writes,
enclosure LEDs, and resizable BARs? For each give the file and the one thing a
reviewer should know about who calls it.

# Devices and drivers

## pci.device-lifecycle: Device lifecycle

- section: Devices and their drivers
- relevance: 4 - a change has to go in the right step
- words: 110

List in order the steps a device goes through from being found on a bus to
being visible to drivers, and then from a removal request to its structure
being freed, naming the function for each step and the flags that record that
a device has been added or removed. Start from `pci_scan_single_device()`,
`pci_bus_add_device()` and `pci_stop_and_remove_bus_device()`.

## pci.driver-binding: Matching and probing

- section: Devices and their drivers
- relevance: 4 - what the core has done before probe runs is not in the driver
- words: 110

How is a driver chosen for a device (static IDs, IDs added at run time, a
forced driver), and what does the core do around the driver's probe and remove
callbacks: references, runtime power management, which CPU probe runs on, and
how probe's return value is treated? Start from `pci_device_probe()` and
`pci_device_remove()` in `drivers/pci/pci-driver.c`.

## pci.locks: Core locks

- section: Devices and their drivers
- relevance: 4 - which lock a caller must already hold is rarely in the diff
- words: 110

What does each of the PCI core's locks protect, which functions require the
caller to hold one already and how do they say so, and what does the lock
taken around a function reset consist of? Start from `pci_bus_sem`,
`pci_rescan_remove_lock`, `pci_lock` and `pci_dev_lock()`.

## pci.device-references: Lookups and references

- section: Devices and their drivers
- relevance: 4 - leaks and extra puts both come from here
- words: 90

Which functions that look a device up return a counted reference, which of
them drop the reference on the device passed in as the starting point, and what
does that mean for leaving an iterating loop early? Is there an automatic
cleanup form? Start from `pci_get_device()`, `for_each_pci_dev` and
`pci_dev_put()`.

## pci.device-naming: Device names

- section: Devices and their drivers
- relevance: 3 - the old guide's rule, asked from both sides
- words: 70

Who sets the device name of a PCI function, of a bus and of a host bridge, in
what format, and what depends on it? What usage of `dev_set_name()` by a PCI
driver is unsafe, and what that looks similar is correct?

## pci.quirk-phases: Fixup phases

- section: Devices and their drivers
- relevance: 3 - a quirk in the wrong phase runs before the state it needs exists
- words: 90

Which fixup phases are there, at which point in a device's life does each run,
and what has and has not been set up at that point? Start from
`pci_fixup_device()` and the `DECLARE_PCI_FIXUP_EARLY()` family of macros in
`include/linux/pci.h`.

# Configuration space

## pci.config-access-returns: Configuration accessor results

- section: Reading and writing configuration space
- relevance: 5 - callers mix two error conventions and test the wrong thing
- words: 100

What do the configuration space read and write functions return on success and
on failure, how is that turned into an errno, what is left in the output value
after a failed read, and how should a caller test a value for a failed read?
Is a failure always one of the positive codes: read what the accessor passes
back from the bus's `read` op, the first test in `pcibios_err_to_errno()`, and
one such op, `raw_pci_read()`, before saying. What do they do for a device
marked as gone? Where the answer names a return code, give its full name. Start
from `pci_read_config_dword()` in `drivers/pci/access.c`.

## pci.pcie-capability-accessors: PCI Express capability accessors

- section: Reading and writing configuration space
- relevance: 4 - they differ from the plain accessors in ways callers trip on
- words: 100

How do the accessors for the PCI Express capability differ from the plain
configuration accessors: what happens for a register the device does not
implement, what is in the output after a failure, and which registers get a
locked read-modify-write, under which lock? Start from
`pcie_capability_read_word()` and `pcie_capability_clear_and_set_word()`.

## pci.save-restore-state: Saved configuration state

- section: Reading and writing configuration space
- relevance: 4 - reset and resume paths depend on when state was saved
- words: 100

When does the core itself save a device's configuration state, what does the
restore function do when no state has been saved, what does the flag that
records a save mean to the power management code, and which capabilities are
covered? Start from `pci_save_state()` and `pci_restore_state()` in
`drivers/pci/pci.c`.

# Resources

## pci.enable-device: Enabling a device

- section: Enabling and mapping
- relevance: 3 - the enable count makes an unbalanced call silent
- words: 80

What does enabling a device do, is it counted, what does disabling do to bus
mastering, and what usage of the enable and disable calls across probe, remove,
suspend and error paths is unsafe while looking balanced? Start from
`pci_enable_device()` and `pci_disable_device()`.

## pci.managed-functions: Managed functions

- section: Enabling and mapping
- relevance: 5 - which plain calls become managed has changed and decides what cleanup is a bug
- words: 110

Which managed (devres) PCI functions does this tree offer, which are marked
deprecated, and which plain functions, if any, change their behaviour on a
device that was enabled with the managed enable call? Start from
`drivers/pci/devres.c`, `pcim_enable_device()` and
`pcim_setup_msi_release()`.

## pci.bar-resources: BAR resources

- section: Enabling and mapping
- relevance: 3 - indexes past the standard BARs depend on configuration
- words: 80

How are a device's resources indexed (standard BARs, ROM, SR-IOV, bridge
windows), which accessors and iterator should code use for them, and which
calls claim a BAR and map it? Start from `PCI_STD_NUM_BARS` and
`pci_dev_for_each_resource()`.

# Interrupts

## pci.irq-vector-api: Allocating interrupt vectors

- section: Interrupt vectors
- relevance: 4 - flag names and fallback conditions are quoted from memory
- words: 110

What flags does the interrupt vector allocation function take, in what order
does it try the interrupt types, when does it fall back to a pin interrupt,
what does it return, and how does a driver then get the Linux interrupt number
and find out which type it got? What does the build without MSI support
provide? Start from `pci_alloc_irq_vectors_affinity()` in
`drivers/pci/msi/api.c`.

## pci.legacy-msi-api: Older MSI functions

- section: Interrupt vectors
- relevance: 3 - the old guide's topic; the list may be longer than it says
- words: 80

Which functions for enabling and disabling MSI and MSI-X does this tree still
export besides the vector allocation interface, which of them does the source
or the documentation call legacy or deprecated, and what does each lack? Start
from `drivers/pci/msi/api.c` and `Documentation/PCI/msi-howto.rst`.

## pci.irq-vector-cleanup: Freeing interrupt vectors

- section: Interrupt vectors
- relevance: 5 - the rule depends on how the device was enabled
- words: 100

What usage of interrupt vectors allocated in probe is unsafe on an error path
or in remove, and what that looks similar is correct? Cover a device enabled
with the plain enable call and one enabled with the managed call, what the
documentation says about the second case, and what the code actually does when
the free function runs twice. Start from `pci_free_irq_vectors()` and
`pcim_msi_release()`.

## pci.msix-dynamic: Dynamic MSI-X allocation

- section: Interrupt vectors
- relevance: 2 - a handful of drivers
- words: 70

Can a driver add and remove individual MSI-X vectors after MSI-X has been
enabled, with which functions, how is it told whether the platform allows it,
and how is failure reported? Start from `pci_msix_alloc_irq_at()`.

# Errors, reset and removal

## pci.error-recovery: Error recovery sequence

- section: When things go wrong
- relevance: 4 - the order of callbacks and when the reset happens have been reworked
- words: 130

In what order does the core call a driver's error handlers when an error is
reported, how are the results of several devices combined, what happens when a
device under the port has no handler, when is the link or slot reset relative
to the callbacks, and what is done on failure? Start from `pcie_do_recovery()`
in `drivers/pci/pcie/err.c`.

## pci.function-reset: Function reset

- section: When things go wrong
- relevance: 4 - the lock and the method list both changed
- words: 110

Which reset methods does the core try for a function and in what order, which
devices are locked and how, what is saved and restored, and which driver
callbacks run around it? How do the variants that expect the caller to hold
locks differ? Start from `pci_reset_function()` and `pci_reset_fn_methods` in
`drivers/pci/pci.c`.

## pci.surprise-removal: Surprise removal

- section: When things go wrong
- relevance: 4 - remove callbacks run against hardware that is gone
- words: 90

How does the core mark a device that has been physically removed, what do the
configuration accessors do for it afterwards, and what usage in a driver's
remove or interrupt path is unsafe when the device may already be gone, and
what is correct? Start from `pci_dev_is_disconnected()` and
`pciehp_unconfigure_device()`.

## pci.sriov: Enabling virtual functions

- section: When things go wrong
- relevance: 3 - the locks held around the driver callback are not visible in a driver
- words: 100

How does a request to change the number of virtual functions reach a driver,
which locks does the core hold around the driver's callback, what may the
callback return, and what does the core check when the physical function's
driver is removed? Start from `sriov_numvfs_store()` and `pci_enable_sriov()`
in `drivers/pci/iov.c`.

# Host bridges

## pci.host-bridge-api: Registering a host bridge

- section: Controller drivers
- relevance: 4 - every controller driver repeats this sequence
- words: 110

How does a controller driver allocate, fill in and register a host bridge, what
does the registering function do in order, which locks does it take, what must
the driver have done about runtime power management first, and how is the
bridge torn down? Start from `devm_pci_alloc_host_bridge()` and
`pci_host_probe()`.

## pci.config-ops: Configuration access callbacks

- section: Controller drivers
- relevance: 3 - the return convention differs from the rest of the kernel
- words: 80

What must a controller's configuration read and write callbacks return, what
may they assume about locking and context, what should a read put in the value
when the device does not answer, and which generic helpers exist for memory
mapped configuration space? Start from `struct pci_ops` and
`pci_generic_config_read()`.

# The endpoint framework

## pci.endpoint-objects: Endpoint objects

- section: Endpoint controllers and functions
- relevance: 4 - the vocabulary the rest depends on
- words: 110

What are the objects of the endpoint framework (controller, function, their
drivers), which callback tables does each supply, how are a function and a
controller bound to each other, and which lock protects calls into the
controller? Start from `include/linux/pci-epc.h`, `include/linux/pci-epf.h`
and `drivers/pci/endpoint/pci-ep-cfs.c`.

## pci.endpoint-error-returns: Endpoint error returns

- section: Endpoint controllers and functions
- relevance: 5 - the wrong test on a returned pointer crashes or hides a failure
- words: 90

Which endpoint framework functions that hand back a pointer report failure
with an error pointer and which with NULL, and with which error codes? A table.
Start from `pci_epc_get()`, `pci_epf_create()`, `pci_epc_get_features()`,
`pci_epf_alloc_space()` and `pci_epc_mem_alloc_addr()`, and the create
functions in `drivers/pci/endpoint/pci-epc-core.c`.

## pci.endpoint-teardown-usage: Endpoint teardown

- section: Endpoint controllers and functions
- relevance: 4 - which release functions tolerate a failed pointer is not uniform
- words: 70

What usage of the endpoint framework's put, destroy and free functions with a
pointer that came back from a failed call is unsafe, and which of them check
their argument and so are correct to call unconditionally? Start from
`pci_epc_put()`, `pci_epf_destroy()` and `pci_epf_free_space()`.

## pci.endpoint-bars: Endpoint BARs

- section: Endpoint controllers and functions
- relevance: 3 - the feature structure has grown
- words: 100

How does a controller describe its BARs to a function driver (fixed size,
reserved, 64-bit only, alignment, anything newer), how does a function driver
allocate backing memory and program a BAR, and in what order are they undone?
Start from `struct pci_epc_features`, `pci_epf_alloc_space()` and
`pci_epc_set_bar()`.

## pci.endpoint-init-events: Endpoint events

- section: Endpoint controllers and functions
- relevance: 3 - work done before the controller is ready touches dead registers
- words: 90

Which events does a controller deliver to its function drivers, through which
functions, and what must a function driver put off until the controller says it
is initialised? What happens for a function bound after that? Start from
`struct pci_epc_event_ops` and `pci_epc_init_notify()`.

# Changing the implementation

## pci.change-checklist: Changing the core

- section: What a change must preserve
- relevance: 4 - the code is built in more configurations than a developer tests
- words: 100

What must a change to `drivers/pci/` or `include/linux/pci.h` keep working
besides the default build: the stubs for kernels without PCI, without MSI and
without the optional features, the architecture hooks, configuration access
without the global lock, and the tests that exist for the endpoint framework
and elsewhere? Say where each lives.

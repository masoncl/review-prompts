# Questions: CXL Subsystem (measurement set)

- guide: cxl.md
- title: CXL Subsystem

A wide set of questions about `drivers/cxl/`, used to measure what a model
already knows before deciding what the built guide should spend its words on.
The hand-written guide it will replace is 218 words and is about one thing: the
type flag on a resource handed to the HMAT lookup for an extended linear cache.
The questions here cover the subject that guide is loaded for: ports, decoders,
regions and memdevs, the core's locking, the mailbox, and the cxl_test mock
under `tools/testing/cxl/`. They ask what this tree does and nothing about
earlier kernels. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## cxl.core-files: Core files

- section: Finding your way
- relevance: 4 - the core has been split into more files than anyone remembers
- words: 110

Which files hold port and decoder registration, HDM decoder programming and DPA
allocation, region assembly and the pmem and dax devices a region spawns, the
memdev and the mailbox core, the PCI mailbox transport, CDAT parsing, protocol
error handling, features and EDAC, platform address translation, and the ACPI
root driver? Which headers are under `include/cxl/` and what is each for? A
table. Start from `drivers/cxl/core/Makefile`.

## cxl.docs: Documentation

- section: Finding your way
- relevance: 2 - says where the driver's own description of itself is
- words: 60

Which files under `Documentation/driver-api/cxl/` describe the driver's device
objects and decoder programming, which document platform quirks the driver
works around, and where is the sysfs interface documented?

## cxl.modules-and-bus: Modules and bus drivers

- section: Finding your way
- relevance: 3 - decides which module a change lands in and what it may call
- words: 90

Which modules does `drivers/cxl/` build, which device type on the CXL bus does
each driver bind to, and how does a driver declare that? How are core symbols
exported to those modules, and are any exported to one named module only?
Start from `struct cxl_driver` and `drivers/cxl/Makefile`.

# The objects

## cxl.port-objects: Ports, dports and endpoints

- section: Object model
- relevance: 4 - every other structure hangs off these
- words: 100

What do `struct cxl_port`, `struct cxl_dport` and `struct cxl_ep` each
represent, how are a port's dports, endpoints and regions stored and keyed,
and how does code tell a root port, a switch port and an endpoint port apart?
Start from `drivers/cxl/cxl.h`.

## cxl.decoder-kinds: Decoder kinds

- section: Object model
- relevance: 4 - the three kinds embed each other and carry different state
- words: 100

What are the kinds of decoder object, how do their structures embed one
another, which fields does each kind add, and which callbacks does a decoder
or a root decoder carry? Start from `struct cxl_decoder` and
`struct cxl_root_decoder`.

## cxl.device-state: Device state structures

- section: Object model
- relevance: 4 - code that assumes a mailbox or a class device crashes on the other kind
- words: 90

What is the difference between `struct cxl_dev_state` and
`struct cxl_memdev_state`, where is each defined, how is each allocated, and
what does `to_cxl_memdev_state()` return for a device that is not a class
memory device? Which in-tree drivers other than `drivers/cxl/pci.c` create a
device state?

## cxl.dpa-partitions: Device address partitions

- section: Object model
- relevance: 4 - the ram and pmem split is stored differently from what people remember
- words: 80

How does a device state describe the volatile and persistent parts of its
device physical address space, how does an endpoint decoder record which part
it maps, and how is that chosen from sysfs? Start from `cxl_dpa_setup()` and
`cxl_dpa_set_part()`.

# Locking and lifetimes

## cxl.core-locks: Core locks

- section: Locking
- relevance: 5 - which lock covers region state and which covers DPA is the first thing a review checks
- words: 110

Which global and per-object locks does the CXL core define, where is each
declared, and what does each protect? Include the locks for region
configuration, device address allocation, the list of regions under a root
decoder, the memdev's pointer to its device state, and the mailbox. A table.
Start from `drivers/cxl/core/core.h`.

## cxl.lock-order: Lock ordering

- section: Locking
- relevance: 5 - an inversion here is a deadlock lockdep only sees if the path runs
- words: 90

In what order are the device lock of a port or memdev, the lock on a root
decoder's regions, the region configuration lock and the device address lock
taken when more than one is held? Name functions that take several of them.
Start from `cxl_add_to_region()`, `attach_target()` and
`cxl_trigger_poison_list()`.

## cxl.conditional-guards: Interruptible lock acquisition

- section: Locking
- relevance: 4 - the idiom is recent and a missing error check compiles
- words: 80

How do sysfs handlers in the CXL core take the region and address locks so
that a signal can interrupt the wait, what must follow the acquisition, and
where does the core take the same lock unconditionally instead and why? Start
from `uuid_store()` and `cxl_decoder_detach()` in `drivers/cxl/core/region.c`.

## cxl.devm-host-usage: Devres host choice

- section: Lifetimes
- relevance: 4 - actions registered on the wrong device run at the wrong time or never
- words: 90

Against which device are the release actions for a port, a dport and a decoder
registered, what check rejects a registration made from the wrong context, and
what usage is unsafe while what that looks similar is correct? Start from
`port_to_host()`, `dport_to_host()` and `__devm_cxl_add_dport()`.

# Ports and decoders

## cxl.port-enumeration: Port enumeration

- section: Port lifetime
- relevance: 4 - the retry loop and its error codes are easy to break
- words: 100

How does a memdev's probe create the ports between itself and the root: which
function walks the ancestry, what makes it start over, what do the error codes
it gets back from its helpers mean, and what is skipped for a device attached
to a restricted host? Start from `cxl_mem_probe()` and
`devm_cxl_enumerate_ports()`.

## cxl.dport-creation: Downstream port creation

- section: Port lifetime
- relevance: 5 - when dports and switch decoders appear has changed and readers will assume the old order
- words: 100

When is a switch or host bridge port's dport created, by which driver callback,
and under which lock? When are that port's component registers mapped and its
HDM decoders enumerated relative to its dports, and how do existing decoders
learn of a dport added later? Start from `cxl_port_add_dport()` and
`cxl_switch_port_probe()` in `drivers/cxl/port.c`.

## cxl.port-removal: Port removal

- section: Port lifetime
- relevance: 4 - two removal directions share the same devres actions
- words: 90

What are the two ways a non-root port is unregistered, what does each rely on,
what does the flag that marks a port as dying block, and which locks are held
while the last endpoint is detached? Start from `cxl_detach_ep()` and
`delete_endpoint()`.

## cxl.dpa-allocation: Device address allocation order

- section: Decoder programming
- relevance: 4 - the ordering rule is enforced by a counter, not by hardware
- words: 90

What ordering does the core enforce when an endpoint decoder reserves or frees
device address space, which port field tracks it, what is a skip and when is
one recorded, and what makes a free or an allocation fail with a busy error?
Start from `__cxl_dpa_reserve()` and `cxl_dpa_free()`.

## cxl.commit-order: Decoder commit order

- section: Decoder programming
- relevance: 4 - out-of-order teardown leaves decoders pinned
- words: 90

In what order must a port's HDM decoders be committed and reset, which port
field tracks that, what happens when a decoder that is not the last committed
one is reset, and what stops a commit on a device that is being sanitized?
Start from `cxl_decoder_commit()`, `cxl_decoder_reset()` and
`cxl_port_commit_reap()`.

# Regions

## cxl.region-states: Region configuration states

- section: Regions
- relevance: 4 - sysfs handlers gate on these and a wrong comparison lets a live region be edited
- words: 90

What are the states of a region's configuration, which writes move it between
them, which attributes refuse a write in which states, and what does writing
zero to the commit attribute do before and after it releases the region
driver? Start from `enum cxl_config_state` and `commit_store()`.

## cxl.region-attach-detach: Attaching and detaching targets

- section: Regions
- relevance: 4 - the detach path is shared by sysfs and by decoder destruction
- words: 100

What does attaching an endpoint decoder to a region check and set up along the
path to the root, and what does detaching undo? What are the two ways the
detach function is called, how do they differ in locking and in what they
invalidate, and what happens to the region driver afterwards? Start from
`cxl_region_attach()` and `cxl_decoder_detach()`.

## cxl.region-flags: Region flags

- section: Regions
- relevance: 3 - each bit changes what teardown and probe may do
- words: 80

Which flag bits does `struct cxl_region` define, what does each mean, who sets
and clears it, and what does each stop from happening? Start from the
`CXL_REGION_F_` definitions in `drivers/cxl/cxl.h`.

## cxl.auto-regions: Firmware-programmed regions

- section: Regions
- relevance: 4 - the boot-time path races with itself and with sysfs
- words: 100

How does the driver turn decoders that firmware committed before boot into
region objects: which function starts it and when, how are the states of an
endpoint decoder used, what serialises several endpoints discovering the same
range, and when is the region driver attached? Start from `discover_region()`
and `cxl_add_to_region()`.

## cxl.cache-invalidation: CPU cache invalidation

- section: Regions
- relevance: 3 - skipping it corrupts data silently on real hardware
- words: 70

When does the region code invalidate CPU caches for a region's address range,
what happens on a platform that cannot, and which configuration option changes
that and who needs it? Start from `cxl_region_invalidate_memregion()`.

## cxl.address-translation: Address translation

- section: Regions
- relevance: 3 - trace events and poison reports depend on it
- words: 90

How does the core convert a device physical address to a host physical address
and then to a system physical address, which callbacks does the platform
supply for the last step and where are they stored, and what does the core do
for a region whose addresses are normalized? Start from `cxl_dpa_to_hpa()` and
`struct cxl_rd_ops`.

## cxl.hmat-resource-usage: Resources compared with firmware tables

- section: Regions
- relevance: 3 - a wrongly typed resource fails the comparison without an error
- words: 90

When CXL code builds a `struct resource` to describe a root decoder's range and
hands it to a helper that compares it with resources taken from firmware
tables, what way of initialising it is unsafe and what that looks similar is
correct? What does the comparison do when the two differ in type, and what does
the caller then store? Start from `hmat_get_extended_linear_cache_size()` and
`cxl_setup_extended_linear_cache()`.

# Memdevs and the mailbox

## cxl.memdev-lifetime: Memdev creation and teardown

- section: Memdevs
- relevance: 4 - the entry points have been renamed and an accelerator path added
- words: 110

Which functions does a driver call to create a device state and register a
memdev for a class memory device, and which for an accelerator with private
memory? What does the optional attach descriptor change about probe failure
and about detach, and what protects the character device's ioctl path against
the memdev being unregistered? Start from `drivers/cxl/mem.c` and
`cxl_memdev_shutdown()`.

## cxl.mbox-send: Sending a mailbox command

- section: Mailbox
- relevance: 5 - the return value and the output size are both misread
- words: 100

What does `cxl_internal_send_cmd()` return on success and for each kind of
failure according to its body, not its comment, what do the output size and
minimum output size fields of the command mean on entry and on return, and
what must the transport callback never return? Start from
`struct cxl_mbox_cmd`.

## cxl.mbox-background: Background commands

- section: Mailbox
- relevance: 4 - sanitize is the exception and it blocks other paths
- words: 100

How does the PCI transport handle a command the device runs in the background:
which lock is held while it waits, what wakes it, and what bounds the wait?
Which command is handled asynchronously instead, what does that block while it
runs, and how does user space learn it finished? Start from
`__cxl_pci_mbox_send_cmd()` and `cxl_mbox_sanitize_work()`.

## cxl.mbox-user-commands: Commands from user space

- section: Mailbox
- relevance: 4 - the checks are the security boundary of the ioctl
- words: 100

What does the ioctl path check before it sends a user's command: enabled and
exclusive bitmaps, payload sizes, payload contents and raw opcodes? What error
does each refusal return, who sets commands exclusive and under which lock,
and what gates raw commands? Start from `cxl_validate_cmd_from_user()` and
`set_exclusive_cxl_commands()`.

## cxl.poison-locking: Poison operations

- section: Mailbox
- relevance: 3 - the locked variants exist because callers already hold the locks
- words: 70

Which locks must be held to list, inject or clear poison on a memdev, which
functions take them and which expect them held, and how does listing differ
when the device has committed decoders? Start from `cxl_trigger_poison_list()`
and `cxl_inject_poison_locked()`.

## cxl.ras-handling: Protocol error handling

- section: Errors
- relevance: 3 - the handlers moved out of the PCI driver and split by topology
- words: 80

Where are the PCI error handlers for a CXL memory device implemented, under
which configuration symbol, how do the restricted host and virtual hierarchy
cases differ, and when are a dport's and a port's RAS registers mapped? Start
from `cxl_error_detected()` and `devm_cxl_dport_ras_setup()`.

# The cxl_test mock

## cxl.test-build: Mock build

- section: cxl_test
- relevance: 5 - a new core file or a new static helper breaks this build, not the normal one
- words: 100

How does `tools/testing/cxl/Kbuild` rebuild the CXL modules for testing: which
objects are compiled from `drivers/cxl/`, which driver is not rebuilt and what
stands in for it, what do the linker and compiler flags do, and what must a
patch that adds a source file to `drivers/cxl/core/Makefile` also change? What
does the build assert about the kernel configuration?

## cxl.test-mock-ops: Mocked symbols

- section: cxl_test
- relevance: 4 - changing the prototype of a wrapped function has to be done in three places
- words: 100

How is a call from the rebuilt modules redirected to the mock: what is a
wrapped symbol, how does the wrapper find the mock's implementation and fall
back to the real one, and which functions of the CXL core itself are wrapped?
List what a patch must touch to wrap one more function. Start from
`struct cxl_mock_ops` and `tools/testing/cxl/test/mock.c`.

## cxl.test-topology: Mock topology and mailbox

- section: cxl_test
- relevance: 3 - tests depend on the counts and on which opcodes the mock answers
- words: 90

What topology does `tools/testing/cxl/test/cxl.c` create, from what kind of
devices, and which module parameters change it? Which module implements the
mock memory device, how does it receive mailbox commands, and what does it do
with an opcode it does not implement? Start from `cxl_mock_mbox_send()`.

# Changing the implementation

## cxl.change-checklist: Core change checklist

- section: What a change must preserve
- relevance: 4 - the things a diff to the core does not show
- words: 100

What must a change to the CXL core keep working besides the code it edits: the
mock build and its wrapped prototypes, configurations without regions, RAS or
features, devices without a mailbox, the stubs in headers, the trace events,
and the sysfs ABI document? Name the file or symbol to check for each.

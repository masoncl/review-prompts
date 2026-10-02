# Questions: CXL Subsystem

- guide: cxl.md
- title: CXL Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/cxl-measurement.md` is the wider
set the readers were measured on and `catalogue/cxl-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## cxl.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## cxl.core-files: Core files

- relevance: 4 - the files nobody guesses, and a structure that moved to a public header

A table and nothing else, topic to file: under `drivers/cxl/core/`, the pmem and dax devices a
region spawns, protocol error handling for a restricted host, platform address translation, and
the definition of the core's global region and address locks; and the header that defines
`struct cxl_dev_state`. Where a reader is likely to look in a file that no longer holds the
thing, say so in the row. Start from `drivers/cxl/core/Makefile`.

# Locks

## cxl.core-locks: Core locks

- section: Locks
- relevance: 5 - which lock covers region state and which covers DPA is the first thing a review checks

A table of the locks a patch to the CXL core has to choose among: for region configuration,
device address allocation, the regions under a root decoder, the memdev's pointer to its device
state, and the mailbox. Give each lock's exact name, the structure or file it lives in and, in
a few words, what it protects. Where a reader's memory offers an older name or an older split
of one lock into two, say what this tree has. Start from `drivers/cxl/core/core.h` and
`struct cxl_root_decoder`.

## cxl.lock-order: Lock ordering

- section: Locks
- relevance: 5 - an inversion here is a deadlock lockdep only sees if the path runs

In what order are the device lock of a port or memdev, the lock on a root decoder's regions,
the region configuration lock and the device address lock taken when more than one is held? One
line for the order, then which calls `cxl_add_to_region()` makes while it holds the lock on the
root decoder's regions.

## cxl.conditional-guards: Interruptible lock acquisition

- section: Locks
- relevance: 4 - the idiom is recent and a missing error check compiles

How do sysfs handlers in the CXL core take the region and address locks so that a signal can
interrupt the wait, and what are the requirements for the code that follows the acquisition in
order to assure safe usage? Where does the core take the same lock unconditionally instead, and
why? Start from `uuid_store()` and `cxl_decoder_detach()` in `drivers/cxl/core/region.c`.

# Device state and memdevs

## cxl.device-state: Device state structures

- section: Device state and memdevs
- relevance: 4 - code that assumes a mailbox or a class device crashes on the other kind

What does the allocator of a bare `struct cxl_dev_state` require of the driver's own structure?
What does `to_cxl_memdev_state()` return for a device that is not a class memory device, and what
are the requirements for using its result in order to assure safe usage?

## cxl.memdev-lifetime: Memdev creation

- section: Device state and memdevs
- relevance: 4 - the entry points have been renamed and an accelerator path added

Which functions does a driver call to create a device state and register a memdev for a class
memory device, and which, if the tree has them, for an accelerator with private memory? Name an
in-tree caller of each. If a memdev can be registered with an attach descriptor, what does that
change when it fails to bind to `cxl_mem` and when it is detached? Start from
`drivers/cxl/mem.c`.

# Ports and dports

## cxl.port-objects: Port xarrays and port kinds

- section: Ports and dports
- relevance: 4 - every other structure hangs off these

How are a port's dports, endpoints and regions stored and what is each keyed by, and how does
code tell a root port, a switch port and an endpoint port apart? Start from `struct cxl_port`,
`struct cxl_dport` and `struct cxl_ep` in `drivers/cxl/cxl.h`.

## cxl.port-enumeration: Port enumeration

- section: Ports and dports
- relevance: 4 - the retry loop and its error codes are easy to break

When a memdev's probe creates the ports between itself and the root, what makes the walk up the
ancestry start over, what do the error codes it gets back from its helpers mean, and what is
skipped for a device attached to a restricted host? Start from `cxl_mem_probe()` and
`devm_cxl_enumerate_ports()`.

## cxl.dport-creation: Downstream port creation

- section: Ports and dports
- relevance: 5 - when dports, switch decoders and RAS mappings appear is not what the port driver's probe suggests

When is a switch or host bridge port's dport created, and by which driver callback? When are
that port's component registers mapped, its HDM decoders enumerated and its RAS registers mapped
relative to its dports? If a dport can be added after the decoders exist, how do they learn of
it? Start from `cxl_port_add_dport()` and `cxl_switch_port_probe()` in `drivers/cxl/port.c`.

## cxl.port-removal: Port removal

- section: Ports and dports
- relevance: 4 - two removal directions share the same devres actions

In what ways is a non-root port unregistered and what does each rely on, what does the flag that
marks a port as dying block, and which locks are held while the last endpoint is detached? Start
from `cxl_detach_ep()` and `delete_endpoint()`.

## cxl.devm-host-usage: Devres host choice

- section: Ports and dports
- relevance: 4 - actions registered on the wrong device run at the wrong time or never

Against which device are the release actions for a port, a dport and a decoder registered, and
what check rejects a registration made from the wrong context? What are the requirements for the
caller of `devm_cxl_add_port()` and of `devm_cxl_add_dport()` in order to assure safe usage? Start
from `port_to_host()`, `dport_to_host()` and `__devm_cxl_add_dport()`.

# Decoders and device addresses

## cxl.decoder-kinds: Decoder kinds

- section: Decoders and device addresses
- relevance: 4 - the three kinds embed each other and carry different state

How do the structures for the kinds of decoder embed one another, and how does code get from a
generic decoder to its kind without casting the wrong one? Which callbacks does a decoder or a
root decoder carry, who sets them and who calls them? Start from `struct cxl_decoder` and
`struct cxl_root_decoder`.

## cxl.dpa-partitions: Device address partitions

- section: Decoders and device addresses
- relevance: 4 - the ram and pmem split is stored differently from what people remember

How does a device state describe the volatile and persistent parts of its device physical
address space, given that a reader may remember one resource for each, how does an endpoint
decoder record which part it maps, and how is that chosen from sysfs? Start from
`cxl_dpa_setup()` and `cxl_dpa_set_part()`.

## cxl.dpa-allocation: Device address allocation order

- section: Decoders and device addresses
- relevance: 4 - the ordering rule is enforced by a counter, not by hardware

What ordering does the core enforce when an endpoint decoder reserves or frees device address
space and what tracks it, what exactly is a skip and when is one recorded, and what makes a free
or an allocation fail with a busy error? Start from `__cxl_dpa_reserve()` and `cxl_dpa_free()`.

## cxl.commit-order: Decoder commit order

- section: Decoders and device addresses
- relevance: 4 - out-of-order teardown leaves decoders pinned

In what order must a port's HDM decoders be committed and reset and what tracks that, what
happens when a decoder that is not the last committed one is reset, and what stops a commit on a
device that is being sanitized? Start from `cxl_decoder_commit()`, `cxl_decoder_reset()` and
`cxl_port_commit_reap()`.

# Regions

## cxl.region-states: Region configuration states

- section: Regions
- relevance: 4 - sysfs handlers gate on these and a wrong comparison lets a live region be edited

What are the states of a region's configuration and which writes move it between them? What must
the store handler of a region attribute compare the state against before it changes the region, in
order to assure safe usage? What does writing zero to the commit attribute do before and after it
releases the region driver? Start from `enum cxl_config_state` and `commit_store()`.

## cxl.region-flags: Region flags

- section: Regions
- relevance: 3 - each bit changes what teardown and probe may do

A table of the flag bits of `struct cxl_region`, each name in full: what each stops from
happening, and who sets it and who, if anyone, clears it. Start from the `CXL_REGION_F_`
definitions in `drivers/cxl/cxl.h`.

## cxl.region-attach-detach: Attaching and detaching targets

- section: Regions
- relevance: 4 - the detach path is shared by sysfs and by decoder destruction

What does attaching an endpoint decoder to a region check and set up along the path to the root,
and what does detaching undo? What happens to the region driver after a detach? Start from
`cxl_region_attach()` and `cxl_decoder_detach()`.

## cxl.detach-modes: Detach modes

- section: Regions
- relevance: 4 - sysfs and decoder destruction share the detach path and lock it differently

In which ways is `cxl_decoder_detach()` called, and how do they differ in locking and in what they
invalidate? Start from `cxl_decoder_detach()` in `drivers/cxl/core/region.c`.

## cxl.auto-regions: Firmware-programmed regions

- section: Regions
- relevance: 4 - the boot-time path races with itself and with sysfs

When the driver turns decoders that firmware committed before boot into region objects, what moves
an endpoint decoder between the values of `enum cxl_decoder_state`? What serialises several
endpoints discovering the same range, and when is the region driver attached? Start from
`discover_region()` and `cxl_add_to_region()`.

## cxl.hmat-resource-usage: Extended linear cache size

- section: Regions
- relevance: 3 - a wrongly typed resource fails the comparison without an error

What are the requirements for the `struct resource` that `cxl_setup_extended_linear_cache()`
builds for a root decoder's range and passes to `hmat_get_extended_linear_cache_size()`, in order
to assure safe usage? What does the caller store when the helper matches nothing, and where does
that value show later? Start from `hmat_get_extended_linear_cache_size()` and
`cxl_setup_extended_linear_cache()`.

# Mailbox

## cxl.mbox-send: Sending a mailbox command

- section: Mailbox
- relevance: 5 - the return value and the output size are both misread

What does `cxl_internal_send_cmd()` return on success and for each kind of failure according to
its body, not its comment, what do the output size and minimum output size fields of the command
mean on entry and on return, and what must the transport callback never return? Start from
`struct cxl_mbox_cmd`.

## cxl.mbox-background: Background commands

- section: Mailbox
- relevance: 4 - sanitize is the exception and it blocks other paths

When the PCI transport runs a command that the device executes in the background, which lock is
held while it waits, and what ends the wait? Start from `__cxl_pci_mbox_send_cmd()`.

## cxl.mbox-sanitize: Sanitize in progress

- section: Mailbox
- relevance: 4 - a sanitize that is still running makes other commands fail, and no caller waits for it to end

How does the PCI transport handle a sanitize command differently from the other commands that the
device executes in the background? What does a sanitize that is still running block, and how does
user space learn that it has finished? Start from `cxl_mbox_sanitize_work()` and
`__cxl_pci_mbox_send_cmd()`.

## cxl.mbox-user-commands: Commands from user space

- section: Mailbox
- relevance: 4 - the checks are the security boundary of the ioctl

What does `cxl_validate_cmd_from_user()` check before the ioctl path sends a user's command, and
what error does each refusal return? Who sets commands exclusive and under which lock, and what
gates raw commands? Start from `cxl_validate_cmd_from_user()` and `set_exclusive_cxl_commands()`.

# The mock build and other builds

## cxl.mock-build: Mock build and wrapped symbols

- section: The mock build and other builds
- relevance: 5 - a new core file or a changed prototype breaks this build, not the normal one

What stands in for a driver under `drivers/cxl/` that `tools/testing/cxl/Kbuild` does not rebuild?
How does that file redirect a call from the rebuilt CXL modules to the mock, and how does the
wrapper fall back to the real function? Start from `struct cxl_mock_ops` and
`tools/testing/cxl/test/mock.c`.

## cxl.mock-build-upkeep: Mock build upkeep

- section: The mock build and other builds
- relevance: 5 - a new core file or a changed prototype breaks this build, not the normal one

What must a patch also change in the mock build when it adds a source file to
`drivers/cxl/core/Makefile`, when it changes the prototype of a redirected function, and when it
redirects one more function? Start from `tools/testing/cxl/Kbuild` and
`tools/testing/cxl/test/mock.c`.

## cxl.change-checklist: Build variants and ABI

- section: The mock build and other builds
- relevance: 4 - the things a diff to the core does not show

Where are the stubs that stand in for each part of the CXL core that can be configured out, which
a change has to keep in step so that a build without that part still succeeds? Where are the trace
events and the sysfs ABI document that a change to a structure or an attribute also has to keep in
step? Start from `drivers/cxl/Kconfig` and `drivers/cxl/core/Makefile`.

# Model gaps

## cxl.model-gaps: Other mistakes models make

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

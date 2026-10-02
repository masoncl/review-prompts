# Questions: GICv5

- guide: gic-v5.md
- title: GICv5

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/gic-v5-measurement.md` is the
wider set the readers were measured on and `catalogue/gic-v5-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## gicv5.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## gicv5.core-files: Core files

- section: Finding your way
- relevance: 4 - the driver is five files and the KVM side is spread wider

A table and nothing else, job to file: the GICv5 host driver and its IRS, ITS
and IWB parts; the shared register and table definitions; the GIC
system-instruction and barrier macros; the code shared with the GICv3 ITS for
MSI parents; KVM's GICv5 support at EL1 and at hyp; the device tree bindings;
the KVM device documentation; the selftests. Where a reader is likely to look
for a file that does not exist in this tree, say so in the row. Start from
`drivers/irqchip/irq-gic-v5.c`.

## gicv5.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to the function to start reading from: probe
from device tree; probe from ACPI; bring up a CPU's interface; take an
interrupt; allocate an LPI; configure an SPI's trigger; register a device with
an ITS; map an event to an LPI; enable an IWB wire. Give the current name where
a reader is likely to reach for another. Do not describe what the functions do
inside.

## gicv5.kvm-entry-points: KVM entry points

- section: Finding your way
- relevance: 4 - the common vgic code branches in a dozen places

A table and nothing else, job to the GICv5-specific function KVM calls and
where it is called from: probe; create the device; initialise; reset a vCPU;
load and put a vCPU; flush state before entry; save and fold state after exit;
check for a pending interrupt.

# Interrupt IDs, domains and chips

## gicv5.components: System components

- section: Interrupt IDs, domains and chips
- relevance: 5 - nothing else makes sense on the older GIC model

Which hardware components make up a GICv5 system as this driver models it, and which of them must
be present for the driver to probe? Which component does the work that the distributor and the
redistributors do in earlier GICs? Start from `gicv5_of_init()`.

## gicv5.typed-id-usage: Typed IDs and bare IDs

- section: Interrupt IDs, domains and chips
- relevance: 5 - the wrong form indexes the wrong element

Where are the type and ID fields of a GICv5 interrupt ID and the macros that take them apart
defined? What are the requirements for code that is handed a GICv5 interrupt ID in order to assure
safe usage: where must it use the full typed ID and where the bare ID within the type? Name
in-tree code on the host and in KVM that converts between the two. Start from
`include/linux/irqchip/arm-gic-v5.h`.

## gicv5.hwirq-meaning: Hardware IRQ numbers per domain

- section: Interrupt IDs, domains and chips
- relevance: 4 - differs in every domain

What does the `hwirq` of an `irq_data` hold in each irqdomain that the GICv5 drivers create? Where
is the value built and where is it taken apart, and what does the ITS chip put in an MSI message?

## gicv5.irq-domains: Interrupt domains

- section: Interrupt IDs, domains and chips
- relevance: 4 - the hierarchy decides where a callback lands

Which irqdomains does the GICv5 host driver create and which is parent of which, when is
`gicv5_init_lpi_domain()` called, and which domains carry a bus token that a lookup has to match?
Start from `gicv5_init_domains()` and `gicv5_init_lpi_domain()`.

## gicv5.chip-operations: Chip operations per interrupt kind

- section: Interrupt IDs, domains and chips
- relevance: 4 - which callback exists decides what a consumer can do

Which of the irqchip callbacks for trigger type, affinity, irqchip state and retrigger are absent
or do nothing in `gicv5_ppi_irq_chip`, `gicv5_spi_irq_chip`, `gicv5_lpi_irq_chip` and
`gicv5_its_irq_chip`, and which flow handler does each kind of interrupt get? How does the driver
make an SPI or LPI pending from software? Start from `gicv5_ppi_irq_chip`.

## gicv5.ipis: Inter-processor interrupts

- section: Interrupt IDs, domains and chips
- relevance: 4 - nothing like the older SGIs

What kind of interrupt backs an inter-processor interrupt on GICv5, through which domain and chip
are they allocated and how many, and how is one sent? Start from `gicv5_smp_init()` and
`gicv5_ipi_send_single()`.

## gicv5.lpi-allocation: LPI number allocation

- section: Interrupt IDs, domains and chips
- relevance: 3 - one allocator feeds IPIs and MSIs

What bounds the number of LPIs that `alloc_lpi()` hands out, and what does it return when the
interrupt state table was never set up? What does `gicv5_lpi_config_reset()` set for a fresh LPI,
and what does it leave as it was? Start from `alloc_lpi()` and `gicv5_lpi_config_reset()`.

## gicv5.domain-alloc-unwind: LPI domain allocation unwind

- section: Interrupt IDs, domains and chips
- relevance: 3 - partial unwinds have leaked LPIs

When `gicv5_irq_lpi_domain_alloc()` fails part way through allocating several interrupts, what
does it undo for the interrupt in flight and for the ones already set up? What are the
requirements for the error path of a domain allocation loop in order to assure safe usage? Start
from `gicv5_irq_lpi_domain_alloc()`.

## gicv5.fwspec-translate: Firmware specifier translation

- section: Interrupt IDs, domains and chips
- relevance: 3 - two firmware formats share one function

How does the driver turn a firmware interrupt specifier into a hardware number
and trigger type for a device tree node and for an ACPI-created fwnode, how is
the trigger of a PPI decided, and how does the core pick between the PPI and
SPI domains that share one firmware node? Start from
`gicv5_irq_domain_translate()` and `gicv5_irq_ppi_domain_select()`.

## gicv5.set-affinity: Interrupt affinity

- section: Interrupt IDs, domains and chips
- relevance: 3 - the target is not an MPIDR

When an SPI or LPI is routed to a CPU, how is the target chosen from the mask
and turned into the value the hardware wants, what does the callback return to
the core, and what does it do for a CPU the hardware has no value for? Start
from `gicv5_iri_irq_set_affinity()`.

# Instructions, barriers and the interrupt path

## gicv5.gic-instructions: GIC system instructions

- section: Instructions, barriers and the interrupt path
- relevance: 5 - configuration is instructions, not register writes

Which GIC system instructions does this tree define and use, what does each do
in a line, and through which macros are they issued? A table. Start from
`gic_insn()` in `arch/arm64/include/asm/sysreg.h`.

## gicv5.ack-sequence: Acknowledge and dispatch

- section: Instructions, barriers and the interrupt path
- relevance: 5 - each step and barrier is there for a reason

Between acknowledging an interrupt and calling the per-domain handler, which barriers does
`gicv5_handle_irq()` issue and what do the comments say each is for? What does it do when the
acknowledge returns no valid interrupt? What does `handle_irq_per_domain()` do when the type is
unknown or no handler is mapped for the ID? Start from `gicv5_handle_irq()` and
`handle_irq_per_domain()`.

## gicv5.priority-drop: Priority drop

- section: Instructions, barriers and the interrupt path
- relevance: 5 - in the wrong place it blocks every other interrupt

Where in the interrupt path is the priority drop issued relative to the handler
and to the deactivate, which instruction does it, and what reason does the code
give? Is the drop tied to a specific interrupt ID?

## gicv5.forwarded-ppi-eoi: Forwarded PPIs

- section: Instructions, barriers and the interrupt path
- relevance: 4 - the missing deactivate is deliberate

How is a PPI marked as forwarded to a vCPU, what changes in its
end-of-interrupt handling once it is, and who is then expected to deactivate
it? Start from `gicv5_ppi_irq_set_vcpu_affinity()`.

## gicv5.mask-sync: Synchronisation after mask and unmask

- section: Instructions, barriers and the interrupt path
- relevance: 5 - lazy disable depends on it, and PPIs follow another rule

What synchronisation follows disabling and what follows enabling an SPI or
LPI, what follows each for a PPI, and what reason do the comments give for
every difference? Start from `gicv5_iri_irq_mask()`, `gicv5_iri_irq_unmask()`,
`gicv5_ppi_irq_mask()` and `gicv5_ppi_irq_unmask()`.

## gicv5.state-query: Reading SPI and LPI state

- section: Instructions, barriers and the interrupt path
- relevance: 4 - a stale read returns the previous query's answer

When `gicv5_iri_irq_get_irqchip_state()` reads the pending or active state of an SPI or LPI, what
synchronisation comes before the result is read from `SYS_ICC_ICSR_EL1`? What are the requirements
for host code between issuing the query and reading the result in order to assure safe usage, and
how does KVM keep host and guest from seeing each other's value? Start from
`gicv5_iri_irq_get_irqchip_state()` and `struct vgic_v5_cpu_if`.

## gicv5.barrier-usage: Completion of GIC operations

- section: Instructions, barriers and the interrupt path
- relevance: 5 - a missing or wrong barrier is invisible in a diff

Which GICv5-specific barriers does the tree define, and what does each guarantee to the code that
follows it? What are the requirements for a barrier after a write to a GIC system register or
after a GIC system instruction in order to assure safe usage? Start from `gsb_sys()`.

## gicv5.eoi-usage: End-of-interrupt callbacks

- section: Instructions, barriers and the interrupt path
- relevance: 5 - the older combined EOI does not exist

What are the requirements for priority drop and deactivation in an `irq_eoi` callback or in a new
handler on GICv5 in order to assure safe usage? What do the `irq_eoi` callbacks of
`gicv5_ppi_irq_chip`, `gicv5_spi_irq_chip` and `gicv5_lpi_irq_chip` do? Start from
`gicv5_hwirq_eoi()`.

# CPU interface and PPIs

## gicv5.priorities: Interrupt priorities

- section: CPU interface and PPIs
- relevance: 4 - one priority for everything is why priority drop matters

Which priority does the GICv5 driver give the interrupts it sets up, and how is the value derived
from the number of priority bits the CPU interface and the IRS implement? Where is it programmed
for PPIs, for SPIs and LPIs, and as the CPU's priority mask? Start from `GICV5_IRQ_PRI_MI`.

## gicv5.cpuif-enable: CPU interface bring-up

- section: CPU interface and PPIs
- relevance: 3 - runs on every CPU that comes online

When a CPU's GICv5 interface is brought up, and when probing fails and it is disabled again, which
register writes are followed by synchronisation and which are not? What are the requirements for a
register write added to `gicv5_cpu_enable_interrupts()` or `gicv5_cpu_disable_interrupts()` in
order to assure safe usage? Start from `gicv5_cpu_enable_interrupts()`,
`gicv5_cpu_disable_interrupts()` and `gicv5_starting_cpu()`.

## gicv5.ppi-trigger: PPI trigger type

- section: CPU interface and PPIs
- relevance: 4 - a set-type callback that sets nothing

Can software configure whether a PPI is edge or level? What does the PPI
chip's set-type callback do and return, and where does the reported trigger
come from? Start from `gicv5_ppi_irq_set_type()`.

## gicv5.ppi-register-banks: PPI register banks

- section: CPU interface and PPIs
- relevance: 4 - register and bit are computed separately

How many PPIs does each enable, pending, active and handling-mode register cover, and how many
does each priority register cover? Which registers set and which clear a pending or active bit?
What are the requirements for computing the register and the bit or field for a given PPI in order
to assure safe usage? Start from `read_ppi_sysreg_s()`.

## gicv5.id-decode-fallbacks: ID register decoding

- section: CPU interface and PPIs
- relevance: 3 - only some encodings are defined

What do `gicv5_set_cpuif_pribits()`, `gicv5_set_cpuif_idbits()` and `irs_setup_pri_bits()` do for
a field encoding they do not know? What are the requirements for code that decodes an ID register
field or turns one into a `bool` in order to assure safe usage? Start from
`gicv5_set_cpuif_pribits()`, `gicv5_set_cpuif_idbits()` and `irs_setup_pri_bits()`.

# IRS probing and registers

## gicv5.init-order: Probe order

- section: IRS probing and registers
- relevance: 4 - each step depends on the one before

After the IRSs are found, what does the common initialisation rely on having
been done already, what does it tear down itself on a failure and what is left
to its callers, and where does the device tree path differ from the ACPI path?
Start from `gicv5_init_common()`, `gicv5_of_init()` and `gic_acpi_init()`.

## gicv5.iaffid-mapping: CPU affinity IDs

- section: IRS probing and registers
- relevance: 4 - routing and CPU registration both need it

What is an interrupt affinity ID, how does the driver learn each CPU's from
device tree and from ACPI and where is it stored, and what do lookups return
for a CPU that has none? Start from `gicv5_irs_cpu_to_iaffid()`.

## gicv5.cpu-registration: CPU registration with an IRS

- section: IRS probing and registers
- relevance: 3 - a select then program sequence with two waits

What does the driver program in the IRS when a CPU comes online and which
completion waits follow, which errors can it return, and which CPU hotplug
state runs it? Start from `gicv5_irs_register_cpu()`.

## gicv5.spi-ownership: SPI ranges and chip data

- section: IRS probing and registers
- relevance: 4 - a pointer that can be NULL is stored as chip data

How does the driver know which IRS owns an SPI, and what does it store as chip data for an SPI
that no IRS claims? What are the requirements for code that reads the chip data of an SPI in order
to assure safe usage? Start from `gicv5_irs_lookup_by_spi_id()`.

## gicv5.irs-id-registers: First-IRS assumptions

- section: IRS probing and registers
- relevance: 3 - what is read once is assumed to hold for every IRS

Which system-wide properties does `gicv5_irs_init()` read from the ID registers of one IRS and
apply to all of them, and which IRS is that? Does the driver check that a later IRS reports the
same values? Start from `GICV5_IRS_IDR0` and `gicv5_irs_init()`.

## gicv5.irs-memory-attributes: IRS memory attributes

- section: IRS probing and registers
- relevance: 3 - programmed once, before anything is valid

Which cacheability and shareability attributes does the driver program into an
IRS for a coherent and for a non-coherent system, when relative to enabling the
IRS and publishing tables, and when does the driver disable an IRS again?

## gicv5.irs-sync: IRS sync operation

- section: IRS probing and registers
- relevance: 3 - the IRS has a sync and no invalidate

What does `gicv5_irs_syncr()` do and return, and which IRS does it address when there are several?
Does the driver write any IRS register that invalidates cached state?

## gicv5.idle-and-valid: Idle and valid status bits

- section: IRS probing and registers
- relevance: 4 - the missing validity check is deliberate in one place

Which status register does each helper that waits for an IRS register write to complete read,
which of the helpers also test that the selected object is valid, and what error does a failed
test produce? Start from `gicv5_irs_wait_for_irs_pe()` and `gicv5_irs_wait_for_spi_op()`.

## gicv5.select-program-usage: Selector register sequences

- section: IRS probing and registers
- relevance: 5 - two CPUs interleaving configure the wrong object

What are the requirements for a write to an IRS selector register and the configuration access
that follows it in order to assure safe usage? Which lock does `gicv5_spi_irq_set_type()` hold
around `GICV5_IRS_SPI_SELR`, and what serialises the accesses to `GICV5_IRS_PE_SELR`? Start from
`gicv5_spi_irq_set_type()`.

## gicv5.timeout-handling: Poll timeout handling

- section: IRS probing and registers
- relevance: 4 - a dropped error leaves a half-published table

What do `gicv5_wait_for_op()` and `gicv5_wait_for_op_atomic()` return when a completion poll times
out? What are the requirements for a caller in the GICv5 drivers that gets that error, in order to
assure safe usage? Name in-tree code that shows it.

## gicv5.firmware-value-handling: Bad firmware values

- section: IRS probing and registers
- relevance: 3 - a backtrace for a firmware bug is the wrong response

What does `gicv5_irs_of_init_affinity()` do for a CPU entry of the device tree that it cannot use:
which faults end the probe, and which entries are skipped? What are the requirements for reporting
a bad firmware-provided value, in order to assure safe usage?

# Interrupt state table

## gicv5.ist-overview: IRS that programs the IST

- section: Interrupt state table
- relevance: 4 - where LPI state lives

Is there one interrupt state table per IRS or one for the system, which IRS's
registers are used to set it up and to map level 2 tables later, and who writes
its contents once it is published? Start from `gicv5_irs_init_ist()`,
`gicv5_irs_iste_alloc()` and `gicv5_irs_enable()`.

## gicv5.lpi-id-bits: LPI ID bits and layout

- section: Interrupt state table
- relevance: 4 - three caps are applied in turn

How is the number of LPI ID bits programmed into the IRS computed from the ID registers of the IRS
and of the CPU interface, what decides between a linear and a two-level table, and how does the
number reach the LPI allocator? Start from `gicv5_irs_init_ist()` and `gicv5_irs_l2_sz()`.

## gicv5.ist-publish: Publishing the table base

- section: Interrupt state table
- relevance: 3 - the order of writes is the contract with the IRS

In what order must the steps come by which `gicv5_irs_init_ist_linear()` or
`gicv5_irs_init_ist_two_level()` hands the interrupt state table to the IRS, what is freed when
the wait fails, and what does `gicv5_irs_init_ist()` do if the IRS already has a valid table?

## gicv5.iste-alloc: Level 2 table allocation

- section: Interrupt state table
- relevance: 4 - runs on every LPI allocation

When does `gicv5_irs_iste_alloc()` allocate a level 2 interrupt state table, and what does it
write to the level 1 entry and to which register before it waits? What serialises concurrent
calls? Start from `gicv5_irs_iste_alloc()`.

## gicv5.hw-written-readback: Reading memory the IRS wrote

- section: Interrupt state table
- relevance: 4 - an invalidate in the wrong place is useless

When the driver later reads a table entry that the IRS has updated, what cache
maintenance is needed on a non-coherent system, where must it sit relative to
the completion poll, and what orders the two? Start from
`gicv5_irs_ist_synchronise()`.

## gicv5.ist-sizing: Table sizing arithmetic

- section: Interrupt state table
- relevance: 4 - a shift that wraps allocates nothing

How are the sizes of the linear table and of the level 1 table computed, and what floor and what
ceiling apply? What are the requirements for the C types in shift-based size arithmetic such as
this in order to assure safe usage? Start from `gicv5_irs_init_ist_linear()` and
`gicv5_irs_init_ist_two_level()`.

## gicv5.ist-valid-bit: Level 1 entry valid bit

- section: Interrupt state table
- relevance: 5 - the obvious fix of setting it is the bug

Who sets the valid bit of a level 1 interrupt state table entry, software or the IRS, and what
does the driver write to the entry? What are the requirements for driver code that writes or tests
a level 1 entry in order to assure safe usage?

## gicv5.noncoherent-maintenance: Non-coherent cache maintenance

- section: Interrupt state table
- relevance: 4 - both arms have to be kept

What does the driver do after writing table memory that an IRS or ITS will read, on a coherent and
on a non-coherent system, and how does it know which it is? What are the requirements for a new
write to such table memory in order to assure safe usage? Start from `IRS_FLAGS_NON_COHERENT` and
`gicv5_its_dcache_clean()`.

# ITS entries and publishing

## gicv5.its-config-model: ITS configuration model

- section: ITS entries and publishing
- relevance: 5 - looking for a command queue finds nothing

How does the driver in `drivers/irqchip/irq-gic-v5-its.c` tell a GICv5 ITS about a device or an
event mapping, and what are the steps of making one change visible to the ITS? Does the driver
have a command queue?

## gicv5.its-valid-bits: ITS table valid bits

- section: ITS entries and publishing
- relevance: 5 - the opposite of the interrupt state table

Who sets the valid bit in ITS device table and translation table entries,
software or the ITS, and which functions set and clear it at each level? How
does this compare with the interrupt state table?

## gicv5.its-invalidate: ITS cache invalidation and sync

- section: ITS entries and publishing
- relevance: 4 - invalidate and sync answer different questions

When the driver invalidates the ITS's cached copy of an event's translation or
of a device's entry, which registers are written in which order and what is
waited for afterwards? How does that wait differ from the ITS sync operation in
the register used, its scope and where it is called? Start from
`gicv5_its_itt_cache_inv()`, `gicv5_its_device_cache_inv()`,
`gicv5_its_cache_sync()` and `gicv5_its_syncr()`.

## gicv5.its-locking: ITS locking

- section: ITS entries and publishing
- relevance: 4 - most sequences rely on a lock taken elsewhere

Which locks does the GICv5 ITS driver take and what does each protect? What serialises
`gicv5_its_itt_cache_inv()`, `gicv5_its_device_cache_inv()` and updates to a device's event bitmap
on every path that reaches them?

## gicv5.its-publish-usage: Changing an ITS table entry

- section: ITS entries and publishing
- relevance: 5 - a mapping the ITS never sees drops every event

What does `its_write_table_entry()` do, and what does it leave for the caller to do afterwards?
What are the requirements for code that changes a device table or translation table entry in order
to assure safe usage? Start from `its_write_table_entry()`.

## gicv5.its-entry-endianness: Table entry byte order

- section: ITS entries and publishing
- relevance: 4 - wrong only on big-endian

In which byte order are interrupt state, device and translation table entries stored, and which C
type holds them? What are the requirements for code that reads or tests a field of an entry in
order to assure safe usage, and which tool checks them?

# ITS devices and tables

## gicv5.its-device-lifetime: Device allocation and teardown

- section: ITS devices and tables
- relevance: 3 - the MSI core drives it

Which lock covers creating and destroying an ITS device? What does `gicv5_its_msi_prepare()` do
when the device ID is already registered, and what does `gicv5_its_msi_teardown()` check before it
tears a device down? Start from `gicv5_its_msi_prepare()` and `gicv5_its_msi_teardown()`.

## gicv5.its-devtab-choice: Device table structure

- section: ITS devices and tables
- relevance: 3 - the chosen layout is kept for every later lookup

How does `gicv5_its_init_devtab()` choose between a linear and a two-level device table, and what
cap applies to the number of device ID bits? When is a level 2 device table allocated, and is it
ever freed? Start from `gicv5_its_init_devtab()`, `gicv5_its_l2sz_two_level()` and
`gicv5_its_alloc_l2_devtab()`.

## gicv5.its-itt-choice: Translation table structure

- section: ITS devices and tables
- relevance: 3 - not built the way the device table is

How does the driver choose between a linear and a two-level translation table for a device, and
when does `gicv5_its_create_itt_two_level()` allocate the level 2 tables? What are the
requirements for the loop that frees them on failure in order to assure safe usage? Start from
`gicv5_its_create_itt_two_level()`.

## gicv5.its-device-register: Registering a device

- section: ITS devices and tables
- relevance: 4 - the full write, invalidate, undo pattern

Which checks can make registering a device with an ITS fail and with which
error, what must be in place before the device table entry is made valid, and
what is undone when the final invalidation fails? Start from
`gicv5_its_device_register()`.

## gicv5.its-device-unregister: Unregistering a device

- section: ITS devices and tables
- relevance: 3 - order of free and invalidate

In what order does unregistering a device clear the device table entry, free
the translation table memory and invalidate the ITS cache? Is the memory freed
before or after the invalidation completes, and what is done if the
invalidation fails? Start from `gicv5_its_device_unregister()`.

## gicv5.its-init: ITS initialisation

- section: ITS devices and tables
- relevance: 3 - attributes before tables before enable

When one ITS is brought up, what must be programmed before its tables and what
before it is enabled, what is done if firmware left the ITS enabled, and what
is undone at each failure? Start from `gicv5_its_init_bases()`.

## gicv5.its-noncoherent-flag: ITS coherency flag

- section: ITS devices and tables
- relevance: 3 - a parameter and a property are both in play

From what does the ITS initialisation decide that an ITS is non-coherent, on
the device tree path and on the ACPI path? Read the body of
`gicv5_its_init_bases()` and say what it actually tests.

# ITS interrupts and MSIs

## gicv5.its-msi-parent: MSI parent operations

- section: ITS interrupts and MSIs
- relevance: 3 - lives in a file shared with the older ITS

How do `its_v5_pci_msi_prepare()` and `its_v5_pmsi_prepare()` find a device's device ID and the
translate frame address, under device tree and under ACPI? What do they put in the scratchpad
slots of the allocation info, and what does `gicv5_its_msi_prepare()` replace it with? Start from
`gic_v5_its_msi_parent_ops`, `its_v5_pci_msi_prepare()` and `its_v5_pmsi_prepare()`.

## gicv5.its-eventid-alloc: Event ID allocation

- section: ITS interrupts and MSIs
- relevance: 3 - the IWB depends on the fixed case

How are event IDs allocated and freed within a device, for ordinary MSIs and
for allocations that ask for fixed message data, and which errors are possible?
Start from `gicv5_its_alloc_eventid()`.

## gicv5.its-domain-alloc: ITS domain allocation

- section: ITS interrupts and MSIs
- relevance: 4 - three resources to release on failure

When `gicv5_its_irq_domain_alloc()` allocates interrupts, where do the parent LPIs come from,
which of its steps can fail, and what does it release on each failure? Start from
`gicv5_its_irq_domain_alloc()`.

## gicv5.its-activate: Mapping and unmapping events

- section: ITS interrupts and MSIs
- relevance: 4 - there is no unmap command

At which point in an interrupt's life is its event mapped to its LPI in the
translation table and unmapped again, what does each write to the entry, and
what does mapping return if the entry is already valid? Start from
`gicv5_its_map_event()`.

## gicv5.its-domain-free: ITS domain free

- section: ITS interrupts and MSIs
- relevance: 5 - a reused LPI can receive its previous owner's event

Which synchronisation operations does `gicv5_its_irq_domain_free()` end with, and what do they
guarantee? What are the requirements for releasing an LPI or an event ID for reuse in order to
assure safe usage? Start from `gicv5_its_irq_domain_free()`.

# Interrupt wire bridge

## gicv5.iwb-overview: IWB device MSI domain

- section: Interrupt wire bridge
- relevance: 4 - wires do not become SPIs

How does the interrupt of a wire on an interrupt wire bridge reach a CPU, and what does
`gicv5_iwb_device_probe()` create for each bridge? How does a wire number become an event ID?
Start from `gicv5_iwb_device_probe()` and `iwb_msi_template`.

## gicv5.iwb-enable: Wire enable and trigger mode

- section: Interrupt wire bridge
- relevance: 3 - enabling a wire is not unmasking the interrupt

How does enabling and disabling an IWB wire differ from masking and unmasking
its interrupt, what is waited for after the enable and the trigger mode
registers are written, and is an error from the wait acted on? Start from
`__gicv5_iwb_set_wire_enable()` and `gicv5_iwb_set_type()`.

## gicv5.iwb-probe: IWB probe requirements

- section: Interrupt wire bridge
- relevance: 3 - firmware has to have enabled it

What must firmware have done to an IWB before the driver will use it, what does
the driver program at probe, and how does it learn the number of wires? Start
from `gicv5_iwb_init_bases()`.

## gicv5.iwb-translate: IWB specifier translation

- section: Interrupt wire bridge
- relevance: 3 - ACPI packs the bridge and the wire into one number

How does the IWB domain translate a device tree specifier and an ACPI one into a
wire number and trigger? How is an ACPI global interrupt number recognised as
belonging to an IWB, and how are the bridge and the wire packed into it? Start from
`gicv5_iwb_irq_domain_translate()` and `gic_v5_get_gsi_domain_id()`.

# Firmware, boot and CPU capabilities

## gicv5.acpi-model: ACPI interrupt model

- section: Firmware, boot and CPU capabilities
- relevance: 3 - how a GSI finds its domain

How does the ACPI probe register GICv5 as the interrupt model, which MADT
entries does it walk for the IRS, for the ITS and for each CPU's affinity ID,
and how does a global interrupt number find its irqdomain? Start from
`gic_acpi_init()`.

## gicv5.boot-requirements: Boot requirements

- section: Firmware, boot and CPU capabilities
- relevance: 3 - a trap left armed breaks the host at EL1

What must be set up at EL2 or by firmware before the kernel is entered at EL1 on
a GICv5 system, according to the boot protocol document, and what does the
kernel do itself when it is entered at EL2? Start from
`Documentation/arch/arm64/booting.rst` and `__init_el2_gicv5`.

## gicv5.cpucaps: CPU capabilities

- section: Firmware, boot and CPU capabilities
- relevance: 4 - the capability type decides when it may be tested

Which arm64 CPU capabilities describe GICv5, and of which capability type is each? What are the
requirements for testing them with `this_cpu_has_cap()`, `cpus_have_cap()` or
`cpus_have_final_cap()` in order to assure safe usage? Start from
`arch/arm64/kernel/cpufeature.c`.

# KVM scope and probing

## gicv5.kvm-scope: KVM GICv5 support

- section: KVM scope and probing
- relevance: 5 - what is not there matters as much as what is

Which kinds of interrupt can a guest of KVM's GICv5 device have, and what does `vgic_get_irq()`
return for a non-private interrupt of a GICv5 guest? Start from
`Documentation/virt/kvm/devices/arm-vgic-v5.rst`, `vgic_v5_init()` and `struct gicv5_vpe`.

## gicv5.kvm-feature-coverage: Feature coverage of the device

- section: KVM scope and probing
- relevance: 5 - a patch that relies on a feature the device lacks fails only when a guest runs

Does KVM's GICv5 device support nested virtualisation, protected KVM, and saving and restoring
state to userspace? If a feature is absent, say so in a line. Start from
`Documentation/virt/kvm/devices/arm-vgic-v5.rst` and `vgic_v5_init()`.

## gicv5.kvm-info-handoff: Handing the GIC to KVM

- section: KVM scope and probing
- relevance: 4 - decides whether KVM gets a vgic at all

How does the irqchip driver tell KVM that the host has a GICv5, and under which conditions does it
publish nothing? Is this done on the ACPI path too? Start from `gic_of_setup_kvm_info()` and
`kvm_vgic_hyp_init()`.

## gicv5.vgic-probe: KVM probe

- section: KVM scope and probing
- relevance: 4 - two devices are registered independently

Which device types does `vgic_v5_probe()` register and under which conditions
is each skipped, when does it return an error, and how is the maximum number of
vCPUs decided?

## gicv5.compat-mode: GICv3 guests on GICv5

- section: KVM scope and probing
- relevance: 4 - only the virtual CPU interface is in hardware

When KVM runs a GICv3 guest on a GICv5 host, what hardware feature is needed and which flag
records it? Which vgic code then runs the guest, and how does it deactivate a physical interrupt?

## gicv5.compat-mode-switch: Leaving compatibility mode

- section: KVM scope and probing
- relevance: 4 - the same register has two layouts

Which control selects between the GICv3-compatible and the native GICv5 virtual CPU interface, and
where does KVM write it before it loads native state? What are the requirements for a write to a
GICv5-layout hypervisor register in order to assure safe usage? Start from
`__vgic_v5_restore_vmcr_apr()`.

## gicv5.kvm-create: KVM device creation

- section: KVM scope and probing
- relevance: 3 - the timers are initialised twice

When `kvm_vgic_create()` creates a GICv5 device, what vCPU limit applies and how are the private
interrupts allocated? Which guest-visible ID register fields does `kvm_vgic_finalize_idregs()` set
for it? Start from `kvm_vgic_create()` and `kvm_vgic_finalize_idregs()`.

## gicv5.kvm-create-timers: Timer setup at creation

- section: KVM scope and probing
- relevance: 3 - timer state set before the device exists may not fit a GICv5 guest

Does `kvm_vgic_create()` change the state of the arch timers when it creates a GICv5 device, and
if so what does it set? Start from `kvm_vgic_create()`.

# KVM interrupt IDs and PPI state

## gicv5.kvm-intid-helpers: KVM interrupt ID helpers

- section: KVM interrupt IDs and PPI state
- relevance: 4 - callers must build the typed form themselves

What form of interrupt number does KVM require from an in-kernel user that raises an interrupt for
a GICv5 guest: the typed ID or the bare ID? Which macros in `include/kvm/arm_vgic.h` build one and
take it apart? Name in-tree code in the timer or PMU code that shows it.

## gicv5.kvm-type-predicates: Interrupt type predicates

- section: KVM interrupt IDs and PPI state
- relevance: 5 - whether a predicate bounds the ID decides if an index is safe

What do the KVM predicates for SGI, PPI, SPI and LPI test for a GICv5 guest: the
type field, a bound on the ID, or both? Which of them can be relied on as a
bounds check before indexing per-interrupt state? Start from `__irq_is_ppi()` in
`include/kvm/arm_vgic.h`.

## gicv5.kvm-private-lookup: Private interrupt lookup

- section: KVM interrupt IDs and PPI state
- relevance: 4 - every per-PPI path goes through it

How does `vgic_get_vcpu_irq()` get from a GICv5 PPI's interrupt ID to its `struct vgic_irq`, and
what does it return for an ID that is out of range? How many PPIs does KVM support for a guest?
Start from `vgic_get_vcpu_irq()` and `vgic_v5_setup_private_irq()`.

## gicv5.kvm-ppi-masks: PPI masks and iteration

- section: KVM interrupt IDs and PPI state
- relevance: 4 - four bitmaps with four owners

Which bitmaps of GICv5 PPIs does KVM keep, and for each, where is it stored and who computes it
and when? Give the answer as a table. What are the requirements for a new loop over the PPIs of a
guest in order to assure safe usage: which iterator and over which mask? Start from `struct
vgic_v5_vm` and `for_each_visible_v5_ppi()`.

## gicv5.kvm-state-placement: Shadow and hardware state

- section: KVM interrupt IDs and PPI state
- relevance: 4 - two copies to reconcile on every entry and exit

Where does the state of a GICv5 guest's PPIs live while the guest runs and while
it does not, and which of the two copies is current at load, at entry, at exit
and at put? Start from `struct vgic_v5_cpu_if` and the GICv5 member of
`struct kvm_host_data`.

## gicv5.kvm-irq-ops: Per-interrupt operations

- section: KVM interrupt IDs and PPI state
- relevance: 4 - PPIs bypass the pending list entirely

Which operations of `struct irq_ops` does GICv5 support set, and for which interrupts? What does
`vgic_v5_ppi_queue_irq_unlock()` do with a pending GICv5 PPI, and does it put the interrupt on a
list? Start from `struct irq_ops` and `vgic_v5_ppi_queue_irq_unlock()`.

## gicv5.kvm-finalize: Finalising PPI state

- section: KVM interrupt IDs and PPI state
- relevance: 4 - per-vCPU entry point, VM-wide result

When does `vgic_v5_finalize_ppi_state()` compute the set of PPIs exposed to a guest, and under
which lock? What are the requirements for computing VM-wide state from a per-vCPU path, in order
to assure safe usage? Start from `vgic_v5_finalize_ppi_state()`.

## gicv5.kvm-userspace-ppis: PPIs driven from userspace

- section: KVM interrupt IDs and PPI state
- relevance: 3 - userspace may drive very few

Which PPIs may userspace drive for a GICv5 guest, and through which device attribute does it find
out? What does `kvm_vm_ioctl_irq_line()` check and do for a GICv5 PPI and for an SPI? Start from
`kvm_vm_ioctl_irq_line()` and `vgic_v5_set_attr()`.

## gicv5.kvm-timers: Arch timers with GICv5

- section: KVM interrupt IDs and PPI state
- relevance: 4 - the timer code changed in five places

For a GICv5 guest, which interrupt IDs do the arch timers use and may userspace
choose them, how is a directly injected timer's interrupt raised, and what
changes in the handling of the physical active state? Start from
`get_vgic_ppi()` and `kvm_timer_init_vm()`.

## gicv5.kvm-pmu: PMU interrupt with GICv5

- section: KVM interrupt IDs and PPI state
- relevance: 3 - the number is fixed and given in typed form

Which interrupt number must the PMU use for a GICv5 guest, in which form is it
given by userspace, and what happens if userspace does not set one? Start from
`KVM_ARMV8_PMU_GICV5_IRQ`.

# KVM entry and exit

## gicv5.kvm-flush: Flushing state before entry

- section: KVM entry and exit
- relevance: 5 - an edge not cleared is delivered twice

What does KVM do to each exposed PPI's shadow state when building the pending
bitmap for guest entry, how are edge and level interrupts treated differently,
and where does the bitmap go? Start from `vgic_v5_flush_ppi_state()`.

## gicv5.kvm-fold: Folding state after exit

- section: KVM entry and exit
- relevance: 5 - an assignment instead of an OR loses an edge

What does `vgic_v5_fold_ppi_state()` copy back from the hardware registers into each exposed PPI's
shadow state after a guest exit, and how are edge and level interrupts treated differently? What
are the requirements for code that moves pending state between the shadow state and the hardware
registers in order to assure safe usage? Start from `vgic_v5_fold_ppi_state()`.

## gicv5.kvm-hyp-ppi-switch: PPI register world switch

- section: KVM entry and exit
- relevance: 4 - a register walk with an order

Which hypervisor PPI registers are saved on exit and restored on entry and in
which order, what is written to the ones KVM keeps no state for, and where are
these functions called from under VHE and nVHE? Start from
`__vgic_v5_save_ppi_state()` and `__vgic_v5_restore_ppi_state()`.

## gicv5.kvm-dvi: Direct injection of PPIs

- section: KVM entry and exit
- relevance: 5 - writing pending over a directly injected PPI corrupts it

How does a PPI become directly injected for a GICv5 guest and where is that recorded, when is
direct injection switched on and off in hardware, and how does it affect the pending state written
on entry? Start from `vgic_v5_set_ppi_dvi()`.

## gicv5.kvm-load-put: Loading and putting a vCPU

- section: KVM entry and exit
- relevance: 4 - both are called twice around WFI

What do `vgic_v5_load()` and `vgic_v5_put()` do when one of them is called twice in a row, and
which flag tracks it? When are the guest's PPI priorities copied from the saved registers into the
shadow interrupt state? Start from `vgic_v5_load()` and `vgic_v5_put()`.

## gicv5.kvm-vmcr-apr: Control and active priority registers

- section: KVM entry and exit
- relevance: 4 - saved at different times by different functions

When are the virtual machine control register and the active priorities register
of a GICv5 guest saved and restored: on every entry and exit, or at load and
put? Which function does each, and which run at hyp through a hypercall? Start
from `__vgic_v5_save_state()` and `__vgic_v5_save_apr()`.

## gicv5.kvm-pending-check: Pending interrupt check

- section: KVM entry and exit
- relevance: 4 - an off-by-one here is a spurious wakeup

When KVM decides whether a GICv5 vCPU has an interrupt it should wake for, how
is the effective priority mask computed, what comparison is made against it,
and where does pending come from for a hardware-mapped interrupt? Start from
`vgic_v5_has_pending_ppi()`.

## gicv5.kvm-bitmap-atomicity: Shared bitmaps and per-interrupt locks

- section: KVM entry and exit
- relevance: 4 - a per-interrupt lock does not cover a shared word

Which lock is held when `vgic_v5_set_ppi_dvi()` changes a bit of the direct-injection bitmap, and
does that lock serialise updates to different bits of the same bitmap? What are the requirements
for the bit operation used on a bitmap indexed by interrupt in order to assure safe usage?

# KVM traps and emulated registers

## gicv5.kvm-enable-trap: PPI enable register trap

- section: KVM traps and emulated registers
- relevance: 4 - the only PPI register KVM traps writes to

What does `access_gicv5_ppi_enabler()` do with the value a guest writes to a PPI enable register,
for the first bank and for the second? Are reads trapped? Start from `access_gicv5_ppi_enabler()`.

## gicv5.kvm-fgt: Fine-grained traps for the guest

- section: KVM traps and emulated registers
- relevance: 3 - almost nothing is trapped

Which GICv5 register and instruction accesses does KVM trap from a GICv5 guest
and why, where are the trap registers computed and written, and what does a
guest without GICv5 get? Start from `kvm_vcpu_load_fgt()` and
`__activate_traps_ich_hfgxtr()`.

## gicv5.kvm-id-emulation: Emulated ID registers

- section: KVM traps and emulated registers
- relevance: 4 - KVM's limit, not the host's, is what the guest sees

What does a GICv5 guest read from the CPU interface ID register and from the affinity ID register,
and which values does `vgic_v5_reset()` set for ID bits and priority bits? What are the
requirements for a path that sets a guest-visible value that KVM has narrowed from the host's in
order to assure safe usage? Start from `access_gicv5_idr0()` and `vgic_v5_reset()`.

# Model gaps

## gicv5.model-gaps: Other mistakes models make

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

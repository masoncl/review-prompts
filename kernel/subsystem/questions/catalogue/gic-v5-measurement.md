# Questions: GICv5 (measurement set)

- guide: gic-v5.md
- title: GICv5

A wide set of questions about the GICv5 host irqchip driver (IRS, ITS, IWB and
the CPU interface) and KVM's GICv5 support, used to measure what a model
already knows before deciding what the built guide should spend its words on.
The hand-written guide it will replace is 9,439 words and was never checked
against current sources. GICv3 and GICv4, and the KVM rules the VGIC shares
with the rest of KVM, have their own sets. Run it with `build-guides.py
--no-sources --check-memory --questions` pointed at this directory. The
trimmed set a guide is built from is `../gic-v5.md`. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## gicv5.core-files: Core files

- section: Finding your way
- relevance: 4 - the driver is five files and the KVM side is spread wider
- words: 140

Which files hold the GICv5 host driver and its IRS, ITS and IWB parts, the
shared register and table definitions, the GIC system-instruction and barrier
macros, the code shared with the GICv3 ITS for MSI parents, the KVM GICv5
support at EL1 and at hyp, the device tree bindings, the KVM device
documentation and the selftests? A table. Start from
`drivers/irqchip/irq-gic-v5.c`.

## gicv5.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

For each job (probe from device tree, probe from ACPI, bring up a CPU's
interface, take an interrupt, allocate an LPI, configure an SPI's trigger,
register a device with an ITS, map an event to an LPI, enable an IWB wire),
which function do you start reading from? A table.

## gicv5.docs: Documentation in the tree

- section: Finding your way
- relevance: 3 - says what firmware owes the kernel
- words: 60

Which files under `Documentation/` describe GICv5: the firmware bindings, what
the boot loader or firmware must set up before entering the kernel, and the KVM
device? One line on what each settles.

## gicv5.components: System components

- section: Finding your way
- relevance: 5 - nothing else makes sense on the older GIC model
- words: 100

Which hardware components make up a GICv5 system as this driver models it, what
does each do, and which of them must be present for the driver to probe at all?
Say how this differs from the distributor and redistributor split of earlier
GICs. Start from `gicv5_of_init()`.

## gicv5.global-data: Global driver state

- section: Finding your way
- relevance: 3 - several files read it
- words: 100

What does `struct gicv5_chip_data` hold, which fields are written once at
probe, and where is the single instance defined? A short list of fields and who
sets each.

## gicv5.irs-chip-data: Per-IRS state

- section: Finding your way
- relevance: 3 - how a CPU or an SPI finds its IRS
- words: 80

What does `struct gicv5_irs_chip_data` hold per IRS, how are the instances
linked together, and how does the driver find the IRS that a given CPU is
attached to? Start from `drivers/irqchip/irq-gic-v5-irs.c`.

# Interrupt IDs and domains

## gicv5.intid-encoding: Interrupt ID encoding

- section: Interrupt IDs
- relevance: 5 - every interface takes one form or the other
- words: 80

How is a GICv5 interrupt ID laid out in 32 bits: which bits carry the type,
which carry the ID within the type, what are the type values, and which macros
extract each? Start from `include/linux/irqchip/arm-gic-v5.h`.

## gicv5.typed-id-usage: Typed IDs and bare IDs

- section: Interrupt IDs
- relevance: 5 - the wrong form indexes the wrong element
- words: 110

What usage of a GICv5 interrupt number is unsafe when a full typed interrupt ID
and a bare ID within the type can both be passed around, for example as an
array index, a bit position or a domain lookup key, and what that looks similar
is correct? Name in-tree code on the host and in KVM that converts between the
two.

## gicv5.hwirq-meaning: Hardware IRQ numbers per domain

- section: Interrupt IDs
- relevance: 4 - differs in every domain
- words: 110

What does the `hwirq` of an `irq_data` mean in each GICv5 domain (PPI, SPI,
LPI, IPI, ITS and IWB): a bare ID, a typed interrupt ID, an index, or a packed
value? Say where a packed value is packed and unpacked, and what the ITS chip
puts in an MSI message.

## gicv5.ppi-numbers: Architected PPI numbers

- section: Interrupt IDs
- relevance: 3 - numbers people quote from the older GICs
- words: 130

Which PPI numbers does the header define for the architected PPIs (timers, PMU,
software PPI, GIC maintenance, doorbells, debug and trace)? A table of name and
number. How many PPIs does the host PPI domain cover? Start from
`GICV5_ARCH_PPI_SW_PPI`.

## gicv5.irq-domains: Interrupt domains

- section: Domains and chips
- relevance: 4 - the hierarchy decides where a callback lands
- words: 130

Which irqdomains does the GICv5 host driver create, of what kind (linear, tree,
hierarchy) and size, which is parent of which, and which bus token does each
carry? A table. Start from `gicv5_init_domains()` and
`gicv5_init_lpi_domain()`.

## gicv5.fwspec-translate: Firmware specifier translation

- section: Domains and chips
- relevance: 3 - two firmware formats share one function
- words: 130

How does the driver turn a firmware interrupt specifier into a hardware number
and trigger type for a device tree node and for an ACPI-created fwnode: how many
cells or parameters, what each holds, how the trigger of a PPI is decided, and
how the core picks between the PPI and SPI domains that share one firmware
node? Start from `gicv5_irq_domain_translate()` and
`gicv5_irq_ppi_domain_select()`.

## gicv5.irq-dispatch: Dispatch to a domain

- section: Domains and chips
- relevance: 4 - the canonical use of type and ID
- words: 70

After an interrupt is acknowledged, how does the driver choose the domain to
hand it to, and what does it do when the type is unknown or no handler is
mapped for the ID? Start from `handle_irq_per_domain()`.

## gicv5.ipis: Inter-processor interrupts

- section: Domains and chips
- relevance: 4 - nothing like the older SGIs
- words: 100

How are inter-processor interrupts implemented on GICv5: what kind of interrupt
backs them, how many are allocated, which domain and chip they use, and how is
one sent? Does GICv5 have SGIs? Start from `gicv5_smp_init()` and
`gicv5_ipi_send_single()`.

## gicv5.lpi-allocation: LPI number allocation

- section: Domains and chips
- relevance: 3 - one allocator feeds IPIs and MSIs
- words: 60

How are LPI numbers handed out and returned, what bounds the number available,
and what happens when the interrupt state table was never set up? Start from
`alloc_lpi()`.

## gicv5.irq-chips: Interrupt chips and flow handlers

- section: Domains and chips
- relevance: 4 - which callback exists decides what a consumer can do
- words: 150

Which `struct irq_chip` instances does the host driver define, which callbacks
does each implement itself and which does it forward to its parent, which chip
flags does each set, and which flow handler is installed for each kind of
interrupt? A table. Start from `gicv5_ppi_irq_chip`.

## gicv5.domain-alloc-unwind: Allocation failure unwind

- section: Domains and chips
- relevance: 3 - partial unwinds have leaked LPIs
- words: 90

When allocating several interrupts in the LPI domain fails part way through,
what is undone for the interrupt in flight and for the ones already set up?
What usage in a domain allocation loop is unsafe here, and what is correct?
Start from `gicv5_irq_lpi_domain_alloc()`.

# The CPU interface

## gicv5.gic-instructions: GIC system instructions

- section: Instructions and barriers
- relevance: 5 - configuration is instructions, not register writes
- words: 150

Which GIC system instructions does this tree define and use, what does each do
in a line, and through which macros are they issued? A table. Start from
`gic_insn()` in `arch/arm64/include/asm/sysreg.h`.

## gicv5.insn-operands: Instruction operand layout

- section: Instructions and barriers
- relevance: 3 - one field in the wrong place addresses another interrupt
- words: 100

How is the 64-bit operand of a GIC system instruction built: which fields carry
the type, the ID and the instruction-specific value (priority, affinity,
pending, handling mode), and which masks are used? Which instruction takes no
interrupt ID at all, and which of the instructions return anything the caller
could check?

## gicv5.gsb-barriers: GIC synchronisation barriers

- section: Instructions and barriers
- relevance: 5 - the older barrier habits do not carry over
- words: 90

Which GICv5-specific barriers does the tree define, what does each guarantee
according to the comments at its call sites, where are they defined, and where
is each used? Start from `gsb_sys()`.

## gicv5.mask-unmask-sync: Masking and unmasking SPIs and LPIs

- section: Instructions and barriers
- relevance: 5 - lazy disable depends on it
- words: 90

What synchronisation follows the instruction that disables an SPI or LPI and
the one that enables it, and what reason do the comments give for any
difference? Start from `gicv5_iri_irq_mask()` and `gicv5_iri_irq_unmask()`.

## gicv5.ppi-mask-sync: Masking and unmasking PPIs

- section: Instructions and barriers
- relevance: 5 - not the same rule as for SPIs and LPIs
- words: 80

How is a PPI enabled and disabled, and what synchronisation follows each, with
what stated reason? Start from `gicv5_ppi_irq_mask()` and
`gicv5_ppi_irq_unmask()`.

## gicv5.barrier-usage: Completion of GIC operations

- section: Instructions and barriers
- relevance: 5 - a missing or wrong barrier is invisible in a diff
- words: 120

What usage is unsafe when code depends on a GIC system instruction or a write
to a PPI system register having taken effect, for example using a plain memory
barrier or no barrier, and what that looks similar is correct? Name in-tree
code for both a case that needs completion and one that does not.

## gicv5.state-query: Reading SPI and LPI state

- section: Instructions and barriers
- relevance: 4 - a stale read returns the previous query's answer
- words: 90

How does the driver read the pending or active state of an SPI or LPI: which
instruction, what synchronisation before the result is read, which register
holds the result, and how is a failed query detected? Start from
`gicv5_iri_irq_get_irqchip_state()`.

## gicv5.icsr-sharing: Sharing of the query result register

- section: Instructions and barriers
- relevance: 3 - one register serves host and guest
- words: 80

The register that receives the result of a configuration query is a single
per-CPU register. What must host code guarantee between issuing the query and
reading the result, and how does KVM keep host and guest from seeing each
other's value? Start from `struct vgic_v5_cpu_if`.

## gicv5.ack-sequence: Acknowledge sequence

- section: Handling an interrupt
- relevance: 5 - each step and barrier is there for a reason
- words: 110

List in order what the top-level handler does from acknowledging an interrupt
to calling the per-domain handler, including each barrier and what the comments
say it is for, and what happens when the acknowledge returns nothing valid.
Start from `gicv5_handle_irq()`.

## gicv5.priority-drop: Priority drop

- section: Handling an interrupt
- relevance: 5 - in the wrong place it blocks every other interrupt
- words: 80

Where in the interrupt path is the priority drop issued relative to the handler
and to the deactivate, which instruction does it, and what reason does the code
give? Is the drop tied to a specific interrupt ID?

## gicv5.eoi-usage: Priority drop and deactivate

- section: Handling an interrupt
- relevance: 5 - the older combined EOI does not exist
- words: 100

What usage is unsafe in an irqchip's end-of-interrupt callback or in a new
handler on GICv5 with respect to priority drop and deactivation, and what that
looks similar is correct? Say what the three chips' `irq_eoi` callbacks do.
Start from `gicv5_hwirq_eoi()`.

## gicv5.forwarded-ppi-eoi: Forwarded PPIs

- section: Handling an interrupt
- relevance: 4 - the missing deactivate is deliberate
- words: 70

How is a PPI marked as forwarded to a vCPU, what changes in its
end-of-interrupt handling once it is, and who is then expected to deactivate
it? Start from `gicv5_ppi_irq_set_vcpu_affinity()`.

## gicv5.lpi-retrigger: Retrigger and software pending

- section: Handling an interrupt
- relevance: 3 - LPIs here have more state than on the older ITS
- words: 90

How does the driver make an SPI or LPI pending from software, which callbacks
use that, and which irqchip states can be read and set for each kind of
interrupt? Does any GICv5 domain set the resend-while-in-progress flag on its
interrupts?

## gicv5.set-affinity: Affinity

- section: Handling an interrupt
- relevance: 3 - the target is not an MPIDR
- words: 100

How is an SPI or LPI routed to a CPU: how is the target chosen from the mask,
how is the CPU turned into the value the hardware wants, which instruction is
used, what is returned, and are interrupts single-target? Start from
`gicv5_iri_irq_set_affinity()`.

## gicv5.priorities: Interrupt priorities

- section: CPU interface setup
- relevance: 4 - one priority for everything is why priority drop matters
- words: 100

Which priority does Linux give every interrupt, how is that value derived from
the number of priority bits the CPU interface and the IRS implement, and where
is it programmed for PPIs, for SPIs and LPIs, and as the CPU's priority mask?
Start from `GICV5_IRQ_PRI_MI`.

## gicv5.cpuif-enable: CPU interface bring-up

- section: CPU interface setup
- relevance: 3 - runs on every CPU that comes online
- words: 100

List what is done to a CPU's GICv5 interface when the CPU comes up and when
probing fails and it is disabled again, in order, including which
synchronisation follows which register write. Start from
`gicv5_cpu_enable_interrupts()` and `gicv5_starting_cpu()`.

## gicv5.ppi-trigger: PPI trigger type

- section: CPU interface setup
- relevance: 4 - a set-type callback that sets nothing
- words: 80

Can software configure whether a PPI is edge or level? What does the PPI chip's
set-type callback do, where does the reported trigger come from, and which
generic trigger constants stand for edge and level? Start from
`gicv5_ppi_irq_set_type()`.

## gicv5.ppi-register-banks: PPI register banks

- section: CPU interface setup
- relevance: 4 - register and bit are computed separately
- words: 130

How are the per-PPI system registers banked: how many PPIs per enable, pending,
active and handling-mode register, how many per priority register, which
registers set and which clear a pending or active bit, and how does the code
pick the register and the bit or field for a given PPI? What usage is unsafe
when computing them? Start from `read_ppi_sysreg_s()`.

## gicv5.lpi-reset: LPI state at allocation

- section: CPU interface setup
- relevance: 3 - an LPI number is reused
- words: 60

What state does the driver program into a freshly allocated LPI before it is
used, and why? Start from `gicv5_lpi_config_reset()` and `gicv5_hwirq_init()`.

# The IRS

## gicv5.init-order: Probe order

- section: Probing
- relevance: 4 - each step depends on the one before
- words: 130

List in order what the common initialisation does after the IRSs are found, and
what is torn down at each failure point. Where does the device tree path differ
from the ACPI path? Start from `gicv5_init_common()`.

## gicv5.irs-dt-probe: IRS probe from device tree

- section: Probing
- relevance: 3 - one bad IRS does not stop the rest
- words: 110

What does probing one IRS node from device tree do, in order, which properties
and register names does it require, and what happens to the other IRSs when one
fails? Start from `gicv5_irs_of_init()`.

## gicv5.irs-acpi-probe: IRS probe from ACPI

- section: Probing
- relevance: 3 - a second firmware path to keep working
- words: 100

How are IRSs discovered from ACPI: which table entries are parsed, how big a
register window is mapped, how is the non-coherent flag conveyed, and how are
CPUs bound to an IRS? Start from `gicv5_irs_acpi_probe()`.

## gicv5.iaffid-mapping: CPU affinity IDs

- section: Probing
- relevance: 4 - routing and CPU registration both need it
- words: 100

What is an interrupt affinity ID, how does the driver learn each CPU's from
device tree and from ACPI, where is it stored, and what do lookups return for a
CPU that has none? Start from `gicv5_irs_cpu_to_iaffid()`.

## gicv5.firmware-value-handling: Bad firmware values

- section: Probing
- relevance: 3 - a backtrace for a firmware bug is the wrong response
- words: 100

How does the affinity parsing react to a malformed CPU phandle, a CPU node with
no logical CPU, and an affinity ID wider than the IRS supports: which are fatal,
which are skipped, and what is logged at which level? What usage of `WARN()` on
firmware-provided values is wrong, and what is right?

## gicv5.cpu-registration: Registering a CPU with its IRS

- section: Probing
- relevance: 3 - a select then program sequence with two waits
- words: 100

What does the driver program in the IRS when a CPU comes online, in which
order, with which completion waits, and which errors can it return? Which CPU
hotplug state runs it? Start from `gicv5_irs_register_cpu()`.

## gicv5.spi-ownership: SPI ranges

- section: Probing
- relevance: 4 - a pointer that can be NULL is stored as chip data
- words: 90

How does the driver know which IRS owns an SPI, how many SPIs exist
system-wide, and what is stored as chip data for an SPI that no IRS claims?
What follows for code that dereferences an SPI's chip data? Start from
`gicv5_irs_lookup_by_spi_id()`.

## gicv5.irs-id-registers: IRS ID register fields

- section: Probing
- relevance: 3 - each capability comes from one field
- words: 150

Which IRS ID registers and fields does the driver read, what does it use each
for, and which system-wide properties are read only from the first IRS probed,
on what assumption? A table. Start from `GICV5_IRS_IDR0` and
`gicv5_irs_init()`.

## gicv5.spi-set-type: SPI trigger configuration

- section: IRS register programming
- relevance: 4 - the worked example of select then program
- words: 90

List the register writes and waits that configure an SPI's trigger mode, which
lock is held over them, and how the four generic trigger types map to hardware.
Start from `gicv5_spi_irq_set_type()`.

## gicv5.select-program-usage: Select then program sequences

- section: IRS register programming
- relevance: 5 - two CPUs interleaving configure the wrong object
- words: 120

Some IRS registers act on whatever object a selector register last named. What
usage of such a selector and configuration pair is unsafe with respect to
locking, and what is correct? Which selector sequences in the tree take a lock,
and what serialises the ones that do not?

## gicv5.status-registers: Completion status registers

- section: IRS register programming
- relevance: 4 - each write has its own status register
- words: 140

For each IRS, ITS and IWB register the driver writes whose completion it waits
for, which status register and bit does it poll, and through which helper? A
table.

## gicv5.wait-helpers: Poll helpers

- section: IRS register programming
- relevance: 3 - two variants with different contexts
- words: 90

What do `gicv5_wait_for_op()` and `gicv5_wait_for_op_atomic()` do, how long do
they wait, what do they return and log on timeout, which may be used in atomic
context, and which can hand back the value read?

## gicv5.idle-and-valid: Idle and valid status bits

- section: IRS register programming
- relevance: 4 - the missing validity check is deliberate in one place
- words: 100

Besides completion, some status registers report whether the selected object is
valid. Which waits check it, which deliberately do not, and what error does a
failed validity check produce? Start from `gicv5_irs_wait_for_irs_pe()` and
`gicv5_irs_wait_for_spi_op()`.

## gicv5.timeout-handling: Poll timeout handling

- section: IRS register programming
- relevance: 4 - a dropped error leaves a half-published table
- words: 120

When a completion poll times out, what do the callers in the IRS, ITS and IWB
code do with the error: which propagate it and undo what they had set up, and
which ignore it? What usage of the return value is unsafe?

## gicv5.irs-sync: IRS sync operation

- section: IRS register programming
- relevance: 3 - the IRS has a sync and no invalidate
- words: 70

What does `gicv5_irs_syncr()` do, which IRS does it address when there are
several, which status does it wait on, and who calls it? Does the IRS have any
cache invalidation register the driver uses?

## gicv5.ist-overview: Interrupt state table

- section: Interrupt state table
- relevance: 4 - where LPI state lives
- words: 100

What is the interrupt state table, who allocates it and who writes its contents
afterwards, is there one per IRS or one for the system, and which IRS's
registers are used to set it up? Start from `gicv5_irs_init_ist()` and
`gicv5_irs_enable()`.

## gicv5.ist-structure-choice: Linear or two-level table

- section: Interrupt state table
- relevance: 3 - three separate choices from the ID registers
- words: 120

How does the driver choose between a linear and a two-level interrupt state
table, how does it choose the level 2 table size, and how does it choose the
entry size? Start from `gicv5_irs_init_ist()` and `gicv5_irs_l2_sz()`.

## gicv5.lpi-id-bits: Number of LPI ID bits

- section: Interrupt state table
- relevance: 4 - three caps are applied in turn
- words: 90

How is the number of LPI ID bits programmed into the IRS computed from the ID
registers of the IRS and of the CPU interface, what caps apply for a linear
table, and how does that number reach the LPI allocator?

## gicv5.ist-sizing: Table sizing arithmetic

- section: Interrupt state table
- relevance: 4 - a shift that wraps allocates nothing
- words: 130

How are the sizes of the linear table and of the level 1 table computed, in
which C types, what floor and what ceiling apply, and what happens when the
ceiling is hit? What usage of such shift-based size arithmetic is unsafe? Start
from `gicv5_irs_init_ist_linear()` and `gicv5_irs_init_ist_two_level()`.

## gicv5.ist-alignment: Table alignment

- section: Interrupt state table
- relevance: 3 - the allocator is what provides it
- words: 90

What alignment do the table base register and level 1 entries require, going by
their address masks, and what in the way the tables are allocated guarantees
it? When would an allocation not be suitably aligned?

## gicv5.ist-publish: Publishing the table base

- section: Interrupt state table
- relevance: 3 - the order of writes is the contract with the IRS
- words: 100

List in order the register writes, cache maintenance and waits that hand the
table to the IRS, and what is freed when the wait fails. What does the driver
do if the IRS already has a valid table when it probes?

## gicv5.iste-alloc: Level 2 table allocation

- section: Interrupt state table
- relevance: 4 - runs on every LPI allocation
- words: 130

When and how is a level 2 interrupt state table allocated and handed to the
IRS: list the steps in order, including what is written to the level 1 entry,
the register that maps it, the wait, and the failure path. Start from
`gicv5_irs_iste_alloc()`.

## gicv5.ist-valid-bit: Level 1 entry valid bit

- section: Interrupt state table
- relevance: 5 - the obvious fix of setting it is the bug
- words: 90

Who sets the valid bit of a level 1 interrupt state table entry, software or
the IRS? What does the driver write to the entry, and what does it use the bit
for? What usage is unsafe, and what that looks similar is correct?

## gicv5.iste-serialisation: Serialisation of table allocation

- section: Interrupt state table
- relevance: 3 - the function takes no lock of its own
- words: 50

What serialises concurrent calls that allocate level 2 tables and write level 1
entries, given that the function takes no lock of its own?

## gicv5.kmemleak: Leak checker annotations

- section: Interrupt state table
- relevance: 2 - only hardware holds the pointer
- words: 80

Which GICv5 table allocations are marked for the memory leak checker, why, and
at what point relative to the failure path? Which table is not marked, and why
does it not need to be?

## gicv5.irs-memory-attributes: IRS memory attributes

- section: Coherency
- relevance: 3 - programmed once, before anything is valid
- words: 90

Which cacheability and shareability attributes does the driver program into an
IRS for a coherent and for a non-coherent system, in which register, and when
relative to enabling the IRS and publishing tables? When does the driver
disable an IRS again?

## gicv5.noncoherent-maintenance: Non-coherent cache maintenance

- section: Coherency
- relevance: 4 - both arms have to be kept
- words: 120

What does the driver do after writing table memory that an IRS or ITS will
read, on a coherent and on a non-coherent system, and how does it know which it
is? What usage is unsafe when adding a new table write, and what is correct?
Start from `IRS_FLAGS_NON_COHERENT` and `gicv5_its_dcache_clean()`.

## gicv5.hw-written-readback: Reading memory the IRS wrote

- section: Coherency
- relevance: 4 - an invalidate in the wrong place is useless
- words: 90

When the driver later reads a table entry that the IRS has updated, what cache
maintenance is needed on a non-coherent system, where must it sit relative to
the completion poll, and what orders the two? Start from
`gicv5_irs_ist_synchronise()`.

## gicv5.id-decode-fallbacks: ID register decoding

- section: ID registers
- relevance: 3 - only some encodings are defined
- words: 110

Which ID register fields does the driver decode with a `switch`, what does each
do for an encoding it does not know, and what usage is unsafe when adding a new
decode? Start from `gicv5_set_cpuif_pribits()`, `gicv5_set_cpuif_idbits()` and
`irs_setup_pri_bits()`.

## gicv5.component-capabilities: Capabilities that may differ

- section: ID registers
- relevance: 3 - a mismatch is not an error
- words: 90

Which capabilities are reported separately by the CPU interface and by the IRS
(ID bits, priority bits), in which encodings, and how does the driver reconcile
them? Is a mismatch treated as an error?

## gicv5.virt-capable: Virtualisation capability

- section: ID registers
- relevance: 3 - decides whether KVM hears about the GIC at all
- words: 80

How does the driver learn whether the GIC implementation supports
virtualisation, where is that kept, and what depends on it? What usage is unsafe
when turning a register field into a `bool`, and what is correct?

# The ITS

## gicv5.its-structures: ITS driver structures

- section: ITS model
- relevance: 3 - two structures carry everything
- words: 110

What do `struct gicv5_its_chip_data` and `struct gicv5_its_dev` hold, what is
the lifetime of each, and how is a device found from its device ID? Start from
`drivers/irqchip/irq-gic-v5-its.c`.

## gicv5.its-config-model: ITS configuration model

- section: ITS model
- relevance: 5 - looking for a command queue finds nothing
- words: 100

How does software configure a GICv5 ITS: through a command queue, through
registers, or through tables in memory? Say what the steps of making one change
visible to the ITS are, and what the driver does not have compared with the
GICv3 ITS driver.

## gicv5.its-table-write: Writing a table entry

- section: ITS model
- relevance: 4 - the helper does half the job
- words: 100

Which helper writes an ITS table entry, what does it do besides the store, and
what must the caller still do afterwards? Which table writes in the file bypass
the helper, and when is that acceptable? Start from `its_write_table_entry()`.

## gicv5.its-invalidate: ITS cache invalidation

- section: ITS model
- relevance: 4 - three registers written in order
- words: 110

How does the driver invalidate the ITS's cached copy of an event's translation
and of a device's entry: which registers are written in which order, and what
is waited for afterwards? Start from `gicv5_its_itt_cache_inv()` and
`gicv5_its_device_cache_inv()`.

## gicv5.its-sync: ITS sync operation

- section: ITS model
- relevance: 4 - invalidate and sync answer different questions
- words: 100

What is the difference between waiting for an ITS invalidation to finish and
the ITS sync operation: which register and status each uses, what scope the
sync has, and where each is called? Start from `gicv5_its_cache_sync()` and
`gicv5_its_syncr()`.

## gicv5.its-valid-bits: ITS table valid bits

- section: ITS model
- relevance: 5 - the opposite of the interrupt state table
- words: 100

Who sets the valid bit in ITS device table and translation table entries,
software or the ITS, and which functions set and clear it at each level? How
does this compare with the interrupt state table?

## gicv5.its-publish-usage: Changing an ITS table entry

- section: ITS model
- relevance: 5 - a mapping the ITS never sees drops every event
- words: 100

What usage is unsafe when code changes an ITS device table or translation table
entry, with respect to the entry write, invalidation and waiting, and what that
looks similar is correct? Is a second invalidation after a helper that already
invalidates needed?

## gicv5.its-entry-endianness: Table entry byte order

- section: ITS model
- relevance: 4 - wrong only on big-endian
- words: 70

In which byte order are interrupt state, device and translation table entries
stored, which C type holds them, and what usage is unsafe when reading or
testing a field of an entry? What catches the mistake?

## gicv5.its-table-formats: ITS table entry layouts

- section: ITS tables
- relevance: 3 - four entry formats in one header
- words: 140

Which fields do a level 1 and level 2 device table entry and a level 1 and
level 2 translation table entry have, going by the masks in the header? A
table. Which of them carry an address with no shift? Start from
`GICV5_DTL2E_VALID`.

## gicv5.its-devtab-choice: Device table structure

- section: ITS tables
- relevance: 3 - the chosen layout is kept for every later lookup
- words: 130

How does the driver choose between a linear and a two-level device table and
the level 2 size, what cap applies to the number of device ID bits and why, and
where is the chosen configuration remembered for later lookups? Start from
`gicv5_its_init_devtab()` and `gicv5_its_l2sz_two_level()`.

## gicv5.its-devtab-l2: Level 2 device tables

- section: ITS tables
- relevance: 3 - allocated on demand and kept
- words: 90

When is a level 2 device table allocated, how big is it and what does the span
field have to do with that, and is it ever freed? Start from
`gicv5_its_alloc_l2_devtab()`.

## gicv5.its-itt-choice: Translation table structure

- section: ITS tables
- relevance: 3 - not built the way the device table is
- words: 130

How does the driver choose between a linear and a two-level translation table
for a device, are the level 2 tables allocated on demand or up front, how is the
last, partly used level 2 table sized, and how is the loop that frees them on
failure written? What usage is unsafe in such a reverse loop? Start from
`gicv5_its_create_itt_two_level()`.

## gicv5.its-device-register: Registering a device

- section: ITS tables
- relevance: 4 - the full write, invalidate, undo pattern
- words: 130

List in order what registering a device with an ITS does, which checks can fail
with which error, and what is undone when the final invalidation fails. Start
from `gicv5_its_device_register()`.

## gicv5.its-device-unregister: Unregistering a device

- section: ITS tables
- relevance: 3 - order of free and invalidate
- words: 80

List in order what unregistering a device does to the device table entry, the
translation table memory and the ITS cache. Is the memory freed before or after
the invalidation completes? Start from `gicv5_its_device_unregister()`.

## gicv5.its-device-lifetime: Device allocation and teardown

- section: ITS tables
- relevance: 3 - the MSI core drives it
- words: 110

Through which MSI domain callbacks is an ITS device created and destroyed, which
lock covers that, what is checked before a device is torn down, and what happens
when a device ID is registered twice? Start from `gicv5_its_msi_prepare()` and
`gicv5_its_msi_teardown()`.

## gicv5.its-scratchpad: Allocation info scratchpad

- section: ITS tables
- relevance: 3 - two files agree on it by convention only
- words: 100

What do the MSI parent prepare functions for GICv5 put in the allocation info
scratchpad slots, what does the ITS driver's prepare replace them with, and who
reads them afterwards? Start from `its_v5_pci_msi_prepare()` and
`its_v5_pmsi_prepare()`.

## gicv5.its-msi-parent: MSI parent operations

- section: ITS tables
- relevance: 3 - lives in a file shared with the older ITS
- words: 130

Which MSI parent operations does the GICv5 ITS use, where are they defined, how
do they find a device's device ID and the translate frame address for PCI and
non-PCI devices under device tree and ACPI, and how is the vector count
rounded? Start from `gic_v5_its_msi_parent_ops`.

## gicv5.its-eventid-alloc: Event ID allocation

- section: ITS interrupts
- relevance: 3 - the IWB depends on the fixed case
- words: 90

How are event IDs allocated and freed within a device, for ordinary MSIs and
for allocations that ask for fixed message data? Which errors are possible?
Start from `gicv5_its_alloc_eventid()`.

## gicv5.its-domain-alloc: ITS domain allocation

- section: ITS interrupts
- relevance: 4 - three resources to release on failure
- words: 120

List in order what allocating interrupts in the ITS domain does, from event IDs
to the parent LPIs to the per-interrupt setup, and what is released on each
failure. Which flags are set on each interrupt? Start from
`gicv5_its_irq_domain_alloc()`.

## gicv5.its-domain-free: ITS domain free

- section: ITS interrupts
- relevance: 5 - a reused LPI can receive its previous owner's event
- words: 110

List in order what freeing interrupts in the ITS domain does, and which
synchronisation operations it ends with. What usage is unsafe when an LPI or
event ID is about to be reused, and what is correct? Start from
`gicv5_its_irq_domain_free()`.

## gicv5.its-activate: Mapping and unmapping events

- section: ITS interrupts
- relevance: 4 - there is no unmap command
- words: 100

At which point in an interrupt's life is its event mapped to its LPI in the
translation table and unmapped again, what does each write to the entry, and
what does mapping return if the entry is already valid? Start from
`gicv5_its_map_event()`.

## gicv5.its-init: ITS initialisation

- section: ITS interrupts
- relevance: 3 - attributes before tables before enable
- words: 120

List in order what bringing up one ITS does, from mapping its registers to
creating its domain, what is done if firmware left the ITS enabled, and what is
undone at each failure. Start from `gicv5_its_init_bases()`.

## gicv5.its-noncoherent-flag: ITS coherency flag

- section: ITS interrupts
- relevance: 3 - a parameter and a property are both in play
- words: 70

From what does the ITS initialisation decide that an ITS is non-coherent, on
the device tree path and on the ACPI path? Read the body of
`gicv5_its_init_bases()` and say what it actually tests.

## gicv5.its-acpi-probe: ITS probe from ACPI

- section: ITS interrupts
- relevance: 3 - devices find their MSI domain through it
- words: 110

How are ITSs and their translate frames discovered from ACPI, which firmware
node handles are created, and how are they registered so that devices can later
find their MSI domain? Start from `gicv5_its_acpi_probe()`.

## gicv5.its-locking: ITS locking

- section: ITS interrupts
- relevance: 4 - most sequences rely on a lock taken elsewhere
- words: 100

Which locks does the GICv5 ITS driver take and what does each protect? What
serialises the multi-register invalidation sequences and updates to a device's
event bitmap, given the locks the functions take themselves?

# The IWB

## gicv5.iwb-overview: Interrupt wire bridge

- section: Interrupt wire bridge
- relevance: 4 - wires do not become SPIs
- words: 90

What does an interrupt wire bridge do, what does its driver create for each one,
and how does a wire's interrupt reach a CPU: through SPIs or some other way?
Start from `gicv5_iwb_device_probe()`.

## gicv5.iwb-msi-template: IWB MSI domain template

- section: Interrupt wire bridge
- relevance: 4 - an empty callback that is correct
- words: 110

What does the IWB's MSI domain template set: bus token, flags, allocation
flags, chip callbacks? Why is its write-message callback empty, and how does a
wire number become an event ID? Start from `iwb_msi_template`.

## gicv5.iwb-enable: Wire enable and trigger mode

- section: Interrupt wire bridge
- relevance: 3 - enabling a wire is not unmasking the interrupt
- words: 120

How does enabling and disabling an IWB wire differ from masking and unmasking
its interrupt, which registers hold the enable and the trigger mode, what is
waited for after each is written, and is an error from the wait acted on? Start
from `__gicv5_iwb_set_wire_enable()` and `gicv5_iwb_set_type()`.

## gicv5.iwb-probe: IWB probe requirements

- section: Interrupt wire bridge
- relevance: 3 - firmware has to have enabled it
- words: 80

What must firmware have done to an IWB before the driver will use it, what does
the driver program at probe, and how does it learn the number of wires? Start
from `gicv5_iwb_init_bases()`.

## gicv5.iwb-translate: IWB specifier translation

- section: Interrupt wire bridge
- relevance: 3 - ACPI packs the bridge and the wire into one number
- words: 110

How does the IWB domain translate a device tree specifier and an ACPI one into a
wire number and trigger? How is an ACPI global interrupt number recognised as
belonging to an IWB, and which fields does it carry? Start from
`gicv5_iwb_irq_domain_translate()` and `gic_v5_get_gsi_domain_id()`.

# Firmware and boot

## gicv5.dt-binding: Device tree binding

- section: Firmware and boot
- relevance: 3 - the node layout decides what the probe walks
- words: 140

Which compatible strings, register names and properties does the GICv5 device
tree binding define for the top-level node, the IRS, the ITS, its translate
frames and the IWB, and how many interrupt cells does each interrupt parent
take? Start from
`Documentation/devicetree/bindings/interrupt-controller/arm,gic-v5.yaml`.

## gicv5.acpi-model: ACPI interrupt model

- section: Firmware and boot
- relevance: 3 - how a GSI finds its domain
- words: 100

How does the ACPI probe register GICv5 as the interrupt model, which MADT entry
types exist for GICv5, and how does a global interrupt number find its
irqdomain? Start from `gic_acpi_init()`.

## gicv5.boot-requirements: Boot requirements

- section: Firmware and boot
- relevance: 3 - a trap left armed breaks the host at EL1
- words: 110

What must be set up at EL2 or by firmware before the kernel is entered at EL1 on
a GICv5 system, according to the boot protocol document, and what does the
kernel do itself when it is entered at EL2? Start from
`Documentation/arch/arm64/booting.rst` and `__init_el2_gicv5`.

## gicv5.cpucaps: CPU capabilities

- section: Firmware and boot
- relevance: 4 - the capability type decides when it may be tested
- words: 100

Which arm64 CPU capabilities describe GICv5, of which capability type is each,
and how is each detected? What does a CPU without the CPU interface do when the
system has GICv5 components? Start from `arch/arm64/kernel/cpufeature.c`.

## gicv5.cap-check-usage: Checking the capabilities

- section: Firmware and boot
- relevance: 3 - three ways to test, each right somewhere
- words: 110

Which call sites test the GICv5 capabilities with `this_cpu_has_cap()`, with
`cpus_have_cap()` and with `cpus_have_final_cap()`, and why does each use that
form? What usage is unsafe, and what is correct?

# KVM

## gicv5.kvm-scope: KVM GICv5 support

- section: KVM scope
- relevance: 5 - what is not there matters as much as what is
- words: 110

What does KVM's GICv5 device support in this tree and what does it not: which
kinds of interrupt a guest can have, nested virtualisation, protected KVM,
saving and restoring state to userspace? Start from
`Documentation/virt/kvm/devices/arm-vgic-v5.rst` and `vgic_v5_init()`.

## gicv5.kvm-entry-points: KVM entry points

- section: KVM scope
- relevance: 4 - the common vgic code branches in a dozen places
- words: 140

For each job (probe, create the device, initialise, reset a vCPU, load and put a
vCPU, flush state before entry, save and fold state after exit, check for a
pending interrupt), which GICv5-specific function does KVM call and from where?
A table.

## gicv5.kvm-info-handoff: Handing the GIC to KVM

- section: KVM scope
- relevance: 4 - decides whether KVM gets a vgic at all
- words: 120

How does the irqchip driver tell KVM that the host has a GICv5, which fields
does it fill in, under which conditions does it publish nothing (including a
missing maintenance interrupt), what does KVM's common init then do, and is this
done on the ACPI path too? Start from `gic_of_setup_kvm_info()` and
`kvm_vgic_hyp_init()`.

## gicv5.vgic-probe: KVM probe

- section: KVM scope
- relevance: 4 - two devices are registered independently
- words: 120

List what `vgic_v5_probe()` sets and registers, in order, which steps are
skipped under protected KVM, when it returns an error, and how the maximum
number of vCPUs is decided.

## gicv5.compat-mode: GICv3 guests on GICv5

- section: KVM scope
- relevance: 4 - only the virtual CPU interface is in hardware
- words: 140

How does KVM run a GICv3 guest on a GICv5 host: what hardware feature is needed,
how is it detected, which flag records it, which vgic code then runs the guest,
what is set up at probe for it, and how does that code deactivate a physical
interrupt? Which parts of a GICv3 does the hardware provide and which are
emulated in software?

## gicv5.compat-mode-switch: Leaving compatibility mode

- section: KVM scope
- relevance: 4 - the same register has two layouts
- words: 100

Which control selects between the GICv3-compatible and the native GICv5 virtual
CPU interface, where does KVM clear it before loading native state, and what
synchronisation follows? What usage is unsafe when writing GICv5-layout
hypervisor registers? Start from `__vgic_v5_restore_vmcr_apr()`.

## gicv5.kvm-not-implemented: Unimplemented virtualisation features

- section: KVM scope
- relevance: 4 - stops a reviewer looking for code that is not there
- words: 90

Does this tree have any code for GICv5 VM tables, VPE tables, virtual interrupt
state tables, doorbells, or virtual SPIs and LPIs? Say what `struct gicv5_vpe`
holds and what looking up a non-private interrupt returns for a GICv5 guest. If
a feature is absent, say so in a line and stop.

## gicv5.kvm-intid-helpers: KVM interrupt ID helpers

- section: KVM interrupt IDs
- relevance: 4 - callers must build the typed form themselves
- words: 100

Which macros does KVM use to build a GICv5 interrupt ID of a given type and to
take it apart, and where are they defined? Where do in-kernel users such as the
timer and PMU code and the interrupt-line ioctl build one?

## gicv5.kvm-type-predicates: Interrupt type predicates

- section: KVM interrupt IDs
- relevance: 5 - whether a predicate bounds the ID decides if an index is safe
- words: 110

What do the KVM predicates for SGI, PPI, SPI and LPI test for a GICv5 guest: the
type field, a bound on the ID, or both? Which of them can be relied on as a
bounds check before indexing per-interrupt state? Start from `__irq_is_ppi()` in
`include/kvm/arm_vgic.h`.

## gicv5.kvm-private-lookup: Private interrupt lookup

- section: KVM interrupt IDs
- relevance: 4 - every per-PPI path goes through it
- words: 110

How does KVM get from a GICv5 PPI's interrupt ID to its `struct vgic_irq`, what
bounds and speculation protection apply, how many private interrupts does a vCPU
have, and how is each initialised (interrupt ID, trigger configuration,
per-interrupt operations)? Start from `vgic_get_vcpu_irq()` and
`vgic_v5_setup_private_irq()`.

## gicv5.kvm-ppi-count: Number of guest PPIs

- section: KVM interrupt IDs
- relevance: 4 - the zero writes are not lost state
- words: 90

How many PPIs does KVM support for a GICv5 guest, what does the code say about
the rest, which build-time check pins the assumption, and what is done with the
hardware registers that cover the unsupported ones?

## gicv5.kvm-irq-ops: Per-interrupt operations

- section: KVM interrupt IDs
- relevance: 4 - PPIs bypass the pending list entirely
- words: 120

Which per-interrupt operations does GICv5 support add or override, what does
each do, and which interrupts get which set? Why are GICv5 PPIs not queued on a
vCPU's list of pending interrupts? Start from `struct irq_ops` and
`vgic_v5_ppi_queue_irq_unlock()`.

## gicv5.kvm-ppi-masks: PPI masks

- section: KVM PPI state
- relevance: 4 - four bitmaps with four owners
- words: 150

KVM keeps several bitmaps of GICv5 PPIs: implemented by the host, exposed to the
guest, drivable from userspace, level-triggered. For each, where is it stored,
who computes it and when, and who reads it? A table. Start from
`struct vgic_v5_vm`.

## gicv5.kvm-finalize: Finalising PPI state

- section: KVM PPI state
- relevance: 4 - per-vCPU entry point, VM-wide result
- words: 110

When is the set of PPIs exposed to a guest computed, from what, under which
lock, and how does the function avoid doing the work twice? What usage is unsafe
when VM-wide state is computed from a per-vCPU path? Start from
`vgic_v5_finalize_ppi_state()`.

## gicv5.kvm-visible-iteration: Iterating PPIs

- section: KVM PPI state
- relevance: 4 - every state loop uses the same mask
- words: 80

Which iterator do the GICv5 state paths use to walk a guest's PPIs, over which
mask, and which functions use it? What usage is unsafe when adding a new per-PPI
loop?

## gicv5.kvm-userspace-ppis: PPIs driven from userspace

- section: KVM PPI state
- relevance: 3 - userspace may drive very few
- words: 100

Which PPIs may userspace drive for a GICv5 guest, how does it find out, and what
does the interrupt-line ioctl check and do for a GICv5 PPI and SPI? Start from
`kvm_vm_ioctl_irq_line()`.

## gicv5.kvm-device-attrs: KVM device attributes

- section: KVM PPI state
- relevance: 3 - a read-only attribute has to reject writes
- words: 120

Which attribute groups and attributes does the GICv5 KVM device accept for set,
get and has, and what error do the others return? What does reading the
userspace PPI attribute copy out, and what happens on an attempt to set it?
Start from `vgic_v5_set_attr()`.

## gicv5.kvm-state-placement: Shadow and hardware state

- section: KVM PPI state
- relevance: 4 - two copies to reconcile on every entry and exit
- words: 110

Where does the state of a GICv5 guest's PPIs live while the guest runs and while
it does not, and which structures hold KVM's copy of each register? Start from
`struct vgic_v5_cpu_if` and the GICv5 member of `struct kvm_host_data`.

## gicv5.kvm-flush: Flushing state before entry

- section: KVM entry and exit
- relevance: 5 - an edge not cleared is delivered twice
- words: 100

What does KVM do to each exposed PPI's shadow state when building the pending
bitmap for guest entry, and how are edge and level interrupts treated
differently? Where does the bitmap go? Start from `vgic_v5_flush_ppi_state()`.

## gicv5.kvm-fold: Folding state after exit

- section: KVM entry and exit
- relevance: 5 - an assignment instead of an OR loses an edge
- words: 100

What does KVM copy back from the hardware registers into each exposed PPI's
shadow state after a guest exit, how are edge and level interrupts treated
differently, and why is one of the updates an OR? Start from
`vgic_v5_fold_ppi_state()`.

## gicv5.kvm-edge-level-usage: Edge and level pending state

- section: KVM entry and exit
- relevance: 5 - making the two directions symmetric is the bug
- words: 90

What usage is unsafe when changing how a GICv5 PPI's pending state is moved
between KVM's shadow state and the hardware on entry and exit, for edge and for
level interrupts, and what is correct?

## gicv5.kvm-hyp-ppi-switch: PPI register world switch

- section: KVM entry and exit
- relevance: 4 - a register walk with an order
- words: 130

Which hypervisor PPI registers are saved on exit and restored on entry, in which
order, and what is written to the ones KVM keeps no state for? Where are these
functions called from under VHE and nVHE? Start from
`__vgic_v5_save_ppi_state()` and `__vgic_v5_restore_ppi_state()`.

## gicv5.kvm-dvi: Direct injection of PPIs

- section: KVM entry and exit
- relevance: 5 - writing pending over a directly injected PPI corrupts it
- words: 120

How does a PPI become directly injected for a GICv5 guest, where is that
recorded, when is direct injection switched on and off in hardware, and how does
it affect the pending state written on entry? Which guest interrupts use it?
Start from `vgic_v5_set_ppi_dvi()`.

## gicv5.kvm-bitmap-atomicity: Shared bitmaps and per-interrupt locks

- section: KVM entry and exit
- relevance: 4 - a per-interrupt lock does not cover a shared word
- words: 110

Which lock is held when a bit of the direct-injection bitmap is changed, does
that lock serialise updates to different bits of the same bitmap, and which bit
operation is used? What usage is unsafe for a bitmap indexed by interrupt, and
where in the GICv5 code is a non-atomic bit operation correct?

## gicv5.kvm-load-put: Loading and putting a vCPU

- section: KVM entry and exit
- relevance: 4 - both are called twice around WFI
- words: 90

What do the GICv5 load and put functions do, what do they guard against being
called twice, and which flag tracks it? Start from `vgic_v5_load()` and
`vgic_v5_put()`.

## gicv5.kvm-vmcr-apr: Control and active priority registers

- section: KVM entry and exit
- relevance: 4 - saved at different times by different functions
- words: 110

When are the virtual machine control register and the active priorities register
of a GICv5 guest saved and restored: on every entry and exit, or at load and
put? Which function does each, and which run at hyp through a hypercall? Start
from `__vgic_v5_save_state()` and `__vgic_v5_save_apr()`.

## gicv5.kvm-pending-check: Pending interrupt check

- section: KVM entry and exit
- relevance: 4 - an off-by-one here is a spurious wakeup
- words: 120

How does KVM decide whether a GICv5 vCPU has an interrupt it should wake for:
how is the effective priority mask computed, what comparison is made against it,
and where does pending come from for a hardware-mapped interrupt? Start from
`vgic_v5_has_pending_ppi()`.

## gicv5.kvm-priority-sync: PPI priority sync

- section: KVM entry and exit
- relevance: 3 - the shadow priority is stale most of the time
- words: 80

When are the guest's PPI priorities copied from the saved registers into the
shadow interrupt state, how is a PPI's field located in the saved registers, and
why is it not done on every exit?

## gicv5.kvm-enable-trap: PPI enable register trap

- section: KVM traps and emulation
- relevance: 4 - the only PPI register KVM traps writes to
- words: 90

How does KVM handle a guest write to the PPI enable registers: what is merged
with which mask, what is updated, and what happens for the second bank? Are
reads trapped? Start from `access_gicv5_ppi_enabler()`.

## gicv5.kvm-fgt: Fine-grained traps for the guest

- section: KVM traps and emulation
- relevance: 3 - almost nothing is trapped
- words: 110

Which GICv5 register and instruction accesses does KVM trap from a GICv5 guest
and why, where are the trap registers computed and written, and what does a
guest without GICv5 get? Start from `kvm_vcpu_load_fgt()` and
`__activate_traps_ich_hfgxtr()`.

## gicv5.kvm-id-emulation: Emulated ID registers

- section: KVM traps and emulation
- relevance: 4 - KVM's limit, not the host's, is what the guest sees
- words: 120

What does a GICv5 guest read from the CPU interface ID register and the affinity
ID register, which values does a vCPU reset set for ID bits and priority bits
and in which encoding, and which host feature is hidden? What usage is unsafe
when a later path can set a guest-visible value that KVM has narrowed? Start
from `access_gicv5_idr0()` and `vgic_v5_reset()`.

## gicv5.kvm-timers: Arch timers with GICv5

- section: KVM in-kernel users
- relevance: 4 - the timer code changed in five places
- words: 140

What changes in the arch timer code for a GICv5 guest: the interrupt IDs used,
whether userspace may choose them, the per-interrupt operations, injection for
directly injected timers, and the handling of the physical active state? Start
from `get_vgic_ppi()` and `kvm_timer_init_vm()`.

## gicv5.kvm-pmu: PMU interrupt with GICv5

- section: KVM in-kernel users
- relevance: 3 - the number is fixed and given in typed form
- words: 60

Which interrupt number must the PMU use for a GICv5 guest, in which form is it
given by userspace, and what happens if userspace does not set one? Start from
`KVM_ARMV8_PMU_GICV5_IRQ`.

## gicv5.kvm-create: Device creation

- section: KVM in-kernel users
- relevance: 3 - the timers are initialised twice
- words: 100

What is specific to GICv5 when the vgic device is created: the vCPU limit, the
private interrupt allocation, the guest-visible feature ID register fields, and
anything redone for the timers? How does KVM test whether a guest has GICv5?
Start from `kvm_vgic_create()` and `kvm_vgic_finalize_idregs()`.

## gicv5.kvm-selftests: KVM selftests

- section: KVM in-kernel users
- relevance: 2 - what a change can be tested with
- words: 70

Which selftests cover the GICv5 KVM device, what do they check, and which header
gives guest code the GICv5 definitions? Start from
`tools/testing/selftests/kvm/arm64/vgic_v5.c`.

# Changing the implementation

## gicv5.change-checklist: Changing the driver

- section: What a change must preserve
- relevance: 4 - most paths have a twin
- words: 100

What must a change to the GICv5 host driver keep working besides the path it
touches: device tree and ACPI probing, coherent and non-coherent systems, linear
and two-level tables, big-endian builds, KVM's use of forwarded PPIs and of the
compatibility mode?

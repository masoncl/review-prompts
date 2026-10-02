# Questions: GICv3 and GICv4 (measurement set)

- guide: gic-v3.md
- title: GICv3/v4 Subsystem Details

A wide set of questions about the GICv3 and GICv4 host irqchip driver, the ITS
driver and KVM's virtual GICv3, used to measure what a model already knows
before deciding what the built guide should spend its words on. The
hand-written guide it will replace is 10,759 words and was never checked
against current sources. GICv2 and native GICv5 are out of scope. Run it with
`build-guides.py --no-sources --check-memory --questions` pointed at this
directory. The trimmed set a guide is built from is `../gic-v3.md`. Format:
`../../../docs/subsystem-questions.md`.

# The host driver

## gicv3.files: Source files

- section: Finding your way
- relevance: 4 - the subject is spread over three directories
- words: 150

Which files hold the GICv3 distributor, redistributor and CPU interface
driver, the ITS driver, the GICv4 layer, the message-based SPI support, the
code shared with GICv2, the MSI parent glue, the register and priority
headers, the arm64 system register accessors, KVM's virtual GIC (one line per
file), the hypervisor save and restore code, and the user-visible system
register table? A table. Start from `drivers/irqchip/irq-gic-v3.c` and
`arch/arm64/kvm/vgic/`.

## gicv3.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 150

For each job, which function do you start reading from: probing from
devicetree and from ACPI, bringing up a secondary CPU, taking an interrupt,
sending an IPI, preparing MSIs for a device, activating one LPI, creating and
initialising a guest's GIC, the work done before each guest entry and after
each exit, injecting an interrupt into a guest, a guest write to the ITS
command queue, and saving the ITS tables for migration? A table.

## gicv3.docs-tests: Documentation and tests

- section: Finding your way
- relevance: 3 - the user ABI rules live only in the documents
- words: 80

Which files under `Documentation/` describe the devicetree binding, the KVM
device ABI for the virtual GICv3 and the virtual ITS, and the errata worked
around, and which selftests exercise the virtual GIC? Start from
`Documentation/virt/kvm/devices/` and `tools/testing/selftests/kvm/arm64/`.

## gicv3.options: Build and boot options

- section: Finding your way
- relevance: 2 - decides which paths are compiled and enabled
- words: 80

Which Kconfig symbols build the GICv3 driver and the ITS driver and can a user
select them, and which kernel command line parameters change the behaviour of
the driver or of KVM's virtual GICv3? Start from `drivers/irqchip/Kconfig` and
`Documentation/admin-guide/kernel-parameters.txt`.

## gicv3.chip-data: Driver state

- section: Driver data
- relevance: 3 - every function reads these
- words: 120

What does `struct gic_chip_data` hold, and what does `struct rdists` hold,
both per CPU and globally? Who else besides `drivers/irqchip/irq-gic-v3.c`
reads `struct rdists`, and how does it get the pointer? Start from
`include/linux/irqchip/arm-gic-v3.h`.

## gicv3.intid-ranges: Interrupt ID ranges

- section: Driver data
- relevance: 4 - the wrong frame or offset silently programs another interrupt
- words: 120

Which interrupt ID ranges does the driver recognise, which register frame is
used for each, and how are a register offset and an index derived for the
extended ranges? A table. Start from `__get_intid_range()`,
`gic_dist_base()` and `convert_offset_index()`.

## gicv3.rdist-discovery: Finding a redistributor

- section: Driver data
- relevance: 3 - a CPU with no redistributor does not boot
- words: 100

How does a CPU find its own redistributor among the redistributor regions:
what is compared, how does the walk step from one redistributor to the next,
what ends it, and what is recorded when it is found? Start from
`gic_iterate_rdists()` and `__gic_populate_rdist()`.

## gicv3.rdist-capabilities: Redistributor capability flags

- section: Driver data
- relevance: 4 - GICv4 features are all-or-nothing across CPUs
- words: 110

How are `has_vlpis`, `has_rvpeid`, `has_direct_lpi` and
`has_vpend_valid_dirty` in `struct rdists` computed, which register bits feed
each, and what later clears them? Start from
`__gic_update_rdist_properties()` and `gic_init_bases()`.

## gicv3.irq-chips: The two interrupt chips

- section: Driver data
- relevance: 4 - the callbacks differ in ways that matter to KVM
- words: 110

`drivers/irqchip/irq-gic-v3.c` defines two `struct irq_chip`. What selects
between them, which callbacks differ and how, and which flow handler is
installed for each interrupt ID range? Start from `gic_irq_domain_map()`.

## gicv3.eoi-mode: Split priority drop and deactivation

- section: Driver data
- relevance: 4 - decides who deactivates an interrupt
- words: 100

What decides whether the driver runs with priority drop and deactivation
split, what does that change in the acknowledge path, in the end-of-interrupt
callback and for an interrupt forwarded to a vCPU, and what does KVM learn
from it? Start from `supports_deactivate_key`.

## gicv3.fwspec: Firmware interrupt specifiers

- section: Driver data
- relevance: 3 - a bad translation delivers the wrong interrupt
- words: 120

How does the driver translate a devicetree specifier and an ACPI one into an
interrupt ID and trigger type, which forms does it reject or warn about, and
how is the affinity of a partitioned PPI found? Start from
`gic_irq_domain_translate()` and `gic_irq_get_fwspec_info()`.

## gicv3.quirks: Quirks and errata

- section: Driver data
- relevance: 3 - each one changes a path reviewers assume is uniform
- words: 150

How is a quirk entry matched to the hardware, and which quirks do the GICv3
driver and the ITS driver carry? A table of the flag or static key each one
sets and what that changes. Start from `gic_quirks`, `its_quirks` and
`gic_enable_quirks()`.

## gicv3.rwp-wait: Waiting for register writes

- section: Register writes
- relevance: 4 - polling the wrong bit returns at once
- words: 100

Which helpers wait for a distributor or a redistributor register write to take
effect, which register and bit does each poll, how long does it wait and what
happens on a timeout? Which writes in the driver are followed by such a wait?
Start from `gic_do_wait_for_rwp()`.

## gicv3.rwp-usage: Completing a register write

- section: Register writes
- relevance: 4 - the error is invisible at the call site
- words: 100

What usage of the write-pending poll, or what omission of a completion step
after a distributor or redistributor write, is unsafe, and what that looks
similar is correct? Name in-tree code that shows each. Start from
`gic_mask_irq()`, `gic_unmask_irq()` and `gic_irq_set_irqchip_state()`.

## gicv3.mask-forwarded: Masking a forwarded interrupt

- section: Register writes
- relevance: 3 - a guest that dies must not leave an interrupt stuck
- words: 60

What does masking do, beyond disabling, for an interrupt that is forwarded to
a vCPU, in which chip, and why? Start from `gic_eoimode1_mask_irq()`.

## gicv3.irqchip-state: Pending and active state

- section: Register writes
- relevance: 3 - KVM drives mapped interrupts through these
- words: 100

Through which callbacks can the pending, active and masked state of an
interrupt be read and written, for which interrupt IDs, which registers are
used, and which write is followed by a read of the same register and why?
Start from `gic_irq_set_irqchip_state()` and `gic_peek_irq()`.

## gicv3.set-affinity: Moving a shared interrupt

- section: Register writes
- relevance: 3 - the order of the steps is the point
- words: 80

What are the steps, in order, of changing the target CPU of an SPI, what does
`force` change, which interrupts is the operation refused for, and what does
it return? Start from `gic_set_affinity()`.

## gicv3.prio-constants: Priority constants

- section: Priorities and pseudo-NMI
- relevance: 4 - the values are chosen to survive a shift
- words: 90

Which priority constants does the GICv3 code define, what is each used for,
and what do the compile-time assertions next to them check? Start from
`include/linux/irqchip/arm-gic-v3-prio.h`.

## gicv3.prio-views: Two views of a priority

- section: Priorities and pseudo-NMI
- relevance: 5 - only one configuration differs and it is the hard one to test
- words: 140

When do the priority written to the distributor and the priority seen in the
CPU interface's mask and running-priority registers differ, how does the
driver find out which case it is in, and what does it do about it, once or at
each use? Start from `gic_prio_init()`, `gic_has_group0()` and
`dist_prio_irq`.

## gicv3.prio-usage: Using a priority value

- section: Priorities and pseudo-NMI
- relevance: 5 - a wrong constant misclassifies NMIs on some machines only
- words: 90

What usage of a priority constant or variable when programming an interrupt's
priority, or when comparing against the running priority or the priority mask,
is incorrect, and what that looks similar is correct? Name in-tree code for
each side.

## gicv3.nmi-setup: Making an interrupt a pseudo-NMI

- section: Priorities and pseudo-NMI
- relevance: 3 - the preconditions are checked in the callbacks
- words: 100

What enables pseudo-NMI support in the driver and what forbids it, and what do
`gic_irq_nmi_setup()` and `gic_irq_nmi_teardown()` check and change? Which
interrupt ID ranges can become NMIs?

## gicv3.nmi-entry: Interrupt entry with pseudo-NMIs

- section: Priorities and pseudo-NMI
- relevance: 4 - an IRQ taken in NMI context is very hard to debug
- words: 120

`gic_handle_irq()` has two paths. What distinguishes them, how does each
decide whether the acknowledged interrupt is an NMI, and what does each do to
the priority mask around the acknowledge? Start from
`__gic_handle_irq_from_irqson()` and `__gic_handle_irq_from_irqsoff()`.

## gicv3.ack-sync: After the acknowledge

- section: Priorities and pseudo-NMI
- relevance: 5 - a handler that runs against stale state
- words: 110

What must happen between reading the interrupt acknowledge register and
running the handler, which function does it, and what form of it would be
unsafe? What is done with the special interrupt IDs and with an interrupt that
has no mapping? Start from `gic_complete_ack()` and
`gic_deactivate_unhandled()`.

## gicv3.sgi-send: Sending an IPI

- section: CPUs and IPIs
- relevance: 4 - the barriers are the contract with the receiver
- words: 120

What does `gic_ipi_send_mask()` do before, during and after writing the SGI
register: which barriers and why each, how are targets grouped into one write,
how wide is the SGI number field, and how many SGIs does Linux register as
IPIs? Start from `gic_send_sgi()` and `gic_smp_init()`.

## gicv3.cpu-init: Per-CPU initialisation

- section: CPUs and IPIs
- relevance: 4 - the order is load-bearing
- words: 140

In what order does a CPU set up its redistributor and its CPU interface: waking
the redistributor, groups and priorities, the priority mask, the binary point,
the EOI mode, the active priority registers, the group enable, and the check
that SGIs can reach every CPU? Start from `gic_cpu_init()` and
`gic_cpu_sys_reg_init()`.

## gicv3.sre-enable: Enabling system register access

- section: CPUs and IPIs
- relevance: 4 - an access before it is UNDEFINED
- words: 90

Where is the system register interface enabled, on which paths (boot CPU,
secondary CPUs, return from a low-power state), what is done if it cannot be
enabled, and what else does the CPU power-management notifier save or redo?
Start from `gic_cpu_sys_reg_enable()` and `gic_cpu_pm_notifier()`.

## gicv3.dist-init: Distributor initialisation

- section: CPUs and IPIs
- relevance: 3 - the order of disable, configure and enable
- words: 110

What does `gic_dist_init()` do and in what order, which control bits does it
enable, how are the extended SPIs handled, and where are all SPIs routed at
boot? What does the driver assume about the security state, and which quirk
changes that?

## gicv3.hotplug-states: CPU hotplug callbacks

- section: CPUs and IPIs
- relevance: 3 - one of them cannot fail and cannot sleep
- words: 100

Which CPU hotplug states do the GICv3 and ITS drivers register, what does each
callback do, which of them may fail, and which run with interrupts off so that
an allocation in them must not sleep? Start from `gic_smp_init()` and
`its_lpi_memreserve_init()`.

# The ITS driver

## gicv3.its-node: One ITS

- section: ITS structures
- relevance: 4 - two locks with different jobs
- words: 120

What does `struct its_node` hold, what does each of its two locks protect, and
which global list and lock tie the ITSs together? Start from
`drivers/irqchip/irq-gic-v3-its.c`.

## gicv3.its-device: One device behind an ITS

- section: ITS structures
- relevance: 4 - shared devices have no tracked lifetime
- words: 120

What do `struct its_device` and `struct event_lpi_map` hold, how is the
interrupt translation table sized and allocated, and what does `shared` mean
for the device's lifetime? Start from `its_create_device()`.

## gicv3.its-collections: Collections

- section: ITS structures
- relevance: 3 - the target address has two encodings
- words: 90

How many collections does each ITS have, what is a collection's target address
in each of the two encodings an ITS may ask for, when is a collection mapped,
and what do `valid_col()` and `valid_vpe()` guard against?

## gicv3.its-probe: Probing an ITS

- section: ITS structures
- relevance: 3 - every ITS is reset before any is probed
- words: 130

What are the steps of bringing up the ITSs, from the first pass over all of
them to enabling each one: what is reset first and why, what is allocated, how
is the command queue register programmed and checked, and what is undone on
failure? Start from `its_of_probe()`, `its_reset_one()` and
`its_probe_one()`.

## gicv3.its-quiesce: Disabling and resuming an ITS

- section: ITS structures
- relevance: 4 - writing the base registers of a live ITS is UNPREDICTABLE
- words: 120

Which state must an ITS be in before its table and command queue base
registers are written, which function gets it there, and what do the suspend
and resume callbacks save, restore and re-issue? Start from
`its_force_quiescent()`, `its_save_disable()` and `its_restore_enable()`.

## gicv3.its-memory: Allocating memory for the GIC

- section: ITS structures
- relevance: 4 - the size argument is easy to misread
- words: 100

Which helpers allocate and free memory that the ITS or a redistributor will
read, what is the unit of their size argument, what else do they do to the
pages, and when do they deliberately leak? How are small translation tables
allocated? Start from `its_alloc_pages_node()` and `itt_alloc_pool()`.

## gicv3.cmdq-layout: Command queue layout

- section: The command queue
- relevance: 3 - the arithmetic rests on these sizes
- words: 90

How big is the command queue and one entry, which fields of `struct its_node`
and which registers track the write and read positions, when is the queue
considered full, and what does the allocation of an entry do when it stays
full? Start from `its_allocate_entry()` and `its_queue_full()`.

## gicv3.cmdq-send: Sending one command

- section: The command queue
- relevance: 5 - each step can be got wrong on its own
- words: 140

List in order the steps of sending one ITS command, from taking the lock to
returning, naming the function for each step and saying which steps run under
the lock. Which macro generates the send functions, and how many are there?
Start from `BUILD_SINGLE_CMD_FUNC`.

## gicv3.cmdq-flush: Publishing a command

- section: The command queue
- relevance: 5 - an unobserved command is silently not executed
- words: 80

How is a command written to the queue made visible to the ITS before the
write pointer register is written, what selects between the two ways of doing
it, and when is that choice made? Start from `its_flush_cmd()`.

## gicv3.cmdq-wait: Waiting for a command

- section: The command queue
- relevance: 5 - wrap-around bugs survive light testing
- words: 120

How does the driver wait for the commands it queued to be consumed: where and
when is the starting read position sampled, how is wrap-around of the queue
handled, how long does it wait, and what happens on a timeout? Does the caller
learn of the failure? Start from `its_wait_for_range_completion()`.

## gicv3.cmdq-builders: Command builders

- section: The command queue
- relevance: 5 - the return value is control flow
- words: 150

What must every command builder do to the command block before returning, and
what does its return value control? Give a table of the builders saying which
send function each is used with and what it returns. Start from
`its_build_mapd_cmd()`, `its_build_vmapp_cmd()` and `its_fixup_cmd()`.

## gicv3.cmdq-sync: Synchronisation commands

- section: The command queue
- relevance: 5 - the wrong one compiles and appears to work
- words: 110

Which synchronisation command does each send function append, against what
object, and when is none appended? How are the virtual forms of INV, INT and
CLEAR sent? Start from `its_build_sync_cmd()`, `its_build_vsync_cmd()` and
`its_send_vinv()`.

## gicv3.cmdq-vmapp-sync: Unmapping a vPE

- section: The command queue
- relevance: 5 - depends on the GIC version
- words: 80

When the driver unmaps a vPE, is a synchronisation command appended after the
VMAPP? Does it depend on the GIC version, and what in the code enforces that?
Start from `its_build_vmapp_cmd()`.

## gicv3.cmdq-usage: Adding a command path

- section: The command queue
- relevance: 5 - three of the four steps fail silently
- words: 110

What usage in a new command builder or a new path that queues ITS commands is
unsafe (publishing, byte order, the choice of send function, the builder's
return value), and what that looks similar is correct? Name in-tree code that
shows the correct form.

## gicv3.its-tables: Programming the ITS tables

- section: ITS tables
- relevance: 4 - the register may not keep what was written
- words: 140

How does the driver size and program a `GITS_BASER` register: probing the page
size, deciding between a flat and a two-level table, what it does when the
shareability or another field does not stick, when it flushes the table, and
how a physical address above 48 bits is handled? Start from
`its_alloc_tables()` and `its_setup_baser()`.

## gicv3.its-l2-alloc: Second-level tables

- section: ITS tables
- relevance: 4 - the table must be visible before a command uses it
- words: 100

When is a second-level device or vPE table page allocated, what is done, in
order, to make the page and the first-level entry visible to the hardware, and
what bounds the device ID? Start from `its_alloc_table_entry()` and
`allocate_vpe_l2_table()`.

## gicv3.its-vpe-table: Sharing the vPE table

- section: ITS tables
- relevance: 3 - GICv4.1 shares one table among ITSs and redistributors
- words: 120

On GICv4.1, which ITSs and redistributors share a vPE table, how does a newly
booted CPU or a newly probed ITS find a table to inherit, and what does
`vpe_table_mask` record? Start from `allocate_vpe_l1_table()`,
`inherit_vpe_l1_table_from_its()` and `find_sibling_its()`.

## gicv3.common-aff: Grouping by affinity

- section: ITS tables
- relevance: 4 - the mask direction is easy to get backwards
- words: 80

How does `compute_common_aff()` turn a redistributor's type register into a
grouping key: which field selects the group size, which affinity bits are kept
and which cleared for each value, and who compares the result?

## gicv3.noncoherent: Non-coherent GICs

- section: ITS tables
- relevance: 4 - a new table type is where this gets forgotten
- words: 130

Which flags say that an ITS or the redistributors cannot snoop the CPU caches,
what sets each (hardware read-back, a devicetree property, an ACPI flag, a
quirk), and what does the driver do differently for the command queue, the ITS
tables, the property table, the pending tables and the GICv4 tables?

## gicv3.lpi-tables: LPI property and pending tables

- section: LPIs
- relevance: 4 - one is global and the other is per CPU
- words: 130

How many LPI property tables and pending tables does the driver have, how big
are they, when and with which allocation flags are they allocated, and how are
they kept from being reused by a kernel started with kexec? Start from
`allocate_lpi_tables()` and `its_cpu_memreserve_lpi()`.

## gicv3.lpi-idbits: LPI ID width

- section: LPIs
- relevance: 4 - the driver caps what the hardware advertises
- words: 100

How is `lpi_id_bits` chosen on each of the two paths in
`its_setup_lpi_prop_table()`, what is `ITS_MAX_LPI_NRBITS` and why, and what
else can reduce the number of LPIs handed to the allocator? Start from
`its_lpi_init()`.

## gicv3.lpi-prealloc: Booting with LPIs already enabled

- section: LPIs
- relevance: 3 - kexec and kdump arrive this way
- words: 120

What does the driver do when a redistributor already has LPIs enabled at boot:
when does it adopt the tables the previous kernel programmed, what does it
check, and what does it do when it cannot? Start from `allocate_lpi_tables()`,
`enabled_lpis_allowed()` and `redist_disable_lpis()`.

## gicv3.lpi-cpu-init: Enabling LPIs on a CPU

- section: LPIs
- relevance: 3 - runs again on every hotplug
- words: 130

What does `its_cpu_init_lpis()` do, in order, what does it do when the
redistributor does not keep the shareability it was given, what does it set up
for GICv4, and what makes a second call on the same CPU return early? What does
`its_cpu_init_collection()` then send?

## gicv3.lpi-config: Changing an LPI's configuration

- section: LPIs
- relevance: 5 - a change that is not invalidated has not been published
- words: 130

What are the steps of enabling, disabling or reprioritising an LPI: where is
the byte written, how is it made visible, and how does the driver choose
between the three ways of invalidating the cached copy? Start from
`lpi_write_config()` and `lpi_update_config()`.

## gicv3.lpi-direct-inv: Invalidating through the redistributor

- section: LPIs
- relevance: 3 - two register accesses that must be atomic
- words: 100

How does the driver invalidate one LPI, or all of a vPE's, by writing a
redistributor register: which registers, which lock makes the write and the
wait atomic, how is the target redistributor chosen and held, and what is
polled? Start from `__direct_lpi_inv()` and `irq_to_cpuid_lock()`.

## gicv3.lpi-allocator: The LPI number allocator

- section: LPIs
- relevance: 4 - a broken invariant shows no symptom where the bug is
- words: 130

How does the driver keep track of free LPI numbers: the data structure, the
lock, how a range is allocated and what the caller does when the request
cannot be met, how a range is freed, and which invariant of the list freeing
must preserve? Start from `alloc_lpi_range()`, `free_lpi_range()` and
`its_lpi_alloc()`.

## gicv3.lpi-affinity: LPI target CPU selection

- section: LPIs
- relevance: 3 - the policy is the driver's own
- words: 120

How does the driver pick the CPU an LPI is routed to at activation and on an
affinity change: what is counted per CPU, how are managed interrupts and the
ITS's NUMA node taken into account, which erratum restricts the choice, which
command moves the LPI, and what happens for an LPI forwarded to a vCPU? Start
from `its_select_cpu()` and `its_set_affinity()`.

## gicv3.msi-prepare: Preparing a device for MSIs

- section: LPIs
- relevance: 4 - two devices can resolve to one device ID
- words: 130

How does `its_msi_prepare()` find or create the ITS device for a device ID:
where does the ID come from, what serialises lookup and creation, what happens
when the device already exists, which ID is refused, and what does
`its_msi_teardown()` keep and what does it free?

## gicv3.msi-parent: Deriving the device ID

- section: LPIs
- relevance: 3 - aliases change both the ID and the vector count
- words: 100

Where is a PCI or platform device's ITS device ID derived, how are DMA aliases
and bridges taken into account when counting vectors, and how does the result
reach the ITS driver? Start from `drivers/irqchip/irq-gic-its-msi-parent.c`.

## gicv3.lpi-activate: Activating an LPI

- section: LPIs
- relevance: 3 - the mapping exists only between activate and deactivate
- words: 80

What do the ITS domain's allocate, activate, deactivate and free callbacks
each do to the hardware and to the driver's bookkeeping, and which commands do
they send? Start from `its_irq_domain_activate()`.

# GICv4 direct injection

## gicv3.v4-structs: vPE and VM objects

- section: GICv4 objects
- relevance: 4 - KVM embeds these and the driver owns their meaning
- words: 140

What do `struct its_vm`, `struct its_vpe` and `struct its_vlpi_map` hold, which
fields exist only for GICv4.0 or only for GICv4.1, and where does KVM embed
them? Start from `include/linux/irqchip/arm-gic-v4.h`.

## gicv3.v4-api: The GICv4 interface

- section: GICv4 objects
- relevance: 4 - everything is tunnelled through one irqchip callback
- words: 150

Which functions does `drivers/irqchip/irq-gic-v4.c` export to KVM, which
command type does each pass through `irq_set_vcpu_affinity()`, and which
function in the ITS driver handles it? A table. Which of them require
preemption to be disabled?

## gicv3.v4-irqchips: vPE and vSGI interrupt chips

- section: GICv4 objects
- relevance: 3 - the doorbell is an ordinary Linux interrupt
- words: 120

Which `struct irq_chip` represents a vPE's doorbell on GICv4.0, which on
GICv4.1, and which represents a virtual SGI, and how do their mask, unmask,
affinity and state callbacks differ? Start from `its_vpe_irq_chip`,
`its_vpe_4_1_irq_chip` and `its_sgi_irq_chip`.

## gicv3.v4-locks: GICv4 locks

- section: GICv4 objects
- relevance: 5 - the order is documented in one comment
- words: 130

Which locks does the GICv4 code use (per VM, per vPE, global, per device, per
redistributor, the proxy device's), what does each protect, and in what order
may they nest? Where is the order written down? Start from `vmapp_lock`,
`vpe_lock`, `vmovp_lock` and `rd_lock`.

## gicv3.v4-col-idx: A vPE's current redistributor

- section: GICv4 objects
- relevance: 5 - the interrupt descriptor lock is not enough
- words: 110

Which field records the redistributor a vPE is mapped to, which paths read it,
and what usage of it is unsafe? What that looks similar is correct, and which
helpers take the lock for the caller? Start from `vpe_to_cpuid_lock()` and
`its_vpe_set_affinity()`.

## gicv3.v4-vpe-affinity: Moving a vPE

- section: vPE scheduling
- relevance: 5 - a regression and its fix both live here
- words: 140

What does `its_vpe_set_affinity()` do, in order: what does it check before
touching hardware and what does it do in each outcome of that check, which
locks does it take, how does it choose the target CPU, and what follows the
move command? Start from `gic_requires_eager_mapping()`.

## gicv3.v4-vmovp: Ordering of vPE moves

- section: vPE scheduling
- relevance: 4 - every ITS must see the moves in one order
- words: 90

When does `its_send_vmovp()` send one command and when one per ITS, what
serialises the second case and what is stamped on each command, and which ITSs
are skipped? Start from `its_list_map` and `vmovp_lock`.

## gicv3.v4-mapping-policy: Eager and lazy vPE mapping

- section: vPE scheduling
- relevance: 4 - decides whether an unmapped vPE is an error
- words: 120

When are a VM's vPEs mapped on every ITS at activation and when only on
demand, which counters drive the on-demand case, and what does `vmapp_count`
count and who reads it? Start from `gic_requires_eager_mapping()`,
`its_map_vm()` and `its_vpe_irq_domain_activate()`.

## gicv3.v4-schedule: Making a vPE resident

- section: vPE scheduling
- relevance: 4 - the two GIC versions program different things
- words: 130

What does making a vPE resident write on GICv4.0 and on GICv4.1, what happens
to the doorbell interrupt in each case, and what does the later commit step
wait for and when can it be skipped? Start from `its_make_vpe_resident()`,
`its_vpe_schedule()`, `its_vpe_4_1_schedule()` and `its_commit_vpe()`.

## gicv3.v4-deschedule: Making a vPE non-resident

- section: vPE scheduling
- relevance: 5 - a lost doorbell is a vCPU that never wakes
- words: 140

What does `its_clear_vpend_valid()` do before and after clearing the valid
bit, what does it report when the hardware does not settle in time, and how do
the GICv4.0 and GICv4.1 deschedule paths use it? What decides whether a
doorbell is requested on GICv4.1, and which lock is held there and why?

## gicv3.v4-vpend-usage: Virtual pending base register writes

- section: vPE scheduling
- relevance: 5 - UNPREDICTABLE while the redistributor is scanning
- words: 80

What usage of a write to a redistributor's virtual pending table base register
is unsafe, and what that looks similar is correct? Name the in-tree helper
that shows the correct form and the boot-time writes that do not use it.

## gicv3.v4-pending-last: The pending-last hint

- section: vPE scheduling
- relevance: 4 - it is a hint and code treats it as one
- words: 90

Who sets and who reads `pending_last` in `struct its_vpe`, what does a true
value promise and what does it not, and why is the bit set unconditionally
when a GICv4.0 vPE is scheduled?

## gicv3.v4-doorbells: Doorbell interrupts

- section: vPE scheduling
- relevance: 4 - GICv4.0 masks in software, GICv4.1 in hardware
- words: 140

How is a vPE's doorbell enabled and disabled on GICv4.0 and on GICv4.1, which
status flags does KVM give the interrupt in each case, what does the doorbell
handler do, and how is a doorbell that fires while the vPE is being made
non-resident kept from being lost? Start from `vgic_v4_doorbell_handler()` and
`its_make_vpe_non_resident()`.

## gicv3.v4-proxy-device: The doorbell proxy device

- section: vPE scheduling
- relevance: 3 - exists only to invalidate a doorbell on GICv4.0
- words: 110

What is the vPE proxy device, on which hardware is it used, how many slots
does it have and how is a slot reclaimed, which device ID does it take, and
which lock protects it? Start from `its_init_vpe_domain()` and
`its_vpe_db_proxy_map_locked()`.

## gicv3.v4-vlpi-map: Mapping a virtual LPI

- section: Virtual LPIs and SGIs
- relevance: 4 - the ITS has no idempotent map
- words: 140

What are the steps of turning a host LPI into a virtual LPI and back: what is
checked first, what is sent when the interrupt is already forwarded, in what
order are the physical mapping dropped and the virtual one installed, and what
is freed with the last one? Start from `its_vlpi_map()` and
`its_vlpi_unmap()`.

## gicv3.v4-vlpi-doorbell: Per-interrupt doorbell control

- section: Virtual LPIs and SGIs
- relevance: 2 - an odd command used on purpose
- words: 70

How does the driver turn the doorbell of one virtual LPI on or off on GICv4.0,
why does it not remap the interrupt, and what does GICv4.1 do instead? Start
from `its_vlpi_set_doorbell()`.

## gicv3.v4-vsgi: Virtual SGIs

- section: Virtual LPIs and SGIs
- relevance: 3 - configuration and pending state need separate commands
- words: 140

On which hardware are virtual SGIs available, how is one configured, made
pending, cleared and read back, which ITS receives the command, and why does
deactivation send two commands? Start from `its_configure_sgi()`,
`its_sgi_set_irqchip_state()` and `its_sgi_get_irqchip_state()`.

## gicv3.v4-vpe-init: Creating and destroying vPEs

- section: Virtual LPIs and SGIs
- relevance: 3 - the unwind has to mirror a partial allocation
- words: 120

What does allocating a VM's vPE interrupts allocate (doorbell LPIs, property
table, vPE IDs, pending tables, table entries), what is undone when one vPE
fails part way, and what is flushed when the last mapping of a vPE goes? Start
from `its_vpe_irq_domain_alloc()`, `its_vpe_init()` and
`its_vpe_irq_domain_deactivate()`.

## gicv3.v4-boot-cleanup: Stale vPE state at boot

- section: Virtual LPIs and SGIs
- relevance: 3 - a previous kernel may have left a vPE resident
- words: 90

Where does the driver clear virtual pending and property table state left in a
redistributor by firmware or a previous kernel, what exactly does it write,
and why in that order? Start from `__gic_update_rdist_properties()` and
`allocate_vpe_l1_table()`.

# KVM's virtual GIC

## gicv3.vgic-global: Host GIC information in KVM

- section: vGIC objects
- relevance: 3 - the irqchip driver and KVM meet here
- words: 110

How does the host GIC driver tell KVM what hardware it found, what does
`kvm_vgic_global_state` hold, and what enables GICv4 use by KVM? Start from
`struct gic_kvm_info`, `vgic_set_kvm_info()` and `vgic_v3_probe()`.

## gicv3.vgic-irq: One virtual interrupt

- section: vGIC objects
- relevance: 5 - every vGIC function manipulates this
- words: 150

What does `struct vgic_irq` hold, which lock protects its contents, what is
the difference between `vcpu` and `target_vcpu`, and where do the structures
for SGIs and PPIs, for SPIs and for LPIs live? Which fields are meaningful only
for an interrupt tied to a hardware one? Start from `include/kvm/arm_vgic.h`.

## gicv3.vgic-irq-ops: Per-interrupt callbacks

- section: vGIC objects
- relevance: 3 - in-kernel devices change vGIC behaviour through these
- words: 100

What can `struct irq_ops` override for one virtual interrupt, what does the
flag it can report mean, how is it installed and under which lock, and who
installs one? Start from `kvm_vgic_set_irq_ops()`.

## gicv3.vgic-lookup: Looking up a virtual interrupt

- section: vGIC objects
- relevance: 4 - bounds and references differ by kind
- words: 110

What do `vgic_get_irq()` and `vgic_get_vcpu_irq()` do for each kind of
interrupt ID: how is the ID bounded, what guards the array index against
speculation, when do they return NULL, and which results must be released with
`vgic_put_irq()`?

## gicv3.vgic-lock-order: vGIC lock order

- section: vGIC objects
- relevance: 5 - written down once, violated by indirect calls
- words: 130

What is the documented order of the VM, vCPU, configuration, ITS, LPI xarray,
list and interrupt locks in the vGIC, which of them must be taken with
interrupts disabled and why, what extra ordering applies to the configuration
lock, and how are two vCPUs' list locks ordered? Start from the comment at the
top of `arch/arm64/kvm/vgic/vgic.c`.

## gicv3.vgic-dist-cpu: Distributor and per-vCPU state

- section: vGIC objects
- relevance: 3 - the flags gate the run loop
- words: 120

Which fields of `struct vgic_dist` say how far set-up has got, what do
`lpi_xa`, `propbaser`, `active_spis` and `rd_regions` hold, and which fields of
`struct vgic_cpu` describe the emulated redistributor?

## gicv3.vgic-lpi-refs: References on an LPI

- section: LPI lifetime
- relevance: 5 - the use-after-free bugs live here
- words: 110

Which long-lived things hold a reference on an LPI's `struct vgic_irq`, which
call takes and which drops each of them, and what do SGIs, PPIs and SPIs do
with the reference count? Start from `vgic_add_lpi()`,
`vgic_queue_irq_unlock()` and `vgic_its_cache_translation()`.

## gicv3.vgic-lpi-get: References taken by lookups

- section: LPI lifetime
- relevance: 5 - a pointer returned without a reference can be freed
- words: 100

What usage in a function that looks an LPI up and returns it is unsafe, and
what that looks similar is correct? What does `vgic_try_get_irq_ref()` return
for an object whose count has reached zero, and which in-tree lookups show the
correct shape?

## gicv3.vgic-lpi-put: Dropping a reference

- section: LPI lifetime
- relevance: 5 - the decrement and the eviction must not be separable
- words: 110

How does `vgic_put_irq()` make dropping the last reference and removing the
LPI from the xarray one step, how is the memory freed, and what extra thing
does it do on a kernel built with lock debugging and why?

## gicv3.vgic-lpi-norelease: Deferred release

- section: LPI lifetime
- relevance: 5 - the caller inherits an obligation
- words: 120

Which callers cannot use `vgic_put_irq()` and why, what do they call instead,
what must they do with its return value and when, and how does the deferred
release find the objects to free? Is there a flag on the object that says it
is awaiting release?

## gicv3.vgic-lpi-add: Registering an LPI

- section: LPI lifetime
- relevance: 4 - two CPUs can map the same LPI at once
- words: 130

What does `vgic_add_lpi()` do outside and inside the xarray lock: what is
reserved or allocated before the lock, which allocation flags does the store
under the lock use and why, what does it do when another CPU got there first or
when the slot holds an object whose count is zero, and what is undone on a
later failure?

## gicv3.vgic-lpi-flush: Disabling LPIs on a redistributor

- section: LPI lifetime
- relevance: 4 - a guest can do this while another vCPU migrates an interrupt
- words: 110

What happens when a guest clears the LPI enable bit of a redistributor: how is
the transition tracked, what does `vgic_flush_pending_lpis()` remove and what
does it leave untouched on each interrupt, and what else is invalidated? Start
from `vgic_mmio_write_v3r_ctlr()`.

## gicv3.vgic-translation-cache: The translation cache

- section: LPI lifetime
- relevance: 5 - three unserialised paths drain it
- words: 140

What does each virtual ITS's translation cache map, what reference does an
entry hold, which interrupts are never cached and what is done when the store
fails or displaces an entry, which paths invalidate it and do they exclude one
another? What usage when draining it is unsafe, and what is correct? Start
from `vgic_its_cache_translation()` and `vgic_its_invalidate_cache()`.

## gicv3.vgic-queue: Queueing an interrupt

- section: The list of active and pending interrupts
- relevance: 5 - the lock dance every injection goes through
- words: 140

What does `vgic_queue_irq_unlock()` do: which lock is held on entry and on
return, when does it do nothing but kick, why does it drop and retake locks
and what does it re-check afterwards, what reference does it take, and when
does it kick every vCPU instead of one?

## gicv3.vgic-target-oracle: Choosing the vCPU

- section: The list of active and pending interrupts
- relevance: 4 - one function answers "where should this go"
- words: 80

What does `vgic_target_oracle()` return for an active interrupt, for an
enabled and pending one, and otherwise, what effect does a disabled
distributor have, and which lock must the caller hold?

## gicv3.vgic-prune: Pruning and migrating

- section: The list of active and pending interrupts
- relevance: 5 - locks are dropped in the middle of a list walk
- words: 150

How does `vgic_prune_ap_list()` move an interrupt to another vCPU's list: what
keeps the interrupt alive while locks are dropped, in what order are the two
lists locked, what is re-checked before the move and what usage of that check
would be unsafe, what happens to the walk afterwards, and is pending state
carried over?

## gicv3.vgic-flush-lr: Filling the list registers

- section: The list of active and pending interrupts
- relevance: 5 - decides what the guest can see
- words: 150

Before guest entry, how does `vgic_flush_lr_state()` decide which interrupts
go into the list registers: when is the list sorted and by what, what is
recorded about the last interrupt loaded, and which maintenance and trap bits
does `vgic_v3_configure_hcr()` set for which condition?

## gicv3.vgic-compute-lr: Encoding a list register

- section: The list of active and pending interrupts
- relevance: 4 - several states are never written together
- words: 140

How does `vgic_v3_compute_lr()` encode an interrupt: when is the hardware bit
set and with which physical ID, when is the end-of-interrupt maintenance bit
set, when is a pending state withheld, how is a multi-source GICv2 SGI
presented, and what stops one interrupt from occupying two list registers?
Start from `vgic_v3_populate_lr()` and `on_lr`.

## gicv3.vgic-fold-lr: Reading the list registers back

- section: The list of active and pending interrupts
- relevance: 4 - the hardware state becomes the software state here
- words: 140

After a guest exit, what does `vgic_v3_fold_lr()` take from a list register
for each kind of interrupt (active state, pending state for edge and level,
LPIs), what may the lookup return and why, when is an acknowledged level
interrupt reported to irqfd users, and what is dropped at the end?

## gicv3.vgic-eoicount: Deactivations outside the list registers

- section: The list of active and pending interrupts
- relevance: 5 - walking from the wrong place deactivates the wrong interrupts
- words: 120

With priority drop and deactivation combined, how does the vGIC account for
interrupts the guest deactivated that were not in a list register: which
counter says how many, where does the walk of the list start and why there,
which entries does it pick, and what is done for one backed by a hardware
interrupt? Start from `vgic_v3_fold_lr_state()` and `last_lr_irq`.

## gicv3.vgic-dir-trap: Deactivations by trap

- section: The list of active and pending interrupts
- relevance: 4 - split EOI mode gives no ordering to rely on
- words: 150

When the guest splits priority drop from deactivation, when is the deactivate
register trapped, what does `active_spis` count and who changes it, and what
are the cases `vgic_v3_deactivate()` distinguishes and what does it do in
each? When does it skip deactivating the physical interrupt, and why?

## gicv3.vgic-pending-check: Deliverable interrupt check

- section: The list of active and pending interrupts
- relevance: 4 - decides whether a vCPU blocks
- words: 100

What does `kvm_vgic_vcpu_pending_irq()` look at to decide that a vCPU has a
deliverable interrupt, where does it get the guest's priority mask from, and
what short-cuts does it take for a disabled distributor and for GICv4?

## gicv3.vgic-vmcr: The virtual machine control register

- section: World switch
- relevance: 5 - a stale priority mask blocks a vCPU for ever
- words: 130

When is the hardware copy of the virtual machine control register written from
and saved to `vgic_vmcr`: at vCPU load and put, or at each guest entry and
exit, and does it depend on the emulated GIC model or on the hypervisor mode?
What does `vgic_get_vmcr()` read? Start from `__vgic_v3_save_state()`,
`__vgic_v3_restore_vmcr_aprs()` and `__vgic_v3_activate_traps()`.

## gicv3.vgic-wfi: Blocking in WFI

- section: World switch
- relevance: 5 - residency cannot be used to infer intent to block
- words: 110

What does `kvm_vcpu_wfi()` do to the vGIC before and after halting, which vCPU
flag does it set, why with preemption disabled, and which vGIC decisions are
keyed on that flag rather than on whether the vPE is resident?

## gicv3.vgic-load-put: Loading and putting a vCPU

- section: World switch
- relevance: 4 - what is per load and what is per entry
- words: 120

What do `vgic_v3_load()` and `vgic_v3_put()` save and restore, and what is
instead handled at every guest entry and exit by `kvm_vgic_flush_hwstate()`
and `kvm_vgic_sync_hwstate()`? What differs for a protected guest and with
the virtualization host extensions?

## gicv3.vgic-traps: Trapping the CPU interface

- section: World switch
- relevance: 3 - errata and options turn traps on for everyone
- words: 110

Which conditions make KVM trap a guest's accesses to the group 0, group 1 and
common CPU interface registers and to the deactivate register, where is the
set of trap bits computed and how does it reach the register, and what handles
a trapped access? Start from `kvm_compute_ich_hcr_trap_bits()` and
`__vgic_v3_perform_cpuif_access()`.

## gicv3.vgic-maint-irq: The maintenance interrupt

- section: World switch
- relevance: 3 - it only forces an exit
- words: 70

What does the vGIC maintenance interrupt handler do, where is the work that
the interrupt signals actually done, and what is different when the vCPU is
running a nested guest? Start from `vgic_maintenance_handler()`.

## gicv3.vgic-mapped: Mapping a hardware interrupt

- section: Mapped and directly injected interrupts
- relevance: 4 - state is split between software and hardware
- words: 110

What does `kvm_vgic_map_phys_irq()` record, how is the physical interrupt ID
found, what does the unmap do, how is a mapped interrupt reset when the VM is
reset and by whom, and who may inject a mapped interrupt? Start from
`kvm_vgic_map_irq()` and `kvm_vgic_reset_mapped_irq()`.

## gicv3.vgic-resample: Resampling a mapped level interrupt

- section: Mapped and directly injected interrupts
- relevance: 4 - a stale level is a spurious injection
- words: 110

When and how does the vGIC re-read the line of a level-triggered interrupt
tied to a hardware one, what does it do to the physical active state as a
result, and what differs for an interrupt whose callbacks ask for software
resampling? Start from `vgic_irq_handle_resampling()`.

## gicv3.vgic-pending-access: Pending state by accessor

- section: Mapped and directly injected interrupts
- relevance: 4 - userspace cannot read hardware state the guest path reads
- words: 140

How do a guest's and userspace's reads and writes of the pending registers
differ: what does each read return for a mapped level interrupt, for a virtual
SGI backed by hardware and for an ordinary one, and what does each write do to
the physical interrupt? Start from `__read_pending()`, `__set_pending()` and
`__clear_pending()`.

## gicv3.vgic-active-access: Active state register writes

- section: Mapped and directly injected interrupts
- relevance: 3 - the interrupt may sit in a running vCPU's list registers
- words: 100

What does the vGIC do before and after a write to the set-active or
clear-active registers so that the change is not overwritten, under which
lock, and what is done for a mapped interrupt and for a hardware-backed
virtual SGI? Start from `vgic_access_active_prepare()` and
`vgic_mmio_change_active()`.

## gicv3.vgic-v4-forwarding: Forwarding a device interrupt

- section: Mapped and directly injected interrupts
- relevance: 4 - failure is deliberately silent
- words: 140

What does `kvm_vgic_v4_set_forwarding()` do: which locks does it take, in
which cases does it return success without mapping anything, what does it hand
the ITS driver, and how is pending state moved? How does
`kvm_vgic_v4_unset_forwarding()` find the interrupt?

## gicv3.vgic-v4-load-put: vPE residency from KVM

- section: Mapped and directly injected interrupts
- relevance: 4 - the put serves two purposes at once
- words: 120

What do `vgic_v4_load()` and `vgic_v4_put()` do and when do they do nothing,
what decides whether a doorbell is requested, and which request makes every
vCPU reload its vPE? Start from `vgic_v4_want_doorbell()`.

## gicv3.vgic-v4-vsgi: Switching SGIs to hardware

- section: Mapped and directly injected interrupts
- relevance: 3 - state has to move between software and hardware
- words: 120

What makes a guest's SGIs hardware-backed on GICv4.1, when can the guest or
userspace change that, what is transferred in each direction, and what is
done to the running vCPUs meanwhile? Start from `vgic_v4_configure_vsgis()`
and `vgic_mmio_write_v3_misc()`.

## gicv3.vgic-v4-init: GICv4 set-up for a VM

- section: Mapped and directly injected interrupts
- relevance: 3 - called from two places
- words: 110

When is `vgic_v4_init()` called, what does it allocate and request, which
interrupt status flags does it set and how do they differ between GICv4.0 and
GICv4.1, and how does it clean up after a failure part way through?

## gicv3.vgic-pending-tables: Guest LPI pending tables

- section: Mapped and directly injected interrupts
- relevance: 3 - migration reads and writes guest memory
- words: 130

When does KVM read an LPI's pending bit from the guest's pending table and
when does it write the table, what does it clear after reading, and how does
saving the tables get the state of directly injected LPIs on GICv4.1? Start
from `vgic_v3_lpi_sync_pending_status()` and
`vgic_v3_save_pending_tables()`.

# The emulated ITS

## gicv3.vits-structs: Virtual ITS objects

- section: Virtual ITS structures
- relevance: 4 - same names as the host driver, different structures
- words: 130

What do `struct vgic_its` and KVM's own `struct its_device`,
`struct its_collection` and `struct its_ite` hold, what does each of the two
mutexes in `struct vgic_its` protect, and what does an unmapped collection
look like? Start from `arch/arm64/kvm/vgic/vgic.h`.

## gicv3.vits-cmdq: Processing guest commands

- section: Virtual ITS commands
- relevance: 4 - the write pointer is a guest-controlled value
- words: 130

What happens when a guest writes the virtual ITS's command write register: how
is the value validated, under which lock are commands processed, what is done
when a command cannot be read from guest memory or a handler returns an error,
and can the emulated queue stall? Start from `vgic_mmio_write_its_cwriter()`
and `vgic_its_process_commands()`.

## gicv3.vits-handlers: Command handlers

- section: Virtual ITS commands
- relevance: 3 - one table to find a handler
- words: 140

Which ITS commands does the emulation handle and with which function, which
does it ignore, and what kinds of values do the handlers return? A table with
the main check each handler makes.

## gicv3.vits-mapti: Mapping an event

- section: Virtual ITS commands
- relevance: 4 - every field is guest-supplied
- words: 120

What does `vgic_its_cmd_handle_mapi()` check about the device, the event ID,
the LPI number and the collection, what does it do when the event is already
mapped, and what does it undo when a later step fails?

## gicv3.vits-mapd-discard: Unmapping devices and events

- section: Virtual ITS commands
- relevance: 5 - a stale entry in guest memory is resurrected by restore
- words: 120

What do `vgic_its_cmd_handle_mapd()` and `vgic_its_cmd_handle_discard()` check,
and what do they do, besides freeing the in-kernel objects, when a device or
an event is unmapped? What does a hardware-forwarded interrupt need on that
path? Start from `its_free_ite()`.

## gicv3.vits-inject: Injecting an MSI

- section: Virtual ITS commands
- relevance: 3 - a fast path and a slow path
- words: 110

What are the two paths `vgic_its_inject_msi()` can take, what does each hold,
what do the different return values mean to the caller, and how is a directly
injected interrupt handled? Start from
`vgic_its_inject_cached_translation()` and `vgic_its_trigger_msi()`.

## gicv3.vits-abi: Table format revisions

- section: Virtual ITS save and restore
- relevance: 4 - the entry size is part of the user ABI
- words: 130

How does the virtual ITS describe the format it saves its tables in, how does
userspace select a revision and how is the value it writes validated, and how
do the helpers that read and write one table entry in guest memory check the
entry size? Start from `struct vgic_its_abi`, `vgic_its_read_entry_lock` and
`vgic_mmio_uaccess_write_its_iidr()`.

## gicv3.vits-save: Saving the tables

- section: Virtual ITS save and restore
- relevance: 4 - the image must restore into something that was live
- words: 120

In what order are the device, translation and collection tables saved, how are
entries ordered and linked, what is written for an event whose collection was
unmapped, and when does saving fail because of a directly injected interrupt?
Start from `vgic_its_save_tables_v0()`.

## gicv3.vits-restore: Restoring the tables

- section: Virtual ITS save and restore
- relevance: 5 - parses data the guest or a migration source controls
- words: 150

In what order are the tables restored, and what does each restore handler
validate about an entry before acting on it? Which of those checks repeat what
the live command handler for the same object refuses, and what is freed when a
restore fails part way? Start from `vgic_its_restore_dte()`,
`vgic_its_restore_ite()` and `vgic_its_restore_cte()`.

## gicv3.vits-scan: Guest table walks

- section: Virtual ITS save and restore
- relevance: 5 - the step comes from the entry being read
- words: 100

How does `scan_its_table()` advance through a table, what bounds the walk, and
what form of the loop would be unsafe? What do its return values mean, and how
is a two-level device table walked with it? Start from `handle_l1_dte()`.

## gicv3.vits-ctrl-locking: Locks for user requests

- section: Virtual ITS save and restore
- relevance: 3 - user requests must exclude running vCPUs
- words: 100

Which locks do the virtual ITS's control and register-access requests take,
in what order, what error is returned when a vCPU is running, and in what
order does the documentation tell userspace to restore the ITS registers and
tables?

# Emulated registers and lifecycle

## gicv3.vgic-mmio: The register emulation framework

- section: Emulated registers
- relevance: 3 - guest and userspace accessors are separate on purpose
- words: 120

How are the emulated distributor, redistributor and ITS registers described:
what does a `struct vgic_register_region` hold, how do guest accesses and
userspace accesses reach different callbacks, and what happens to an access of
a width the region does not allow? Start from
`arch/arm64/kvm/vgic/vgic-mmio.h` and `vgic_uaccess()`.

## gicv3.vgic-rd-inv: Invalidate registers of the redistributor

- section: Emulated registers
- relevance: 4 - the value is an interrupt ID the guest chose
- words: 100

What do the emulated redistributor's LPI invalidate registers check before
acting on a guest write, in each dimension of the value and of the access, and
what do they do while the operation runs? Start from
`vgic_mmio_write_invlpi()` and `vgic_mmio_write_invall()`.

## gicv3.vgic-rd-typer: The redistributor type register

- section: Emulated registers
- relevance: 3 - userspace can read it before anything is configured
- words: 90

How is the emulated redistributor type register built, how is the bit that
marks the last redistributor of a region computed, and what does that
computation do when the redistributor has not been placed in a region yet?
Start from `vgic_mmio_vcpu_rdist_is_last()`.

## gicv3.vgic-propbaser: LPI table base registers

- section: Emulated registers
- relevance: 3 - one property table for the whole VM
- words: 90

Where are the emulated LPI property and pending table base registers stored,
which of them is shared by all redistributors and what does the virtual ITS
advertise as a result, when is a write ignored, and how is the value
sanitised?

## gicv3.vgic-sgi-dispatch: Guest-generated SGIs

- section: Emulated registers
- relevance: 4 - the register value is guest-supplied
- words: 110

How does `vgic_v3_dispatch_sgi()` decode a guest's write to an SGI generation
register: how are the SGI number, the targets and the broadcast mode
extracted, how do the three registers differ in which group they may raise,
and what is done for a hardware-backed SGI?

## gicv3.vgic-id-regs: Identification registers from userspace

- section: Emulated registers
- relevance: 4 - the write must use the value written
- words: 120

Which distributor registers may userspace write before the vGIC is
initialised and why, what does a write to the implementer identification
register or to the second type register validate and change, and what usage in
such a write handler would be incorrect? Start from
`vgic_mmio_uaccess_write_v3_misc()` and `reg_allowed_pre_init()`.

## gicv3.vgic-create: Creating the vGIC

- section: vGIC lifecycle
- relevance: 4 - excludes half-created vCPUs
- words: 120

What does `kvm_vgic_create()` lock and check before creating the device, what
makes it refuse, what does it set up for the vCPUs that already exist, and
what does it undo on failure?

## gicv3.vgic-init: Initialising the vGIC

- section: vGIC lifecycle
- relevance: 4 - GICv3 must be initialised explicitly
- words: 110

What does `vgic_init()` allocate and set up and under which lock, when does it
refuse, which model may be initialised lazily on first use, and what may a
caller do before `vgic_initialized()` is true? Start from `vgic_lazy_init()`
and `kvm_vgic_inject_irq()`.

## gicv3.vgic-map-resources: Publishing readiness

- section: vGIC lifecycle
- relevance: 5 - a vCPU must not run against a half-built distributor
- words: 130

What does `kvm_vgic_map_resources()` do on a vCPU's first run: which locks does
it take and which does it drop before registering the distributor's registers,
how and when is the ready flag published and read, which model registers no
distributor at all, and what happens to the VM on failure?

## gicv3.vgic-redist-iodev: Registering redistributors

- section: vGIC lifecycle
- relevance: 4 - registration and its undo happen in different places
- words: 140

When is a vCPU's redistributor register frame registered, which locks are
held and which is dropped around the bus registration, what is rolled back
when setting a region's base fails for one vCPU, and where is the frame
unregistered for a vCPU that was created successfully and for one whose
creation failed? Start from `vgic_register_redist_iodev()` and
`__kvm_vgic_vcpu_destroy()`.

## gicv3.vgic-destroy: Tearing the vGIC down

- section: vGIC lifecycle
- relevance: 4 - the unwind is not the mirror image it seems
- words: 110

In what order does `kvm_vgic_destroy()` release things, which locks does it
hold for which part, and why are the redistributor frames unregistered after
the configuration lock is dropped?

## gicv3.vgic-config-lock: Scope of the configuration lock

- section: vGIC lifecycle
- relevance: 5 - fixes have both added and removed it
- words: 100

What usage of `kvm->arch.config_lock` around registering or unregistering
emulated register frames is unsafe, and what that looks similar is correct?
Which locks must be taken before it, and which calls must not be made while
holding it?

## gicv3.vgic-debugfs: The state dump

- section: vGIC lifecycle
- relevance: 3 - a walker over objects that can vanish
- words: 100

How does the vGIC state file in debugfs walk the interrupts, how does it find
the next LPI, what does it do when an interrupt it is about to print no longer
exists, and what does it hold while printing? Start from
`arch/arm64/kvm/vgic/vgic-debug.c`.

## gicv3.vgic-nested: A guest hypervisor's list registers

- section: Nested guests and GICv5 hosts
- relevance: 3 - the guest hypervisor owns the list registers
- words: 140

When a vCPU runs a nested guest, where do the list registers loaded into
hardware come from, what is translated on the way in, what is copied back on
exit, how is a hardware-backed entry's deactivation emulated, and how is the
guest hypervisor's maintenance interrupt generated? Start from
`vgic_state_is_nested()` and `arch/arm64/kvm/vgic/vgic-v3-nested.c`.

## gicv3.vgic-v5-host: GICv3 guests on GICv5 hosts

- section: Nested guests and GICv5 hosts
- relevance: 4 - half of the code applies and half does not
- words: 130

What does KVM need from a GICv5 host to offer a guest a GICv3, which parts of
the GICv3 code then run and which hardware is absent, what is done differently
to deactivate a physical interrupt, and what selects the compatibility mode on
the CPU? Start from `vgic_v5_probe()`, `vgic_host_has_gicv3()` and
`__vgic_v3_compat_mode_enable()`.

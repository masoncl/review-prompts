# Questions: GICv3 and GICv4

- guide: gic-v3.md
- title: GICv3/v4 Subsystem Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/gic-v3-measurement.md` is the
wider set the readers were measured on and `catalogue/gic-v3-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## gicv3.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## gicv3.files: Source files

- section: Finding your way
- relevance: 4 - the subject is spread over three directories

A table and nothing else, job to file: the distributor, redistributor and CPU
interface driver; the ITS driver; the GICv4 layer; message-based SPIs; the code
shared with GICv2; the MSI parent glue; the register and priority headers; the
arm64 system register accessors; KVM's virtual GIC, one row per file; the
hypervisor save and restore code; the user-visible system register table; the
documents that hold the KVM device ABI for the virtual GICv3 and the virtual
ITS. Where a reader is likely to look for a file that does not exist in this
tree, say so in the row. Start from `drivers/irqchip/irq-gic-v3.c` and
`arch/arm64/kvm/vgic/`.

## gicv3.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to the function to start reading from: probing
from devicetree and from ACPI; bringing up a secondary CPU; taking an
interrupt; sending an IPI; preparing MSIs for a device; activating one LPI;
creating and initialising a guest's GIC; the work done before each guest entry
and after each exit; injecting an interrupt into a guest; a guest write to the
ITS command queue; saving the ITS tables for migration. Give the current name
where it has changed. Do not describe what the functions do inside.

# Distributor, redistributors and interrupt chips

## gicv3.intid-ranges: Interrupt ID ranges

- section: Distributor, redistributors and interrupt chips
- relevance: 4 - the wrong frame or offset silently programs another interrupt

For an interrupt in one of the extended ID ranges, which register frame does the driver use, and
how does it derive the register offset and the index within that register? What are the
requirements for using an interrupt ID as a register index in order to assure safe usage? Start
from `__get_intid_range()`, `gic_dist_base()` and `convert_offset_index()`.

## gicv3.rdist-capabilities: Redistributor capability flags

- section: Distributor, redistributors and interrupt chips
- relevance: 4 - GICv4 features are all-or-nothing across CPUs

What does one redistributor that lacks a feature do to each GICv4 capability flag in `struct
rdists`, and what can clear a flag after it was first computed? What must code test to decide
whether a GICv4 feature can be used? Start from `__gic_update_rdist_properties()` and
`gic_init_bases()`.

## gicv3.irq-chips: The two interrupt chips

- section: Distributor, redistributors and interrupt chips
- relevance: 4 - the callbacks differ in ways that matter to KVM

What selects between `gic_chip` and `gic_eoimode1_chip`, what does the choice change for an
interrupt that KVM forwards to a vCPU, and which flow handler does each interrupt ID range get?
Start from `gic_irq_domain_map()`.

## gicv3.eoi-mode: Split priority drop and deactivation

- section: Distributor, redistributors and interrupt chips
- relevance: 4 - decides who deactivates an interrupt

What decides whether the driver runs with priority drop and deactivation
split, who deactivates an interrupt in each mode and when it is forwarded to a
vCPU, and what does KVM learn from the choice? Start from
`supports_deactivate_key`.

## gicv3.fwspec: Firmware interrupt specifiers

- section: Distributor, redistributors and interrupt chips
- relevance: 3 - a bad translation delivers the wrong interrupt

How does the driver translate a devicetree specifier and an ACPI one into an
interrupt ID and trigger type, which forms does it reject and which only warn
about, and how is the affinity of a partitioned PPI found? Start from
`gic_irq_domain_translate()` and `gic_irq_get_fwspec_info()`.

## gicv3.quirks: Quirks and errata

- section: Distributor, redistributors and interrupt chips
- relevance: 3 - each one changes a path reviewers assume is uniform

How does `gic_enable_quirks()` match an entry of `gic_quirks` or of `its_quirks` to the hardware?
Which flag or static key does each quirk set, and what does the driver do differently where it
tests that flag or key? Start from `gic_quirks`, `its_quirks` and `gic_enable_quirks()`.

# Register writes and priorities

## gicv3.rwp-completion: Completing a register write

- section: Register writes and priorities
- relevance: 4 - the error is invisible at the call site

Which bit of which register does the driver poll, for each frame, when it waits for a register
write to take effect, and what does the caller learn when the wait times out? What are the
requirements for waiting after a write to a distributor or a redistributor register in order to
assure safe usage? Start from `gic_do_wait_for_rwp()`, `gic_mask_irq()` and `gic_set_affinity()`.

## gicv3.irqchip-state: Pending and active state

- section: Register writes and priorities
- relevance: 3 - KVM drives mapped interrupts through these

For which interrupt IDs can the pending, active and masked state be read and
written through the irqchip state callbacks and what do the callbacks return
for the rest, and which write is followed by a read of the same register and
why? Start from `gic_irq_set_irqchip_state()` and `gic_peek_irq()`.

## gicv3.prio-views: Distributor and PMR priority views

- section: Register writes and priorities
- relevance: 5 - only one configuration differs and it is the hard one to test

When do the priority written to the distributor and the priority seen in the
CPU interface's mask and running-priority registers differ, how does the
driver find out which case it is in, and does it compensate once or at each
use? Start from `gic_prio_init()`, `gic_has_group0()` and `dist_prio_irq`.

## gicv3.nmi-setup: Making an interrupt a pseudo-NMI

- section: Register writes and priorities
- relevance: 3 - the preconditions are checked in the callbacks

What enables pseudo-NMI support in the driver and what forbids it, what do
`gic_irq_nmi_setup()` and `gic_irq_nmi_teardown()` check and change, and how
does what they change differ between an interrupt that lives in a
redistributor and any other?

## gicv3.nmi-entry: Interrupt entry with pseudo-NMIs

- section: Register writes and priorities
- relevance: 4 - an IRQ taken in NMI context is very hard to debug

What decides whether `gic_handle_irq()` runs `__gic_handle_irq_from_irqson()` or
`__gic_handle_irq_from_irqsoff()`, how does each of them decide whether the acknowledged interrupt
is an NMI, and what does each do to the priority mask around the acknowledge?

## gicv3.ack-sync: After the acknowledge

- section: Register writes and priorities
- relevance: 5 - a handler that runs against stale state

What are the requirements for the code between the read of the interrupt acknowledge register and
the call of the handler, in order to assure safe usage? What does the driver do with the special
interrupt IDs and with an interrupt that has no mapping? Start from `gic_complete_ack()` and
`gic_deactivate_unhandled()`.

## gicv3.prio-usage: Priority constants and variables

- section: Register writes and priorities
- relevance: 5 - a wrong constant misclassifies NMIs on some machines only

What are the requirements for choosing between `GICV3_PRIO_IRQ` and `GICV3_PRIO_NMI` and the
variables `dist_prio_irq` and `dist_prio_nmi`, when code programs an interrupt's priority or
compares against the running priority or the priority mask, in order to assure safe usage? What do
the compile-time assertions beside the constants guarantee that such code relies on? Start from
`include/linux/irqchip/arm-gic-v3-prio.h`.

## gicv3.spec-register-writes: What the architecture specification says

- section: Register writes and priorities
- verbatim: ../verbatim/gic-v3-register-writes.md

# CPU bring-up and IPIs

## gicv3.cpu-init: Per-CPU initialisation

- section: CPU bring-up and IPIs
- relevance: 4 - the order is load-bearing

When a CPU sets up its redistributor and its CPU interface, which steps of
`gic_cpu_init()` and `gic_cpu_sys_reg_init()` rely on an earlier step having
run? What does the check that SGIs can reach every CPU do when it fails?
Start from `gic_cpu_init()` and `gic_cpu_sys_reg_init()`.

## gicv3.sre-enable: Enabling system register access

- section: CPU bring-up and IPIs
- relevance: 4 - an access before it is UNDEFINED

On which paths does the driver enable the system register interface, and what does it do when the
interface cannot be enabled? What else does `gic_cpu_pm_notifier()` save or redo? Start from
`gic_cpu_sys_reg_enable()` and `gic_cpu_pm_notifier()`.

## gicv3.sgi-send: Sending an IPI

- section: CPU bring-up and IPIs
- relevance: 4 - the barriers are the contract with the receiver

What does each barrier before and after the SGI register write in
`gic_ipi_send_mask()` guarantee to the receiver, how are targets grouped into
one write, and how wide is the SGI number field against the number of SGIs
Linux registers as IPIs? Start from `gic_send_sgi()` and `gic_smp_init()`.

## gicv3.hotplug-states: CPU hotplug callbacks

- section: CPU bring-up and IPIs
- relevance: 3 - one of them cannot fail and cannot sleep

Which CPU hotplug callbacks of the GICv3 and ITS drivers may fail, and which run with interrupts
off? What are the requirements for an allocation in a callback that runs with interrupts off, in
order to assure safe usage? Start from `gic_smp_init()` and `its_lpi_memreserve_init()`.

# The ITS command queue

## gicv3.its-node: ITS locks

- section: The ITS command queue
- relevance: 4 - two locks with different jobs

What does each lock in `struct its_node` protect, which of them may be held across a sleep, and
which global list and lock tie the ITSs together? Start from `drivers/irqchip/irq-gic-v3-its.c`.

## gicv3.cmdq-send: Sending one command

- section: The ITS command queue
- relevance: 5 - each step can be got wrong on its own

When `its_send_single_command()` sends one command, which steps run under the ITS lock and which
after it is dropped? What does it do while the queue stays full, and does the caller learn of a
failure? Start from `BUILD_SINGLE_CMD_FUNC` and `its_allocate_entry()`.

## gicv3.cmdq-flush: Publishing a command

- section: The ITS command queue
- relevance: 5 - an unobserved command is silently not executed

How is a command written to the queue made visible to the ITS before the write pointer register is
written, what selects how that is done, and when is the choice made? Start from `its_flush_cmd()`.

## gicv3.cmdq-wait: Waiting for a command

- section: The ITS command queue
- relevance: 5 - wrap-around bugs survive light testing

When the driver waits for the commands it queued to be consumed, what are the requirements for
where and when it samples the starting read position, in order to assure safe usage? How does the
wait handle wrap-around of the queue, and what does it do on a timeout? Start from
`its_wait_for_range_completion()`.

## gicv3.cmdq-builders: Command builders

- section: The ITS command queue
- relevance: 5 - the return value is control flow

What must every command builder do to the command block before returning,
what does its return value control, and which builders return nothing, always
or only on some hardware? Start from `its_build_mapd_cmd()`,
`its_build_vmapp_cmd()` and `its_fixup_cmd()`.

## gicv3.cmdq-sync: Synchronisation commands

- section: The ITS command queue
- relevance: 5 - the wrong one compiles and appears to work

Which synchronisation command does each send function append and against what
object, and how are the virtual forms of INV, INT and CLEAR sent? Start from
`its_build_sync_cmd()`, `its_build_vsync_cmd()` and `its_send_vinv()`.

## gicv3.cmdq-vmapp-sync: Unmapping a vPE

- section: The ITS command queue
- relevance: 5 - depends on the GIC version

When the driver unmaps a vPE, is a synchronisation command appended after the
VMAPP? Does it depend on the GIC version, and what in the code enforces that?
Start from `its_build_vmapp_cmd()`.

## gicv3.cmdq-usage: Adding a command path

- section: The ITS command queue
- relevance: 5 - three of the four steps fail silently

What are the requirements for a new command builder of type `its_cmd_builder_t` or
`its_cmd_vbuilder_t`, and for a new function that sends a command through it, in order to assure
safe usage? Name in-tree code that shows it.

## gicv3.spec-its-commands: What the architecture specification says

- section: The ITS command queue
- verbatim: ../verbatim/gic-v3-its-commands.md

# ITS tables and memory

## gicv3.its-memory: Allocating memory for the GIC

- section: ITS tables and memory
- relevance: 4 - the size argument is easy to misread

For `its_alloc_pages_node()`, `its_alloc_pages()` and `itt_alloc_pool()`, in what unit does the
caller give the amount of memory, and what do they do to the pages besides allocating them? When
does one of them, or `its_free_pages()`, not return pages to the allocator? Start from
`its_alloc_pages_node()` and `itt_alloc_pool()`.

## gicv3.its-quiesce: Disabling and resuming an ITS

- section: ITS tables and memory
- relevance: 4 - writing the base registers of a live ITS is UNPREDICTABLE

Which state must an ITS be in before its table and command queue base
registers are written, which function gets it there, and what do suspend and
resume have to re-issue besides restoring registers? Start from
`its_force_quiescent()`, `its_save_disable()` and `its_restore_enable()`.

## gicv3.its-tables: Programming the ITS tables

- section: ITS tables and memory
- relevance: 4 - the register may not keep what was written

When the driver programs a `GITS_BASER` register, what does it do when the
page size, the shareability or another field does not read back as written,
what decides between a flat and a two-level table, and how is a physical
address above 48 bits handled? Start from `its_alloc_tables()` and
`its_setup_baser()`.

## gicv3.its-l2-alloc: Second-level tables

- section: ITS tables and memory
- relevance: 4 - the table must be visible before a command uses it

When is a second-level device or vPE table page allocated, what must be done,
and in what order, to make the page and the first-level entry visible to the
hardware before a command relies on them, and what bounds the device ID? Start
from `its_alloc_table_entry()` and `allocate_vpe_l2_table()`.

## gicv3.common-aff: Redistributor grouping by affinity

- section: ITS tables and memory
- relevance: 4 - the mask direction is easy to get backwards

How does `compute_common_aff()` turn a redistributor's type register into a
grouping key, which affinity bits are kept and which cleared as the group size
grows, and who compares the result?

## gicv3.noncoherent: Non-coherent GICs

- section: ITS tables and memory
- relevance: 4 - a new table type is where this gets forgotten

Which flags say that an ITS or the redistributors cannot snoop the CPU caches, and what sets each?
What must code that allocates or writes a table that the ITS or a redistributor reads do because
of those flags? Start from `its_probe_one()` and `its_cpu_init_lpis()`.

# LPIs

## gicv3.lpi-tables: LPI property and pending tables

- section: LPIs
- relevance: 4 - one is global and the other is per CPU

Which CPUs share each LPI property table and each LPI pending table? When, and with which
allocation flags, are the tables allocated? How are they kept from being reused by a kernel
started with kexec? Start from `allocate_lpi_tables()` and `its_cpu_memreserve_lpi()`.

## gicv3.lpi-idbits: LPI ID width

- section: LPIs
- relevance: 4 - the driver caps what the hardware advertises

How does `its_setup_lpi_prop_table()` choose `lpi_id_bits` on each of its paths, and how does the
chosen value relate to what the hardware advertises? What else can reduce the number of LPIs
handed to the allocator? Start from `its_lpi_init()` and `ITS_MAX_LPI_NRBITS`.

## gicv3.lpi-prealloc: Booting with LPIs already enabled

- section: LPIs
- relevance: 3 - kexec and kdump arrive this way

When a redistributor already has LPIs enabled at boot, when does the driver
adopt the tables the previous kernel programmed, what does it check first, and
what does it do when it cannot adopt them? Start from `allocate_lpi_tables()`,
`enabled_lpis_allowed()` and `redist_disable_lpis()`.

## gicv3.lpi-config: Changing an LPI's configuration

- section: LPIs
- relevance: 5 - a change that is not invalidated has not been published

When an LPI is enabled, disabled or reprioritised, what are the requirements for writing its
configuration byte and for making the change visible, in order to assure safe usage? How does the
driver choose how to invalidate the cached copy? Start from `lpi_write_config()` and
`lpi_update_config()`.

## gicv3.lpi-direct-inv: Invalidating through the redistributor

- section: LPIs
- relevance: 3 - two register accesses that must be atomic

When the driver invalidates one LPI, or all of a vPE's, by writing a
redistributor register, which lock makes the write and the wait one step, how
is the target redistributor chosen and kept from changing meanwhile, and what
is polled? Start from `__direct_lpi_inv()` and `irq_to_cpuid_lock()`.

## gicv3.lpi-allocator: The LPI number allocator

- section: LPIs
- relevance: 4 - a broken invariant shows no symptom where the bug is

How does the driver keep track of free LPI numbers and under which lock, what
does a caller do when its request cannot be met in full, and which invariant
of the free list must freeing preserve? Start from `alloc_lpi_range()`,
`free_lpi_range()` and `its_lpi_alloc()`.

## gicv3.its-device: One device behind an ITS

- section: LPIs
- relevance: 4 - shared devices have no tracked lifetime

How is a device's interrupt translation table sized and allocated, what marks
an ITS device as shared, and what does being shared mean for the device's
lifetime? Start from `its_create_device()`.

## gicv3.msi-prepare: Preparing a device for MSIs

- section: LPIs
- relevance: 4 - two devices can resolve to one device ID

When `its_msi_prepare()` is called for a device ID that already has an ITS device, what is reused,
and what serialises the lookup against creation? What does `its_msi_teardown()` keep, and what
does it free?

## gicv3.spec-lpi-tables: What the architecture specification says

- section: LPIs
- verbatim: ../verbatim/gic-v3-lpi-tables.md

# vPE mapping and movement

## gicv3.v4-api: The GICv4 interface

- section: vPE mapping and movement
- relevance: 4 - not everything is tunnelled through one irqchip callback

How do KVM's requests reach the ITS driver: which go through
`irq_set_vcpu_affinity()` carrying a command and which take another route,
which function in the ITS driver receives each kind, and which of the exported
functions require preemption to be disabled? Start from
`drivers/irqchip/irq-gic-v4.c`.

## gicv3.v4-locks: GICv4 locks

- section: vPE mapping and movement
- relevance: 5 - the order is documented in one comment

What does each lock that the GICv4 code takes protect? In what order do they nest in the code, and
where is that order written down? Start from `vmapp_lock`, `vpe_lock`, `vmovp_lock` and `rd_lock`.

## gicv3.v4-vpe-affinity: Moving a vPE

- section: vPE mapping and movement
- relevance: 5 - a regression and its fix both live here

What does `its_vpe_set_affinity()` check before it touches hardware, and what does it do in each
outcome of that check? Which locks does it hold across the move? Start from
`gic_requires_eager_mapping()`.

## gicv3.v4-vpe-target: Target CPU of a move

- section: vPE mapping and movement
- relevance: 5 - the CPU that is chosen decides which redistributor and which doorbell the vPE uses afterwards

How does `its_vpe_set_affinity()` choose the CPU that it moves the vPE to, and what does it send
or update after the move command?

## gicv3.v4-vmovp: VMOVP and the ITS list

- section: vPE mapping and movement
- relevance: 4 - every ITS must see the moves in one order

When does `its_send_vmovp()` send one command, and when one to each ITS? What serialises the sends
to several ITSs, and which ITSs are skipped? Start from `its_list_map` and `vmovp_lock`.

## gicv3.v4-mapping-policy: Eager and lazy vPE mapping

- section: vPE mapping and movement
- relevance: 4 - decides whether an unmapped vPE is an error

When are a VM's vPEs mapped on every ITS at activation, and when only on demand? Which counters
drive the on-demand case, and what does `vmapp_count` count? Start from
`gic_requires_eager_mapping()`, `its_map_vm()` and `its_vpe_irq_domain_activate()`.

## gicv3.v4-col-idx: A vPE's current redistributor

- section: vPE mapping and movement
- relevance: 5 - the interrupt descriptor lock is not always enough

Which field of `struct its_vpe` records the redistributor that a vPE is mapped to, and what are
the requirements for reading it and for writing it in order to assure safe usage? Which helpers
take the required lock for the caller? Start from `vpe_to_cpuid_lock()` and
`its_vpe_set_affinity()`.

# Virtual LPIs and SGIs

## gicv3.v4-vlpi-map: Mapping a virtual LPI

- section: Virtual LPIs and SGIs
- relevance: 4 - the ITS has no idempotent map

What does `its_vlpi_map()` send when the interrupt is already forwarded? Otherwise, in what order
does it drop the physical mapping and install the virtual one? What does `its_vlpi_unmap()` free
with the last mapping? Start from `its_vlpi_map()` and `its_vlpi_unmap()`.

## gicv3.vgic-v4-forwarding: Forwarding a device interrupt

- section: Virtual LPIs and SGIs
- relevance: 4 - failure is deliberately silent

In which cases does `kvm_vgic_v4_set_forwarding()` return success without mapping anything? Which
locks does it take, and how does it move pending state to the hardware?

## gicv3.vgic-v4-unset-forwarding: Removing a forwarded interrupt

- section: Virtual LPIs and SGIs
- relevance: 4 - the caller has the host interrupt and not the virtual one

How does `kvm_vgic_v4_unset_forwarding()` find the `struct vgic_irq` that it acts on, and what
does it do when that interrupt is not forwarded?

## gicv3.v4-vsgi: Virtual SGIs

- section: Virtual LPIs and SGIs
- relevance: 3 - configuration and pending state need separate commands

On which hardware are virtual SGIs available? How, and through which ITS, is a virtual SGI made
pending, cleared and read back? Which commands does `its_sgi_irq_domain_deactivate()` send, and
why? Start from `its_sgi_irq_chip`, `its_configure_sgi()` and `its_sgi_set_irqchip_state()`.

## gicv3.vgic-v4-vsgi: Switching SGIs to hardware

- section: Virtual LPIs and SGIs
- relevance: 3 - state has to move between software and hardware

What makes a guest's SGIs hardware-backed on GICv4.1, when can the guest or
userspace change that, and what is transferred in each direction while the
running vCPUs are held off? Start from `vgic_v4_configure_vsgis()` and
`vgic_mmio_write_v3_misc()`.

# vPE scheduling

## gicv3.v4-schedule: Making a vPE resident

- section: vPE scheduling
- relevance: 4 - the two GIC versions program different things

What does making a vPE resident write on GICv4.0 and on GICv4.1, and what happens to the doorbell
interrupt in each case? When does `its_commit_vpe()` wait, and for what? Start from
`its_make_vpe_resident()`, `its_vpe_schedule()`, `its_vpe_4_1_schedule()` and `its_commit_vpe()`.

## gicv3.v4-deschedule: Making a vPE non-resident

- section: vPE scheduling
- relevance: 5 - a lost doorbell is a vCPU that never wakes

What does `its_clear_vpend_valid()` return to its caller when the hardware settles and when it
does not settle in time, and how do the GICv4.0 and GICv4.1 deschedule paths use the result? What
decides whether a doorbell is requested on GICv4.1?

## gicv3.v4-pending-last: The pending-last hint

- section: vPE scheduling
- relevance: 4 - it is a hint and code treats it as one

What does a true `pending_last` in `struct its_vpe` guarantee, and what does it not guarantee?
What does `its_vpe_schedule()` write to the PendingLast bit of `GICR_VPENDBASER`, and why?

## gicv3.v4-doorbells: Doorbell interrupts

- section: vPE scheduling
- relevance: 4 - GICv4.0 masks in software, GICv4.1 in hardware

Which interrupt chip stands for a vPE's doorbell on GICv4.0 and which on GICv4.1, and how is the
doorbell enabled and disabled in each case? How is a doorbell that fires while the vPE is being
made non-resident kept from being lost? Start from `its_vpe_irq_chip`, `its_vpe_4_1_irq_chip`,
`vgic_v4_doorbell_handler()` and `its_make_vpe_non_resident()`.

## gicv3.vgic-v4-load-put: vPE residency from KVM

- section: vPE scheduling
- relevance: 4 - the put serves two purposes at once

When do `vgic_v4_load()` and `vgic_v4_put()` return without changing the residency of the vPE?
What decides whether a doorbell is requested? Which request makes every vCPU reload its vPE? Start
from `vgic_v4_want_doorbell()`.

## gicv3.vgic-wfi: Blocking in WFI

- section: vPE scheduling
- relevance: 5 - residency cannot be used to infer intent to block

What does `kvm_vcpu_wfi()` do to the vGIC before and after halting? Which vCPU flag does it set,
and which vGIC decisions test that flag?

## gicv3.v4-vpend-usage: Virtual pending base register writes

- section: vPE scheduling
- relevance: 5 - UNPREDICTABLE while the redistributor is scanning

What are the requirements for a write to a redistributor's `GICR_VPENDBASER` in order to assure
safe usage? Name the in-tree helper that meets them. Which in-tree writes do not go through the
helper, and what makes them correct?

## gicv3.spec-vpe-residency: What the architecture specification says

- section: vPE scheduling
- verbatim: ../verbatim/gic-v3-vpe-residency.md

# Virtual interrupts and their lifetime

## gicv3.vgic-irq: One virtual interrupt

- section: Virtual interrupts and their lifetime
- relevance: 5 - every vGIC function manipulates this

Which lock protects the contents of a `struct vgic_irq`, and what is the difference between `vcpu`
and `target_vcpu`? How long does the structure live for an SGI or a PPI, for an SPI and for an
LPI? Start from `include/kvm/arm_vgic.h`.

## gicv3.vgic-lock-order: vGIC lock order

- section: Virtual interrupts and their lifetime
- relevance: 5 - written down once, violated by indirect calls

What is the documented order of the VM, vCPU, configuration, ITS, LPI xarray,
list and interrupt locks in the vGIC, which of them must be taken with
interrupts disabled and why, and how are two vCPUs' list locks ordered? Start
from the comment at the top of `arch/arm64/kvm/vgic/vgic.c`.

## gicv3.vgic-lookup: Looking up a virtual interrupt

- section: Virtual interrupts and their lifetime
- relevance: 4 - bounds and references differ by kind

For each kind of interrupt ID, how do `vgic_get_irq()` and
`vgic_get_vcpu_irq()` bound the ID and guard the array index against
speculation, when do they return NULL, and which results must be released
with `vgic_put_irq()`?

## gicv3.vgic-lpi-refs: References on an LPI

- section: Virtual interrupts and their lifetime
- relevance: 5 - the use-after-free bugs live here

What holds a reference on an LPI's `struct vgic_irq` after the function that took the reference
has returned, and which call takes and which drops each such reference? What do SGIs, PPIs and
SPIs do with the reference count? Start from `vgic_add_lpi()`, `vgic_queue_irq_unlock()` and
`vgic_its_cache_translation()`.

## gicv3.vgic-lpi-put: Dropping a reference

- section: Virtual interrupts and their lifetime
- relevance: 5 - the decrement and the eviction must not be separable

How does `vgic_put_irq()` make dropping the last reference and removing the
LPI from the xarray one step, how is the memory freed, and what extra thing
does it do on a kernel built with lock debugging and why?

## gicv3.vgic-lpi-norelease: Deferred release

- section: Virtual interrupts and their lifetime
- relevance: 5 - the caller inherits an obligation

In which contexts can `vgic_put_irq()` not be used, and why? What must code that calls
`vgic_put_irq_norelease()` do with its return value, and when? How does
`vgic_release_deleted_lpis()` tell which objects are awaiting release? Start from
`vgic_put_irq_norelease()` and `vgic_release_deleted_lpis()`.

## gicv3.vgic-lpi-add: Registering an LPI

- section: Virtual interrupts and their lifetime
- relevance: 4 - two CPUs can map the same LPI at once

What does `vgic_add_lpi()` do before it takes the xarray lock, and why? What does it do when the
slot already holds an object, whether the count of that object is zero or not? What is undone on a
later failure?

## gicv3.vgic-lpi-flush: Disabling LPIs on a redistributor

- section: Virtual interrupts and their lifetime
- relevance: 4 - a guest can do this while another vCPU migrates an interrupt

When a guest clears the LPI enable bit of a redistributor, what does `vgic_flush_pending_lpis()`
remove, and what does it change on each interrupt that it removes? How does it drop its
references? Start from `vgic_mmio_write_v3r_ctlr()`.

## gicv3.vgic-translation-cache: The translation cache

- section: Virtual interrupts and their lifetime
- relevance: 5 - three unserialised paths drain it

What reference does an entry of a virtual ITS's translation cache hold? What are the requirements
for a path that invalidates the cache in order to assure safe usage, and do the paths that
invalidate it exclude one another? Start from `vgic_its_cache_translation()` and
`vgic_its_invalidate_cache()`.

## gicv3.vgic-translation-cache-store: Storing a cached translation

- section: Virtual interrupts and their lifetime
- relevance: 5 - each path out of the store has a reference to account for

Which interrupts does `vgic_its_cache_translation()` not cache, and what does it do with the
reference that it took when the store fails or displaces an entry?

## gicv3.vgic-debugfs: The debugfs state file

- section: Virtual interrupts and their lifetime
- relevance: 3 - a walker over objects that can vanish

How does the vGIC state file in debugfs find the next LPI and what does it
hold while it prints one, and what does it do when an interrupt it is about to
print no longer exists? Start from `arch/arm64/kvm/vgic/vgic-debug.c`.

## gicv3.vgic-lpi-get: References taken by lookups

- section: Virtual interrupts and their lifetime
- relevance: 5 - a pointer returned without a reference can be freed

What are the requirements for a function that looks up an LPI's `struct vgic_irq` in `lpi_xa` and
returns it, in order to assure safe usage? What does `vgic_try_get_irq_ref()` return for an object
whose count has reached zero? Name in-tree lookups that show it.

# List registers

## gicv3.vgic-queue: Queueing an interrupt

- section: List registers
- relevance: 5 - the lock dance every injection goes through

Which lock must be held on entry to `vgic_queue_irq_unlock()`, and which locks are held when it
returns? What does it check again before it queues the interrupt, and why? What reference does it
take?

## gicv3.vgic-queue-kick: Kick after queueing

- section: List registers
- relevance: 5 - a vCPU that is not kicked does not see the interrupt

Which vCPUs does `vgic_queue_irq_unlock()` kick after it has queued an interrupt, and what decides
between one vCPU and all of them?

## gicv3.vgic-prune: ap_list pruning and migration

- section: List registers
- relevance: 5 - locks are dropped in the middle of a list walk

While `vgic_prune_ap_list()` moves an interrupt to another vCPU's list, what keeps the interrupt
alive while locks are dropped, and in what order are the two lists locked? What are the
requirements for the check that it makes before the move, in order to assure safe usage?

## gicv3.vgic-flush-lr: Filling the list registers

- section: List registers
- relevance: 5 - decides what the guest can see

Before guest entry, how does `vgic_flush_lr_state()` decide which interrupts
go into the list registers: when is the list sorted and by what, what is
recorded about the last interrupt loaded, and which maintenance and trap bits
does `vgic_v3_configure_hcr()` set for which condition?

## gicv3.vgic-compute-lr: Encoding a list register

- section: List registers
- relevance: 4 - several states are never written together

When `vgic_v3_compute_lr()` encodes an interrupt, when is the hardware bit set, and with which
physical ID? When is a pending state withheld? What stops one interrupt from occupying two list
registers? Start from `vgic_v3_populate_lr()` and `on_lr`.

## gicv3.vgic-v2-sgi-source: GICv2 SGI sources

- section: List registers
- relevance: 4 - an SGI with several sources needs more than one list register entry over time

How does `vgic_v3_compute_lr()` present a GICv2 SGI that has more than one source, and how do the
other sources reach the guest afterwards?

## gicv3.vgic-fold-lr: Reading the list registers back

- section: List registers
- relevance: 4 - the hardware state becomes the software state here

After a guest exit, what does `vgic_v3_fold_lr()` take from a list register for each kind of
interrupt? What may its lookup of the interrupt return, and why? When is an acknowledged level
interrupt reported to irqfd users?

## gicv3.vgic-eoicount: Deactivations outside the list registers

- section: List registers
- relevance: 5 - walking from the wrong place deactivates the wrong interrupts

With priority drop and deactivation combined, how does the vGIC account for
interrupts the guest deactivated that were not in a list register: which
counter says how many, where does the walk of the list start and why there,
and what is done for an entry backed by a hardware interrupt? Start from
`vgic_v3_fold_lr_state()` and `last_lr_irq`.

## gicv3.vgic-dir-trap: Deactivations by trap

- section: List registers
- relevance: 4 - split EOI mode gives no ordering to rely on

Which conditions make KVM trap the deactivate register? What does `active_spis` count? For which
interrupts does `vgic_v3_deactivate()` deactivate the physical interrupt, and for which does it
not?

## gicv3.spec-list-registers: What the architecture specification says

- section: List registers
- verbatim: ../verbatim/gic-v3-list-registers.md

# World switch

## gicv3.vgic-pending-check: Deliverable interrupt check

- section: World switch
- relevance: 4 - decides whether a vCPU blocks

What does `kvm_vgic_vcpu_pending_irq()` look at to decide that a vCPU has a
deliverable interrupt, where does it get the guest's priority mask from, and
what short-cuts does it take for a disabled distributor and for GICv4?

## gicv3.vgic-vmcr: The virtual machine control register

- section: World switch
- relevance: 5 - a stale priority mask blocks a vCPU for ever

When is the hardware copy of the virtual machine control register written from
and saved to `vgic_vmcr`: at vCPU load and put, or at each guest entry and
exit, and does it depend on the emulated GIC model or on the hypervisor mode?
What does `vgic_get_vmcr()` read? Start from `__vgic_v3_save_state()`,
`__vgic_v3_restore_vmcr_aprs()` and `__vgic_v3_activate_traps()`.

## gicv3.vgic-load-put: Loading and putting a vCPU

- section: World switch
- relevance: 4 - what is per load and what is per entry

What do `vgic_v3_load()` and `vgic_v3_put()` save and restore, and what is
instead handled at every guest entry and exit by `kvm_vgic_flush_hwstate()`
and `kvm_vgic_sync_hwstate()`? What differs for a protected guest and with
the virtualization host extensions?

## gicv3.vgic-traps: Trapping the CPU interface

- section: World switch
- relevance: 3 - errata and options turn traps on for everyone

Which conditions make KVM trap a guest's accesses to the group 0, group 1 and common CPU interface
registers? How does the set of trap bits get from where it is computed to the register? What
handles a trapped access? Start from `kvm_compute_ich_hcr_trap_bits()` and
`__vgic_v3_perform_cpuif_access()`.

# Mapped hardware interrupts

## gicv3.vgic-mapped: Mapping a hardware interrupt

- section: Mapped hardware interrupts
- relevance: 4 - state is split between software and hardware

What does `kvm_vgic_map_phys_irq()` record? Who resets a mapped interrupt when the VM is reset?
Who may inject a mapped interrupt? Start from `kvm_vgic_map_irq()` and
`kvm_vgic_reset_mapped_irq()`.

## gicv3.vgic-mapped-unmap: Physical interrupt lookup and unmap

- section: Mapped hardware interrupts
- relevance: 4 - state that stays after an unmap changes how the interrupt is handled next

How does `kvm_vgic_map_phys_irq()` find the physical interrupt ID, and which state of the `struct
vgic_irq` does `kvm_vgic_unmap_phys_irq()` clear?

## gicv3.vgic-irq-ops: Per-interrupt callbacks

- section: Mapped hardware interrupts
- relevance: 3 - in-kernel devices change vGIC behaviour through these

How does a `struct irq_ops` report that an interrupt needs software resampling? Who installs one,
and under which lock? Do mapping and unmapping a hardware interrupt install or clear it? Start
from `kvm_vgic_set_irq_ops()`.

## gicv3.vgic-resample: Resampling a mapped level interrupt

- section: Mapped hardware interrupts
- relevance: 4 - a stale level is a spurious injection

When and how does the vGIC re-read the line of a level-triggered interrupt
tied to a hardware one, what does it do to the physical active state as a
result, and what differs for an interrupt whose callbacks ask for software
resampling? Start from `vgic_irq_handle_resampling()`.

## gicv3.vgic-pending-access: Pending state by accessor

- section: Mapped hardware interrupts
- relevance: 4 - userspace cannot read hardware state the guest path reads

How do a guest's and userspace's reads and writes of the pending registers
differ: what does each read return for a mapped level interrupt, for a virtual
SGI backed by hardware and for an ordinary one, and what does each write do to
the physical interrupt? Start from `__read_pending()`, `__set_pending()` and
`__clear_pending()`.

# Virtual ITS

## gicv3.vits-structs: Virtual ITS objects

- section: Virtual ITS
- relevance: 4 - same names as the host driver, different structures

KVM's virtual ITS has its own `struct its_device`, `struct its_collection` and `struct its_ite`,
named like the host driver's. Where are they defined, what does each mutex in `struct vgic_its`
protect, and what does an unmapped collection look like? Start from `arch/arm64/kvm/vgic/vgic.h`.

## gicv3.vits-cmdq: Processing guest commands

- section: Virtual ITS
- relevance: 4 - the write pointer is a guest-controlled value

When a guest writes the virtual ITS's command write register, how is the value validated, and
under which lock are commands processed? What is done when a command cannot be read from guest
memory or a handler returns an error? Start from `vgic_mmio_write_its_cwriter()` and
`vgic_its_process_commands()`.

## gicv3.vits-mapti: Mapping an event

- section: Virtual ITS
- relevance: 4 - every field is guest-supplied

What does `vgic_its_cmd_handle_mapi()` check about the device, the event ID,
the LPI number and the collection, what does it do when the event is already
mapped, and what does it undo when a later step fails?

## gicv3.vits-mapd-discard: Unmapping devices and events

- section: Virtual ITS
- relevance: 5 - a stale entry in guest memory is resurrected by restore

What do `vgic_its_cmd_handle_mapd()` and `vgic_its_cmd_handle_discard()` check,
and what do they do, besides freeing the in-kernel objects, when a device or
an event is unmapped? What does a hardware-forwarded interrupt need on that
path? Start from `its_free_ite()`.

## gicv3.vits-abi: Table format revisions

- section: Virtual ITS
- relevance: 4 - the entry size is part of the user ABI

How does `struct vgic_its_abi` describe the format in which the virtual ITS saves its tables? How
is the revision that userspace writes validated? How do `vgic_its_read_entry_lock()` and
`vgic_its_write_entry_lock()` check the entry size? Start from `struct vgic_its_abi`,
`vgic_its_read_entry_lock` and `vgic_mmio_uaccess_write_its_iidr()`.

## gicv3.vits-save: Saving the tables

- section: Virtual ITS
- relevance: 4 - the image must restore into something that was live

In what order does `vgic_its_save_tables_v0()` save the device, translation and collection tables?
What does it write for an event whose collection was unmapped? For which interrupts does saving
fail? Start from `vgic_its_save_tables_v0()`.

## gicv3.vits-restore: Restoring the tables

- section: Virtual ITS
- relevance: 5 - parses data the guest or a migration source controls

In what order are the tables restored? What does each of `vgic_its_restore_dte()`,
`vgic_its_restore_ite()` and `vgic_its_restore_cte()` validate about an entry before it acts on
it? What is freed when a restore fails part way?

## gicv3.vits-restore-checks: Restore and command handler checks

- section: Virtual ITS
- relevance: 5 - a restore must not create an object that a running guest could not create

What are the requirements for a function that restores an object of the virtual ITS from guest
memory, compared with the command handler that creates the same object for a running guest, in
order to assure safe usage? Name in-tree code that shows it. Start from `vgic_its_restore_ite()`
and `vgic_its_cmd_handle_mapi()`.

## gicv3.vits-scan: Guest table walks

- section: Virtual ITS
- relevance: 5 - the step comes from the entry being read

How does `scan_its_table()` advance through a table, and what are the requirements for the step
and for the bound of its loop in order to assure safe usage? What do its return values mean? Start
from `handle_l1_dte()`.

## gicv3.vits-ctrl-locking: Locks for user requests

- section: Virtual ITS
- relevance: 3 - user requests must exclude running vCPUs

Which locks do the virtual ITS's control and register-access requests take and
in what order, what error is returned when a vCPU is running, and in what
order does the documentation tell userspace to restore the ITS registers and
tables?

# Emulated distributor and redistributor registers

## gicv3.vgic-mmio: The register emulation framework

- section: Emulated distributor and redistributor registers
- relevance: 3 - guest and userspace accessors are separate on purpose

How do guest accesses and userspace accesses to an emulated distributor,
redistributor or ITS register reach different callbacks, what does userspace
get when a region has no callback of its own, and what happens to an access of
a width the region does not allow? Start from
`arch/arm64/kvm/vgic/vgic-mmio.h` and `vgic_uaccess()`.

## gicv3.vgic-rd-inv: Invalidate registers of the redistributor

- section: Emulated distributor and redistributor registers
- relevance: 4 - the value is an interrupt ID the guest chose

What do `vgic_mmio_write_invlpi()` and `vgic_mmio_write_invall()` check before they act on a guest
write to the emulated redistributor's LPI invalidate registers, and what do they do with a write
that fails a check? What state do they change while the operation runs? Start from
`vgic_mmio_write_invlpi()` and `vgic_mmio_write_invall()`.

## gicv3.vgic-sgi-dispatch: Guest-generated SGIs

- section: Emulated distributor and redistributor registers
- relevance: 4 - the register value is guest-supplied

How does `vgic_v3_dispatch_sgi()` take the SGI number, the targets and the broadcast mode out of a
guest's write to an SGI generation register, how do the SGI generation registers differ in which
group they may raise, and what is done for a hardware-backed SGI?

## gicv3.vgic-id-regs: Identification registers from userspace

- section: Emulated distributor and redistributor registers
- relevance: 4 - the write must use the value written

Which distributor registers may userspace write before the vGIC is initialised, and why? What does
a userspace write to `GICD_IIDR` or to `GICD_TYPER2` validate and change? What are the
requirements for the handler of such a write in order to assure safe usage? Start from
`vgic_mmio_uaccess_write_v3_misc()` and `reg_allowed_pre_init()`.

## gicv3.vgic-rd-typer: The redistributor type register

- section: Emulated distributor and redistributor registers
- relevance: 3 - userspace can read it before anything is configured

How is the emulated redistributor type register built, how is the bit that
marks the last redistributor of a region computed, and what does that
computation do when the redistributor has not been placed in a region yet?
Start from `vgic_mmio_vcpu_rdist_is_last()`.

# vGIC lifecycle

## gicv3.vgic-create: Creating the vGIC

- section: vGIC lifecycle
- relevance: 4 - excludes half-created vCPUs

Which locks does `kvm_vgic_create()` take, and what makes it refuse to create the device? What
does it set up for the vCPUs that already exist?

## gicv3.vgic-create-failure: Failure of vGIC creation

- section: vGIC lifecycle
- relevance: 4 - an error path that leaves state behind breaks the next attempt

What does `kvm_vgic_create()` undo when it fails after it has set up state for the vCPUs that
already exist, and in which state does it leave the VM?

## gicv3.vgic-init: Initialising the vGIC

- section: vGIC lifecycle
- relevance: 4 - GICv3 must be initialised explicitly

When does `vgic_init()` refuse? Which GIC model does `vgic_lazy_init()` initialise on first use?
What happens to an injection or a userspace register access that arrives before
`vgic_initialized()` is true? Start from `vgic_lazy_init()` and `kvm_vgic_inject_irq()`.

## gicv3.vgic-map-resources: Resource mapping and ready flag

- section: vGIC lifecycle
- relevance: 5 - a vCPU must not run against a half-built distributor

On a vCPU's first run, which locks does `kvm_vgic_map_resources()` hold while it registers the
distributor's registers? How and when is the ready flag published and read? What happens to the VM
on failure?

## gicv3.vgic-redist-iodev: Registering redistributors

- section: vGIC lifecycle
- relevance: 4 - registration and its undo happen in different places

Which locks does `vgic_register_redist_iodev()` hold around the bus registration? What is rolled
back when setting a region's base fails for one vCPU? Where is the frame unregistered for a vCPU
that was created successfully, and where for one whose creation failed? Start from
`vgic_register_redist_iodev()` and `__kvm_vgic_vcpu_destroy()`.

## gicv3.vgic-config-lock: Scope of the configuration lock

- section: vGIC lifecycle
- relevance: 5 - fixes have both added and removed it

What are the requirements for holding `kvm->arch.config_lock` around registering or unregistering
emulated register frames in order to assure safe usage? Which locks must be taken before it? How
does `kvm_vgic_destroy()` split its teardown between what runs under the lock and what runs after
it is dropped?

# Host handoff, nested guests and GICv5 hosts

## gicv3.vgic-global: Host GIC information in KVM

- section: Host handoff, nested guests and GICv5 hosts
- relevance: 3 - the irqchip driver and KVM meet here

How does the host GIC driver tell KVM what hardware it found, what does KVM
refuse or downgrade when that information is incomplete, and what enables
GICv4 use by KVM? Start from `struct gic_kvm_info`, `vgic_set_kvm_info()` and
`vgic_v3_probe()`.

## gicv3.vgic-nested: A guest hypervisor's list registers

- section: Host handoff, nested guests and GICv5 hosts
- relevance: 3 - the guest hypervisor owns the list registers

When a vCPU runs a nested guest, where do the list registers loaded into hardware come from, and
what is translated on the way in? What is copied back on exit? Start from `vgic_state_is_nested()`
and `arch/arm64/kvm/vgic/vgic-v3-nested.c`.

## gicv3.vgic-nested-deactivation: Nested deactivation and maintenance interrupt

- section: Host handoff, nested guests and GICv5 hosts
- relevance: 3 - the guest hypervisor relies on both to see the state of its guest's interrupts

When a vCPU runs a nested guest, how does KVM emulate the deactivation of a list register entry
that is backed by a hardware interrupt, and how does it generate the maintenance interrupt of the
guest hypervisor? Start from `arch/arm64/kvm/vgic/vgic-v3-nested.c`.

## gicv3.vgic-v5-host: GICv3 guests on GICv5 hosts

- section: Host handoff, nested guests and GICv5 hosts
- relevance: 4 - half of the code applies and half does not

What does KVM need from a GICv5 host to offer a guest a GICv3? What selects the compatibility mode
on the CPU? What does KVM do differently on such a host to deactivate a physical interrupt? Start
from `vgic_v5_probe()`, `vgic_host_has_gicv3()` and `__vgic_v3_compat_mode_enable()`.

# Model gaps

## gicv3.model-gaps: Other mistakes models make

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

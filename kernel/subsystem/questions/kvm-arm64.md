# Questions: KVM on arm64

- guide: kvm-arm64.md
- title: KVM on arm64

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/kvm-arm64-measurement.md` is the
wider set the readers were measured on and `catalogue/kvm-arm64-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## kvmarm.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## kvmarm.core-files: Core files

- section: Finding your way
- relevance: 4 - several jobs have moved to files that are new

A table and nothing else, job to file under `arch/arm64/kvm/`: the VM and vCPU ioctls and run
loop; exit handling; system register emulation; the feature-to-register-bit dependency tables;
stage-2 fault handling; reset; PSCI and other hypercalls; exception injection; the timer; the
PMU; debug; FP/SIMD; nested virtualisation; the host side of pKVM; each interrupt controller
model. Where a reader is likely to look for a file that does not exist in this tree, say so in
the row.

# Modes and the hypervisor

## kvmarm.modes: Modes of operation

- section: Modes and the hypervisor
- relevance: 5 - almost every path branches on the mode

Which modes can arm64 KVM run in (the values of `kvm-arm.mode`, and VHE, nVHE and hVHE
underneath them), how is the mode chosen at boot, and which predicate must code use to test
for each? Start from `kvm_get_mode()`, `has_vhe()` and `is_protected_kvm_enabled()`.

## kvmarm.hyp-dirs: Hypervisor source directories

- section: Modes and the hypervisor
- relevance: 4 - the same source is built for two different worlds

What is in `arch/arm64/kvm/hyp/`, `arch/arm64/kvm/hyp/nvhe/` and `arch/arm64/kvm/hyp/vhe/`, and
which files in the first are compiled into both hypervisor objects, so that a change to one
runs in two worlds? Where are the page-table code, the world switch, the host hypercall
handlers and the pKVM memory ownership code?

## kvmarm.nvhe-build: nVHE object build

- section: Modes and the hypervisor
- relevance: 4 - kernel facilities are not available there

What does `arch/arm64/kvm/hyp/nvhe/Makefile` do to the symbol and section names of the nVHE
hypervisor object when it is linked, and how does host code refer to one of its symbols? What are
the requirements for code compiled into the nVHE object, in what it calls and what it references,
in order to assure that it links and runs at EL2? Start from `arch/arm64/kvm/hyp/nvhe/Makefile`.

## kvmarm.hyp-call: Calling into the hypervisor

- section: Modes and the hypervisor
- relevance: 4 - adding a call touches an enum, a table and a handler

What do `kvm_call_hyp()`, `kvm_call_hyp_ret()` and `kvm_call_hyp_nvhe()` do on VHE and on nVHE?
What do a new value of `enum __kvm_host_smccc_func`, its entry in `host_hcall[]` and its handler
have to agree on?

## kvmarm.hyp-call-refused: Refused host hypercalls

- section: Modes and the hypervisor
- relevance: 4 - a hypercall placed in the wrong group of the enum is refused at the wrong time

When does the hypervisor refuse a value of `enum __kvm_host_smccc_func`, and what does the host
get back then? Start from `handle_host_hcall()`.

## kvmarm.vhe-nvhe-split: VHE and nVHE world switch

- section: Modes and the hypervisor
- relevance: 4 - work done at load on one is done at every entry on the other

Which parts of the guest context are switched at vCPU load and put on VHE but at every entry and
exit on nVHE, and which are written at every entry on both? What does the nVHE `__kvm_vcpu_run()`
do differently for a pKVM guest?

## kvmarm.hyp-exit-fixup: Exits handled in the hypervisor

- section: Modes and the hypervisor
- relevance: 4 - some traps never reach the host

Which kinds of exit are handled inside the world switch without returning to the host run
loop, how are the handlers selected for VHE, nVHE and a protected guest, and what does a
handler's return value mean? Start from `__fixup_guest_exit()` and `kvm_hyp_handle_exit()`.

# Configuration, first run and teardown

## kvmarm.first-run: First run sequence

- section: Configuration, first run and teardown
- relevance: 5 - the order is what makes late configuration safe to reject

What does `kvm_arch_vcpu_run_pid_change()` finalise the first time a vCPU runs, per VM and per
vCPU, so that configuration arriving later can be refused, and where does the order of its
steps matter? Which error does it return for a vCPU that was never initialised and for one not
finalised?

## kvmarm.has-run-predicates: Has-run predicates

- section: Configuration, first run and teardown
- relevance: 5 - the wrong predicate accepts reconfiguration after the guest ran

Which predicates answer "this vCPU has entered the guest", "some vCPU of this VM has entered the
guest" and "`KVM_ARM_VCPU_INIT` was done", and can any of them become false again after it was
true? What are the requirements for choosing the predicate that gates an ioctl, a capability or a
register write in order to assure safe usage? Name in-tree users of each.

## kvmarm.config-lock: Configuration lock

- section: Configuration, first run and teardown
- relevance: 5 - the order against the generic KVM locks is easy to invert

What does `kvm->arch.config_lock` protect, where does it sit in the order with `kvm->lock`,
`vcpu->mutex`, `kvm->slots_lock` and `kvm->srcu`, and how does the code teach lockdep that
order? Name a path that needs more than one of them.

## kvmarm.vcpu-init: vCPU initialisation call

- section: Configuration, first run and teardown
- relevance: 4 - the call may be repeated, with conditions, and the bits are not kept where older code kept them

Which combinations of target and feature bits does `kvm_arch_vcpu_ioctl_vcpu_init()` reject? Where
are the accepted bits kept, and which helper tests them? Start from
`kvm_arch_vcpu_ioctl_vcpu_init()`.

## kvmarm.vcpu-init-repeat: Repeated vCPU initialisation

- section: Configuration, first run and teardown
- relevance: 4 - a repeated call is allowed only under conditions that a new feature bit must respect

What does `KVM_ARM_VCPU_INIT` return on a second call for the same vCPU, for another vCPU of the
same VM with different features, and on a VM that has already run? Start from
`kvm_arch_vcpu_ioctl_vcpu_init()`.

## kvmarm.finalize: Feature finalisation

- section: Configuration, first run and teardown
- relevance: 4 - running before it fails with a specific error

Which vCPU features need `KVM_ARM_VCPU_FINALIZE`, what does finalising allocate and freeze,
and what does each of `KVM_RUN`, a second finalise and a finalise of an absent feature return?
Start from `kvm_arm_vcpu_finalize()`.

## kvmarm.reset: vCPU reset

- section: Configuration, first run and teardown
- relevance: 4 - runs both on an unloaded and on a loaded vCPU

How does `kvm_reset_vcpu()` cope with the vCPU being loaded when it is called, which of its
callers run it on a loaded vCPU, and how does state passed by PSCI reach it?

## kvmarm.vm-destroy-order: VM destruction order

- section: Configuration, first run and teardown
- relevance: 4 - several objects are freed by more than one owner

In what order does `kvm_arch_destroy_vm()` tear down the vgic, the pKVM hypervisor VM, the stage-2
page tables and the vCPUs? Which of those steps uses state that a later step frees?

# Running a vCPU

## kvmarm.run-loop: Run loop order

- section: Running a vCPU
- relevance: 5 - the flush and sync calls depend on each other's order

In `kvm_arch_vcpu_ioctl_run()`, which of the flushes before entry and the syncs after exit
(vgic, timer, PMU, nested, FP) depend on each other's order and on preemption or interrupts
being off, and where is `vcpu->mode` set relative to them? What is undone when the entry is
abandoned at the last check?

## kvmarm.vcpu-load-put: Load and put

- section: Running a vCPU
- relevance: 4 - called from preempt notifiers as well as ioctls

Which ordering constraints between its steps does `kvm_arch_vcpu_load()` state in its comments,
and which of its steps differ under pKVM, VHE and nested virtualisation? From which contexts
besides an ioctl is it called?

## kvmarm.vcpu-requests: vCPU requests

- section: Running a vCPU
- relevance: 4 - new work for a running vCPU is added here

Which of the arm64 vCPU requests defined beside `KVM_REQ_SLEEP` does `check_vcpu_requests()`
handle, and which does `check_nested_vcpu_requests()` handle? Which of them make `KVM_RUN` return
to userspace and not enter the guest?

## kvmarm.vcpu-flags: vCPU flag sets

- section: Running a vCPU
- relevance: 4 - three sets with different owners, reached through one macro family

Who may write each of the flag sets `cflags`, `iflags` and `sflags` in `struct kvm_vcpu_arch`, and
which of them does the hypervisor read or clear? What are the requirements for choosing the set of
a new flag in order to assure safe usage? Start from `vcpu_set_flag()` and `__vcpu_single_flag()`.

## kvmarm.pending-exception: Pending exception state

- section: Running a vCPU
- relevance: 5 - injection is deferred, and two deferred actions exclude each other

How does the host record that an exception is to be injected or that the PC is to be advanced,
where and when is that turned into register state, and what happens if `KVM_RUN` returns to
userspace with one pending? Start from `kvm_pend_exception()`, `kvm_incr_pc()` and
`__kvm_adjust_pc()`.

## kvmarm.inject-usage: Injecting an exception safely

- section: Running a vCPU
- relevance: 5 - the wrong sequence clobbers the guest's ELR or SPSR

What are the requirements for calling `kvm_pend_exception()` and `kvm_incr_pc()` while handling
one exit in order to assure safe usage? What order of reading and writing the guest's ELR, SPSR
and ESR is required when the state may be loaded on the CPU? Name in-tree code that injects from
an abort handler, by the names this tree gives those functions.

## kvmarm.fp-ownership: FP and SIMD ownership

- section: Running a vCPU
- relevance: 5 - the tracking moved and the host state is no longer saved lazily

Where is ownership of the FP/SIMD registers tracked while a vCPU is loaded, and what are its
states? What does `kvm_arch_vcpu_load_fp()` do with the host's state?

## kvmarm.fp-guest-load: Guest FP state load

- section: Running a vCPU
- relevance: 5 - a path that assumes the guest's state is on the CPU after load reads the wrong registers

What loads the guest's FP/SIMD state after a vCPU is loaded? What do `kvm_arch_vcpu_load_fp()` and
`kvm_arch_vcpu_put_fp()` do when they run during a transition between a guest hypervisor and its
nested guest?

# Guest system registers

## kvmarm.sysreg-access: Register accessors and location

- section: Guest system registers
- relevance: 5 - the in-memory accessor is no longer an lvalue, and memory is stale while the value is live on the CPU

Which accessor reads or writes a guest system register in memory and which goes to the CPU when
the state is loaded, and how does code assign or modify an in-memory register? While a vCPU is
loaded on VHE, how does `vcpu_read_sys_reg()` decide where the current value of a register is?
Start from `__vcpu_sys_reg()` and `vcpu_read_sys_reg()`.

## kvmarm.sysreg-storage: Register storage

- section: Guest system registers
- relevance: 5 - the enum is not dense and not in declaration order

How is `enum vcpu_sysreg` numbered, and what do its marker entries delimit? Where is the value of
a register kept for a guest with and without nested virtualisation?

## kvmarm.sysreg-enum-usage: Ranges over the register enum

- section: Guest system registers
- relevance: 5 - a numeric range silently covers unrelated registers

What are the requirements for code that compares `enum vcpu_sysreg` values with `<` or `>`, or
that selects a numeric range of them, in order to assure safe usage? Which order of the enum's
entries does the tree guarantee? Name code that selects a group of registers by name.

## kvmarm.sysreg-desc: Trap descriptors

- section: Guest system registers
- relevance: 4 - every emulated register is one entry

What ordering must a table of `struct sys_reg_desc` keep and what checks it, and what do the
visibility flags make a register look like to the guest and to userspace?

## kvmarm.sysreg-trap-flow: Trap handling flow

- section: Guest system registers
- relevance: 4 - three different things can happen before the access function runs

From a trapped MSR or MRS to the access function, what decides, and in which order, that the
access gets an UNDEF because the feature is disabled for the VM, that it is forwarded to a
guest hypervisor, or that it is emulated? How is the descriptor found? Start from
`kvm_handle_sys_reg()` and `triage_sysreg_trap()`.

# ID registers and traps

## kvmarm.idreg-storage: ID register storage

- section: ID registers and traps
- relevance: 4 - feature checks read the VM's copy, not the host's

Where are a VM's ID register values kept, and what initialises them? Which lock covers a write?
Start from `kvm_read_vm_id_reg()` and `kvm_has_feat()`.

## kvmarm.idreg-feature-test: Feature test for a VM

- section: ID registers and traps
- relevance: 4 - a test that reads the host's value enables for a guest what the VM was not given

What does `kvm_has_feat()` read when it tests a feature field for a VM? What are the requirements
for code that tests whether a guest has a feature in order to assure safe usage?

## kvmarm.idreg-desc-kinds: ID register descriptor kinds

- section: ID registers and traps
- relevance: 5 - the kind decides what userspace may change

A table of the macros that declare an ID register in the descriptor table, to choose between:
for each, whether the guest sees a value or zero, whether userspace can write it, and what the
descriptor's `val` field means.

## kvmarm.idreg-writes: Userspace ID register writes

- section: ID registers and traps
- relevance: 5 - this check is what stops a guest being promised an absent feature

When userspace writes an ID register, what is each field compared against, and how are fields
outside the writable mask treated? Once a VM has run, what does a write return that matches the
current value, and one that does not? Start from `set_id_reg()`.

## kvmarm.idreg-late-change: Late ID register changes

- section: ID registers and traps
- relevance: 5 - a kernel path that changes an ID register after the first run changes what the guest was promised

What does `kvm_set_vm_id_reg()` do when the VM has already run? How does userspace discover the
writable masks of the ID registers?

## kvmarm.idreg-expose-usage: Exposing a new ID field

- section: ID registers and traps
- relevance: 5 - each half can be forgotten without a build error

What are the requirements for a patch that makes a new ID register field visible or writable to a
guest in order to assure safe usage? Which tables and functions must agree with the field's
descriptor in `sys_reg_descs[]`? Name an in-tree field that shows it.

## kvmarm.feat-map: Feature dependency tables

- section: ID registers and traps
- relevance: 5 - a new file that readers have not seen

What do the tables in `arch/arm64/kvm/config.c` describe and how is an entry written, what is
computed from them for a VM, and what checks at boot that they cover every bit of a register?
Start from `NEEDS_FEAT()` and `compute_fgu()`.

## kvmarm.trap-calc: Trap computation

- section: ID registers and traps
- relevance: 5 - it must run after the feature set is final

What must be final before `kvm_calculate_traps()` runs? Which of what it computes is per VM and
done once, which per vCPU, and under which lock?

## kvmarm.sysreg-finalize: System register finalisation

- section: ID registers and traps
- relevance: 5 - the traps are computed from values that this step still changes

What does `kvm_finalize_sys_regs()` change the first time a vCPU runs, and which of that does it
do only once per VM? Where does it run relative to `kvm_calculate_traps()`?

## kvmarm.fgt: Fine-grained trap state

- section: ID registers and traps
- relevance: 4 - two arrays with similar names hold different things

What is held in `kvm->arch.fgu[]` and what in `vcpu->arch.fgt[]`, when is each computed, and
where are the values written to the hardware for VHE, nVHE and a nested guest? Start from
`kvm_vcpu_load_fgt()`.

## kvmarm.hcr-el2: Guest HCR_EL2 value

- section: ID registers and traps
- relevance: 4 - it is assembled in several places at different times

At which points are the bits of `vcpu->arch.hcr_el2` set, and when is the register itself written
on VHE and on nVHE? What does pKVM use in its place for a protected guest?

# Stage-2 page tables

## kvmarm.mmu-lock-mode: MMU lock mode

- section: Stage-2 page tables
- relevance: 5 - the mode differs by operation and by pKVM

Which stage-2 operations take `kvm->mmu_lock` for read and which for write: faults,
access-flag updates, unmap from the MMU notifier, write protection, huge page splitting,
teardown? What changes under pKVM? Start from `kvm_fault_lock()`.

## kvmarm.shared-walk: Shared walks

- section: Stage-2 page tables
- relevance: 5 - concurrent faults update the same tables

How does a walk flagged `KVM_PGTABLE_WALK_SHARED` update an entry so that two walkers do not both
succeed, and what does the walker that fails return? What protects a table page that another
walker has just unlinked?

## kvmarm.shared-walk-callers: Callers of shared walks

- section: Stage-2 page tables
- relevance: 5 - a caller that treats a lost race as a failure returns an error to userspace for a fault that needs a retry

What may run concurrently with a walk flagged `KVM_PGTABLE_WALK_SHARED`? What does the caller of
such a walk do with the error that a walker returns when another walker changed the entry first?

## kvmarm.walker-flags: Walker flags

- section: Stage-2 page tables
- relevance: 4 - the flags change locking and error behaviour

For each flag of `enum kvm_pgtable_walk_flags` that does not select which entries are visited,
what does a walk do differently when the flag is set?

## kvmarm.pgtable-api: Page-table library

- section: Stage-2 page tables
- relevance: 4 - the host calls it through a switch that changes under pKVM

How does the host's stage-2 code select between the page-table library in
`arch/arm64/kvm/hyp/pgtable.c` and the pKVM variants, and what does the pKVM side keep in place
of a page table? What do the memory-management callbacks a user of the library supplies have to
guarantee? Start from `KVM_PGT_FN()`.

## kvmarm.s2-mmu-struct: Stage-2 MMU structure

- section: Stage-2 page tables
- relevance: 4 - a VM can have more than one

Which `struct kvm_s2_mmu` does a vCPU use on its next entry and where is that chosen, and
which of its state only means anything for the shadow stage-2 of a nested guest?

## kvmarm.s2-teardown: Stage-2 teardown

- section: Stage-2 page tables
- relevance: 5 - page tables are freed while other paths may still look at them

In what order does `kvm_free_stage2_pgd()` detach and destroy the page table, and which lock does
it hold for which part? What keeps an MMU notifier or a fault from touching a table that is going
away?

## kvmarm.s2-teardown-usage: Freeing table pages safely

- section: Stage-2 page tables
- relevance: 4 - double free and use after free have both shipped here

What are the requirements for freeing a stage-2 table page, and for dropping a reference on one,
in order to assure safe usage: for a table that still has children, for a subtree detached by a
shared walk, and for a valid entry being replaced? Start from `stage2_free_walker()` and
`kvm_pgtable_stage2_free_unlinked()`.

# Stage-2 faults

## kvmarm.fault-entry: Guest abort dispatch

- section: Stage-2 faults
- relevance: 4 - several cases are peeled off before the memslot lookup

In `kvm_handle_guest_abort()`, which kinds of fault are handled before the memslot lookup and
which after it? Which functions does it call to inject an abort back into the guest?

## kvmarm.fault-stages: Fault handler stages

- section: Stage-2 faults
- relevance: 5 - the handler has been split into stages that pass state in structures

Which of the functions that `user_mem_abort()` calls in turn run before `mmu_lock` is taken and
which under it, and how is state passed from one to the next? Which handlers take a fault on a
guest_memfd slot and a fault of a pKVM guest?

## kvmarm.fault-stale-inputs: Inputs sampled outside the lock

- section: Stage-2 faults
- relevance: 4 - several inputs cap the mapping size, and what detects that they went stale is one check

Which inputs to the mapping size and permissions does the stage-2 fault handler sample before
`mmu_lock` is taken, and what detects that one has gone stale? Where is `mmu_invalidate_seq`
sampled relative to them, and where is `mmu_invalidate_retry()` checked? Start from
`user_mem_abort()`.

## kvmarm.fault-memcache: Fault-path memory cache

- section: Stage-2 faults
- relevance: 4 - the cache type changes under pKVM and the top-up is conditional

How does `get_mmu_memcache()` choose between the normal and the pKVM memory cache, and when does
the fault handler top the cache up and when not? Where is each cache freed? Start from
`get_mmu_memcache()`.

## kvmarm.fault-release-usage: Releasing the faulted-in page

- section: Stage-2 faults
- relevance: 5 - each early return after the page is resolved must release it

What are the requirements for releasing the page that `__kvm_faultin_pfn()` returned, on every
return path of the stage-2 fault handler, in order to assure safe usage? Which release helper does
each kind of exit use, and what does the pKVM handler do in its place?

## kvmarm.mte: Memory tagging for guests

- section: Stage-2 faults
- relevance: 3 - enabling it constrains memslots, VMAs and ID registers

How is MTE enabled for a VM, and what does enabling it forbid? What does the stage-2 fault path
check and do for tags?

# Interrupt controller and timer

## kvmarm.vgic-lock-order: VGIC lock order

- section: Interrupt controller and timer
- relevance: 5 - raw spinlocks taken from interrupt context

What is the documented order of the vgic locks from the VM mutexes down to the per-interrupt
lock, which must be taken with interrupts disabled and why, and how are two vCPUs' list locks
ordered? Start from the comment at the top of `arch/arm64/kvm/vgic/vgic.c`.

## kvmarm.vgic-irq-refs: Interrupt references

- section: Interrupt controller and timer
- relevance: 4 - only one kind of interrupt is reference counted

Of private, shared and LPI interrupts, which `struct vgic_irq` are reference counted? What
protects the lookup of an LPI in `vgic_get_irq()` until the caller holds a reference, and what
frees an LPI?

## kvmarm.vgic-lpi-release-usage: Dropping LPI references under locks

- section: Interrupt controller and timer
- relevance: 5 - the final put takes a lock that ranks above the ones usually held

What are the requirements for calling `vgic_put_irq()` while holding a vCPU's `ap_list_lock` or an
interrupt's `irq_lock` in order to assure safe usage? How does in-tree code that must drop a
reference while it holds one of those locks do it? What does the tree do so that lockdep sees the
lock order when the count does not reach zero?

## kvmarm.vgic-init-stages: VGIC creation and initialisation

- section: Interrupt controller and timer
- relevance: 4 - three stages, each refusing different late configuration

What are the stages from creating the vgic device to the guest being able to run, and which model
may be initialised lazily? What configuration is refused once each stage is passed? Start from
`kvm_vgic_create()`, `vgic_init()` and `kvm_vgic_map_resources()`.

## kvmarm.vgic-ap-list: Pending list and list registers

- section: Interrupt controller and timer
- relevance: 4 - the flush and sync paths were reworked

How does a pending interrupt get from `vgic_queue_irq_unlock()` to a list register, and what
happens when there are more interrupts than list registers? How is a deactivation that the
hardware did not report folded back?

## kvmarm.vgic-v4-forwarding: Direct injection of LPIs

- section: Interrupt controller and timer
- relevance: 4 - setup is silently skipped in many cases and teardown cannot fail

What do `kvm_vgic_v4_set_forwarding()` and `kvm_vgic_v4_unset_forwarding()` check before they
change anything, and what does the caller learn when a check fails? Which state do they update,
and under which lock?

## kvmarm.vgic-cpuif-traps: GICv3 CPU interface traps

- section: Interrupt controller and timer
- relevance: 4 - the trap bits are no longer a runtime variable

How are the `ICH_HCR_EL2` trap bits that apply to every guest decided, and how does code obtain
them? Which per-vCPU bits are added, and when?

## kvmarm.vgic-cpuif-switch: GICv3 CPU interface switch

- section: Interrupt controller and timer
- relevance: 4 - state that is saved only at put is stale in memory while the vCPU is loaded

At what point of guest entry is `ICH_HCR_EL2` written, relative to the list registers and the
VMCR? Which of that state is saved on every exit, and which only at put?

## kvmarm.timer-contexts: Timer contexts

- section: Interrupt controller and timer
- relevance: 4 - which timers are backed by hardware depends on the mode

Which of a vCPU's timer contexts does `get_timer_map()` report as loaded onto the hardware and
which as emulated with an hrtimer, on VHE, on nVHE and for a nested guest? How are the counter
offsets represented, and which lock covers changing them?

# Protected mode

## kvmarm.pkvm-objects: pKVM objects

- section: Protected mode
- relevance: 5 - the hypervisor keeps its own copy of every VM and vCPU

Which structures hold the hypervisor's own copy of a VM and of a vCPU under pKVM, and how does the
host refer to them in a hypercall? How does code test for a protected VM on the host and in the
hypervisor?

## kvmarm.pkvm-protected-vm: Protected VMs and hypervisor vCPUs

- section: Protected mode
- relevance: 5 - the hypervisor trusts its own copy of a vCPU and not the host's

What makes a VM protected under pKVM, and at which point in the VM's life is that fixed? How does
a `struct pkvm_hyp_vcpu` relate to the host's `struct kvm_vcpu`?

## kvmarm.pkvm-vm-lifecycle: Hypervisor VM life cycle

- section: Protected mode
- relevance: 5 - the hypervisor objects appear late and are torn down in steps

When in a VM's life are the hypervisor VM handle reserved, the hypervisor VM and vCPUs
created, and the VM torn down, and which hypercall does each step? Which locks does the host
hold, and in which order? What is unreserved or freed when creation fails part way?

## kvmarm.pkvm-before-first-run: Hypercalls before first run

- section: Protected mode
- relevance: 5 - an ioctl reachable before first run can hit a missing hyp vCPU

What does `pkvm_get_loaded_hyp_vcpu()` return before the first `KVM_RUN` of a vCPU, and what do
the guest memory hypercall handlers do with that result? What are the requirements for an ioctl or
capability that issues those hypercalls before the first run in order to assure safe usage? Start
from `pkvm_get_loaded_hyp_vcpu()`.

## kvmarm.pkvm-state-sync: Flushing and syncing vCPU state

- section: Protected mode
- relevance: 4 - state lives in two copies and only some of it is copied each way

Which vCPU state do `flush_hyp_vcpu()` and `sync_hyp_vcpu()` copy between the host's vCPU and the
hypervisor's, and how does that differ for a protected and a non-protected guest? When does the
host ask for a full sync?

## kvmarm.pkvm-host-dirty: Host changes to vCPU state

- section: Protected mode
- relevance: 4 - a host change that is not marked never reaches the hypervisor's copy

Under pKVM, what marks the host's copy of a vCPU's state as newer than the hypervisor's, and what
does `flush_hyp_vcpu()` do when it finds the mark? What are the requirements for host code that
changes vCPU state between runs in order to assure that the change reaches the guest?

## kvmarm.pkvm-restrictions: Restrictions on protected VMs

- section: Protected mode
- relevance: 4 - capabilities and features are filtered per VM type

Which function decides whether a capability is allowed for a protected VM, and which decides
whether a vCPU feature is? What does userspace get when it asks `KVM_ARM_VCPU_INIT` for a vCPU
feature that is refused for a protected VM? Start from `kvm_pkvm_ext_allowed()`.

## kvmarm.pkvm-memslot-limits: Memslot and backing memory limits

- section: Protected mode
- relevance: 4 - a memslot change that is harmless for a normal VM breaks the isolation of a protected one

Which memslot operations and kinds of backing memory does KVM refuse for a protected VM, and which
for every VM once pKVM is on? Start from `kvm_arch_prepare_memory_region()`.

## kvmarm.pkvm-guest-registers: Protected guest registers and traps

- section: Protected mode
- relevance: 4 - the host's tables do not decide what a protected guest sees

Where are the ID registers of a protected guest decided, and where are its system register traps
decided?

## kvmarm.pkvm-ownership: Page ownership

- section: Protected mode
- relevance: 4 - every transition checks and sets the states, and one that skips a check breaks isolation

Where does pKVM keep the `enum pkvm_page_state` of a page for the host, the hypervisor and a
guest, and which lock covers each? How are host pages shared with a non-protected guest counted?
Start from `enum pkvm_page_state` and `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.

# Nested virtualisation

## kvmarm.nv-state: Guest hypervisor state

- section: Nested virtualisation
- relevance: 4 - the vCPU can be in its own EL2 or in a nested guest

How does KVM tell whether a vCPU with virtual EL2 is currently in its hypervisor context or
running a nested guest, where are the virtual EL2 registers kept and which of them are backed
by the VNCR page, and how does a transition between the two contexts happen?

## kvmarm.nv-shadow-s2: Shadow stage-2 MMUs

- section: Nested virtualisation
- relevance: 4 - a pool of MMUs recycled under the MMU lock

How are shadow stage-2 MMUs for a nested guest looked up, reference counted and recycled, what
marks one as invalid or as needing an unmap before reuse, and what do the MMU notifier paths do
to them?

## kvmarm.nv-trap-forwarding: Trap forwarding tables

- section: Nested virtualisation
- relevance: 4 - every new trapped register needs an entry

How does KVM decide that a trap taken from a nested guest belongs to the guest hypervisor, when
are the coarse and fine-grained tables that encode it built and checked, and what does a
missing entry cause? Start from `arch/arm64/kvm/emulate-nested.c`.

## kvmarm.nv-resx: Sanitising virtual EL2 registers

- section: Nested virtualisation
- relevance: 4 - the stored value is masked on every access

Which guest registers have RES0 and RES1 masks applied, which accessors apply them, and where
are the masks computed from the VM's ID registers and kept? Say whether it is only the
registers backed by the VNCR page.

# Model gaps

## kvmarm.model-gaps: Other mistakes models make

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

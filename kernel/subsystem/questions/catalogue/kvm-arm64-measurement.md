# Questions: KVM on arm64 (measurement set)

- guide: kvm-arm64.md
- title: KVM on arm64

A wide set of questions about the arm64 part of KVM (`arch/arm64/kvm/`), used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 1,851 words. The
architecture-independent part of KVM (memslots, the MMU notifier protocol,
guest_memfd, requests) has its own set, `kvm-measurement.md`. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## kvmarm.core-files: Core files

- section: Finding your way
- relevance: 4 - several jobs have moved to files that are new
- words: 140

Which files under `arch/arm64/kvm/` hold the VM and vCPU ioctls and run loop,
exit handling, system register emulation, the feature-to-register-bit
dependency tables, stage-2 fault handling, reset, PSCI and other hypercalls,
exception injection, the timer, the PMU, debug, FP/SIMD, nested
virtualisation, the host side of pKVM, and the interrupt controller? A table.

## kvmarm.hyp-dirs: Hypervisor source directories

- section: Finding your way
- relevance: 4 - the same source is built for two different worlds
- words: 90

What is in `arch/arm64/kvm/hyp/`, `arch/arm64/kvm/hyp/nvhe/` and
`arch/arm64/kvm/hyp/vhe/`, which files in the first are compiled into both
hypervisor objects, and which directory holds the
page-table code, the world switch, the host hypercall handlers and the pKVM
memory ownership code?

## kvmarm.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

For each job, which function do you start reading from: creating a VM,
`KVM_ARM_VCPU_INIT`, `KVM_RUN`, deciding what to do with an exit, a stage-2
abort, a trapped system register access, a guest HVC or SMC, and a hypercall
from the host kernel into the nVHE hypervisor? A table.

## kvmarm.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - the user-visible ordering rules are written there
- words: 60

Which files under `Documentation/virt/kvm/` describe the arm64 vCPU features,
the hypercall and firmware pseudo-register interface, pKVM, the hypervisor stub
ABI, and the vgic device interfaces, and where is the arm64 lock order written
down?

## kvmarm.selftests: Selftests

- section: Finding your way
- relevance: 3 - says which behaviour is pinned by a test
- words: 70

Where are the arm64 KVM selftests, and which of them cover ID register writes,
the register list, vgic initialisation order, vgic interrupt injection, LPI
stress, stage-2 faults, the timer, PSCI, the SMCCC filter and external aborts?
Start from `tools/testing/selftests/kvm/arm64/`.

## kvmarm.modes: Modes of operation

- section: Finding your way
- relevance: 5 - almost every path branches on the mode
- words: 110

What are the modes arm64 KVM can run in (the values of `kvm-arm.mode`, and VHE,
nVHE and hVHE underneath them), how is the mode chosen at boot, and which
predicate does code use to test for each? Start from `kvm_get_mode()`,
`has_vhe()` and `is_protected_kvm_enabled()`.

# VM and vCPU life cycle

## kvmarm.vm-destroy-order: VM destruction order

- section: Creating and destroying
- relevance: 4 - several objects are freed by more than one owner
- words: 80

In what order does `kvm_arch_destroy_vm()` tear down the vgic, the pKVM
hypervisor VM, the stage-2 page tables and the vCPUs, and what would break if
the vCPUs went first?

## kvmarm.vcpu-init-ioctl: vCPU initialisation call

- section: Configuring a vCPU
- relevance: 4 - the call may be repeated, with conditions
- words: 90

What does `KVM_ARM_VCPU_INIT` check about the target and the feature bits, what
happens on a second call for the same vCPU or for another vCPU of the same VM
with different features, and what does it do to a VM that has already run?
Start from `kvm_arch_vcpu_ioctl_vcpu_init()`.

## kvmarm.vcpu-features: vCPU feature bits

- section: Configuring a vCPU
- relevance: 4 - where they are stored is not where older code kept them
- words: 60

Where are the vCPU feature bits passed to `KVM_ARM_VCPU_INIT` stored once
accepted, which helpers
test them, which combinations are rejected, and which bit is never stored?

## kvmarm.finalize: Feature finalisation

- section: Configuring a vCPU
- relevance: 4 - running before it fails with a specific error
- words: 60

Which vCPU features need `KVM_ARM_VCPU_FINALIZE`, what does finalising
allocate and freeze, and what does each of `KVM_RUN`, a second finalise and a
finalise of an absent feature return? Start from `kvm_arm_vcpu_finalize()`.

## kvmarm.first-run: First run sequence

- section: Configuring a vCPU
- relevance: 5 - the order is what makes late configuration safe to reject
- words: 120

List in order what `kvm_arch_vcpu_run_pid_change()` does the first time a vCPU
runs, which steps are per VM and which per vCPU, and which error codes it
returns for a vCPU that was never initialised or not finalised.

## kvmarm.has-run-predicates: Has-run predicates

- section: Configuring a vCPU
- relevance: 5 - the wrong predicate accepts reconfiguration after the guest ran
- words: 100

Which predicates answer "this vCPU has entered the guest", "some vCPU of this
VM has entered the guest" and "`KVM_ARM_VCPU_INIT` was done", what does each
read, and can the last one become false again? What usage of them to gate an
ioctl, capability or register write is unsafe, and what is correct? Name
in-tree users of each.

## kvmarm.arch-flags: VM flag bits

- section: State and flags
- relevance: 3 - each bit is a one-way latch with its own lock rule
- words: 100

Give a table of the bits in `kvm->arch.flags`, saying what sets each and what
it gates. Start from the flag definitions inside `struct kvm_arch` in
`arch/arm64/include/asm/kvm_host.h`.

## kvmarm.vcpu-flags: vCPU flag sets

- section: State and flags
- relevance: 4 - three sets with different owners, reached through one macro family
- words: 90

What are the flag sets in `struct kvm_vcpu_arch`, who may write each, which of
them does the hypervisor read or clear, and how is a new flag declared and
accessed? Start from `vcpu_set_flag()` and `__vcpu_single_flag()`.

## kvmarm.config-lock: Configuration lock

- section: State and flags
- relevance: 5 - the order against the generic KVM locks is easy to invert
- words: 90

What does `kvm->arch.config_lock` protect, where does it sit in the order with
`kvm->lock`, `vcpu->mutex`, `kvm->slots_lock` and `kvm->srcu`, and how does the
code teach lockdep that order? Name a path that needs more than one of them.

## kvmarm.vcpu-requests: vCPU requests

- section: Running a vCPU
- relevance: 4 - new work for a running vCPU is added here
- words: 110

Give a table of the arm64 vCPU requests (`KVM_REQ_SLEEP` and the others defined
beside it), saying who raises each and what
`check_vcpu_requests()` or the nested request check does for it. Which return
to userspace?

## kvmarm.run-loop: Run loop order

- section: Running a vCPU
- relevance: 5 - the flush and sync calls depend on each other's order
- words: 120

In `kvm_arch_vcpu_ioctl_run()`, in what order are the vgic, timer, PMU, nested
and FP state flushed before entry and synced after exit, where are preemption
and interrupts disabled, where is `vcpu->mode` set, and what is undone when the
entry is abandoned at the last check?

## kvmarm.vcpu-load-put: Load and put

- section: Running a vCPU
- relevance: 4 - called from preempt notifiers as well as ioctls
- words: 90

In order, what does `kvm_arch_vcpu_load()` do, which steps differ under pKVM,
VHE and nested virtualisation, and which ordering constraint between the timer
and the vgic does it state?

## kvmarm.reset: vCPU reset

- section: Running a vCPU
- relevance: 4 - runs both on an unloaded and on a loaded vCPU
- words: 90

From which paths is `kvm_reset_vcpu()` called, how does it cope with the vCPU
being loaded, in what order does it reset SVE, core registers, system registers
and the timer, and how does state passed by PSCI reach it?

## kvmarm.mpidr: MPIDR and vCPU lookup

- section: Running a vCPU
- relevance: 3 - identifiers must stay unique and the fast lookup is optional
- words: 80

How is a vCPU's `MPIDR_EL1` derived, can userspace change it, how does
`kvm_mpidr_to_vcpu()` find a vCPU, and how is the optional lookup table built,
protected and thrown away?

## kvmarm.vpidr-vmpidr: Virtual ID register programming

- section: Running a vCPU
- relevance: 3 - the hardware registers have no usable reset value
- words: 60

Where are `VPIDR_EL2` and `VMPIDR_EL2` written for a guest on VHE and on nVHE,
which guest values do they take, and what differs for a guest that has its own
virtual EL2?

# System registers

## kvmarm.sysreg-storage: Register storage

- section: Register state
- relevance: 5 - the enum is not dense and not in declaration order
- words: 100

How is `enum vcpu_sysreg` numbered, what do its marker entries delimit, where
is the value of a register kept for a guest with and without nested
virtualisation, and what decides the size of the array?

## kvmarm.sysreg-enum-usage: Ranges over the register enum

- section: Register state
- relevance: 5 - a numeric range silently covers unrelated registers
- words: 90

What usage of `<`, `>` or a numeric range over `enum vcpu_sysreg` values is
unsafe, and which in-tree comparisons against enum markers are correct? Name
code that selects a group of registers by name where a range would have been
wrong.

## kvmarm.sysreg-accessors: Register accessors

- section: Register state
- relevance: 5 - the in-memory accessor is no longer an lvalue
- words: 100

Which accessors read and write a guest system register in memory, which go to
the CPU when the state is loaded, how is an in-memory register assigned or
modified in place, and what extra processing applies to some registers of a
nested guest? Start from `__vcpu_sys_reg()` and `vcpu_read_sys_reg()`.

## kvmarm.sysreg-location: Register location while loaded

- section: Register state
- relevance: 4 - reading memory while the value is live on the CPU returns stale data
- words: 90

While a vCPU is loaded on VHE, how does the code decide whether a given guest
register is in memory, live in its own CPU register, or live in a different CPU
register, possibly in another format? Start from `vcpu_read_sys_reg()`.

## kvmarm.sysreg-desc: Trap descriptors

- section: Trap tables
- relevance: 4 - every emulated register is one entry
- words: 110

What are the fields of `struct sys_reg_desc`, which tables of them exist, what
ordering must a table keep and what checks it, and what do the visibility flags
make a register look like to the guest and to userspace?

## kvmarm.sysreg-trap-flow: Trap handling flow

- section: Trap tables
- relevance: 4 - three different things can happen before the access function runs
- words: 100

From a trapped MSR or MRS to the access function, what decides that the access
gets an UNDEF because the feature is disabled for the VM, that it is forwarded
to a guest hypervisor, or that it is emulated? Start from
`kvm_handle_sys_reg()` and `triage_sysreg_trap()`.

## kvmarm.idreg-storage: ID register storage

- section: ID registers
- relevance: 4 - feature checks read the VM's copy, not the host's
- words: 90

Where are a VM's ID register values stored, how are they initialised, which
helpers read them or test a feature field, and which lock covers a write?
Start from `kvm_read_vm_id_reg()` and `kvm_has_feat()`.

## kvmarm.idreg-desc-kinds: ID register descriptor kinds

- section: ID registers
- relevance: 5 - the kind decides what userspace may change
- words: 100

Give a table of the macros that declare an ID register in the descriptor table,
saying for each whether the guest sees a value or zero, whether userspace can
write it, and what the descriptor's `val` field means.

## kvmarm.idreg-write-check: Userspace ID register writes

- section: ID registers
- relevance: 5 - this check is what stops a guest being promised an absent feature
- words: 100

When userspace writes an ID register, which function validates the value, what
is each field compared against, how are fields outside the writable mask
treated, and which error does userspace see? How does userspace discover the
writable masks?

## kvmarm.idreg-after-run: ID registers after first run

- section: ID registers
- relevance: 4 - the rule is per VM, not per vCPU
- words: 50

Once a VM has run, what happens to a userspace write of an ID register that
matches the current value and to one that does not, and what does a kernel
path that tries to change one hit?

## kvmarm.idreg-expose-usage: Exposing a new ID register field

- section: ID registers
- relevance: 5 - each half can be forgotten without a build error
- words: 100

What usage when making a new ID register field visible or writable to a guest
is unsafe, and what does a complete change touch: the descriptor's mask, the
sanitising of the host value, the trap or enable bits, the feature dependency
tables, the pKVM and nested limits? Name a recent field that shows it.

## kvmarm.feat-map: Feature dependency tables

- section: Traps and features
- relevance: 5 - a new file that readers have not seen
- words: 110

What do the tables in `arch/arm64/kvm/config.c` describe, how is an entry
written, what is computed from them for a VM, and what checks at boot that they
cover every bit of a register? Start from `NEEDS_FEAT()` and `compute_fgu()`.

## kvmarm.trap-calc: Trap computation

- section: Traps and features
- relevance: 5 - it must run after the feature set is final
- words: 90

What does `kvm_calculate_traps()` compute, which parts are per vCPU and which
are done once per VM, which lock does it take, and where is it called from?
What does `kvm_finalize_sys_regs()` do before it?

## kvmarm.fgt: Fine-grained trap state

- section: Traps and features
- relevance: 4 - two arrays with similar names hold different things
- words: 80

What is held in `kvm->arch.fgu[]` and what in `vcpu->arch.fgt[]`, when is each
computed, and where are the values written to the hardware for VHE, nVHE and a
nested guest? Start from `kvm_vcpu_load_fgt()`.

## kvmarm.hcr-el2: Guest HCR_EL2 value

- section: Traps and features
- relevance: 4 - it is assembled in several places at different times
- words: 100

Where are the bits of `vcpu->arch.hcr_el2` set: at vCPU init, at first run, at
each load, and at each entry on VHE? Which bits depend on the host CPU, which
on the VM's features, and what does pKVM use instead for a protected guest?

## kvmarm.trap-sync: Synchronising trap register writes

- section: Traps and features
- relevance: 3 - the two switch paths rely on different events
- words: 80

After the world switch writes `HCR_EL2` and the other trap control registers,
what guarantees they take effect before the guest runs, on VHE and on nVHE, and
which writes in the switch code are followed by an explicit barrier or TLB
maintenance and why?

# Exits and exceptions

## kvmarm.hyp-exit-fixup: Exits handled in the hypervisor

- section: Handling exits
- relevance: 4 - some traps never reach the host
- words: 90

Which exits are handled inside the world switch without returning to the host
run loop, how are the handlers selected for VHE, nVHE and a protected guest,
and what does a handler's return value mean? Start from
`__fixup_guest_exit()` and `kvm_hyp_handle_exit()`.

## kvmarm.pending-exception: Pending exception state

- section: Injecting exceptions
- relevance: 5 - injection is deferred, and two deferred actions exclude each other
- words: 100

How does the host record that an exception is to be injected or that the PC is
to be advanced, where and when is that turned into register state, and what
happens if `KVM_RUN` returns to userspace with one pending? Start from
`kvm_pend_exception()`, `kvm_incr_pc()` and `__kvm_adjust_pc()`.

## kvmarm.inject-usage: Injecting an exception safely

- section: Injecting exceptions
- relevance: 5 - the wrong sequence clobbers the guest's ELR or SPSR
- words: 90

What usage of exception injection and PC increment in one exit is unsafe, what
order of reading and writing the guest's ELR, SPSR and ESR is required when the
state may be loaded on the CPU, and what is correct? Name in-tree code that
injects from an abort handler.

## kvmarm.hypercalls: Guest hypercalls

- section: Handling exits
- relevance: 3 - userspace can filter and re-route calls
- words: 90

How is a guest HVC or SMC dispatched, how do the SMCCC filter and the firmware
pseudo-registers change what the guest may call, when can they no longer be
changed, and what differs for a protected guest? Start from
`kvm_smccc_call_handler()`.

# Stage 2 and memory

## kvmarm.s2-mmu-struct: Stage-2 MMU structure

- section: Stage-2 objects
- relevance: 4 - a VM can have more than one
- words: 90

What does `struct kvm_s2_mmu` hold, which instance does a vCPU use on its next
entry and where is that chosen, and which fields only matter for the shadow
stage-2 of a nested guest?

## kvmarm.pgtable-api: Page-table library

- section: Stage-2 objects
- relevance: 4 - the host calls it through a switch that changes under pKVM
- words: 110

What are the main stage-2 entry points of the page-table library in
`arch/arm64/kvm/hyp/pgtable.c`, what are the memory-management callbacks a user
supplies, and how does the host's stage-2 code select between that library and
the pKVM variants? Start from `KVM_PGT_FN()`.

## kvmarm.walker-flags: Walker flags

- section: Stage-2 objects
- relevance: 4 - the flags change locking and error behaviour
- words: 90

Give a table of `enum kvm_pgtable_walk_flags`, saying what each makes a walk
visit, skip or tolerate.

## kvmarm.shared-walk: Shared walks

- section: Stage-2 objects
- relevance: 5 - concurrent faults update the same tables
- words: 100

What may run concurrently with a walk flagged as shared, how does such a walk
update an entry so that two walkers do not both win, what does a loser return
and what does the caller do with it, and what protects a table page that
another walker has just unlinked?

## kvmarm.mmu-lock-mode: MMU lock mode

- section: Stage-2 objects
- relevance: 5 - the mode differs by operation and by pKVM
- words: 90

Which stage-2 operations take `kvm->mmu_lock` for read and which for write:
faults, access-flag updates, unmap from the MMU notifier, write protection,
huge page splitting, teardown? What changes under pKVM? Start from
`kvm_fault_lock()`.

## kvmarm.fault-entry: Guest abort dispatch

- section: Handling a stage-2 fault
- relevance: 4 - several cases are peeled off before the memslot lookup
- words: 110

In `kvm_handle_guest_abort()`, in what order are external aborts, address size
faults, faults on a nested guest's own stage-2, VNCR faults, MMIO, access-flag
faults and permission or translation faults told apart, and which handler does
each reach?

## kvmarm.fault-stages: Fault handler stages

- section: Handling a stage-2 fault
- relevance: 5 - the handler has been split into stages that pass state in structures
- words: 120

What are the stages of `user_mem_abort()`, what does each stage's helper read,
compute and return, which structures carry the state between them, and which
separate handlers take a guest_memfd slot and a pKVM guest?

## kvmarm.fault-release-usage: Releasing the faulted-in page

- section: Handling a stage-2 fault
- relevance: 5 - each early return after the page is resolved must release it
- words: 90

Once the fault handler holds a page from `__kvm_faultin_pfn()`, what usage on
an early return is unsafe, which release helper is used on each kind of exit
(before the lock, under the lock after a retry, after success), and what does
the pKVM handler do instead?

## kvmarm.fault-memcache: Fault-path memory cache

- section: Handling a stage-2 fault
- relevance: 4 - the cache type changes under pKVM and the top-up is conditional
- words: 80

Which memory cache supplies page-table pages to the fault handler, when is it
topped up and when not, how is the choice made between the normal and the pKVM
cache, and where is each freed? Start from `get_mmu_memcache()`.

## kvmarm.fault-mapping-size: Mapping size selection

- section: Handling a stage-2 fault
- relevance: 4 - several inputs cap the size, some read outside the lock
- words: 100

How does the fault handler choose the mapping size from the VMA, the memslot
alignment, dirty logging, transparent huge pages and a nested guest's own
stage-2, which of those are sampled before `mmu_lock` is taken, and what
detects that they went stale?

## kvmarm.fault-retry: Invalidation retry in the fault path

- section: Handling a stage-2 fault
- relevance: 4 - the sequence count must be read at the right point
- words: 70

Where does the arm64 fault handler sample `mmu_invalidate_seq`, which barrier
pairs with the notifier side, where is `mmu_invalidate_retry()` checked, and
what does the handler return when it must retry?

## kvmarm.s2-teardown: Stage-2 teardown

- section: Unmapping and teardown
- relevance: 5 - page tables are freed while other paths may still look at them
- words: 100

How does `kvm_free_stage2_pgd()` make the page table unreachable before
destroying it, which lock does it hold for which part, how are table pages that
a walk unlinked freed, and what keeps an MMU notifier or a fault from touching
a table that is going away?

## kvmarm.s2-teardown-usage: Freeing table pages safely

- section: Unmapping and teardown
- relevance: 4 - double free and use after free have both shipped here
- words: 80

What usage when freeing or dropping references on stage-2 table pages is
unsafe, and what is correct for a table that still has children, for a subtree
detached by a shared walk, and for a valid entry being replaced? Start from
`stage2_free_walker()` and `kvm_pgtable_stage2_free_unlinked()`.

## kvmarm.mte: Memory tagging for guests

- section: Unmapping and teardown
- relevance: 3 - enabling it constrains memslots, VMAs and ID registers
- words: 80

How is MTE enabled for a VM and what does that forbid, what does the fault
path check and do for tags, how are the guest's MTE ID fields filtered for
hardware support, VM configuration and pKVM, and which trap bits follow from
it?

# World switch

## kvmarm.vhe-nvhe-split: VHE and nVHE switch

- section: Entering the guest
- relevance: 4 - work done at load on one is done at every entry on the other
- words: 100

Which parts of the guest context are switched at vCPU load and put on VHE but
at every entry and exit on nVHE, where is each `__kvm_vcpu_run()`, and what
does the nVHE one do differently for a pKVM guest?

## kvmarm.nvhe-build: nVHE object build

- section: Entering the guest
- relevance: 4 - kernel facilities are not available there
- words: 90

How is the nVHE hypervisor object built and linked, what happens to its symbol
and section names, how does host code refer to one of its symbols, and what
may nVHE code not call or rely on? Start from
`arch/arm64/kvm/hyp/nvhe/Makefile`.

## kvmarm.hyp-call: Calling into the hypervisor

- section: Entering the guest
- relevance: 4 - adding a call touches an enum, a table and a handler
- words: 100

What do `kvm_call_hyp()`, `kvm_call_hyp_ret()` and `kvm_call_hyp_nvhe()` do on
VHE and on nVHE, how are host hypercalls numbered and grouped by when they are
allowed, what does a failed call return, and what does adding one require?

## kvmarm.fp-ownership: FP and SIMD ownership

- section: Entering the guest
- relevance: 5 - the tracking moved and the host state is no longer saved lazily
- words: 110

Where is ownership of the FP/SIMD registers tracked while a vCPU is loaded,
what are its states, what happens to the host's state at load, what loads the
guest's state, what do the hooks around guest entry and at put do, and what is
skipped during a nested exception return?

## kvmarm.debug-ownership: Debug register ownership

- section: Entering the guest
- relevance: 3 - the debug code was rewritten around an owner field
- words: 80

How does KVM decide whether the hardware debug registers hold the guest's
values, the values from `KVM_SET_GUEST_DEBUG`, or the host's, where is that
decided, and how does it set the debug traps in `MDCR_EL2`? Start from
`kvm_vcpu_load_debug()`.

# pKVM

## kvmarm.pkvm-objects: pKVM objects

- section: Protected mode
- relevance: 5 - the hypervisor keeps its own copy of every VM and vCPU
- words: 100

What are the hypervisor-side VM and vCPU objects under pKVM, how does the host
name them, how does a hypervisor vCPU relate to the host's `struct kvm_vcpu`,
what makes a VM protected, and how does code test for a protected VM on each
side?

## kvmarm.pkvm-vm-lifecycle: Hypervisor VM life cycle

- section: Protected mode
- relevance: 5 - the hypervisor objects appear late and are torn down in steps
- words: 110

When in a VM's life are the hypervisor VM handle reserved, the hypervisor VM
and vCPUs created, and the VM torn down, which hypercalls do each step, which
locks does the host hold, and what is unreserved or freed when creation fails
part way?

## kvmarm.pkvm-before-first-run: Hypercalls before first run

- section: Protected mode
- relevance: 5 - an ioctl reachable before first run can hit a missing hyp vCPU
- words: 100

Before the first `KVM_RUN`, what does the vCPU load hypercall do, what do the
guest memory hypercalls find when they ask for the loaded hypervisor vCPU, and
what usage in a new ioctl or capability is therefore unsafe? What correct
handling exists in the hypervisor's handlers? Start from
`pkvm_get_loaded_hyp_vcpu()`.

## kvmarm.pkvm-state-sync: Flushing and syncing vCPU state

- section: Protected mode
- relevance: 4 - state lives in two copies and only some of it is copied each way
- words: 100

Under pKVM, which vCPU state is copied from the host's vCPU to the
hypervisor's before entry and back after exit, how does that differ for a
protected and a non-protected guest, what marks the host copy as newer, and
when does the host ask for a full sync?

## kvmarm.pkvm-page-states: Page ownership states

- section: Protected mode
- relevance: 4 - every transition checks and sets these
- words: 90

What are the page ownership states pKVM tracks, where is the state of a page
stored for the host, the hypervisor and a guest, and which locks guard each?
Start from `enum pkvm_page_state`.

## kvmarm.pkvm-transitions: Ownership transitions

- section: Protected mode
- relevance: 4 - a transition that skips a check breaks isolation
- words: 100

Which functions share, unshare, donate and reclaim pages between host,
hypervisor and guest, what must each check before changing anything, and how
are host pages shared with a non-protected guest counted? Start from
`arch/arm64/kvm/hyp/nvhe/mem_protect.c`.

## kvmarm.pkvm-restrictions: Restrictions on protected VMs

- section: Protected mode
- relevance: 4 - capabilities and features are filtered per VM type
- words: 100

Which capabilities, vCPU features, memslot operations and kinds of backing
memory are refused for a protected VM, where is each filter, and where are a
protected guest's ID registers and system register traps decided? Start from
`kvm_pkvm_ext_allowed()`.

# Interrupt controller

## kvmarm.vgic-lock-order: VGIC lock order

- section: VGIC structure
- relevance: 5 - raw spinlocks taken from interrupt context
- words: 100

What is the documented order of the vgic locks from the VM mutexes down to the
per-interrupt lock, which must be taken with interrupts disabled and why, and
how are two vCPUs' list locks ordered? Start from the comment at the top of
`arch/arm64/kvm/vgic/vgic.c`.

## kvmarm.vgic-irq-refs: Interrupt references

- section: VGIC structure
- relevance: 4 - only one kind of interrupt is reference counted
- words: 90

How does code look up a `struct vgic_irq` for a private, shared and LPI
interrupt, which of them are reference counted, how is an LPI found and pinned
without a lock, and what frees it?

## kvmarm.vgic-lpi-release-usage: Dropping LPI references under locks

- section: VGIC structure
- relevance: 5 - the final put takes a lock that ranks above the ones usually held
- words: 100

What usage of `vgic_put_irq()` while holding a vCPU's list lock or an
interrupt's lock is unsafe, how does in-tree code that must drop a reference in
that position do it correctly, and what helps lockdep see the problem on paths
where the count rarely reaches zero?

## kvmarm.vgic-init-stages: VGIC creation and initialisation

- section: VGIC structure
- relevance: 4 - three stages, each refusing different late configuration
- words: 110

What are the stages from creating the vgic device to the guest being able to
run (created, initialised, ready), what does each allocate or register, which
model may be initialised lazily, and what is refused once each stage is
passed? Start from `kvm_vgic_create()`, `vgic_init()` and
`kvm_vgic_map_resources()`.

## kvmarm.vgic-ap-list: Pending list and list registers

- section: VGIC operation
- relevance: 4 - the flush and sync paths were reworked
- words: 100

How does a pending interrupt get from `vgic_queue_irq_unlock()` to a list
register, what do flush and sync do around a guest entry, what happens when
there are more interrupts than list registers, and how is a deactivation that
the hardware did not report folded back?

## kvmarm.vgic-v4-forwarding: Direct injection of LPIs

- section: VGIC operation
- relevance: 4 - setup is silently skipped in many cases and teardown cannot fail
- words: 100

What do `kvm_vgic_v4_set_forwarding()` and `kvm_vgic_v4_unset_forwarding()`
check before doing anything, which failures are silent, which state and count
do they update under which lock, and can unmapping a vLPI report an error?

## kvmarm.vgic-cpuif-traps: GICv3 CPU interface traps

- section: VGIC operation
- relevance: 4 - the trap bits are no longer a runtime variable
- words: 100

How are the `ICH_HCR_EL2` trap bits that apply to every guest decided, how does
code obtain them, which per-vCPU bits are added and when, and at what point of
guest entry is the register written relative to the list registers and the
VMCR? What does a guest without an in-kernel GICv3 get?

## kvmarm.vgic-apr-vmcr: Priority and control state

- section: VGIC operation
- relevance: 3 - saved at load and put, not at every entry
- words: 70

When are the active priority registers and the VMCR saved and restored relative
to vCPU load, put and guest entry, what differs on nVHE and under pKVM, and why
does WFI emulation force a save?

## kvmarm.vgic-v5: GICv5 guests

- section: VGIC operation
- relevance: 3 - a new model that many paths now special-case
- words: 80

What does this tree support for a GICv5 guest and for a GICv3 guest on a GICv5
host, how are its interrupt IDs encoded, which vgic paths return early for it,
and what is finalised for it at first run? If the tree has no GICv5 support,
say so and stop.

# Timer and PMU

## kvmarm.timer-contexts: Timer contexts

- section: Timer and PMU
- relevance: 4 - which timers are backed by hardware depends on the mode
- words: 100

Which timer contexts does a vCPU have, how are the counter offsets represented,
which contexts are loaded onto the hardware and which emulated with an hrtimer
on VHE, nVHE and for a nested guest, and what is `get_timer_map()` for?

## kvmarm.pmu: PMU emulation

- section: Timer and PMU
- relevance: 3 - configuration is frozen at first run
- words: 90

How is a guest's PMU backed by host perf events, which attributes must
userspace set before first run and which are refused afterwards, how is the
number of counters chosen, and which requests reprogram it?

# Nested virtualisation

## kvmarm.nv-state: Guest hypervisor state

- section: Nested virtualisation
- relevance: 4 - the vCPU can be in its own EL2 or in a nested guest
- words: 100

How does KVM tell whether a vCPU with virtual EL2 is currently in its
hypervisor context or running a nested guest, where are the virtual EL2
registers kept, which of them are backed by the VNCR page, and how does a
transition between the two contexts happen?

## kvmarm.nv-shadow-s2: Shadow stage-2 MMUs

- section: Nested virtualisation
- relevance: 4 - a pool of MMUs recycled under the MMU lock
- words: 100

How are shadow stage-2 MMUs for a nested guest allocated, looked up, reference
counted and recycled, what marks one as invalid or as needing an unmap before
reuse, and what do the MMU notifier paths do to them?

## kvmarm.nv-trap-forwarding: Trap forwarding tables

- section: Nested virtualisation
- relevance: 4 - every new trapped register needs an entry
- words: 100

How does KVM decide that a trap taken from a nested guest belongs to the guest
hypervisor, what are the coarse and fine-grained tables that encode it, when
are they built and checked, and what does a missing entry cause? Start from
`arch/arm64/kvm/emulate-nested.c`.

## kvmarm.nv-resx: Sanitising virtual EL2 registers

- section: Nested virtualisation
- relevance: 4 - the stored value is masked on every access
- words: 90

Which guest registers have RES0 and RES1 masks applied, where are the masks
computed and stored, which accessor applies them, and how do they follow from
the VM's ID registers?


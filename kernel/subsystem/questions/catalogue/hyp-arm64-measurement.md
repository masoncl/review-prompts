# Questions: ARM64 Hyp (EL2) (measurement set)

- guide: hyp-arm64.md
- title: ARM64 Hyp (EL2) Subsystem Details

A wide set of questions about the arm64 KVM code that runs at EL2 (the nVHE
object, protected KVM, the EL2 stage-1 and the stage-2 and page ownership
machinery), used to measure what a model already knows before deciding what
the built guide should spend its words on. The hand-written guide it will
replace is 5,733 words and was never checked against current sources. The
host side of KVM on arm64, the architecture code and the generic KVM core have
their own sets. Format: `../../../docs/subsystem-questions.md`.

# The hypervisor object

## hyp.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 140

Which files hold the host hypercall dispatch, the host stage-2 and page
ownership code, the table of hyp VMs and vCPUs, the EL2 stage-1 mappings, the
EL2 page allocator, the pKVM setup code, the FF-A proxy, the PSCI relay, the
protected-VM system register emulation, the world switch, the EL2 vectors, the
code shared with the VHE build, and the host-side pKVM glue? A table. Start
from `arch/arm64/kvm/hyp/`.

## hyp.entry-points: Entry points

- section: Finding your way
- relevance: 4 - where to start reading for each job
- words: 110

For each job (a host hypercall arrives, the host takes a stage-2 fault, the
host issues an SMC, a vCPU is run, a guest exit is fixed up at EL2, a hyp VM
is created, a page changes owner, EL2 panics), which function do you start
reading from? A table.

## hyp.modes: KVM modes on arm64

- section: Finding your way
- relevance: 4 - the same source runs under different trust rules
- words: 90

Which modes can KVM on arm64 run in (with and without VHE, protected, and any
hybrid), how is one chosen at boot, and which predicate tells code which mode
it is in? Start from `is_protected_kvm_enabled()`, `has_vhe()` and
`has_hvhe()`.

## hyp.build-namespace: The nVHE object

- section: Building and linking
- relevance: 4 - explains link errors and why a kernel symbol is not visible
- words: 100

How is the nVHE hypervisor code compiled and linked into the kernel image:
which define marks it, what happens to its section and symbol names, which
compiler instrumentation is removed, and how are pointers in it fixed up for
the EL2 address space? Start from `arch/arm64/kvm/hyp/nvhe/Makefile`.

## hyp.shared-sources: Sources built twice

- section: Building and linking
- relevance: 3 - a change to a shared file changes two hypervisors
- words: 70

Which source files and headers under `arch/arm64/kvm/hyp/` are compiled into
both the VHE and the nVHE hypervisor, and how does such code tell which one it
is being built for?

## hyp.symbol-sharing: Symbols shared with the kernel

- section: Building and linking
- relevance: 3 - the usual cause of an undefined symbol at EL2
- words: 70

How does kernel code refer to a symbol defined in the nVHE object, and what
must be done before nVHE code can use a symbol defined in the kernel proper?
Start from `kvm_nvhe_sym()` and `arch/arm64/kernel/image-vars.h`.

## hyp.library-code: Kernel code usable at EL2

- section: Building and linking
- relevance: 3 - a harmless-looking helper may not exist at EL2
- words: 80

Which pieces of generic kernel code (string and page copy routines, lists,
atomics, per-CPU accessors, capability checks and static keys) can nVHE code
call, and how do capability checks and static keys get their values at EL2?

## hyp.debug-options: Debug configuration

- section: Building and linking
- relevance: 3 - several checks exist only with the debug option
- words: 80

Which configuration options change the behaviour of the nVHE hypervisor for
debugging (assertions, the host stage-2 on panic, stack traces, tracing,
sanitizers), and what does each turn on? Start from `CONFIG_NVHE_EL2_DEBUG` in
`arch/arm64/kvm/Kconfig`.

# Running at EL2

## hyp.execution-context: Execution context

- section: The EL2 environment
- relevance: 5 - rules from kernel context do not carry over
- words: 100

In what context does nVHE code handling a trap from the host run: is there a
scheduler, preemption, sleeping, deferred work, memory allocation from the
kernel allocators, user access or logging, and how does the handler return to
the host?

## hyp.interrupts: Interrupts while at EL2

- section: The EL2 environment
- relevance: 4 - decides whether a handler can be interrupted
- words: 70

Are interrupts and SErrors masked while nVHE code handles a host trap, where
is a physical interrupt that arrives while a guest runs delivered, and what
happens if an exception is taken from EL2 itself?

## hyp.concurrency: Concurrency at EL2

- section: The EL2 environment
- relevance: 5 - false races are reported when this is misjudged
- words: 80

Which kinds of concurrency must nVHE code allow for and which cannot happen:
preemption of a handler, deferral of part of it, and two physical CPUs in EL2
at once on the same data?

## hyp.vectors: EL2 vector tables

- section: The EL2 environment
- relevance: 4 - which one is installed decides how a fault at EL2 is handled
- words: 80

Which exception vector tables does the nVHE hypervisor have, when is each
installed in VBAR_EL2, and what does each do with a synchronous exception
taken from EL2? Start from `__kvm_hyp_host_vector` and `__kvm_hyp_vector`.

## hyp.host-context: Saved host registers

- section: The EL2 environment
- relevance: 3 - arguments and results travel through it
- words: 70

Where are the host's general purpose registers saved on a trap to EL2, how
does a handler read an argument and set a result, and which function returns
to the host? Start from `__host_exit` and `DECLARE_REG()`.

## hyp.percpu-data: Per-CPU data

- section: The EL2 environment
- relevance: 3 - the usual accessors are redefined
- words: 80

How does nVHE code reach per-CPU data, who sets up the per-CPU areas and
their offsets, and which per-CPU objects carry the host context, the init
parameters and the loaded vCPU? Start from `struct kvm_host_data` and
`host_data_ptr()`.

## hyp.stack: Hypervisor stack

- section: The EL2 environment
- relevance: 3 - large on-stack copies overflow it
- words: 70

How large is a CPU's EL2 stack under nVHE, how is an overflow detected, and
what runs when one is? Start from `pkvm_create_stack()` and
`NVHE_STACK_SIZE`.

## hyp.spinlock: Hypervisor spinlock

- section: Locking
- relevance: 4 - the only lock there is
- words: 80

What lock type does nVHE code use, how is it implemented, does it have
interrupt-saving or sleeping variants, and when does `hyp_assert_lock_held()`
actually check anything? Start from `arch/arm64/kvm/hyp/include/nvhe/spinlock.h`.

## hyp.lock-inventory: Locks and what they protect

- section: Locking
- relevance: 5 - every ownership change rests on these
- words: 140

List the locks the nVHE hypervisor defines and say what each protects: the VM
table, the host stage-2 and host page state, the EL2 stage-1 and hyp page
state, a guest's stage-2, a page pool, the FF-A buffers and version, the block
fixmap, the trace buffer. A table.

## hyp.lock-order: Lock ordering

- section: Locking
- relevance: 5 - there is no lockdep at EL2
- words: 80

In what order are the host, hypervisor and guest page-table locks taken when a
function needs more than one, where is that order written down, and where does
the VM table lock sit relative to them? Start from `enum pkvm_component_id`
and `__pkvm_host_force_reclaim_page_guest()`.

# Panics and assertions

## hyp.bug-warn: BUG and WARN at EL2

- section: Fatal paths
- relevance: 5 - error handling after a WARN_ON is dead code
- words: 80

What do `BUG()`, `BUG_ON()` and `WARN_ON()` expand to in nVHE code, does
execution continue after a `WARN_ON()` whose condition is true, and what does
that mean for `if (WARN_ON(x)) return ...;`?

## hyp.panic-path: Route to the host panic

- section: Fatal paths
- relevance: 4 - two routes, depending on the vector table
- words: 100

Trace how a BRK or an unexpected exception taken at EL2 reaches `hyp_panic()`
when the host vector table is installed and when the guest one is, what
`hyp_panic()` restores first, and how control gets to
`nvhe_hyp_panic_handler()` in the host.

## hyp.panic-report: Hyp panic report

- section: Fatal paths
- relevance: 3 - how to read a report
- words: 80

What does the host print for a hyp panic, when can it name the file and line
of a `BUG()` or print an EL2 stack trace, and which options does that depend
on?

## hyp.warn-usage: Asserting versus returning an error

- section: Fatal paths
- relevance: 5 - a wrong assertion lets the host or a guest take the machine down
- words: 100

What use of `WARN_ON()` or `BUG_ON()` on a condition in nVHE code is unsafe,
and what that looks similar is correct? Show both with code from
`arch/arm64/kvm/hyp/nvhe/mem_protect.c`: a condition that is returned as an
error, and one that is asserted.

## hyp.threat-model: Protection goals

- section: Trust
- relevance: 5 - decides whether a finding is a bug at all
- words: 110

What is pKVM meant to protect, from whom: the hypervisor from the host and
from guests, a protected guest from the host, the host from guests? What is
outside its protection, such as the host harming itself or firmware
misbehaving? Start from `Documentation/virt/kvm/arm/pkvm.rst`.

## hyp.isolation-status: Isolation implemented so far

- section: Trust
- relevance: 5 - part of the design is not in this tree
- words: 80

Which of pKVM's isolation mechanisms (guest memory, guest CPU state, DMA,
proxying of secure-world services, guest firmware) does this tree implement
and which does it say are unimplemented? What does creating a protected VM do
to the kernel's taint state? Start from `Documentation/virt/kvm/arm/pkvm.rst`
and `pkvm_init_host_vm()`.

# Boot and de-privilege

## hyp.init-sequence: Init sequence

- section: Becoming a hypervisor
- relevance: 4 - which code runs with the host still at EL2
- words: 120

List in order the steps from early boot to the host losing control of EL2 in
protected mode: the memory reservation, KVM's arm64 init, the hypercall that
hands memory to the hypervisor, and finalisation, with the function and the
initcall level of each. Start from `kvm_hyp_reserve()`, `kvm_arm_init()` and
`finalize_pkvm()`.

## hyp.pkvm-init: Hypervisor self-initialisation

- section: Becoming a hypervisor
- relevance: 4 - the last code that trusts the host
- words: 110

What does `__pkvm_init()` do, in order, with the memory it is given, how does
it move onto its own page tables, and what does `__pkvm_init_finalise()` then
set up before returning to the host?

## hyp.deprivilege: De-privilege point

- section: Becoming a hypervisor
- relevance: 5 - trust assumptions flip here
- words: 90

Which function takes EL2 away from the host for good, at which initcall level,
what does it run on each CPU, and what does that per-CPU call change? What
stops it being repeated on a CPU? Start from `pkvm_drop_host_privileges()` and
`__pkvm_prot_finalize()`.

## hyp.init-predicates: Init state predicates

- section: Becoming a hypervisor
- relevance: 4 - they are true at different times
- words: 90

When does each of `is_protected_kvm_enabled()`, `is_kvm_arm_initialised()`,
`is_pkvm_initialized()` and the `kvm_protected_mode_initialized` static key
become true, and which one does the hypervisor itself test to tell the two
phases apart?

## hyp.init-memory: Init sections after de-privilege

- section: Becoming a hypervisor
- relevance: 3 - the host can no longer read some of its own image
- words: 70

After de-privilege, which parts of the kernel image and which reserved memory
can the host no longer access, what is done for kmemleak because of it, and
may a runtime hypercall handler refer to host `__init` code or data?

## hyp.psci-relay: PSCI relay

- section: Becoming a hypervisor
- relevance: 3 - CPUs coming up must enter through EL2
- words: 90

Which PSCI calls from the host does the hypervisor intercept and why, which
CPUs may the host boot, how are a CPU's entry point and argument handed to it
safely, and what does a CPU run at EL2 before entering the host? Start from
`kvm_host_psci_handler()`.

# The hypercall interface

## hyp.hcall-dispatch: Hypercall dispatch

- section: Host hypercalls
- relevance: 4 - the front door
- words: 90

How does an HVC from the host reach its handler: how is the function number
taken from the register, what is returned for a number that is out of range or
has no handler, and where do the status and the handler's result go? Start
from `handle_host_hcall()`.

## hyp.hcall-bands: Hypercall availability by phase

- section: Host hypercalls
- relevance: 5 - a number in the wrong place is callable at the wrong time
- words: 90

How does the position of an entry in `enum __kvm_host_smccc_func` decide
whether the hypercall can be used before pKVM is finalised, afterwards, or
both? Name the marker entries and say which hypercall is a deliberate
exception and why.

## hyp.hcall-add: Adding a hypercall

- section: Host hypercalls
- relevance: 4 - several places must agree
- words: 80

What has to be added, and where, for a new host hypercall: the number, the
handler, the table entry, the host-side call? What catches a table that is out
of step with the enum?

## hyp.hcall-args: Hypercall arguments

- section: Host hypercalls
- relevance: 4 - pointers and scalars are not alike
- words: 80

How does a handler read its arguments, what must it do to a host kernel
pointer before using it, and what is the difference in trust between a scalar
passed in a register and memory reached through such a pointer?

## hyp.hcall-host-side: Calling hyp from the host

- section: Host hypercalls
- relevance: 3 - the same call is a function call under VHE
- words: 80

What do `kvm_call_hyp()`, `kvm_call_hyp_ret()` and `kvm_call_hyp_nvhe()` do in
each mode, and what does the host do when the hypervisor reports that a call
is not supported?

## hyp.host-smc: Host SMC handling

- section: Other host traps
- relevance: 4 - part of the boundary with the secure world
- words: 90

What does the hypervisor do with an SMC from the host: which encodings and
function ids are refused, which handlers are tried in which order, what
happens to a call none of them claims, and why? Start from
`handle_host_smc()`.

## hyp.host-abort: Host stage-2 faults

- section: Other host traps
- relevance: 4 - the host's memory map is built here
- words: 100

What does the hypervisor do when the host takes a stage-2 fault: how is the
address found, when is a mapping installed and how large, when is an exception
sent back to the host and how does the host recognise it, and which results
are fatal? Start from `handle_host_mem_abort()`.

## hyp.guest-hvc: Protected guest hypercalls

- section: Other host traps
- relevance: 3 - the guest's only way to reach the host's memory
- words: 80

Which hypercalls from a protected guest does EL2 handle itself, what does each
do, and what happens to the rest? What happens when a guest asks to share a
page that is not mapped yet? Start from `kvm_handle_pvm_hvc64()`.

# Data from the host

## hyp.host-inputs: Host-controlled inputs

- section: Trusting the host
- relevance: 5 - the attack surface
- words: 100

After de-privilege, which inputs to EL2 can the host change at will: hypercall
registers, host kernel memory, the host's `struct kvm` and `struct kvm_vcpu`,
memcaches, EL1 system registers? Which can it change while another CPU is in
the middle of a hypercall?

## hyp.toctou-usage: Reading host memory

- section: Trusting the host
- relevance: 5 - the classic hypervisor bug
- words: 100

What way of reading a field of host-owned memory at EL2 is unsafe, and what
that looks similar is correct? Show in-tree code that reads a host field once
and validates the copy, and say what the large size of `struct kvm_vcpu` rules
out.

## hyp.hyp-structs: Hyp copies and back pointers

- section: Trusting the host
- relevance: 5 - the two are one dereference apart
- words: 90

What do `struct pkvm_hyp_vm` and `struct pkvm_hyp_vcpu` contain, which of
their members are EL2-private copies and which point back at host memory, and
how do you get from a hyp vCPU to its hyp VM?

## hyp.pinning: Pinning shared host memory

- section: Trusting the host
- relevance: 4 - what keeps a back pointer dereferenceable
- words: 90

What does `hyp_pin_shared_mem()` check and do, what does it guarantee while
the pin is held and what does it not guarantee about the contents, and which
host objects stay pinned for the life of a VM or vCPU?

## hyp.memcache: Hyp memcaches

- section: Trusting the host
- relevance: 4 - how the host feeds pages to EL2
- words: 90

What is a `struct kvm_hyp_memcache`, how are its pages linked, which helpers
push and pop, and which memcaches exist per vCPU and per VM and in which
direction do pages flow through each?

## hyp.memcache-usage: Taking pages from a host memcache

- section: Trusting the host
- relevance: 5 - the list head is in host memory
- words: 90

What way of taking a page from a memcache that lives in host memory is unsafe,
and what does the in-tree code do that makes it correct? Start from
`refill_memcache()` and `admit_host_page()`.

## hyp.donated-memory: Memory donated for hyp objects

- section: Trusting the host
- relevance: 4 - sizes and alignment come from the host
- words: 80

How does EL2 take over host memory offered for a VM, a vCPU or a page-table
root, what does it check, when is the memory cleared, and how is it handed
back? Start from `map_donated_memory()` and `unmap_donated_memory()`.

## hyp.sysreg-trust: System registers the host can write

- section: Trusting the host
- relevance: 4 - reading back a value is only safe for some registers
- words: 80

Which system registers that EL2 code reads can the host have written, and
which can it not? From where does the hypervisor take its own HCR_EL2, VTTBR
and VTCR for the host instead of reading the hardware back?

## hyp.at-translation: Resolving a fault address

- section: Trusting the host
- relevance: 3 - the translation can fail under the hypervisor's feet
- words: 70

When HPFAR_EL2 is not valid for a fault, how does EL2 find the faulting IPA:
which address translation instruction, how is failure reported, what is done
with PAR_EL1, and what does the caller do on failure? Start from
`__get_fault_info()`.

# EL2 addresses

## hyp.address-space: EL2 address space layout

- section: Addresses
- relevance: 4 - which conversion applies depends on the region
- words: 110

How is the nVHE EL2 virtual address space divided (the linear map, the
identity map, the private range, the vmemmap), where is each region's base
decided, and which helpers convert between a hyp VA, a physical address and a
`struct hyp_page`? A table. Start from `hyp_create_idmap()` and
`arch/arm64/kvm/hyp/include/nvhe/memory.h`.

## hyp.kern-hyp-va: Host pointers at EL2

- section: Addresses
- relevance: 4 - every host pointer goes through it
- words: 80

What does `kern_hyp_va()` do to a pointer, how and when are its mask and tag
computed, and what does it become under VHE? Start from `__kern_hyp_va()` and
`arch/arm64/kvm/va_layout.c`.

## hyp.kern-hyp-va-repeat: Converting a pointer twice

- section: Addresses
- relevance: 4 - misjudged in both directions
- words: 90

For which pointers is applying `kern_hyp_va()` a second time harmless and for
which does it corrupt the address: a host linear-map pointer already
converted, an object from the EL2 page allocator, an address in the private
range such as the vmemmap, the fixmap or a stack? Name in-tree code that
relies on the harmless case.

## hyp.private-range: Private VA range

- section: Addresses
- relevance: 3 - allocations are never returned
- words: 70

How are addresses in the EL2 private range allocated, what uses them, what
limits the range, and can an allocation be freed? Start from
`pkvm_alloc_private_va_range()`.

# EL2 memory management

## hyp.hyp-page: Per-page metadata

- section: Pages and pools
- relevance: 5 - ownership and the allocator share this structure
- words: 90

What are the fields of `struct hyp_page`, which lock guards each, what size
must the structure stay and what enforces it, and how is the array of them
found and backed? Start from `hyp_vmemmap` and `hyp_back_vmemmap()`.

## hyp.pools: Page pools

- section: Pages and pools
- relevance: 4 - there are more than two
- words: 80

Which `struct hyp_pool` instances does the hypervisor have, where is each
defined and initialised, and what is each used for?

## hyp.pool-api: Page allocator interface

- section: Pages and pools
- relevance: 4 - semantics differ from the kernel allocator
- words: 100

What do `hyp_alloc_pages()`, `hyp_get_page()`, `hyp_put_page()`,
`hyp_split_page()` and `hyp_pool_init()` do: what reference count does a new
page have, when are pages zeroed, what is returned when the pool is empty, and
what are reserved pages?

## hyp.pool-locking: Pool locking

- section: Pages and pools
- relevance: 4 - the refcount helpers take no lock themselves
- words: 80

What does a pool's lock protect, which reference count helpers rely on the
caller for exclusion, and where is a page's reference count changed without
the pool lock and what protects it there?

## hyp.page-order: Page order convention

- section: Pages and pools
- relevance: 3 - walkers misread tail pages
- words: 60

How is the order of a free block recorded across its head and tail
`struct hyp_page` entries, and what does splitting a block do to them? Start
from `HYP_NO_ORDER`.

## hyp.pool-foreign-pages: Pages from outside a pool's range

- section: Pages and pools
- relevance: 3 - looks like a bug and is not
- words: 60

What happens when a page outside a pool's physical range is freed into it, why
does that happen in normal operation, and how is such a page treated
differently? Start from `__hyp_attach_page()`.

## hyp.pool-usage: Using the page allocator

- section: Pages and pools
- relevance: 4 - misuse corrupts a free list silently
- words: 90

What usage of the EL2 page allocator is unsafe (which pool a page is returned
to, what is done when allocation fails, touching the count or order directly),
and what that looks similar is correct in-tree?

## hyp.fixmap: Fixmap slots

- section: Temporary mappings
- relevance: 4 - the only way to touch a page EL2 has no mapping for
- words: 90

How does `hyp_fixmap_map()` map a physical page and `hyp_fixmap_unmap()`
remove it: whose slot is used, what is written to the PTE, and which of the
two does the TLB invalidation and with what scope?

## hyp.fixmap-usage: Using the fixmap

- section: Temporary mappings
- relevance: 4 - a missed unmap exposes the wrong page to the next user
- words: 80

What usage of the fixmap is unsafe (nesting, an exit path that skips the
unmap, keeping the pointer), what goes wrong in each case, and which in-tree
callers show the correct pairing?

## hyp.stage1: EL2 stage-1 mappings

- section: Page tables at EL2
- relevance: 3 - the hypervisor's own page table
- words: 80

Which page table is the hypervisor's own stage-1, which lock guards it, which
functions add linear-map and private mappings, and how is a mapping removed?
Start from `pkvm_pgtable` and `pkvm_create_mappings_locked()`.

## hyp.mm-ops: Page-table memory callbacks

- section: Page tables at EL2
- relevance: 3 - each table allocates from a different place
- words: 90

Which `struct kvm_pgtable_mm_ops` does the hypervisor set up for its stage-1,
the host stage-2 and a guest stage-2, where does each get table pages from,
and how do the guest callbacks know which VM they are acting for?

# Page ownership

## hyp.page-states: Page states

- section: Ownership state
- relevance: 5 - the vocabulary of every transition
- words: 90

What are the values of `enum pkvm_page_state`, what does each mean from the
point of view of one component, and which are stored as such and which are
inferred?

## hyp.state-storage: Page state storage

- section: Ownership state
- relevance: 5 - three components, three encodings
- words: 100

Where is a page's state stored for the host, for the hypervisor and for a
guest, how is the hypervisor's state encoded so that zeroed metadata has a safe
meaning, and which accessors read and write each?

## hyp.state-usage: Testing page state

- section: Ownership state
- relevance: 4 - zero does not mean the same thing in each field
- words: 70

What way of testing a page's state is unsafe, such as comparing a field of
`struct hyp_page` with zero, and what is the correct form? What does all-zero
metadata mean for the host's view and for the hypervisor's?

## hyp.transitions: Ownership transitions

- section: Transitions
- relevance: 5 - the map of the ownership code
- words: 150

Give a table of the share, unshare, donate and reclaim transitions in
`arch/arm64/kvm/hyp/nvhe/mem_protect.c`: the function, who initiates it, the
state each side must be in before, and the state each side is left in.

## hyp.transition-shape: Shape of a transition

- section: Transitions
- relevance: 5 - what a new transition has to look like
- words: 100

What order of steps do the transition functions follow: argument validation,
locks, state checks on each side, resource checks, then updates? Why can the
updates be asserted rather than checked, and what is checked beforehand to
make that true for a guest stage-2 map?

## hyp.transition-usage: Failing part way through a transition

- section: Transitions
- relevance: 5 - leaves metadata and page tables disagreeing
- words: 90

What ordering of checks and updates in an ownership transition is unsafe, and
what that looks similar is correct? Name an in-tree transition whose last step
can fail without an assertion and say why that is safe there.

## hyp.range-validation: Validating physical ranges

- section: Transitions
- relevance: 5 - the range comes from the host
- words: 90

Which helpers validate a pfn and page count or a physical range from an
untrusted caller, what does each check (overflow, the physical address size,
memory versus MMIO, NOMAP regions), and which transitions use which? Start
from `pfn_range_is_valid()` and `check_range_allowed_memory()`.

## hyp.host-stage2: Host stage-2 map

- section: The host's stage-2
- relevance: 4 - an identity map filled in on demand
- words: 100

How is the host's stage-2 populated: what is mapped up front, what on a fault,
with which permissions for memory and for MMIO, when may a block mapping be
used and what forces page granularity? Start from `host_stage2_idmap()` and
`host_stage2_force_pte_cb()`.

## hyp.host-annotations: Invalid entries in the host stage-2

- section: The host's stage-2
- relevance: 4 - the only record of who owns a page the host lost
- words: 100

How does the host stage-2 record that a page belongs to the hypervisor or to a
guest: which invalid entry types exist, how are the owner and the extra
metadata laid out, what is stored for a guest-owned page, and which function
writes it? Start from `host_stage2_set_owner_metadata_locked()`.

## hyp.multi-share: Sharing one page with several guests

- section: Guest memory
- relevance: 3 - the only case where a shared page is shared again
- words: 70

When may a host page be shared with more than one guest, what counts the
shares, what bounds the count, and when does the page return to being owned
outright by the host?

## hyp.guest-map-sizes: Mapping sizes for guests

- section: Guest memory
- relevance: 4 - block mappings are restricted
- words: 80

What sizes may the host ask for when sharing memory with or donating memory to
a guest under pKVM, what alignment is required, and where is that checked at
EL2 and on the host side?

## hyp.np-guest-ops: Non-protected guest stage-2 operations

- section: Guest memory
- relevance: 3 - the host no longer owns these page tables
- words: 90

Under pKVM, which hypercalls let the host change permissions, write-protect
and age pages of a non-protected guest, what does each check, and what happens
if they are used on a protected VM?

## hyp.host-mappings: Host-side record of guest mappings

- section: Guest memory
- relevance: 3 - the host cannot read the guest's stage-2
- words: 80

How does the host remember what it has mapped into a guest under pKVM, which
functions stand in for the generic stage-2 page-table functions, and how do
they differ for protected and non-protected VMs? Start from
`struct pkvm_mapping` and `pkvm_pgtable_stage2_map()`.

## hyp.poison: Forced reclaim and poisoned entries

- section: Guest memory
- relevance: 4 - new state that readers may not know
- words: 100

What happens when the host touches a page it donated to a protected guest: who
decides to reclaim it, what does EL2 do to the page and to the guest's
stage-2 entry, how does the guest's next access to it end, and why does EL2
work out the faulting address itself?

## hyp.reclaim-clearing: Clearing pages returned to the host

- section: Guest memory
- relevance: 4 - a missed clean leaks guest data
- words: 70

Before a page leaves a protected guest or the hypervisor for the host, what
clears it and what cache maintenance is done, and why is the guest-page
variant of the cache clean not used there?

## hyp.share-with-hyp: Sharing host memory with the hypervisor

- section: Guest memory
- relevance: 3 - refcounted on the host side
- words: 70

How does host code share one of its pages with the hypervisor and take it
back, what keeps count of repeated shares of the same page, and what refuses
an unshare at EL2? Start from `kvm_share_hyp()`.

# VMs and vCPUs at EL2

## hyp.vm-table: VM handles and the VM table

- section: Lifecycle
- relevance: 4 - the handle is the host's only name for a VM
- words: 90

How are VM handles allocated and looked up: where does numbering start, how
many VMs can exist, what marks a slot that is reserved but not yet
initialised, and how is the VMID derived?

## hyp.vm-create: Creating a hyp VM

- section: Lifecycle
- relevance: 4 - host fields are sampled here
- words: 110

What are the steps of creating a VM at EL2, from reserving a handle to
publishing the VM, which host fields are read and when, and what is undone on
each failure? When does the host trigger it and under which locks? Start from
`__pkvm_init_vm()` and `pkvm_create_hyp_vm()`.

## hyp.vcpu-create: Creating a hyp vCPU

- section: Lifecycle
- relevance: 4 - published to other CPUs
- words: 90

What does `__pkvm_init_vcpu()` do in order, what is pinned, how is the new
vCPU made visible to the load path and with what memory ordering, and what is
undone on failure?

## hyp.vm-refcount: References to a hyp VM

- section: Lifecycle
- relevance: 4 - teardown waits on it
- words: 80

What counts references to a hyp VM, which functions take and drop one, and
which operations refuse to proceed while the count is not zero?

## hyp.vcpu-load: Loading and putting a vCPU

- section: Lifecycle
- relevance: 4 - most hypercalls act on the loaded vCPU
- words: 90

What does loading a hyp vCPU on a physical CPU record, what makes a load fail,
what does a put do, and how do later hypercalls find the vCPU they act on?
Start from `pkvm_load_hyp_vcpu()`.

## hyp.teardown: Tearing a VM down

- section: Lifecycle
- relevance: 5 - pages must not leak or come back early
- words: 120

What are the stages of tearing a VM down under pKVM, in host order: what does
each hypercall require and do, what does the dying flag stop and allow, how do
guest pages, page-table pages and metadata pages each get back to the host,
and who chooses which guest pages to reclaim?

## hyp.vm-features: Features allowed for protected VMs

- section: Lifecycle
- relevance: 3 - the host's feature set is filtered
- words: 80

How are a VM's vCPU features and flags decided at EL2 for a protected VM and
for a non-protected one, and where is the list of capabilities a protected VM
may use? Start from `pkvm_init_features_from_host()` and
`kvm_pkvm_ext_allowed()`.

# Running a vCPU

## hyp.run-path: The run hypercall

- section: Entry and exit
- relevance: 4 - two different paths share one handler
- words: 90

What does `handle___kvm_vcpu_run()` do under pKVM and without it, how is the
vCPU pointer from the host checked, and what is refused before entry?

## hyp.flush-sync: Per-entry flush and sync

- section: Entry and exit
- relevance: 5 - which state crosses the boundary on every entry
- words: 130

Which vCPU state is copied from the host's vCPU to the hyp vCPU before each
guest entry and back after each exit, and how does that differ between a
protected and a non-protected vCPU? Start from `flush_hyp_vcpu()` and
`sync_hyp_vcpu()`.

## hyp.load-vs-entry: Load-time versus entry-time state

- section: Entry and exit
- relevance: 4 - a missing copy is only missing at the right place
- words: 90

Which state is brought over from the host when a vCPU is loaded rather than on
each entry, for protected and for non-protected vCPUs? A table of what is
copied where. Start from `handle___pkvm_vcpu_load()`.

## hyp.dirty-state: On-demand register sync

- section: Entry and exit
- relevance: 3 - new, and readers may not know it
- words: 70

What is `PKVM_HOST_STATE_DIRTY`, which vCPUs does it apply to, and when is the
full register state copied from the hyp vCPU to the host's and back? Start
from `handle___pkvm_vcpu_sync_state()`.

## hyp.hcr: HCR_EL2 for a hyp vCPU

- section: Traps
- relevance: 5 - the host must not define a protected guest's regime
- words: 100

Where is a hyp vCPU's HCR_EL2 value computed, which bits are taken from the
host at load and on each entry, and why those? Start from
`pkvm_vcpu_reset_hcr()`, `pvm_init_traps_hcr()` and `flush_hyp_vcpu()`.

## hyp.hcr-usage: Taking trap bits from the host

- section: Traps
- relevance: 4 - both too many and too few bits are bugs
- words: 80

What way of combining the host's HCR_EL2 value into a protected vCPU's is
unsafe, what goes wrong if a bit the host legitimately sets at run time is
left out, and what does the correct in-tree form look like?

## hyp.trap-init: Other trap registers

- section: Traps
- relevance: 4 - protected and non-protected take different paths
- words: 90

For a hyp vCPU, where do MDCR_EL2, HCRX_EL2, CPTR_EL2 and the fine-grained
trap registers get their values, for a protected and for a non-protected VM,
and which are refreshed from the host and when?

## hyp.exit-handlers: Exit handling at EL2

- section: Traps
- relevance: 4 - protected guests get a different table
- words: 90

How does the nVHE hypervisor decide whether to handle a guest exit itself or
return to the host, which handler tables exist and how do they differ for a
protected vCPU, and what is done about a protected guest found in AArch32?
Start from `fixup_guest_exit()`.

## hyp.pvm-sysregs: Protected guest system registers

- section: Traps
- relevance: 3 - the feature set is fixed at EL2
- words: 90

How are a protected guest's system register traps emulated: where is the
table, how are ID register values worked out, what happens to an access with
no entry or one marked as handled by the host, and what is verified about the
table at init? Start from `kvm_handle_pvm_sysreg()`.

## hyp.fp-switch: FP and SVE switching at EL2

- section: Floating point
- relevance: 4 - lazy, and tracked per CPU
- words: 90

How does EL2 switch FP and SVE state lazily: what records who owns the
registers, which trap starts the switch, and what does the handler do in
order? Start from `kvm_hyp_handle_fpsimd()` and `fp_owner`.

## hyp.fp-host-state: Host FP state

- section: Floating point
- relevance: 5 - differs by KVM mode, not by guest type
- words: 110

Who saves and restores the host's FP and SVE state around a guest run when
pKVM is enabled and when it is not, what condition selects between them, at
which vector length is host state saved, and do protected and non-protected
guests differ? Start from `kvm_hyp_save_fpsimd_host()` and
`fpsimd_lazy_switch_to_host()`.

## hyp.fp-usage: Changing FP switching code

- section: Floating point
- relevance: 4 - host register contents can leak into a guest
- words: 80

What is unsafe in EL2 FP switching code (the vector length used for a save,
what the eager save is keyed on, exposing registers before a save), and what
that looks similar is correct?

## hyp.sve-buffers: SVE state buffers

- section: Floating point
- relevance: 3 - host memory used by EL2 for the VM's lifetime
- words: 70

Where does EL2 keep a guest's SVE state and the host's, who allocates each,
how is each made accessible to EL2, and what bounds the guest's vector length?

## hyp.debug-state: Debug and profiling state

- section: Other state
- relevance: 3 - profiling buffers use the guest's translation regime
- words: 80

How is debug register state passed between the host's vCPU and the hyp vCPU,
and what is done to the statistical profiling and trace buffers before the
translation regime changes, and why? Start from
`__debug_save_host_buffers_nvhe()`.

## hyp.switch-order: Ordering in the world switch

- section: Other state
- relevance: 4 - barriers and errata fix the order
- words: 100

Which ordering constraints does `__kvm_vcpu_run()` observe on nVHE: barriers
before the stage-2 context changes, the order of system register restore
against stage-2 and trap activation, and the order on the way out? Say what
each is for.

## hyp.vmid: VMIDs under pKVM

- section: Other state
- relevance: 3 - the allocator moves to EL2
- words: 70

Who assigns VMIDs under pKVM and how, which VMID does the host's stage-2 use,
what is done before a VMID can be reused, and how is the common-not-private
bit of VTTBR_EL2 decided? Start from `kvm_get_vttbr()`.

# The FF-A proxy

## hyp.ffa-calls: FF-A calls handled at EL2

- section: FF-A
- relevance: 4 - the host must not lend memory it does not own
- words: 100

Which FF-A calls from the host does the hypervisor handle itself, which does
it refuse, which does it pass through, and how is a call recognised as FF-A?
What is refused until a version has been agreed? Start from
`kvm_host_ffa_handler()` and `ffa_call_supported()`.

## hyp.ffa-descriptor: Memory transfer descriptor checks

- section: FF-A
- relevance: 5 - offsets and lengths come from the host
- words: 110

In a memory share or lend, what does the proxy copy and then check before
acting: the fragment and total lengths, the endpoint count and sender, the
composite offset and its overflow, the constituent array? What is done to the
host's pages, and what if the secure world then fails the call? Start from
`__do_ffa_mem_xfer()`.

## hyp.ffa-version: FF-A version negotiation

- section: FF-A
- relevance: 3 - state shared across CPUs
- words: 90

How does the proxy negotiate the FF-A version with the secure world and with
the host: what is asked at init, what happens when the host asks for a lower
or higher minor version, when can it no longer change, and which lock and
memory ordering protect the state?

## hyp.ffa-features: FF-A feature queries

- section: FF-A
- relevance: 3 - optional interfaces must not be advertised
- words: 70

How does the proxy answer a feature query from the host, and what has to
change when the FF-A specification adds an optional interface that the
hypervisor does not implement?

# Tracing

## hyp.tracing: Hypervisor tracing

- section: Tracing
- relevance: 3 - the only way to see inside EL2 at run time
- words: 100

How can the nVHE hypervisor emit trace events: where are events defined, what
buffer do they go to and whose memory is it, which hypercalls load and control
it, and what does the host-side reader look like? Start from `HYP_EVENT()` and
`arch/arm64/kvm/hyp_trace.c`.

# Changing the implementation

## hyp.change-hyp-structs: Hyp structure sizes

- section: What a change must preserve
- relevance: 3 - the host allocates them by a generated size
- words: 70

How does the host know how much memory to donate for a hyp VM and a hyp vCPU,
and what follows for a change that adds a field to either structure? Start
from `arch/arm64/kvm/hyp/hyp-constants.c`.

## hyp.change-ownership: Adding an ownership transition

- section: What a change must preserve
- relevance: 4 - the invariants are spread over several files
- words: 100

What must a new ownership transition keep true: agreement between page state
and page tables on every side, lock order, validation of untrusted ranges, no
fallible step after the first update, cache and TLB maintenance, and coverage
in the selftest? Start from `pkvm_ownership_selftest()`.

## hyp.testing: Testing hypervisor changes

- section: What a change must preserve
- relevance: 3 - little of it runs in a normal test
- words: 80

What is there to test a change to the nVHE hypervisor with: the ownership
selftest and when it runs, the debug options, the hypervisor trace selftest
and the KVM selftests, and how is protected mode enabled on a test machine?

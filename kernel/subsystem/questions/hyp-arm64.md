# Questions: ARM64 Hyp (EL2)

- guide: hyp-arm64.md
- title: ARM64 Hyp (EL2) Subsystem Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/hyp-arm64-measurement.md` is the
wider set the readers were measured on and `catalogue/hyp-arm64-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## hyp.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## hyp.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: the host hypercall dispatch; the host stage-2 and page
ownership code; the table of hyp VMs and vCPUs; the EL2 stage-1 mappings; the EL2 page
allocator; the pKVM setup code; the FF-A proxy; the PSCI relay; the protected-VM system register
emulation; the world switch; the EL2 vectors; the code shared with the VHE build; the host-side
pKVM glue. Where two files in different directories share a name, say which is which in the
row. Start from `arch/arm64/kvm/hyp/`.

## hyp.entry-points: Entry points

- section: Finding your way
- relevance: 4 - where to start reading for each job

A table and nothing else, job to the function to start reading from: a host hypercall arrives;
the host takes a stage-2 fault; the host issues an SMC; a vCPU is run; a guest exit is fixed up
at EL2; a hyp VM is created; a page changes owner; EL2 panics. Where the host side and the EL2
side each have a function for the job, name both. Do not describe what the functions do inside.

## hyp.build-namespace: The nVHE object

- section: Finding your way
- relevance: 4 - explains link errors and why a kernel symbol is not visible

What does the build do to the section and symbol names of nVHE hypervisor code when it links that
code into the kernel image, and what must a patch therefore do before EL2 code can use a kernel
symbol or the host can call an EL2 symbol? How are pointers in the nVHE object fixed up for the
EL2 address space? Start from `arch/arm64/kvm/hyp/nvhe/Makefile`.

## hyp.debug-and-test: Debug options and tests

- section: Finding your way
- relevance: 3 - several checks exist only with a debug option, and little runs in a normal test

What does this tree call the options that turn on EL2 assertions, relax the host stage-2 on a
panic, and give stack traces and tracing, where a reader's memory offers other names? Which
checks exist only under one of them, so that code relying on them is unchecked in a normal
build? What runs the ownership selftest, and when? Start from `CONFIG_NVHE_EL2_DEBUG` in
`arch/arm64/kvm/Kconfig` and `pkvm_ownership_selftest()`.

# KVM modes and pKVM init

## hyp.modes: KVM modes on arm64

- section: KVM modes and pKVM init
- relevance: 4 - the same source runs under different trust rules

Which modes can KVM on arm64 run in? Which of `is_protected_kvm_enabled()`, `has_vhe()` and
`has_hvhe()` must code test to know whether the host is trusted, and which to know whether the
code is running at EL2?

## hyp.mode-selection: Mode selection at boot

- section: KVM modes and pKVM init
- relevance: 4 - the mode that runs is not always the mode that was asked for

How is the mode of KVM on arm64 chosen at boot, and which requests for a mode does
`early_kvm_mode_cfg()` refuse?

## hyp.init-predicates: Init state predicates

- section: KVM modes and pKVM init
- relevance: 4 - they are true at different times

When does each of `is_protected_kvm_enabled()`, `is_kvm_arm_initialised()`,
`is_pkvm_initialized()` and the `kvm_protected_mode_initialized` static key become true? Which of
them does code at EL2 test to tell whether pKVM initialisation has finished? What are the
requirements for choosing which of the four to test in order to assure safe usage?

## hyp.init-phases: Init sequence

- section: KVM modes and pKVM init
- relevance: 4 - decides which code runs with the host still trusted at EL2

From the memory reservation at early boot to finalisation, which steps of pKVM initialisation run
while the host still owns EL2, and at which initcall level does each run? Where in that sequence
do `__pkvm_init()` and `__pkvm_init_finalise()` run? Start from `kvm_hyp_reserve()`,
`kvm_arm_init()` and `finalize_pkvm()`.

## hyp.deprivilege: De-privilege point

- section: KVM modes and pKVM init
- relevance: 5 - trust assumptions flip here

Which function takes EL2 away from the host for good and at which initcall level, what does the
call it runs on each CPU change, and what stops that call being repeated on a CPU? Start from
`pkvm_drop_host_privileges()` and `__pkvm_prot_finalize()`.

# The EL2 environment

## hyp.el2-context: Execution context and concurrency

- section: The EL2 environment
- relevance: 5 - rules from kernel context do not carry over, and false races are reported

When nVHE code handles a trap from the host, what of kernel context is absent, and are interrupts
and SErrors masked? Which kinds of concurrency must that code allow for, and which cannot happen
at EL2? Start from `handle_trap()`.

## hyp.el2-exceptions: Vectors and the panic route

- section: The EL2 environment
- relevance: 4 - which vector table is installed decides how a fault at EL2 is handled

Which exception vector tables does the nVHE hypervisor have, and when is each installed? Under
each table, how does an exception taken at EL2 itself reach `hyp_panic()`? What does `hyp_panic()`
restore before control gets to `nvhe_hyp_panic_handler()` in the host? Start from
`__kvm_hyp_host_vector` and `__kvm_hyp_vector`.

## hyp.el2-extable: EL2 exception fixup table

- section: The EL2 environment
- relevance: 4 - decides whether an instruction that faults at EL2 panics the machine

Under which vector table does an exception taken at EL2 go through
`__kvm_unexpected_el2_exception()`, and which exceptions does that function recover from? How does
code mark an instruction so that a fault on it is recovered?

## hyp.bug-warn: BUG and WARN at EL2

- section: The EL2 environment
- relevance: 5 - error handling after a WARN_ON is dead code

What do `BUG()`, `BUG_ON()` and `WARN_ON()` expand to in nVHE code, does execution continue
after a `WARN_ON()` whose condition is true, and what does that mean for a statement of the form
`if (WARN_ON(x)) return ...;`?

## hyp.warn-usage: Asserting versus returning an error

- section: The EL2 environment
- relevance: 5 - a wrong assertion lets the host or a guest take the machine down

What are the requirements for a condition that nVHE code tests with `WARN_ON()` or `BUG_ON()` in
order to assure safe usage, and which conditions must the code return as an error? Name code in
`arch/arm64/kvm/hyp/nvhe/mem_protect.c` that shows each.

# Locks

## hyp.spinlock: Hypervisor spinlock

- section: Locks
- relevance: 4 - the only lock there is

What lock type does nVHE code use, and which variants of it does the tree provide? Under which
configuration does `hyp_assert_lock_held()` check anything? Start from
`arch/arm64/kvm/hyp/include/nvhe/spinlock.h`.

## hyp.lock-inventory: Locks and what they protect

- section: Locks
- relevance: 5 - every ownership change rests on these

A table of state against the lock code must hold to touch it: the VM table; the host stage-2
and host page state; the EL2 stage-1 and hyp page state; a guest's stage-2; a page pool; the
FF-A buffers and version; the block fixmap; the trace buffer. Say which of those share one lock.

## hyp.lock-order: Lock ordering

- section: Locks
- relevance: 5 - there is no lockdep at EL2

In what order are the host, hypervisor and guest page-table locks taken when a function needs
more than one, where is that order written down, and where does the VM table lock sit relative
to them? Start from `enum pkvm_component_id` and `__pkvm_host_force_reclaim_page_guest()`.

# Threat model and host inputs

## hyp.threat-model: Protection goals

- section: Threat model and host inputs
- relevance: 5 - decides whether a finding is a bug at all

What does pKVM protect, and from whom? What does it leave unprotected? Start from
`Documentation/virt/kvm/arm/pkvm.rst`.

## hyp.isolation-status: Isolation implemented so far

- section: Threat model and host inputs
- relevance: 5 - part of the design is not in this tree

Which of pKVM's isolation mechanisms does this tree implement, and which does it say are
unimplemented? What does creating a protected VM do to the kernel's taint state? Start from
`Documentation/virt/kvm/arm/pkvm.rst` and `pkvm_init_host_vm()`.

## hyp.host-inputs: Host-controlled inputs

- section: Threat model and host inputs
- relevance: 5 - the attack surface

After de-privilege, which inputs to EL2 code can the host change at will? Which of them can the
host change while another CPU is in the middle of a hypercall?

## hyp.toctou-usage: Reading host memory

- section: Threat model and host inputs
- relevance: 5 - the classic hypervisor bug

What are the requirements for reading a field of host-owned memory at EL2 in order to assure safe
usage? How does EL2 code meet them for a field of the host's `struct kvm_vcpu`? Name in-tree code
that shows it.

## hyp.sysreg-trust: Host-writable system registers

- section: Threat model and host inputs
- relevance: 4 - reading back a value is only safe for some registers

Which system registers that EL2 code reads can the host have written, and which can it not? From
where does the hypervisor take the HCR_EL2, VTTBR_EL2 and VTCR_EL2 values it uses for the host?

## hyp.pinning: Pinning shared host memory

- section: Threat model and host inputs
- relevance: 4 - what keeps a back pointer dereferenceable

What does `hyp_pin_shared_mem()` check before it pins a range, and what does it guarantee, and not
guarantee, about the range while the pin is held? Which host objects stay pinned for the life of a
hyp VM or a hyp vCPU?

# Host hypercalls and SMCs

## hyp.hcall-table: Hypercall dispatch

- section: Host hypercalls and SMCs
- relevance: 4 - the front door, and several places must agree

How does an HVC from the host reach its handler, and what does the host get back for a number that
is out of range or has no handler? When a hypercall is added, what catches a handler table that is
out of step with `enum __kvm_host_smccc_func`? Start from `handle_host_hcall()`.

## hyp.hcall-return: Hypercall return registers

- section: Host hypercalls and SMCs
- relevance: 4 - a handler that writes the wrong register returns a wrong status to the host

In which registers of the host context does the host receive the status of a hypercall and the
value that the handler returns, and which of the two does the handler write itself? Start from
`handle_host_hcall()`.

## hyp.hcall-bands: Hypercall availability by phase

- section: Host hypercalls and SMCs
- relevance: 5 - a number in the wrong place is callable at the wrong time

How does the position of an entry in `enum __kvm_host_smccc_func` decide whether the hypercall can
be used before pKVM is finalised, afterwards, or both? Name the marker entries. Which hypercalls,
if any, are placed against that rule, and what reason does the tree give?

## hyp.hcall-args: Hypercall arguments

- section: Host hypercalls and SMCs
- relevance: 4 - pointers and scalars are not alike

How does a handler read its arguments, what must it do to a host kernel pointer before using
it, and what is the difference in trust between a scalar passed in a register and memory reached
through such a pointer?

## hyp.host-smc: Host SMC handling

- section: Host hypercalls and SMCs
- relevance: 4 - part of the boundary with the secure world

What does the hypervisor refuse outright in an SMC from the host, in which order are the
handlers tried, and what happens to a call none of them claims, and why? Start from
`handle_host_smc()`.

# Memory from the host

## hyp.memcache: Hyp memcaches

- section: Memory from the host
- relevance: 4 - how the host feeds pages to EL2

How are the pages of a `struct kvm_hyp_memcache` linked, and who can write the links? Which
memcaches exist per vCPU and per VM, and in which direction do pages flow through each?

## hyp.memcache-usage: Taking pages from memcaches

- section: Memory from the host
- relevance: 5 - the list head is in host memory

What are the requirements for taking a page from a `struct kvm_hyp_memcache` that lives in host
memory in order to assure safe usage? Start from `refill_memcache()` and `admit_host_page()`.

## hyp.donated-memory: Memory donated for hyp objects

- section: Memory from the host
- relevance: 4 - sizes and alignment come from the host

How does EL2 take over host memory offered for a VM, a vCPU or a page-table root: what does it
check, when is the memory cleared, and how is it handed back? Start from `map_donated_memory()`
and `unmap_donated_memory()`.

## hyp.change-hyp-structs: Hyp structure sizes

- section: Memory from the host
- relevance: 3 - the host allocates them by a generated size

How does the host know how much memory to donate for a hyp VM and a hyp vCPU, and what follows
for a change that adds a field to either structure? Start from
`arch/arm64/kvm/hyp/hyp-constants.c`.

# Hyp VMs and vCPUs

## hyp.hyp-structs: Hyp copies and back pointers

- section: Hyp VMs and vCPUs
- relevance: 5 - the two are one dereference apart

In `struct pkvm_hyp_vm` and `struct pkvm_hyp_vcpu`, what is an EL2-private copy that the host
cannot change and what points back at host memory that it can, and how does code tell which it
has in hand? How do you get from a hyp vCPU to its hyp VM?

## hyp.vm-table: VM handles and table

- section: Hyp VMs and vCPUs
- relevance: 4 - the handle is the host's only name for a VM

How does `get_vm_by_handle()` turn a VM handle into a `struct pkvm_hyp_vm`, and which handles must
a lookup refuse? How is the VMID derived?

## hyp.vm-refcount: References to a hyp VM

- section: Hyp VMs and vCPUs
- relevance: 4 - teardown waits on it

What counts references to a hyp VM, which operations take one and must drop it on every path,
and which operations refuse to proceed while the count is not zero, with what error?

## hyp.vm-create: Creating a hyp VM

- section: Hyp VMs and vCPUs
- relevance: 4 - host fields are sampled here

In creating a VM at EL2, from reserving a handle to publishing the VM, which host fields are read
and when, and what is undone on each failure? Start from `__pkvm_init_vm()`.

## hyp.vm-create-host: Host side of VM creation

- section: Hyp VMs and vCPUs
- relevance: 4 - the host's locks decide what can run at the same time as creation

When does the host call `pkvm_create_hyp_vm()`, and which of its locks does it hold across the
call, taken in which order?

## hyp.vcpu-create: Creating a hyp vCPU

- section: Hyp VMs and vCPUs
- relevance: 4 - published to other CPUs

What does `__pkvm_init_vcpu()` pin, how is the new vCPU made visible to the load path and with
what memory ordering, and what is undone on failure?

## hyp.vcpu-load: Loading and putting a vCPU

- section: Hyp VMs and vCPUs
- relevance: 4 - most hypercalls act on the loaded vCPU

What makes `pkvm_load_hyp_vcpu()` fail? How do later hypercalls find the vCPU that it loaded, and
what do they do when none is loaded?

## hyp.vcpu-put: Putting a vCPU

- section: Hyp VMs and vCPUs
- relevance: 4 - a load without its put blocks every later load on that CPU

What does a put of a loaded hyp vCPU do, in `handle___pkvm_vcpu_put()` and in
`pkvm_put_hyp_vcpu()`? What are the requirements for pairing a load with a put in order to assure
safe usage?

## hyp.teardown: Tearing a VM down

- section: Hyp VMs and vCPUs
- relevance: 5 - pages must not leak or come back early

What are the stages of tearing a VM down under pKVM, in the order the host runs them, and what
does each hypercall return when the VM is still in use? What does `is_dying` stop and what does it
allow? Start from `__pkvm_start_teardown_vm()`.

## hyp.teardown-pages: Pages returned at teardown

- section: Hyp VMs and vCPUs
- relevance: 5 - pages must not leak or come back early

How does each kind of page that a VM holds get back to the host at teardown, and who chooses which
guest pages to reclaim? Start from `__pkvm_reclaim_dying_guest_page()` and
`__pkvm_finalize_teardown_vm()`.

## hyp.vm-features: Features allowed for protected VMs

- section: Hyp VMs and vCPUs
- relevance: 3 - the host's feature set is filtered

How does EL2 decide a VM's vCPU features and flags for a protected VM and for a non-protected one?
Which features that the host asks for does EL2 refuse for a protected VM, and where is the list of
capabilities a protected VM may use? Start from `pkvm_init_features_from_host()` and
`kvm_pkvm_ext_allowed()`.

# EL2 addresses

## hyp.address-space: EL2 address space layout

- section: EL2 addresses
- relevance: 4 - which conversion applies depends on the region

A table of the regions of the nVHE EL2 virtual address space: where each region's base is decided,
and which helper converts an address in it to a physical address or a `struct hyp_page` and back.
For which regions is no such conversion valid? Start from `hyp_create_idmap()` and
`arch/arm64/kvm/hyp/include/nvhe/memory.h`.

## hyp.kern-hyp-va: Host pointer conversion

- section: EL2 addresses
- relevance: 4 - every host pointer goes through it

What does `kern_hyp_va()` do to a pointer, when are its mask and tag computed and how do they
get into the code, and what does it become under VHE? Start from `__kern_hyp_va()` and
`arch/arm64/kvm/va_layout.c`.

## hyp.kern-hyp-va-repeat: Converting a pointer twice

- section: EL2 addresses
- relevance: 4 - misjudged in both directions

For which EL2 addresses does a second `kern_hyp_va()` return the address unchanged, and for which
does it return a different address? Name in-tree code that relies on the first case.

## hyp.fixmap: Fixmap slots

- section: EL2 addresses
- relevance: 4 - the only way to touch a page EL2 has no mapping for

Whose slot does `hyp_fixmap_map()` use and what does that require of the caller, and which of
it and `hyp_fixmap_unmap()` does the TLB invalidation, and with what scope?

## hyp.fixmap-usage: Using the fixmap

- section: EL2 addresses
- relevance: 4 - a missed unmap exposes the wrong page to the next user

What are the requirements for a caller of `hyp_fixmap_map()` and `hyp_fixmap_unmap()` in order to
assure safe usage? Name in-tree callers that show the pairing.

# The page allocator

## hyp.hyp-page: Per-page metadata

- section: The page allocator
- relevance: 5 - ownership and the allocator share this structure

In `struct hyp_page`, which lock guards the allocator's part and which the ownership part, what
size must the structure stay and what enforces it, and how is the array of them found and
backed? Start from `hyp_vmemmap` and `hyp_back_vmemmap()`.

## hyp.pools: Page pools

- section: The page allocator
- relevance: 4 - there are more than two

Which `struct hyp_pool` instances does the hypervisor have, and what may be allocated from
each? A table of pool against what it backs and where its pages come from.

## hyp.pool-api: Page allocator interface

- section: The page allocator
- relevance: 4 - semantics differ from the kernel allocator

What reference count does a page returned by `hyp_alloc_pages()` have, when are its contents
zeroed, and what does the function return when the pool is empty?

## hyp.pool-locking: Pool locking

- section: The page allocator
- relevance: 4 - the refcount helpers take no lock themselves

What does a pool's lock protect, which reference count helpers rely on the caller for
exclusion, and where is a page's reference count changed without the pool lock and what
protects it there?

## hyp.pool-usage: Using the page allocator

- section: The page allocator
- relevance: 4 - misuse corrupts a free list silently

What are the requirements for a caller of `hyp_alloc_pages()`, `hyp_get_page()` and
`hyp_put_page()` in order to assure safe usage? Name in-tree code that shows it.

# Page ownership state

## hyp.page-states: Page states

- section: Page ownership state
- relevance: 5 - the vocabulary of every transition

A table of the values of `enum pkvm_page_state`: what each means from the point of view of one
component, and whether it is stored as such or inferred.

## hyp.state-encoding: State storage and testing

- section: Page ownership state
- relevance: 5 - three components, three encodings, and zero does not mean the same in each

Where is a page's state kept for the host, for the hypervisor and for a guest, and what does
all-zero metadata mean for the host's view and for the hypervisor's? What are the requirements for
code that tests a page's state in order to assure safe usage? Start from `get_host_state()` and
`get_hyp_state()`.

## hyp.host-annotations: Host stage-2 invalid entries

- section: Page ownership state
- relevance: 4 - the only record of who owns a page the host lost

How does the host stage-2 record that a page belongs to the hypervisor or to a guest: which
types of invalid entry are there, where in the entry are the type, the owner and the extra
metadata, and what is stored for a guest-owned page? Start from
`host_stage2_set_owner_metadata_locked()`.

## hyp.host-stage2: Host stage-2 map

- section: Page ownership state
- relevance: 4 - an identity map filled in on demand

What does the host's stage-2 hold before the first fault, and what does `host_stage2_idmap()` add
on a fault, with which permissions for memory and for MMIO? When does `host_stage2_force_pte_cb()`
force page granularity?

## hyp.host-abort: Host stage-2 faults

- section: Page ownership state
- relevance: 4 - the host's memory map is built here

When the host takes a stage-2 fault, how does `handle_host_mem_abort()` find the faulting address?
Which results of trying to map the address does it treat as benign, which as fatal, and which does
it turn into an exception for the host? How does the host recognise that exception?

# Ownership transitions

## hyp.transitions: Share, donate and reclaim functions

- section: Ownership transitions
- relevance: 5 - the map of the ownership code

A table of the share, unshare, donate and reclaim transitions in
`arch/arm64/kvm/hyp/nvhe/mem_protect.c`: the function, who initiates it, the state each side must
be in before, and the state each side is left in.

## hyp.transition-order: Order of checks and updates

- section: Ownership transitions
- relevance: 5 - a failure part way leaves metadata and page tables disagreeing

What are the requirements for the order of checks and updates in the transition functions in
`arch/arm64/kvm/hyp/nvhe/mem_protect.c` in order to assure safe usage? Which updates do those
functions assert and not check, and what do they check beforehand for a guest stage-2 map? Name an
in-tree transition that shows the order.

## hyp.range-validation: Validating physical ranges

- section: Ownership transitions
- relevance: 5 - the range comes from the host

Which of the helpers that validate a pfn and page count, or a physical range, from an untrusted
caller is used when? What does each check, and what does each leave unchecked? Start from
`pfn_range_is_valid()` and `check_range_allowed_memory()`.

## hyp.guest-map-sizes: Mapping sizes for guests

- section: Ownership transitions
- relevance: 4 - block mappings are restricted

What sizes may the host ask for when sharing memory with or donating memory to a guest under
pKVM, what alignment is required, and where is that checked at EL2 and on the host side?

## hyp.poison: Forced reclaim and poisoned entries

- section: Ownership transitions
- relevance: 4 - new state that readers may not know

When the host faults on a page it donated to a protected guest, who decides to reclaim the page,
and what does `__pkvm_host_force_reclaim_page_guest()` do to the page and to the guest's stage-2
entry? How does the guest's next access to that page end?

## hyp.reclaim-clearing: Clearing reclaimed pages

- section: Ownership transitions
- relevance: 4 - a missed clean leaks guest data

Before a page leaves a protected guest or the hypervisor for the host, which function clears it,
and which cache maintenance does that function do?

# Entering a guest

## hyp.run-path: The run hypercall

- section: Entering a guest
- relevance: 4 - two different paths share one handler

What does `handle___kvm_vcpu_run()` do under pKVM and without it, how is the vCPU pointer from
the host checked, and what is refused before entry?

## hyp.entry-state-copy: Per-entry flush and sync

- section: Entering a guest
- relevance: 5 - which state crosses the boundary on every entry

Which vCPU state do `flush_hyp_vcpu()` and `sync_hyp_vcpu()` copy between the host's vCPU and the
hyp vCPU on each guest entry and exit, and how does that differ between a protected and a
non-protected vCPU?

## hyp.full-state-copy: Full register state copy

- section: Entering a guest
- relevance: 5 - decides which copy of the registers is current at each point

What does `PKVM_HOST_STATE_DIRTY` record, and to which vCPUs does it apply? When is the full
register state copied between the host's vCPU and the hyp vCPU? Start from
`handle___pkvm_vcpu_sync_state()`.

## hyp.load-vs-entry: Load-time versus entry-time state

- section: Entering a guest
- relevance: 4 - a missing copy is only missing at the right place

Which state is brought over from the host when a vCPU is loaded and not on each entry, for
protected and for non-protected vCPUs, so that a new piece of state is copied at the right
point? A table of what is copied where. Start from `handle___pkvm_vcpu_load()`.

## hyp.hcr-from-host: HCR_EL2 for a hyp vCPU

- section: Entering a guest
- relevance: 5 - the host must not define a protected guest's regime, and too few bits is a bug too

Where is a hyp vCPU's HCR_EL2 value computed, and which bits are taken from the host's value at
load and on each entry? What are the requirements for combining the host's HCR_EL2 value into a
protected vCPU's value in order to assure safe usage? Start from `pkvm_vcpu_reset_hcr()`,
`pvm_init_traps_hcr()` and `flush_hyp_vcpu()`.

## hyp.trap-init: Other trap registers

- section: Entering a guest
- relevance: 4 - protected and non-protected take different paths

For a hyp vCPU, where do MDCR_EL2, HCRX_EL2, CPTR_EL2 and the fine-grained trap registers get
their values, for a protected and for a non-protected VM, and which are overwritten from the
host's copy, and when?

## hyp.switch-order: Ordering in the world switch

- section: Entering a guest
- relevance: 4 - barriers and errata fix the order

Which ordering constraints does `__kvm_vcpu_run()` observe on nVHE on the way into a guest and on
the way out, and what is each for?

## hyp.exit-handlers: Exit handling at EL2

- section: Entering a guest
- relevance: 4 - protected guests get a different table

How does the nVHE hypervisor decide whether to handle a guest exit itself or return to the
host, how does the handler table for a protected vCPU differ, and what is done about a protected
guest found in AArch32? Start from `fixup_guest_exit()`.

# Floating point

## hyp.fp-host-state: Host FP state

- section: Floating point
- relevance: 5 - differs by KVM mode, not by guest type

Who saves and restores the host's FP and SVE state around a guest run when pKVM is enabled and
when it is not, and what condition selects between them? At which vector length is host state
saved, and do protected and non-protected guests differ? Start from
`kvm_hyp_save_fpsimd_host()` and `fpsimd_lazy_switch_to_host()`.

## hyp.fp-switch: Lazy FP and SVE switching

- section: Floating point
- relevance: 4 - lazy, and tracked per CPU

What records who owns the FP registers at EL2, which trap starts the lazy switch, and what must
the handler have done before the guest's registers are exposed? Start from
`kvm_hyp_handle_fpsimd()` and `fp_owner`.

## hyp.fp-usage: Changing FP switching code

- section: Floating point
- relevance: 4 - host register contents can leak into a guest

What are the requirements for EL2 code that saves the host's FP and SVE state and hands the
registers to a guest, in order to assure safe usage? Start from `kvm_hyp_save_fpsimd_host()` and
`kvm_hyp_handle_fpsimd()`.

# The FF-A proxy

## hyp.ffa-calls: FF-A calls handled at EL2

- section: The FF-A proxy
- relevance: 4 - the host must not lend memory it does not own

How is a call from the host recognised as FF-A, and which calls does the hypervisor handle
itself, which does it refuse and which does it pass through? What is refused until a version has
been agreed? Start from `kvm_host_ffa_handler()` and `ffa_call_supported()`.

## hyp.ffa-version: FF-A version negotiation

- section: The FF-A proxy
- relevance: 3 - state shared across CPUs

What happens when the host asks the proxy for a lower or a higher minor version than the one
agreed with the secure world at init, when can the version no longer change, and which lock and
memory ordering protect that state?

## hyp.ffa-descriptor: Memory transfer descriptor checks

- section: The FF-A proxy
- relevance: 5 - offsets and lengths come from the host

In a memory share or lend, what does the proxy copy from the host, and what does it check in the
copy before acting? Start from `__do_ffa_mem_xfer()`.

## hyp.ffa-host-pages: Host pages in a transfer

- section: The FF-A proxy
- relevance: 5 - a failed call must not leave the host's pages in the wrong state

In a memory share or lend, what does the proxy do to the host's pages before it forwards the call
to the secure world, and what does it do to them when the secure world then fails the call? Start
from `__do_ffa_mem_xfer()`.

## hyp.ffa-features: FF-A feature queries

- section: The FF-A proxy
- relevance: 3 - optional interfaces must not be advertised

How does the proxy answer a feature query from the host, and what has to change when the FF-A
specification adds an optional interface that the hypervisor does not implement?

# Model gaps

## hyp.model-gaps: Other mistakes models make

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

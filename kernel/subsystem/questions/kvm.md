# Questions: KVM

- guide: kvm.md
- title: KVM Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/kvm-measurement.md` is the wider
set the readers were measured on and `catalogue/kvm-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## kvm.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## kvm.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers have moved between files and the x86 directory has been split

A table and nothing else, job to file: the generic VM and vCPU ioctl code; memslots; the MMU
notifier glue; the pfn cache; the dirty ring; guest_memfd; irqfd and ioeventfd; the I/O bus;
async page faults; the binary statistics; and, under `arch/x86/kvm/`, the MMU, the vendor
directories, MSR handling and register access. Where a reader is likely to look for a file that
does not exist in this tree, or in a file that has been split, say so in the row. Start from
`virt/kvm/` and `include/linux/kvm_host.h`.

## kvm.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to the function to start reading from: create a VM; create a
vCPU; dispatch a VM ioctl and a vCPU ioctl; set a memory region; handle an MMU notifier
invalidation; read the dirty log; resolve a guest frame to a host page for a fault, on x86 and
on arm64; make a request of a vCPU. Give the current name where it has changed. Do not describe
what the functions do inside.

## kvm.symbol-exports: Symbol exports

- section: Finding your way
- relevance: 3 - the export macro decides who may call a function, and the build enforces it

Which macros may code under `virt/kvm/` and `arch/x86/kvm/` use to export a symbol, and which
modules can use a symbol exported with each? What does the build do with an export made by any
other macro? Start from `include/linux/kvm_types.h`.

## kvm.new-features: New guest-visible features

- section: Finding your way
- relevance: 4 - decides whether a feature can be migrated

What does the in-tree review checklist require of a patch that adds a guest-visible feature or a
userspace interface? Start from `Documentation/virt/kvm/review-checklist.rst`.

# Locks and SRCU

## kvm.lock-order: Mutex acquisition order

- section: Locks and SRCU
- relevance: 5 - violations are deadlocks that lockdep only sees if both paths run

In what order may `kvm_lock`, `kvm_usage_lock`, the CPU hotplug read lock, a VM's `lock`,
`slots_lock`, `slots_arch_lock` and `irq_lock`, and a vCPU's `mutex` be nested, and which
x86-only locks nest inside the vCPU mutex? Give the order as the documentation states it and say
where the code asserts it. Start from `Documentation/virt/kvm/locking.rst`.

## kvm.struct-kvm-fields: VM state and its locks

- section: Locks and SRCU
- relevance: 4 - which lock covers which state is the first thing a review needs

A table of the state kept in `struct kvm` against the lock or mechanism that protects it:
memslots, the vCPU array, MMU notifier state, pfn caches, I/O buses, irqfds, dirty logging state,
the reference count and the liveness flags. Which of them share a lock?

## kvm.srcu-vs-mutexes: Mutexes held across SRCU waits

- section: Locks and SRCU
- relevance: 5 - the deadlock needs a concurrent memslot update to show

Which KVM mutexes have `synchronize_srcu()` on the VM's `srcu` called inside their critical
sections? What are the requirements for taking one of those mutexes inside a read side section of
that `srcu`, in order to assure safe usage? Name in-tree code that shows it.

## kvm.slots-arch-lock: The arch memslot lock

- section: Locks and SRCU
- relevance: 4 - the one memslot lock that may be taken inside SRCU

What does a VM's `slots_arch_lock` protect, and may it be taken inside a read side section of the
VM's `srcu`? What must code that holds `slots_arch_lock` without `slots_lock` do before it reads
the current memslots pointer?

## kvm.notifier-memslot-sync: Notifiers and memslot swaps

- section: Locks and SRCU
- relevance: 4 - explains why notifier callbacks may not take the memslot locks

How does KVM make sure an MMU notifier start and its matching end see the same memslots: where
does a memslot update wait and on what, and which locks must the notifier callbacks therefore
never take? Start from `kvm_swap_active_memslots()`.

## kvm.srcu-protected-data: SRCU protected data

- section: Locks and SRCU
- relevance: 4 - what a reader may touch and what frees it

Which data does a VM's `srcu` protect and which does `irq_srcu` protect? How does an update of
each wait for readers before it frees the old copy? What does VM destruction do about an SRCU
callback that is still pending?

## kvm.mmu-lock-type: MMU lock type and mode

- section: Locks and SRCU
- relevance: 4 - the type differs by architecture and generic code must not assume

What decides the type of a VM's `mmu_lock`? How does generic code take it without knowing the
type, and in which mode do the generic MMU notifier and dirty log paths take it?

## kvm.mmu-lock-sleeping: Work under the MMU lock

- section: Locks and SRCU
- relevance: 4 - sleeping under a spinning lock is only caught with debugging on

What are the requirements for code that runs with `mmu_lock` held in order to assure safe usage?
How does a fault handler get the memory it needs for page tables while it holds `mmu_lock`, and
what happens when that memory runs out? Start from `kvm_mmu_topup_memory_cache()`.

# VMs and vCPUs

## kvm.vm-refcount: VM references

- section: VMs and vCPUs
- relevance: 4 - a missing or extra reference is a use-after-free or a leak

When must code call `kvm_get_kvm_safe()` and not `kvm_get_kvm()`, and when
`kvm_put_kvm_no_destroy()` and not `kvm_put_kvm()`? Which file descriptors hold a reference on the
VM? Start from `kvm_get_kvm()` and `kvm_put_kvm()`.

## kvm.vm-dead-bugged: Dead and bugged VMs

- section: VMs and vCPUs
- relevance: 4 - the sanctioned way to handle an impossible state

How do `KVM_BUG_ON()`, `KVM_BUG_ON_DATA_CORRUPTION()` and `kvm_vm_dead()` differ in what they do
to the VM and to the host? What happens to running vCPUs and to later ioctls once a VM is marked?
Start from `KVM_BUG_ON()` and `kvm_vm_dead()`.

## kvm.warn-usage: Assertions reachable by guests

- section: VMs and vCPUs
- relevance: 4 - a guest-triggerable warning is a host denial of service

What are the requirements for a `WARN_ON()` or a `BUG_ON()` in KVM code that a guest or
unprivileged userspace can reach, in order to assure safe usage? What does KVM provide for a state
that should be impossible? Name in-tree code that shows each.

## kvm.vcpu-create: vCPU creation

- section: VMs and vCPUs
- relevance: 4 - a vCPU visible before it is complete has been a NULL dereference

In what order does `kvm_vm_ioctl_create_vcpu()` insert the vCPU into the VM's array, install the
file descriptor and publish the new count, and under which locks? What stops userspace from using
the descriptor before the vCPU is fully visible? Start from `kvm_vm_ioctl_create_vcpu()`.

## kvm.vcpu-id: vCPU ids

- section: VMs and vCPUs
- relevance: 4 - code that looks a vCPU up by id relies on what creation checked

What does `kvm_vm_ioctl_create_vcpu()` check about the vCPU id that userspace passes, and what
makes the id unique within the VM? Start from `kvm_vm_ioctl_create_vcpu()`.

## kvm.vcpu-ioctl-dispatch: vCPU ioctl dispatch

- section: VMs and vCPUs
- relevance: 4 - which lock an ioctl handler runs under

What does `kvm_vcpu_ioctl()` check and wait for before it calls any handler, and which lock does a
handler run under? Through which hook, if any, can an architecture handle an ioctl without that
lock? Start from `kvm_vcpu_ioctl()`.

## kvm.run-thread-identity: Thread that runs a vCPU

- section: VMs and vCPUs
- relevance: 4 - other vCPUs read what the run ioctl records about its caller

What does the `KVM_RUN` case of `kvm_vcpu_ioctl()` record about the calling thread, and which
locks protect that record? Start from `kvm_vcpu_ioctl()`.

## kvm.vcpu-load: Loading a vCPU

- section: VMs and vCPUs
- relevance: 4 - the pair brackets every access to hardware-switched state

What do `vcpu_load()` and `vcpu_put()` make valid between them, and what do they register with the
scheduler? What are the requirements for an ioctl handler that reads or writes vCPU state, with
respect to `vcpu_load()`, in order to assure safe usage?

# Requests and kicks

## kvm.vcpu-mode: vCPU mode

- section: Requests and kicks
- relevance: 4 - senders decide whether to send an interrupt from it

Which code makes each transition of `vcpu->mode`, and which transitions may a thread other than
the vCPU's own make? What ordering between a write of `vcpu->mode` and a read of the vCPU's
requests do the entry path and a sender rely on? Start from `kvm_vcpu_exiting_guest_mode()`.

## kvm.requests-api: Request functions

- section: Requests and kicks
- relevance: 4 - the barriers are inside the helpers

Which memory barriers do `kvm_make_request()`, `kvm_test_request()` and `kvm_check_request()`
contain, and what does each barrier pair with? What does `kvm_make_all_cpus_request()` do besides
setting the bit?

## kvm.request-flags: Request flags

- section: Requests and kicks
- relevance: 4 - the flags of a request decide whether its sender may assume that the target left guest mode

What do `KVM_REQUEST_WAIT`, `KVM_REQUEST_NO_WAKEUP` and `KVM_REQUEST_NO_ACTION` each change in how
a request reaches the target vCPU, and what does each guarantee about the target having left guest
mode?

## kvm.request-usage: Making requests safely

- section: Requests and kicks
- relevance: 4 - extra barriers and missing kicks both get proposed in review

What are the requirements for code that makes a vCPU request with `kvm_make_request()`, and for
code that reads or writes `requests` in `struct kvm_vcpu` directly, in order to assure safe usage?

## kvm.kick: Kicks and wakeups

- section: Requests and kicks
- relevance: 4 - a kick guarantees less than people assume

What does `__kvm_vcpu_kick()` do for a vCPU that is blocked, for one in guest mode and for one
that is neither, and what does its `wait` argument add? What does a kick guarantee about the
target having left guest mode? Start from `__kvm_vcpu_kick()`.

# Memslots

## kvm.memslot-layout: Active and inactive sets

- section: Memslots
- relevance: 4 - the old array layout is gone

How many sets of memslots does an address space have, and how does code choose which of a slot's
tree and hash nodes belongs to which set? What becomes of the old set after an update? Start from
`struct kvm_memslots` and `struct kvm_memory_slot`.

## kvm.memslot-update-entry: Memslot update entry points

- section: Memslots
- relevance: 5 - the function readers name is not callable outside one file

Which function may code outside `virt/kvm/kvm_main.c` call to change a memslot, what does that
function restrict, and which lock must its caller hold? Start from
`kvm_vm_ioctl_set_memory_region()`.

## kvm.internal-memslots: Slots reserved for the kernel

- section: Memslots
- relevance: 5 - a check written for userspace slots may not hold for a slot the kernel made

How does the memslot code tell a slot reserved for the kernel's own use from a slot that userspace
created, and which limits apply to only one of the two? Start from `kvm_set_internal_memslot()`.

## kvm.memslot-change-rules: Changing an existing slot

- section: Memslots
- relevance: 4 - flags that can flip create transitions nothing handles

For a memslot that already exists, which properties may a later call to `kvm_set_memory_region()`
change, and which changes does it reject? Into which values of `enum kvm_mr_change` does the
kernel classify a request?

## kvm.memslot-overlap-check: Overlap check on guest frames

- section: Memslots
- relevance: 4 - two slots that cover one guest frame give one frame two backings

What does `kvm_check_memslot_overlap()` compare, for which kinds of change does
`kvm_set_memory_region()` call it, and does it treat a memslot bound to a guest_memfd differently
from any other?

## kvm.memslot-update-flow: Memslot update flow

- section: Memslots
- relevance: 4 - every step exists so vCPUs can keep running during an update

For each kind of change, in what order does `kvm_set_memslot()` change the active and inactive
sets, wait for readers and call architecture code? How does it undo a failure part way?

## kvm.memslot-invalid-flag: Slots being deleted or moved

- section: Memslots
- relevance: 4 - readers must not map through a slot that is going away

What does `KVM_MEMSLOT_INVALID` on a memslot tell a reader, and what must a reader that finds such
a slot do? What does the x86 fault path do when it finds one?

## kvm.memslot-readers-usage: Reading memslots

- section: Memslots
- relevance: 5 - a reader without protection is a use-after-free

What are the requirements for reading the memslots pointer with `__kvm_memslots()`, and for using
a memslot found through it, in order to assure safe usage? Which protections does
`__kvm_memslots()` itself accept? Name in-tree code that reads memslots without an SRCU read lock
and meets the requirements. Start from `__kvm_memslots()`.

# Guest frame translation

## kvm.hva-helpers: Guest frame to host address

- section: Guest frame translation
- relevance: 5 - the write intent of each helper is invisible at the call site

A table of the functions that translate a guest frame to a host virtual address, to choose
between: whether each asks for write or read access, and what it returns for a read-only slot.
Say which are static to one file. Start from `__gfn_to_hva_many()` in `virt/kvm/kvm_main.c`.

## kvm.hva-write-intent-usage: Read paths and read-only slots

- section: Guest frame translation
- relevance: 4 - a read through a write-intent helper fails on valid ROM slots

What are the requirements for a path that only reads guest memory and may meet a read-only slot,
when it chooses between `gfn_to_hva()` and `gfn_to_hva_prot()` or their memslot and vCPU forms, in
order to assure correct usage? Name in-tree callers that read through a read-only slot.

## kvm.error-values: Error addresses and frames

- section: Guest frame translation
- relevance: 4 - testing for the wrong sentinel maps garbage

Which sentinel values do the host address and host frame translation helpers return on failure,
and what must the caller do next on each? Which predicate in `include/linux/kvm_host.h` tests for
which of them?

## kvm.faultin-pfn: Resolving and releasing a frame

- section: Guest frame translation
- relevance: 5 - the older family of helpers is gone, and the release has a locking requirement

What do `kvm_faultin_pfn()` and `__kvm_faultin_pfn()` return to the caller besides the host frame,
and what reference do they hold for it? What are the requirements for calling
`kvm_release_faultin_page()` afterwards, in order to assure safe usage? Start from
`kvm_faultin_pfn()`, `struct kvm_follow_pfn` and `kvm_release_faultin_page()`.

## kvm.pfn-cache-api: The pfn cache

- section: Guest frame translation
- relevance: 4 - users must follow a check and refresh protocol

What is a `struct gfn_to_pfn_cache` for, and which of its locks must a user hold while it accesses
the mapped page? What must a user do when `kvm_gpc_check()` fails? Name an in-tree user that shows
it.

## kvm.pfn-cache-refresh: Refreshing the pfn cache

- section: Guest frame translation
- relevance: 4 - the race with invalidation is closed in an unusual way

What closes the race between a pfn cache refresh in `hva_to_pfn_retry()` and an MMU notifier
invalidation? What reference or pin does the cache hold on the page once it is valid, and what
does that guarantee to a user of the cache? Start from `hva_to_pfn_retry()`.

# Invalidation and the retry protocol

## kvm.invalidate-state: Invalidation state

- section: Invalidation and the retry protocol
- relevance: 5 - the retry check is only as good as these writers, and every reader had the names wrong

What state in `struct kvm` do `kvm_mmu_invalidate_start()`, `kvm_mmu_invalidate_range_add()` and
`kvm_mmu_invalidate_end()` write, and under which lock? How do they record several invalidations
that overlap in time? Start from `kvm_mmu_invalidate_start()` and `kvm_mmu_invalidate_end()`.

## kvm.notifier-callbacks: Notifier callbacks

- section: Invalidation and the retry protocol
- relevance: 4 - the common walker hides the locking

What protection does `kvm_handle_hva_range()` take before it calls a handler, when does it take
`mmu_lock`, and when does it flush? Start from `kvm_handle_hva_range()`.

## kvm.other-invalidators: Invalidation outside notifiers

- section: Invalidation and the retry protocol
- relevance: 4 - the same start and end protocol has users that are not notifiers

What must a caller of `kvm_mmu_invalidate_start()` and `kvm_mmu_invalidate_end()` do between the
two calls, and what does `kvm_mmu_invalidate_end()` assert? Name in-tree callers outside the MMU
notifier that show it.

## kvm.fault-sequence: Fault handler sequence

- section: Invalidation and the retry protocol
- relevance: 5 - the order of the steps is the whole protocol

In what order must a fault handler snapshot the invalidation sequence, resolve the host frame,
take `mmu_lock`, check for a race and install the mapping, and what memory barrier follows the
snapshot? Show where the x86 and arm64 fault handlers do each step, naming the function that
holds it now. Start from `kvm_mmu_faultin_pfn()` and `user_mem_abort()`.

## kvm.retry-helpers: Retry helpers

- section: Invalidation and the retry protocol
- relevance: 5 - each has a different locking requirement

Of `mmu_invalidate_retry()`, `mmu_invalidate_retry_gfn()` and `mmu_invalidate_retry_gfn_unsafe()`,
which is used when? What does each check, and what does each require its caller to hold? Start
from `mmu_invalidate_retry()`.

## kvm.retry-usage: Using the retry check

- section: Invalidation and the retry protocol
- relevance: 5 - a stale mapping is guest memory corruption

What are the requirements for a fault handler's call to `mmu_invalidate_retry()` or
`mmu_invalidate_retry_gfn()`, and for the code between that call and the install of the mapping,
in order to assure safe usage? What are the requirements for a check made before `mmu_lock` is
taken? Name in-tree code that shows each.

## kvm.x86-fault-stale: Stale fault check on x86

- section: Invalidation and the retry protocol
- relevance: 4 - the check covers more than notifier races

What conditions does the x86 function that gates installing a mapping test, and for each, which
code changes the state it looks at? Start from `is_page_fault_stale()`.

## kvm.tlb-flush: Remote TLB flushes

- section: Invalidation and the retry protocol
- relevance: 4 - where the flush happens relative to the lock decides correctness

Of `kvm_flush_remote_tlbs()`, `kvm_flush_remote_tlbs_range()` and
`kvm_flush_remote_tlbs_memslot()`, which is used when, and what does each require its caller to
hold? How does an architecture replace the default flush that is based on a request?

## kvm.long-loops: Long walks under MMU lock

- section: Invalidation and the retry protocol
- relevance: 3 - soft lockups recur, and the fix differs by path

How does a walk over many guest frames under `mmu_lock` give up the lock or the CPU, in generic
code and in the x86 MMU? What must a walk recheck after it has yielded?

# x86 shadow pages and SPTEs

## kvm.x86-invalid-pages: Invalid shadow pages

- section: x86 shadow pages and SPTEs
- relevance: 4 - invalid is a state, not the end of the page's life

What does the invalid bit in the role of a `struct kvm_mmu_page` mean: can an invalid page still
be linked from a parent or be in use as a root? What does `kvm_mmu_child_role()` do with the bit
when it derives the role of a child? What does `__kvm_mmu_prepare_zap_page()` assert about it?
Start from `__kvm_mmu_prepare_zap_page()` and `kvm_mmu_child_role()`.

## kvm.x86-obsolete-pages: Obsolete shadow pages

- section: x86 shadow pages and SPTEs
- relevance: 4 - invalid and old-generation are different states with one test

What makes a shadow page obsolete for `is_obsolete_sp()`, and where is the generation changed?
What does `kvm_zap_obsolete_pages()` rely on about the order of the list of active shadow pages?
Start from `is_obsolete_sp()` and `kvm_zap_obsolete_pages()`.

## kvm.x86-spte-atomic: Atomic SPTE updates

- section: x86 shadow pages and SPTEs
- relevance: 4 - a plain write can lose a bit the hardware just set

When does `spte_needs_atomic_update()` say that an SPTE must be updated atomically, and which bits
does it ignore? Which forms of atomic update do the shadow MMU and the TDP MMU use?

# Dirty tracking

## kvm.dirty-mark: Marking a page dirty

- section: Dirty tracking
- relevance: 4 - the helper has a precondition about the running vCPU

What does `mark_page_dirty_in_slot()` require of its caller, and which architecture hook changes
that requirement? How does it choose between the dirty ring and the bitmap?

## kvm.dirty-bitmap: Dirty bitmap

- section: Dirty tracking
- relevance: 4 - the get and clear flows have a strict order

In reading the dirty log with and without manual protection enabled, in which order are the bitmap
snapshot, the write protection and the TLB flush done, and under which locks? How large does the
memslot code allocate the dirty bitmap of a slot, and what does it use the space for? Start from
`kvm_get_dirty_log_protect()`.

## kvm.dirty-ring: Dirty ring

- section: Dirty tracking
- relevance: 4 - the soft limit and the request keep the ring from overflowing

How are a vCPU's dirty ring entries published to userspace and collected back, and what ordering
does that rely on? What does KVM do when the ring reaches its soft limit? Start from
`kvm_dirty_ring_push()`.

## kvm.dirty-ring-with-bitmap: Ring together with bitmap

- section: Dirty tracking
- relevance: 3 - the relation between the two mechanisms is often misdescribed

When are the dirty ring and the dirty bitmap both in use for one VM, and which writes go to the
bitmap in that mode? What does `kvm_use_dirty_bitmap()` tell the rest of the code?

# guest_memfd and memory attributes

## kvm.gmem-files-bindings: guest_memfd files and bindings

- section: guest_memfd and memory attributes
- relevance: 4 - the file and the inode own different things, and the file pins the VM, not the reverse

What does a guest_memfd's `struct gmem_inode` own and what does each `struct gmem_file` own, and
which way do the references between the file, the VM and a bound memslot run? What happens to a
binding made by `kvm_gmem_bind()` when the file is closed before the memslot is deleted? Start
from `struct gmem_file`, `struct gmem_inode` and `kvm_gmem_bind()`.

## kvm.gmem-bind-checks: Checks made at binding

- section: guest_memfd and memory attributes
- relevance: 4 - a memslot bound to the wrong range or file maps memory that belongs elsewhere

What does `kvm_gmem_bind()` check about the file and about the range of it that a memslot asks
for, and what does it return when part of that range is already bound? Which lock orders the close
of the file against the deletion of a bound memslot? Start from `kvm_gmem_bind()`.

## kvm.gmem-get-pfn: Frames from guest_memfd

- section: guest_memfd and memory attributes
- relevance: 4 - the contract differs from the host address path and the hooks were renamed

What does `kvm_gmem_get_pfn()` return and hold for the caller, and how does it guard against the
file being closed concurrently? Which architecture hook does it run on a page, and on which calls?

## kvm.gmem-fault-choice: Faults that use guest_memfd

- section: guest_memfd and memory attributes
- relevance: 4 - a fault resolved through the wrong path maps the wrong backing page

How does the x86 fault path decide whether to resolve a fault through `kvm_gmem_get_pfn()` or
through the host address of the memslot? Start from `kvm_mmu_faultin_pfn()`.

## kvm.mem-attributes: Memory attributes

- section: guest_memfd and memory attributes
- relevance: 4 - the set flow is a second user of the invalidation protocol

What protects writers and what protects readers of per-frame memory attributes? In
`kvm_vm_set_mem_attributes()`, which steps can fail, and which architecture hooks run before and
after the change? Start from `kvm_vm_set_mem_attributes()`.

# Model gaps

## kvm.model-gaps: Other mistakes models make

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

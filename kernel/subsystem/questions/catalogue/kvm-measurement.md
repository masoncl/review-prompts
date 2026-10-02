# Questions: KVM (measurement set)

- guide: kvm.md
- title: KVM Subsystem

A wide set of questions about the architecture-independent KVM core under
`virt/kvm/` and the parts of the x86 MMU the hand-written guide covers, used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 2,152 words and
was never checked against current sources. The arm64 host and hypervisor code
have their own guides. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## kvm.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers have moved between files and the x86 directory has been split
- words: 120

Which files hold the generic VM and vCPU ioctl code, memslots, the MMU notifier
glue, the pfn cache, the dirty ring, guest_memfd, irqfd and ioeventfd, the I/O
bus, async page faults and the binary statistics, which headers declare the
structures for each, and how is `arch/x86/kvm/` laid out (MMU, vendor
directories, MSR and register code)? A table. Start from `virt/kvm/` and
`include/linux/kvm_host.h`.

## kvm.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

For each job (create a VM, create a vCPU, dispatch a VM ioctl and a vCPU ioctl,
set a memory region, handle an MMU notifier invalidation, read the dirty log,
resolve a guest frame to a host page for a fault, make a request of a vCPU),
which function do you start reading from? A table.

## kvm.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules live only there
- words: 70

Which files under `Documentation/virt/kvm/` are the authority on lock
ordering, on vCPU requests, on the userspace API, on what a patch must include,
and on the x86 MMU?

## kvm.arch-hooks: Architecture hooks

- section: Finding your way
- relevance: 3 - generic code changes have to keep every architecture building
- words: 100

Which groups of `kvm_arch_` functions does the generic code call (VM and vCPU
lifetime, memslot changes, MMU notifier handlers, dirty logging, hardware
enabling), which of them have weak or inline default implementations, and
where are they declared? Start from `include/linux/kvm_host.h`.

## kvm.kconfig-options: Configuration symbols

- section: Finding your way
- relevance: 2 - generic code is compiled per architecture by these
- words: 80

Which configuration symbols in `virt/kvm/Kconfig` turn on the optional generic
features (dirty ring, pfn cache, guest_memfd, memory attributes, generic
hardware enabling, lockless aging), and how does an architecture choose them?

## kvm.selftests: Selftests

- section: Finding your way
- relevance: 3 - a change is expected to come with a test
- words: 80

Where do the KVM selftests live, how are they laid out between common and
per-architecture tests and the support library, and which tests exercise
memslot changes, dirty logging, guest_memfd and the MMU under stress? Start
from `tools/testing/selftests/kvm/`.

## kvm.symbol-exports: Symbol exports

- section: Finding your way
- relevance: 3 - the export macro decides who may call a function
- words: 60

Which macros does KVM use to export symbols from `virt/kvm/` and from
`arch/x86/kvm/`, what does each restrict the symbol to, and where are they
defined? Start from `include/linux/kvm_types.h`.

# VM and vCPU objects

## kvm.struct-kvm-fields: VM structure

- section: Objects and lifetime
- relevance: 4 - which lock covers which field is the first thing a review needs
- words: 130

What are the main groups of fields in `struct kvm` (locks, memslots, vCPU
array, MMU notifier state, pfn caches, I/O buses, irqfds, dirty logging state,
reference count, liveness flags), and which lock or mechanism protects each
group? A table.

## kvm.vm-refcount: VM references

- section: Objects and lifetime
- relevance: 4 - a missing or extra reference is a use-after-free or a leak
- words: 100

How is a VM reference counted: which functions take and drop a reference, which
variant is for an object that may already be dying, which is for undoing a
reference after a file descriptor install fails, and which file descriptors
(vCPU, device, statistics, guest_memfd) each hold one? Start from
`kvm_get_kvm()` and `kvm_put_kvm()`.

## kvm.vm-destroy-order: VM destruction order

- section: Objects and lifetime
- relevance: 3 - reordering teardown has caused use-after-free
- words: 110

List in order what `kvm_destroy_vm()` does, and say where the MMU notifier is
unregistered relative to freeing the I/O buses, the architecture state, the
devices and the memslots, and what it does about an invalidation that was in
progress.

## kvm.vcpu-create: vCPU creation

- section: Objects and lifetime
- relevance: 4 - a vCPU visible before it is complete has been a NULL dereference
- words: 120

In what order does vCPU creation reserve an id, allocate, call the architecture,
insert into the VM's array, install the file descriptor and publish the new
count, which locks does it hold at each step, and what stops userspace from
using the descriptor before the vCPU is fully visible? Start from
`kvm_vm_ioctl_create_vcpu()`.

## kvm.vcpu-lookup: Finding a vCPU

- section: Objects and lifetime
- relevance: 3 - the index and the id are different things
- words: 80

How are a VM's vCPUs stored and looked up by index and by id, what bounds and
speculation checks does the lookup do, what memory ordering pairs it with
creation, and how is the set iterated? Start from `kvm_get_vcpu()` and
`kvm_for_each_vcpu()`.

## kvm.vcpu-ioctl-dispatch: vCPU ioctl dispatch

- section: Objects and lifetime
- relevance: 4 - which lock an ioctl handler runs under
- words: 100

What does the generic vCPU ioctl handler check before dispatching (calling
process, VM liveness, vCPU visibility), which lock does it take, how does an
architecture handle an ioctl without that lock, and what does the run ioctl do
about the calling thread's identity? Start from `kvm_vcpu_ioctl()`.

## kvm.vm-dead-bugged: Dead and bugged VMs

- section: Objects and lifetime
- relevance: 4 - the sanctioned way to handle an impossible state
- words: 100

How does KVM mark a VM as bugged or dead, which macros do that on a failed
invariant and how do they differ, what happens to running vCPUs and to later
ioctls, and which variant may bring down the host? Start from `KVM_BUG_ON()`
and `kvm_vm_dead()`.

## kvm.devices: In-kernel devices

- section: Objects and lifetime
- relevance: 2 - only matters when adding or changing a device type
- words: 80

How is an in-kernel device type registered and instantiated, which operations
does it supply, which of its two teardown callbacks runs when, and which lock
protects the VM's device list? Start from `struct kvm_device_ops`.

# Locking

## kvm.lock-order: Mutex acquisition order

- section: Lock ordering
- relevance: 5 - violations are deadlocks that lockdep only sees if both paths run
- words: 130

In what order may `kvm_lock`, `kvm_usage_lock`, the CPU hotplug read lock, a
VM's `lock`, `slots_lock`, `slots_arch_lock` and `irq_lock`, and a vCPU's
`mutex` be nested, and which x86-only locks nest inside the vCPU mutex? Give the
order as the documentation states it and say where the code asserts it. Start
from `Documentation/virt/kvm/locking.rst`.

## kvm.srcu-vs-mutexes: SRCU and the mutexes

- section: Lock ordering
- relevance: 5 - the deadlock needs a concurrent memslot update to show
- words: 100

Which KVM mutexes have `synchronize_srcu()` on the VM's SRCU called inside
their critical sections, and what does that mean for taking them inside a read
side section of that SRCU? What usage is unsafe, and what that looks similar is
correct? Name in-tree code that shows the correct form.

## kvm.slots-arch-lock: The arch memslot lock

- section: Lock ordering
- relevance: 4 - the one memslot lock that may be taken inside SRCU
- words: 90

What does a VM's `slots_arch_lock` protect, where in a memslot update is it
taken and released, may it be taken inside a read side section of the VM's SRCU
and what about where it is released decides that, and what must a writer outside
`slots_lock` do before reading the current memslots pointer?

## kvm.srcu-protected-data: SRCU protected data

- section: Lock ordering
- relevance: 4 - what a reader may touch and what frees it
- words: 90

Which data does a VM's `srcu` protect and which does `irq_srcu` protect, how is
each updated and the old copy freed, and which update paths use the expedited
grace period or a callback rather than a plain synchronous wait?

## kvm.vcpu-srcu-helpers: vCPU SRCU helpers

- section: Lock ordering
- relevance: 3 - the index field must not be touched directly
- words: 70

How does vCPU code enter and leave the VM's SRCU read side across function
boundaries, where is the index kept, what debugging check catches unbalanced
use, and where in the x86 run loop is the read side dropped and retaken? Start
from `kvm_vcpu_srcu_read_lock()`.

## kvm.mmu-lock-type: The MMU lock

- section: Lock ordering
- relevance: 4 - the type differs by architecture and generic code must not assume
- words: 90

What type is a VM's `mmu_lock` on each architecture, how does generic code take
it without knowing the type, in which mode do the generic MMU notifier and
dirty log paths take it, and which x86 paths take it for read?

## kvm.mmu-lock-sleeping: Work under the MMU lock

- section: Lock ordering
- relevance: 4 - sleeping under a spinning lock is only caught with debugging on
- words: 100

What usage under `mmu_lock` is unsafe (allocation, user access, other locks),
how do fault handlers get the memory they need for page tables without
allocating under it, and which locks are documented as nesting inside it? Start
from `kvm_mmu_topup_memory_cache()`.

## kvm.vm-list-walking: The VM list

- section: Lock ordering
- relevance: 3 - the documented ordering is easy to violate by accident
- words: 80

Which lock protects the global list of VMs, what does the documentation warn
about regarding CPU hotplug while walking it, and which x86 lock was added
because using the list lock for module loading deadlocked?

## kvm.hardware-enable: Hardware enabling

- section: Lock ordering
- relevance: 3 - the usage count and hotplug callbacks interact with suspend
- words: 100

How does generic code enable and disable hardware virtualization: what counts
users, which lock protects the count, how are CPUs coming online, suspend,
resume and shutdown handled, and what decides whether it is enabled at module
load or at first VM creation? Start from `kvm_enable_virtualization()`.

## kvm.lock-all-vcpus: Locking every vCPU

- section: Lock ordering
- relevance: 3 - open-coded loops get the lockdep annotation wrong
- words: 70

Which helpers lock and unlock every vCPU mutex of a VM, what must the caller
hold, how do the blocking and non-blocking forms differ in what they return on
failure, and how is lockdep told about taking many locks of one class?

## kvm.notifier-memslot-sync: Notifiers and memslot swaps

- section: Lock ordering
- relevance: 4 - explains why notifier callbacks may not take the memslot locks
- words: 110

How does KVM make sure an MMU notifier start and its matching end see the same
memslots: which counter and lock are involved, where does a memslot update wait
and on what, and which locks must the notifier callbacks therefore never take?
Start from `kvm_swap_active_memslots()`.

# Memslots

## kvm.memslot-struct: Memslot structure

- section: Memslot layout
- relevance: 4 - the fields and internal flags are what every path reads
- words: 100

What are the fields of `struct kvm_memory_slot`, why does it embed two of each
tree or hash node, which flag bits are internal to the kernel rather than
userspace visible, and what does the guest_memfd part hold and what protects
it?

## kvm.memslots-sets: Active and inactive sets

- section: Memslot layout
- relevance: 4 - the old array layout is gone
- words: 100

How are a VM's memslots organised: how many sets per address space, which
structures index a set by guest frame, by host address and by id, how does a
slot know which node belongs to which set, and how is the active set published
to readers? Start from `struct kvm_memslots`.

## kvm.memslot-generation: Memslot generation

- section: Memslot layout
- relevance: 3 - caches keyed on it go stale silently if it is misused
- words: 90

What is the memslot generation number, how does it change across an update and
across address spaces, what does the update in progress bit mean, and which
caches compare against it?

## kvm.memslot-lookup: Memslot lookup

- section: Memslot layout
- relevance: 3 - the VM and vCPU variants differ on x86
- words: 90

Which functions find the memslot for a guest frame, how do the per-VM and
per-vCPU variants differ (address space, last used slot cache), and which
iterators walk slots overlapping a guest frame range or a host address range?
Start from `gfn_to_memslot()` and `kvm_vcpu_gfn_to_memslot()`.

## kvm.memslot-update-entry: Memslot update entry points

- section: Changing memslots
- relevance: 5 - the function the old guide names is not callable outside one file
- words: 90

Through which functions can a memslot be created, deleted, moved or have its
flags changed, which of them is reachable from architecture code and with what
restrictions, which lock must the caller hold, and how are slots reserved for
the kernel's own use told apart from userspace slots? Start from
`kvm_vm_ioctl_set_memory_region()`.

## kvm.memslot-validation: Memory region validation

- section: Changing memslots
- relevance: 4 - each check exists because its absence was exploitable
- words: 110

Which checks does setting a memory region make on the slot id, address space,
alignment, size, userspace address, guest_memfd offset and overlap with other
slots, and which error does each return? Does overlap checking distinguish
guest_memfd slots from ordinary ones?

## kvm.memslot-flag-mutability: Changing an existing slot

- section: Changing memslots
- relevance: 4 - flags that can flip create transitions nothing handles
- words: 90

For a slot that already exists, which properties may a later call change and
which are rejected (size, userspace address, read-only, guest_memfd, dirty
logging, base address), what kinds of change does the kernel classify a request
into, and what can be done with a guest_memfd slot after creation?

## kvm.memslot-update-flow: Memslot update flow

- section: Changing memslots
- relevance: 4 - every step exists so vCPUs can keep running during an update
- words: 130

For each kind of change, what does `kvm_set_memslot()` do in order: when is a
temporary invalid copy installed, when are the active and inactive sets
swapped, where does it wait for readers, when does the architecture get to
prepare, commit and flush, and how is a failure part way undone?

## kvm.memslot-invalid-flag: Slots being deleted or moved

- section: Changing memslots
- relevance: 4 - readers must not map through a slot that is going away
- words: 80

How do readers see a slot that is in the middle of being deleted or moved, which
helpers treat such a slot as absent, and what does the x86 fault path do when it
finds one?

## kvm.memslot-readers-usage: Reading memslots

- section: Changing memslots
- relevance: 5 - a reader without protection is a use-after-free
- words: 110

What usage of the memslots pointer or of a memslot found through it is unsafe,
and what that looks similar is correct? Say which protections the accessor
itself accepts, including the case of a VM with no users left, and name in-tree
code that reads memslots without an SRCU read lock correctly. Start from
`__kvm_memslots()`.

# Guest memory access

## kvm.hva-helpers: Guest frame to host address

- section: Translating addresses
- relevance: 5 - the write intent of each helper is invisible at the call site
- words: 120

Which functions translate a guest frame to a host virtual address, and for each
does it ask for write access or read access and what does it return for a
read-only slot? Say which are static to one file. A table. Start from
`__gfn_to_hva_many()` in `virt/kvm/kvm_main.c`.

## kvm.hva-write-intent-usage: Read paths and read-only slots

- section: Translating addresses
- relevance: 4 - a read through a write-intent helper fails on valid ROM slots
- words: 90

What usage of the host address helpers on a path that only reads guest memory is
incorrect when the slot may be read-only, and which helper is the correct one?
Name in-tree callers that read through a read-only slot correctly.

## kvm.error-values: Error addresses and frames

- section: Translating addresses
- relevance: 4 - testing for the wrong sentinel maps garbage
- words: 100

Which sentinel values do the host address and host frame translation helpers
return on failure, what does each mean (no slot, read-only, fault, poison,
signal, needs I/O), and which predicates test for which sets of them?

## kvm.pfn-helpers: Guest frame to host frame

- section: Translating addresses
- relevance: 5 - the older family of helpers is gone
- words: 120

Which functions resolve a guest frame to a host frame for mapping into the
guest in this tree, what do they return alongside the frame, which structure
carries the request internally, and do the older helpers that returned a bare
frame number with a reference held still exist? Start from `kvm_faultin_pfn()`
and `struct kvm_follow_pfn`.

## kvm.faultin-release: Releasing a faulted-in page

- section: Translating addresses
- relevance: 4 - the release has a locking requirement
- words: 80

After a fault handler has resolved a page, how must it release it: which helper,
what do its arguments mean, which lock must be held and why, and what does it do
about dirtying the page? Start from `kvm_release_faultin_page()`.

## kvm.hva-to-pfn-paths: Host address to frame

- section: Translating addresses
- relevance: 3 - special mappings and pinning take a different path
- words: 110

What paths does `hva_to_pfn()` try in order, when is the fast path skipped, how
are mappings without page structures resolved, when does it pin rather than take
a reference, and how does a read fault end up mapped writable?

## kvm.guest-read-write: Reading and writing guest memory

- section: Translating addresses
- relevance: 3 - the helpers differ in context and in dirty tracking
- words: 100

Which helpers copy to and from guest memory by guest physical address, which of
them may be called from atomic context, which mark the page dirty, what do they
return on failure, and what protection must the caller hold? Start from
`kvm_read_guest()` and `kvm_write_guest()`.

## kvm.vcpu-map: Mapping a guest page

- section: Translating addresses
- relevance: 3 - the mapping is pinned and must be released in the right way
- words: 80

How does `kvm_vcpu_map()` give the kernel a mapping of a guest page, what does
it hold on the page while mapped, what does unmapping do about dirty state, and
what is the read-only form?

## kvm.pfn-cache-api: The pfn cache

- section: The pfn cache
- relevance: 4 - users must follow a check and refresh protocol
- words: 120

What is a `struct gfn_to_pfn_cache` for, which functions initialise, activate,
check, refresh and deactivate it, which of its locks must a user hold while
accessing the mapped page, and what must a user do when the check fails? Name an
in-tree user that follows the protocol.

## kvm.pfn-cache-refresh: Refreshing the pfn cache

- section: The pfn cache
- relevance: 4 - the race with invalidation is closed in an unusual way
- words: 110

How does a pfn cache refresh detect that an MMU notifier invalidation raced with
it: which counters does it read and in what order, is that the same in-progress
counter the page fault path uses and if not why not, and does the cache keep a
reference or a pin on the page once it is valid? Start from
`hva_to_pfn_retry()`.

## kvm.pfn-cache-invalidate: Invalidating pfn caches

- section: The pfn cache
- relevance: 3 - explains where in the notifier the caches are handled
- words: 80

Where in the MMU notifier sequence are pfn caches invalidated relative to taking
`mmu_lock`, what does invalidation compare against, and which locks does it
take? Start from `gfn_to_pfn_cache_invalidate_start()`.

# MMU notifiers and the retry protocol

## kvm.notifier-callbacks: Notifier callbacks

- section: Invalidation
- relevance: 4 - the common walker hides the locking
- words: 120

Which MMU notifier callbacks does KVM register, and how does the common walker
they share turn a host address range into per-slot guest frame ranges: which
protection does it take, when does it take `mmu_lock`, what are the handler and
on-lock hooks, and when does it flush? Start from `kvm_handle_hva_range()`.

## kvm.invalidate-state: Invalidation state

- section: Invalidation
- relevance: 5 - the retry check is only as good as these writers
- words: 110

Which fields of `struct kvm` record an invalidation in progress and completed
invalidations, which functions write each, under which lock, with what memory
ordering, and how are several overlapping ranges tracked? Start from
`kvm_mmu_invalidate_start()` and `kvm_mmu_invalidate_end()`.

## kvm.retry-helpers: Retry helpers

- section: Invalidation
- relevance: 5 - each has a different locking requirement
- words: 110

Which helpers tell a fault handler that an invalidation raced with it, what
does each check, which assert that `mmu_lock` is held, which may be called
without it and what can that one get wrong? Start from `mmu_invalidate_retry()`.

## kvm.fault-sequence: Fault handler sequence

- section: Invalidation
- relevance: 5 - the order of the steps is the whole protocol
- words: 110

In what order must a fault handler snapshot the invalidation sequence, resolve
the host frame, take `mmu_lock`, check for a race and install the mapping, and
what memory barrier follows the snapshot? Show where the x86 and arm64 fault
handlers do each step. Start from `kvm_mmu_faultin_pfn()` and
`user_mem_abort()`.

## kvm.retry-usage: Using the retry check

- section: Invalidation
- relevance: 5 - a stale mapping is guest memory corruption
- words: 100

What usage of the retry check is unsafe (where it is done, which lock is held,
what happens between the check and the install), and what that looks similar is
correct, including a check made before taking the lock? Name in-tree code for
each.

## kvm.x86-fault-stale: Stale fault check on x86

- section: Invalidation
- relevance: 4 - the check covers more than notifier races
- words: 100

What conditions does the x86 function that gates installing a mapping test, and
for each which code changes the state it looks at? Start from
`is_page_fault_stale()`.

## kvm.other-invalidators: Invalidation outside notifiers

- section: Invalidation
- relevance: 4 - the same begin and end protocol has users that are not notifiers
- words: 100

Which paths other than the MMU notifier bracket work with the invalidation begin
and end functions (memory attribute changes, guest_memfd hole punching and
release, anything in architecture code), and what must each add between begin
and end for the assertion in the end function to hold?

## kvm.aging: Page aging

- section: Invalidation
- relevance: 3 - the locking of the aging callbacks is configurable
- words: 90

How do the aging notifier callbacks reach architecture code, when do they run
without `mmu_lock`, when is a TLB flush skipped, and which configuration symbols
control each?

## kvm.tlb-flush: Remote TLB flushes

- section: Invalidation
- relevance: 4 - where the flush happens relative to the lock decides correctness
- words: 100

Which helpers flush guest TLBs on all vCPUs, by range and by memslot, how does
an architecture replace the default request-based flush, what ordering with
`vcpu->mode` do they rely on, and which helper asserts a lock and why?

## kvm.long-loops: Long walks under the MMU lock

- section: Invalidation
- relevance: 3 - soft lockups recur, and the fix differs by path
- words: 100

How do the generic and x86 paths that walk many guest frames under `mmu_lock`
(memory attributes, dirty log, zapping a range, zapping all roots) avoid holding
the lock or the CPU too long, and which helpers yield? Is there one mechanism
used everywhere?

# guest_memfd and memory attributes

## kvm.gmem-objects: guest_memfd objects

- section: Private memory
- relevance: 4 - the file and the inode own different things
- words: 100

What are the objects behind a guest_memfd: what does the inode hold and what
does each open file hold, how do they relate to a VM, how are memslot bindings
recorded, and which flags can be given at creation? Start from
`struct gmem_file` and `struct gmem_inode`.

## kvm.gmem-bind: Binding to a memslot

- section: Private memory
- relevance: 4 - the file pins the VM, not the reverse
- words: 100

What does binding a guest_memfd range to a memslot check and record, which
direction do the references between the file, the VM and the slot run, what
happens to bindings when the file is closed before the slot is deleted, and
which lock orders those two events?

## kvm.gmem-get-pfn: Frames from guest_memfd

- section: Private memory
- relevance: 4 - the contract differs from the host address path
- words: 100

What does `kvm_gmem_get_pfn()` return and hold for the caller, how does it guard
against the file being closed concurrently, what does it do to a page seen for
the first time, and how does the x86 fault path decide to use it rather than the
host address path?

## kvm.gmem-invalidate: guest_memfd invalidation

- section: Private memory
- relevance: 3 - hole punching has to zap every VM's mappings
- words: 90

When a range of a guest_memfd is truncated or its file is released, which
function zaps the guest mappings, which locks are taken in which order, and how
does it choose whether to zap private mappings, shared mappings or both?

## kvm.mem-attributes: Memory attributes

- section: Private memory
- relevance: 4 - the set flow is a second user of the invalidation protocol
- words: 110

Where are per-frame memory attributes stored, which lock covers writers and
what covers readers, what are the steps of setting attributes on a range
including what is reserved up front and what cannot fail afterwards, and which
architecture hooks run before and after? Start from
`kvm_vm_set_mem_attributes()`.

## kvm.private-fault: Private and shared mismatch

- section: Private memory
- relevance: 3 - the exit to userspace is part of the ABI
- words: 80

What does the x86 fault path do when the kind of access (private or shared)
does not match the frame's attribute, which exit reason and helper report it,
and how is a concurrent attribute change detected?

# Dirty logging

## kvm.dirty-mark: Marking a page dirty

- section: Dirty tracking
- relevance: 4 - the helper has a precondition about the running vCPU
- words: 100

What does `mark_page_dirty_in_slot()` require of its caller, what does it warn
about, how does it choose between the dirty ring and the bitmap, and which
architecture hook relaxes the running vCPU requirement?

## kvm.dirty-bitmap: Dirty bitmap

- section: Dirty tracking
- relevance: 4 - the get and clear flows have a strict order
- words: 120

How is a slot's dirty bitmap allocated and why is it twice the needed size, what
are the steps and their order in reading the log with and without manual
protection enabled, which locks are held, and where is the TLB flushed? Start
from `kvm_get_dirty_log_protect()`.

## kvm.dirty-clear-checks: Clearing the dirty log

- section: Dirty tracking
- relevance: 3 - the alignment checks are easy to get slightly wrong
- words: 80

Which alignment and range checks does clearing the dirty log make on the first
page and the page count, which case is allowed to be unaligned, and how does it
avoid clearing bits past the end of the slot? Start from
`kvm_clear_dirty_log_protect()`.

## kvm.dirty-ring: Dirty ring

- section: Dirty tracking
- relevance: 4 - the soft limit and the request keep the ring from overflowing
- words: 110

How is a vCPU's dirty ring laid out, how are entries published to userspace and
harvested back, what happens when the ring reaches its soft limit and how does
that stop the vCPU from running, and what is reserved beyond the soft limit?
Start from `kvm_dirty_ring_push()`.

## kvm.dirty-ring-reset: Resetting the dirty ring

- section: Dirty tracking
- relevance: 3 - the batching and its termination condition have had bugs
- words: 90

How does resetting the dirty rings walk harvested entries, how does it batch
write-protection, which lock serialises it, what ends the loop early, and which
locks are taken per batch? Start from `kvm_dirty_ring_reset()`.

## kvm.dirty-ring-with-bitmap: Ring together with bitmap

- section: Dirty tracking
- relevance: 3 - the relation between the two mechanisms is often misdescribed
- words: 90

When are the dirty ring and the dirty bitmap both in use for one VM, which
writes go to the bitmap in that mode, which capability and configuration symbol
enable it, and which helper tells the rest of the code whether bitmaps are in
use? Are ring entries ever copied into the bitmap?

# vCPU execution

## kvm.vcpu-load-put: Loading a vCPU

- section: Running vCPUs
- relevance: 4 - the pair brackets every access to hardware-switched state
- words: 90

What do `vcpu_load()` and `vcpu_put()` do in order, what per-CPU state do they
set, and what is registered that makes the scheduler call back into KVM?

## kvm.vcpu-load-usage: Handlers needing a loaded vCPU

- section: Running vCPUs
- relevance: 4 - touching hardware-switched state on an unloaded vCPU corrupts it
- words: 90

What usage of vCPU state in an ioctl handler is unsafe without loading the vCPU,
and which handlers correctly run without it? Say where the generic handlers
leave loading to architecture code, and name in-tree code for each side.

## kvm.preempt-notifiers: Scheduling in and out

- section: Running vCPUs
- relevance: 3 - the flags set here drive directed yield
- words: 90

What do the scheduler callbacks for a loaded vCPU do on the way out and on the
way in, which vCPU flags do they set and from what conditions, and who reads
those flags? Start from `kvm_sched_out()`.

## kvm.vcpu-mode: vCPU mode

- section: Running vCPUs
- relevance: 4 - senders decide whether to send an interrupt from it
- words: 100

What values can `vcpu->mode` take, who makes each transition and with what
ordering against reading requests, which is the only transition made by another
thread, and how does the x86 entry path use it? Start from
`kvm_vcpu_exiting_guest_mode()`.

## kvm.requests-api: Request functions

- section: Running vCPUs
- relevance: 4 - the barriers are inside the helpers
- words: 100

Which functions make, test, clear and consume a vCPU request, which memory
barriers do they contain and what do those pair with, and what does the form
that makes a request of every vCPU do beyond setting the bit?

## kvm.request-flags: Request flag bits

- section: Running vCPUs
- relevance: 3 - the flags change who is waited for and who is woken
- words: 100

What do the flag bits that can be combined into a request number mean, which
generic requests exist and which flags does each carry, what is the request that
is never recorded in the vCPU, and where does the architecture range start?

## kvm.kick: Kicks and wakeups

- section: Running vCPUs
- relevance: 4 - a kick guarantees less than people assume
- words: 100

What does kicking a vCPU do depending on whether it is blocked, in guest mode or
neither, what kind of interrupt is used and why, what does the waiting form add,
and what does a kick not guarantee about the target having left guest mode?
Start from `__kvm_vcpu_kick()`.

## kvm.request-usage: Making requests safely

- section: Running vCPUs
- relevance: 4 - extra barriers and missing kicks both get proposed in review
- words: 90

What usage of the request functions is incorrect (barriers around them, a
request with no kick, direct bit operations on the request word, recording a
request that needs no action), and what that looks similar is correct?

## kvm.blocking: Blocking and halt polling

- section: Running vCPUs
- relevance: 3 - the wait conditions are rechecked under SRCU
- words: 100

How does a vCPU block until it has work: what conditions end the wait, what
protection is held while they are checked, which architecture hooks bracket it,
and how does halt polling grow and shrink its window? Start from
`kvm_vcpu_block()` and `kvm_vcpu_halt()`.

## kvm.guest-entry-exit: Guest entry accounting

- section: Running vCPUs
- relevance: 3 - the window where RCU and tracing are unusable
- words: 90

Which helpers bracket entry to and exit from the guest for time accounting,
context tracking and lockdep, in what order are they called, which older
helpers are marked deprecated, and what may not be used between them? Start
from `guest_state_enter_irqoff()`.

# In-kernel I/O

## kvm.io-bus: The I/O bus

- section: I/O and interrupts
- relevance: 3 - registration and lookup use different protection
- words: 100

How are in-kernel devices registered on and removed from a VM's I/O buses, which
lock must the caller hold, how is the old bus array freed on each path, what
happens when shrinking the array fails, and what protects a lookup during an
exit? Start from `kvm_io_bus_register_dev()`.

## kvm.irqfd: irqfd

- section: I/O and interrupts
- relevance: 3 - teardown races with the eventfd wait queue
- words: 110

How is an irqfd assigned and torn down: which locks protect the VM's list and
the cached routing entry, what runs from the eventfd wake-up in atomic context
and what is deferred to a work item, how do resampling irqfds differ, and what
does releasing the VM do? Start from `kvm_irqfd_assign()`.

# x86 shadow pages

## kvm.x86-obsolete-pages: Obsolete shadow pages

- section: x86 MMU
- relevance: 4 - invalid and old-generation are different states with one test
- words: 100

What makes a shadow page obsolete on x86, in which order are the conditions
tested, which iterators skip obsolete pages, and what does the fast zap of all
pages rely on about the order of the active list? Start from `is_obsolete_sp()`
and `kvm_zap_obsolete_pages()`.

## kvm.x86-shadow-page-invalid: Invalid shadow pages

- section: x86 MMU
- relevance: 4 - invalid is a state, not the end of the page's life
- words: 110

What does the invalid bit in a shadow page's role mean, where is it set, can an
invalid page still be allocated, linked from a parent or in use as a root, which
list is it on in each case, and what do the zap and commit paths assert about
it? Start from `__kvm_mmu_prepare_zap_page()`.

## kvm.x86-child-role: Child page roles

- section: x86 MMU
- relevance: 4 - whether a child can be created invalid
- words: 80

When a new shadow page is linked under a parent, which fields of the role does
it take from the parent and which are overridden, and what happens to the
invalid bit? Start from `kvm_mmu_child_role()`.

## kvm.x86-shadow-accounting: Shadow page accounting

- section: x86 MMU
- relevance: 3 - the account and unaccount conditions are not mirror images
- words: 80

Under which conditions does allocating a shadow page account it as shadowing
guest page tables, under which conditions does zapping unaccount it, and what
follows for a page zapped twice? Start from `account_shadowed()`.

## kvm.x86-zap-root: Zapping an in-use root

- section: x86 MMU
- relevance: 3 - the root outlives its invalidation
- words: 90

What happens when a shadow page that is in use as a root is zapped: which list
operations are done, when is it freed, what request tells vCPUs to stop using
it, and how do the shadow MMU and the TDP MMU differ here?

## kvm.x86-spte-atomic: Updating hardware-written entries

- section: x86 MMU
- relevance: 4 - a plain write can lose a bit the hardware just set
- words: 110

When must an x86 page table entry be updated atomically because hardware or the
lockless fault path may change it concurrently, which helpers decide that in the
shadow MMU and in the TDP MMU, and which forms of atomic update are in use? Is a
compare-and-swap loop required?

# Interface rules

## kvm.new-features: New guest-visible features

- section: ABI
- relevance: 4 - decides whether a feature can be migrated
- words: 100

What does the in-tree review checklist require of a patch that adds a
guest-visible feature or a userspace interface: default state, discoverability,
save and restore, documentation, layout of structures, tests? Start from
`Documentation/virt/kvm/review-checklist.rst`.

## kvm.warn-usage: Assertions reachable by guests

- section: ABI
- relevance: 4 - a guest-triggerable warning is a host denial of service
- words: 100

What usage of warnings and fatal assertions in KVM is unsafe because a guest or
unprivileged userspace can trigger it, what does KVM offer for states that
should be impossible, and what that looks similar is correct? Name in-tree code
for each.

## kvm.capabilities: Capabilities

- section: ABI
- relevance: 3 - generic and architecture capabilities are split
- words: 90

How does KVM report and enable capabilities: which functions answer a
capability query and enable one in generic code, how do they hand off to the
architecture, and which generic capabilities can only be enabled before vCPUs or
memslots exist?

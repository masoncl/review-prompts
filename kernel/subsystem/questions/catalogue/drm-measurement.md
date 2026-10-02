# Questions: DRM (measurement set)

- guide: drm.md
- title: DRM Subsystem

A wide set of questions about the DRM core (devices, files and ioctls, GEM and
TTM, fences and reservation objects, the GPU scheduler, GPUVM, atomic mode
setting, connectors, bridges and panels) and about the parts of the amdgpu, xe,
i915 and msm drivers that the hand-written guide covers. It is used to measure
what a model already knows before deciding what the built guide should spend
its words on. The hand-written guide it will replace is 4,973 words. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## drm.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers have moved between directories and out of the DRM directory
- words: 120

Which files and directories hold the device and file core, the ioctl
dispatcher, GEM and its helper libraries, PRIME, TTM, the GPU scheduler, GPUVM,
the locking helper for many buffer objects, sync objects, the range and buddy
allocators, the atomic core and its helpers, vblank handling, bridges, panels,
the DisplayPort and HDMI helpers, the in-kernel clients, the panic screen, the
KUnit tests, the compute accelerator core and the Rust abstractions, and which
headers declare them? A table. Start from `drivers/gpu/drm/`, `include/drm/` and
`drivers/dma-buf/`.

## drm.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 100

For each job (open a device node, dispatch an ioctl, turn a GEM handle into an
object, export and import a buffer through PRIME, check and commit an atomic
update from user space, run the commit tail, handle a vblank interrupt, report
a hotplug, run a scheduler job, handle a job timeout), which function do you
start reading from? A table.

## drm.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules are written down only there
- words: 80

Which files under `Documentation/gpu/` are the authority on driver and device
internals, memory management, mode setting and its helpers, the rules for new
user space interfaces, VM_BIND locking, device wedging and the list of wanted
cleanups, and which files under `Documentation/driver-api/` cover buffer
sharing and fences?

## drm.kunit-tests: KUnit tests

- section: Finding your way
- relevance: 3 - a core change usually has a test that pins it
- words: 70

Which parts of the DRM core, the scheduler, TTM and the buddy allocator have
KUnit tests, where do they live, and what do the helpers for building a mock
device and mock mode setting objects provide? Start from
`drivers/gpu/drm/tests/` and `include/drm/drm_kunit_helpers.h`.

# Devices, files and ioctls

## drm.device-lifetime: Device lifetime

- section: Device and driver
- relevance: 5 - use after free on unbind is the commonest driver bug
- words: 100

How is a `struct drm_device` allocated, registered, unregistered and freed,
which reference keeps it alive while a file is open, and which driver callback
runs when the last reference goes? Start from `devm_drm_dev_alloc()`,
`drm_dev_register()` and `drm_dev_put()`.

## drm.managed-resources: Managed resources

- section: Device and driver
- relevance: 5 - the wrong lifetime is a use after free the diff does not show
- words: 100

What is the difference in lifetime between memory and actions registered with
the `drmm_` functions and those registered with the `devm_` functions, what
usage of `devm_` allocation in a DRM driver is unsafe, and what that looks
similar is correct? Start from `drivers/gpu/drm/drm_managed.c`.

## drm.unplug-usage: Hardware access after unplug

- section: Device and driver
- relevance: 4 - the guard is easy to leave out of a new path
- words: 90

How does a driver stop touching hardware once its device has gone away while
files are still open, what does the guard guarantee to code inside it, what
does the unplug call wait for, and which entry points does the core already
guard? Start from `drm_dev_enter()` and `drm_dev_unplug()`.

## drm.driver-features: Driver feature flags

- section: Device and driver
- relevance: 3 - each flag turns on a set of ioctls and nodes
- words: 80

Which driver feature flags does this tree define, what does each enable, which
are marked as legacy, and how does a driver turn a feature off for one device
at run time? Start from `enum drm_driver_feature`.

## drm.wedged-event: Device wedging

- section: Device and driver
- relevance: 3 - a newer interface with rules about when to send it
- words: 80

What does a driver do to tell user space that its device is wedged, what are the
recovery methods it can advertise, what must the driver have done before
sending the event, and what task information can it attach? Start from
`drm_dev_wedged_event()`.

## drm.file-lifetime: Open files

- section: Files and ioctls
- relevance: 4 - per-client state hangs off this
- words: 90

What does a `struct drm_file` hold, which driver callbacks run when one is
opened and closed and in what order relative to the core's own cleanup of
handles, framebuffers and events, and how is the owning process tracked when the
file descriptor is passed to another process? Start from `drm_file_alloc()` and
`drm_file_free()`.

## drm.node-types: Device nodes and authentication

- section: Files and ioctls
- relevance: 4 - decides who may call an ioctl
- words: 90

What are the kinds of device node, what may a client do on each, what is DRM
master and how does a client become authenticated on the primary node, and how
do leases fit in? Start from `drm_ioctl_permit()` and
`drivers/gpu/drm/drm_auth.c`.

## drm.ioctl-dispatch: Ioctl dispatch

- section: Files and ioctls
- relevance: 5 - size handling and flags are easy to get wrong in a new ioctl
- words: 100

How does `drm_ioctl()` find the handler, how does it size, copy in, zero and
copy out the argument when user space and the kernel disagree on the structure
size, and what does each flag in an ioctl table entry mean? Start from
`DRM_IOCTL_DEF_DRV()` and `enum drm_ioctl_flags`.

## drm.uapi-rules: New user space interfaces

- section: Files and ioctls
- relevance: 4 - a new ioctl that breaks these is rejected or becomes permanent
- words: 100

What does the tree require before a new ioctl, property or other user space
interface is merged, and what must the argument structure and the handler do
about padding, alignment, flags, unknown values and extension? Start from the
open source user space section of `Documentation/gpu/drm-uapi.rst` and
`Documentation/process/botching-up-ioctls.rst`.

## drm.ioctl-errnos: Ioctl error codes

- section: Files and ioctls
- relevance: 3 - user space depends on the DRM meanings
- words: 80

Which error codes have a DRM-specific meaning when returned from an ioctl, what
does each mean, and what does user space do with an interrupted call? Start from
the recommended return values section of `Documentation/gpu/drm-uapi.rst`.

## drm.events: Events to user space

- section: Files and ioctls
- relevance: 3 - a leaked or double-sent event corrupts a list
- words: 80

How does a driver reserve, send and cancel an event that user space reads from
the device file, which lock protects the lists, what happens to a pending event
when the file closes, and how can a fence be attached to one? Start from
`drm_event_reserve_init()` and `drm_send_event_locked()`.

## drm.logging-debugfs: Logging and debugfs

- section: Files and ioctls
- relevance: 3 - reviewers ask for the device-aware forms
- words: 80

Which logging macros should new DRM code use and which older ones are
deprecated, how are debug categories selected, and how does a driver add
debugfs files for a device, for a connector and for a CRTC? Start from
`include/drm/drm_print.h` and `include/drm/drm_debugfs.h`.

# Memory management

## drm.gem-object-lifetime: GEM object lifetime

- section: GEM
- relevance: 5 - two counts with different meanings
- words: 100

What are the two counts on a `struct drm_gem_object`, what does each keep alive,
what happens when each reaches zero, which lock protects the handle count, the
global name and the dma-buf pointer, and which of the put functions remain?
Start from `drm_gem_object_put()` and `drm_gem_object_handle_put_unlocked()`.

## drm.gem-handle-usage: Publishing a handle

- section: GEM
- relevance: 5 - a handle is visible to other threads the moment it exists
- words: 90

In an ioctl that creates an object and returns a handle, what usage of the
object around `drm_gem_handle_create()` is unsafe, and what that looks similar
is correct? Name in-tree code that shows the correct order.

## drm.gem-lookup: Looking up handles

- section: GEM
- relevance: 4 - the reference rules are what callers get wrong
- words: 70

What do `drm_gem_object_lookup()` and `drm_gem_objects_lookup()` return on
success and on failure, what must the caller release, and does this tree have an
ioctl that moves an object from one handle to another?

## drm.gem-object-funcs: Object callbacks

- section: GEM
- relevance: 4 - the locking contract differs per callback
- words: 100

Which callbacks does `struct drm_gem_object_funcs` have, which are mandatory,
and which are called with the object's reservation lock already held? A table.

## drm.gem-mmap: Mapping objects to user space

- section: GEM
- relevance: 4 - access control and the vm_ops contract live here
- words: 90

How does an mmap on the device file find the object, how is a client's right to
map it checked, what reference does the mapping hold, and what must a driver's
own mmap callback do that the default path would otherwise do? Start from
`drm_gem_mmap()`, `drm_gem_mmap_obj()` and `drm_vma_node_is_allowed()`.

## drm.gem-shmem: Shmem helper

- section: GEM
- relevance: 4 - most small drivers use it and its counters have changed type
- words: 100

In the shmem GEM helper, which counters track page use, pinning and kernel
mappings and what type are they, which functions need the reservation lock held
and which take it, and what does the purgeable state do? Start from
`struct drm_gem_shmem_object`.

## drm.gem-lru: LRU lists and shrinkers

- section: GEM
- relevance: 3 - the lock moved
- words: 80

How does the GEM LRU helper track objects for a driver's shrinker, which lock
protects an LRU and the object's link to it, where does that lock live, and
what does the scan callback get called with? Start from `struct drm_gem_lru` and
`drm_gem_lru_scan()`.

## drm.prime: PRIME import and export

- section: Buffer sharing
- relevance: 4 - reference loops and self-import are the classic bugs
- words: 100

How does exporting a GEM object create or reuse a dma-buf, how does importing a
dma-buf that this device exported avoid wrapping it twice, what per-file cache
links handles and dma-bufs, and how should code test whether an object is
imported? Start from `drm_gem_prime_handle_to_dmabuf()`,
`drm_gem_prime_import_dev()` and `drm_gem_is_imported()`.

## drm.dma-buf-locking: dma-buf locking convention

- section: Buffer sharing
- relevance: 4 - the convention changed from exporter locks to caller locks
- words: 100

Which dma-buf operations must the importer call with the buffer's reservation
lock held, which must it call without it, which are the unlocked wrappers, and
what is the difference between a dynamic and a non-dynamic importer when the
exporter moves the buffer? Start from the locking convention comment in
`drivers/dma-buf/dma-buf.c`.

## drm.ttm-bo-lifetime: TTM buffer object lifetime

- section: TTM
- relevance: 4 - the release function has been renamed and the counts are layered
- words: 100

How is a TTM buffer object initialised and released, how do its own reference
count and the embedded GEM object's count relate, what does a driver call to
drop its object, and what happens to an object that is still busy when the last
reference goes? Start from `ttm_bo_init_reserved()` and `ttm_bo_fini()`.

## drm.ttm-validate: Placement and validation

- section: TTM
- relevance: 4 - the context flags decide whether a call may block or evict
- words: 100

What does `ttm_bo_validate()` do with a placement list, what does each field of
`struct ttm_operation_ctx` change, which error codes can come back and which
must be passed to user space for a restart, and what does pinning forbid?

## drm.ttm-lru: LRU, eviction and shrinking

- section: TTM
- relevance: 3 - the walk helpers replaced open-coded list walks
- words: 100

How does TTM keep buffer objects on LRU lists, which lock protects them, what
are bulk moves for, how does code walk an LRU to evict or shrink, and how are
pages backed up when system memory is short? Start from
`ttm_lru_walk_for_evict()`, `ttm_bo_lru_cursor_first()` and `ttm_bo_shrink()`.

## drm.ttm-tt-pool: Page backing and pools

- section: TTM
- relevance: 3 - allocation flags and caching live here
- words: 80

What does a `struct ttm_tt` hold, when is it populated and by which function,
what does the page pool cache, and which flags control DMA allocation and
caching for a device? Start from `ttm_bo_populate()`, `ttm_device_init()` and
`drivers/gpu/drm/ttm/ttm_pool.c`.

## drm.range-allocators: Range and buddy allocators

- section: TTM
- relevance: 3 - the buddy allocator has moved and been renamed
- words: 80

Which allocators does the tree offer for carving up an address range or VRAM,
where does each live, what are the structures and the main allocate and free
calls named, and what locking does each expect from the caller? Start from
`include/drm/drm_mm.h`, `include/drm/drm_buddy.h` and `include/drm/drm_suballoc.h`.

# Fences and synchronisation

## drm.fence-structure: Fence structure and lock

- section: dma-fence
- relevance: 5 - the lock and ops members have changed shape
- words: 100

What are the members of `struct dma_fence`, which lock protects it and how does
code reach that lock, what arguments does `dma_fence_init()` take and which may
be NULL, and what is the difference between the 32-bit and 64-bit sequence
number forms?

## drm.fence-ops-lifetime: Fence ops and module unload

- section: dma-fence
- relevance: 5 - a fence can outlive the driver that made it
- words: 100

Can a fence outlive the module that created it? Say how the ops pointer of a
fence is protected, what if anything happens to it when the fence signals, which
callbacks keep a fence tied to its driver after that, how code must read the
driver and timeline names, and what a driver must do before its module can be
unloaded. Start from `dma_fence_signal_timestamp_locked()` and
`dma_fence_driver_name()`.

## drm.fence-signalling-usage: Fence signalling path

- section: dma-fence
- relevance: 5 - a deadlock against reclaim that no test shows
- words: 110

In code that must run before a fence can signal, what usage is unsafe (kinds of
allocation, locks taken, things waited for), and what that looks similar is
correct? How is such a section annotated for lockdep? Start from the
cross-driver contract and the signalling annotation comments in
`drivers/dma-buf/dma-fence.c`.

## drm.fence-callbacks: Callbacks and enable signalling

- section: dma-fence
- relevance: 4 - reference and return-value rules
- words: 90

What does `dma_fence_add_callback()` return when the fence has already signalled
and what must the caller then do, in what context does a callback run, what may
it not do, and what must `enable_signaling` guarantee about references when it
returns true?

## drm.resv-usage: Reservation object usage levels

- section: Reservation objects
- relevance: 5 - the wrong level breaks implicit sync or memory management
- words: 110

What are the usage levels a fence can be added to a `struct dma_resv` with, who
waits on each, what must be called before adding a fence and with which lock
held, and which level do kernel memory moves, implicit-sync writers and readers,
and page table updates use? Start from `enum dma_resv_usage`.

## drm.resv-iteration: Iterating reservation fences

- section: Reservation objects
- relevance: 4 - the unlocked iterator restarts
- words: 90

What is the difference between iterating the fences of a reservation object
with the lock held and without it, what must a loop using the unlocked iterator
cope with, and which helpers wait on or test all fences of a usage level? Start
from `dma_resv_for_each_fence()` and `dma_resv_for_each_fence_unlocked()`.

## drm.exec-locking: Locking many objects

- section: Reservation objects
- relevance: 4 - the retry macro hides a jump
- words: 100

How does the helper for locking many GEM objects at once work: what does the
loop macro do on contention, what usage inside the loop is unsafe, what do the
flags do, and what does preparing an object add to locking it? Start from
`drm_exec_until_all_locked()` and `drm_exec_retry_on_contention()`.

## drm.syncobj: Sync objects

- section: Reservation objects
- relevance: 3 - timeline points have ordering rules
- words: 90

What is a sync object, how does a driver look one up and find or replace its
fence, how are timeline points added and what ordering do they need, and what
does waiting for a point that has no fence yet involve? Start from
`drm_syncobj_find_fence()` and `drm_syncobj_add_point()`.

# GPU scheduler

## drm.sched-objects: Scheduler objects

- section: GPU scheduler
- relevance: 4 - the run queue code has been reworked
- words: 100

What are the scheduler, entity, run queue, job and scheduler fence objects, how
many run queues does a scheduler have, which entity selection policies exist and
which is the default, and which files hold each part? Start from
`struct drm_sched_init_args` and `drivers/gpu/drm/scheduler/`.

## drm.sched-job-lifecycle: Job lifecycle

- section: GPU scheduler
- relevance: 5 - the point of no return is where error paths go wrong
- words: 110

In what order does a driver initialise, add dependencies to, arm and push a
scheduler job, after which call can submission no longer fail or be undone, what
must an error path call before and after that point, and who frees the job?
Start from `drm_sched_job_init()`, `drm_sched_job_arm()` and
`drm_sched_job_cleanup()`.

## drm.sched-backend-ops: Backend callbacks

- section: GPU scheduler
- relevance: 5 - reference and context rules are per callback
- words: 110

For each callback in `struct drm_sched_backend_ops`, in what context is it
called, what may it return, and what reference rule applies to a fence it
returns? Which are optional?

## drm.sched-timeout: Job timeout handling

- section: GPU scheduler
- relevance: 4 - the return values were renamed and one was added
- words: 110

What values can the timeout callback return and what does the scheduler do for
each, what sequence of scheduler calls does recovery follow for a hardware
scheduler and for a firmware scheduler, and which older recovery helpers are
deprecated? Start from `enum drm_gpu_sched_stat` and `drm_sched_stop()`.

## drm.sched-teardown: Scheduler and entity teardown

- section: GPU scheduler
- relevance: 4 - leaked jobs and unsignalled fences on unload
- words: 100

What do flushing, killing, finishing and destroying an entity each do, what does
`drm_sched_fini()` do about jobs that are still pending or queued, what is the
cancel callback for, and what order must teardown follow?

## drm.sched-flow-control: Credits and work queues

- section: GPU scheduler
- relevance: 3 - decides how many jobs are in flight
- words: 90

How do job credits and the scheduler's credit limit bound the jobs in flight,
which work queues does the scheduler use for submission and for timeouts, what
may a driver pass for each, and what may work on the submission queue not do?

## drm.sched-tests: Scheduler unit tests

- section: GPU scheduler
- relevance: 2 - a handler that can run twice needs flags that survive it
- words: 90

How does the mock scheduler used by the scheduler KUnit tests model job
completion and timeouts, which job flags does it define and which of them does
the timeout handler read and which does it set, and can the handler run more
than once for one job while a test waits, and if so what has to stay the same
across runs? Start from `drivers/gpu/drm/scheduler/tests/mock_scheduler.c`.

# GPU virtual memory

## drm.gpuvm-objects: GPUVM objects

- section: GPUVM
- relevance: 4 - the manager has three object kinds with separate lifetimes
- words: 100

What are the VM, the mapping and the VM-and-buffer-object objects in the GPU VA
manager, what do the VM and mapping flags mean, how is each object reference
counted or owned, and which drivers use the manager? Start from
`struct drm_gpuvm`, `struct drm_gpuva` and `struct drm_gpuvm_bo`.

## drm.gpuvm-split-merge: Map and unmap operations

- section: GPUVM
- relevance: 4 - the callbacks may not fail half way
- words: 100

How does a map or unmap request become a sequence of map, remap and unmap
steps, what are the two ways a driver can consume them, what must the driver
have allocated before the steps run, and what does the request structure for a
map carry? Start from `drm_gpuvm_sm_map()` and `struct drm_gpuvm_map_req`.

## drm.gpuvm-locking: GPUVM locking

- section: GPUVM
- relevance: 5 - which lock protects the per-object list depends on a flag
- words: 110

Which lock protects the list of mappings hanging off a GEM object, which protect
the VM's lists of external and evicted objects, do the VM flags change that and
how, and what may code not do while holding the lock used on the fence
signalling path? Start from the `gpuva` member of `struct drm_gem_object` and
`enum drm_gpuvm_flags`.

## drm.gpuvm-deferred: Deferred unlink and cleanup

- section: GPUVM
- relevance: 3 - newer calls for use where sleeping locks are not allowed
- words: 80

Does this tree let a mapping be unlinked and a VM-and-buffer-object reference
be dropped from a context that cannot take the reservation lock, and if so
which calls defer the work and which call completes it? Start from
`drm_gpuva_unlink_defer()` and `drm_gpuvm_bo_deferred_cleanup()`.

## drm.gpusvm: Shared virtual memory

- section: GPUVM
- relevance: 3 - notifier locking is strict
- words: 90

What do the GPU shared virtual memory helper and the page map helper provide,
how are ranges and notifiers organised, which lock must a driver hold when it
checks that a range's pages are still valid and commits the GPU binding, and
which drivers use them? Start from `drivers/gpu/drm/drm_gpusvm.c` and
`drivers/gpu/drm/drm_pagemap.c`.

# Mode setting

## drm.kms-objects: Mode setting objects

- section: Atomic mode setting
- relevance: 4 - some objects are reference counted and most are not
- words: 100

Which mode setting objects live as long as the device and which are reference
counted and can go away while the device is up, how are object ids looked up,
and which managed allocation helpers exist for CRTCs, planes, encoders and
connectors? Start from `struct drm_mode_object` and `drm_mode_object_find()`.

## drm.atomic-update-container: Atomic update container

- section: Atomic mode setting
- relevance: 5 - the structure and its functions have been renamed
- words: 100

What is the structure that carries the set of object states through an atomic
update called in this tree, what are its allocate, get, put and clear functions
called, which mode config callbacks let a driver subclass it, and how does code
get the old and the new state of a CRTC, plane or connector from it? Start from
`include/drm/drm_atomic.h`.

## drm.atomic-check-rules: Atomic check

- section: Atomic mode setting
- relevance: 5 - check runs for test-only commits and may be retried
- words: 110

What may an atomic check callback not do, why can it run more than once for one
update, how must it handle the deadlock error from taking more locks, when may
it pull extra CRTCs, planes or connectors into the update, and what decides
whether a full modeset is allowed? Start from `drm_atomic_helper_check()` and
`drm_atomic_crtc_needs_modeset()`.

## drm.atomic-commit-sequence: Commit sequence

- section: Atomic mode setting
- relevance: 5 - the order of steps is the contract drivers build on
- words: 120

List in order what the helper commit does from the ioctl to the end of the
commit tail: set up, prepare planes, wait or queue, swap state, then each step
of the default commit tail and of the runtime PM variant. After which step can
the commit no longer fail? Start from `drm_atomic_helper_commit()`.

## drm.atomic-commit-context: Commit callback context

- section: Atomic mode setting
- relevance: 5 - atomic names an all-or-nothing update, not a context
- words: 120

In what execution context does the commit tail run for a blocking and for a
non-blocking commit, may the CRTC, plane, encoder and bridge enable, disable,
update and flush callbacks sleep, and which display driver paths do run where
sleeping is not allowed? What usage of a sleeping delay or allocation in display
code is unsafe, and what that looks similar is correct?

## drm.atomic-commit-tracking: Commit ordering and completions

- section: Atomic mode setting
- relevance: 4 - a missed completion stalls every later commit
- words: 100

How does the helper order commits on the same CRTC: what are the completions in
`struct drm_crtc_commit`, who signals each, what does a later commit wait for,
what must a driver with its own commit tail call, and what happens to a CRTC
that has no vblank interrupt? Start from `drm_atomic_helper_setup_commit()`.

## drm.atomic-state-subclass: Object state subclassing

- section: Atomic mode setting
- relevance: 4 - a missed field copy or reference is a leak or stale pointer
- words: 90

How does a driver subclass a CRTC, plane or connector state, which helpers must
its reset, duplicate and destroy callbacks call, and what in the base state
holds a reference that duplicate must take and destroy must drop? Start from
`drivers/gpu/drm/drm_atomic_state_helper.c`.

## drm.private-objects: Private objects

- section: Atomic mode setting
- relevance: 3 - shared resources tracked through the same update
- words: 80

What is a private object in an atomic update for, how is it initialised, what
locks it when its state is fetched, and which in-tree users rely on it? Start
from `drm_atomic_private_obj_init()` and `drm_atomic_get_private_obj_state()`.

## drm.modeset-locks: Modeset locks

- section: Atomic mode setting
- relevance: 4 - the back-off dance is mandatory
- words: 100

How do the modeset locks and their acquire context work, what must code do when
a lock call returns the deadlock error, which macros wrap the retry loop, which
lock covers what, and which older take-everything calls should new code avoid?
Start from `drivers/gpu/drm/drm_modeset_lock.c`.

## drm.plane-prepare-fb: Preparing framebuffers

- section: Atomic mode setting
- relevance: 4 - pins and fences are taken here and must be undone
- words: 90

What are the prepare and cleanup framebuffer callbacks of a plane for, when in
the commit is each called and may they fail, what is the separate pair for
short-term access, and which helper sets up the fence a plane update waits on?
Start from `struct drm_plane_helper_funcs`.

## drm.async-updates: Asynchronous plane updates

- section: Atomic mode setting
- relevance: 3 - skips the normal state swap
- words: 80

What is an asynchronous plane update, which conditions does the helper check
before allowing one, which plane callbacks implement it, and how does it differ
from an asynchronous page flip requested through the atomic ioctl? Start from
`drm_atomic_helper_async_check()`.

## drm.vblank-api: Vblank counting

- section: Vblank
- relevance: 4 - reference and on/off pairing rules
- words: 100

How does a driver enable vblank support, what do the get and put calls do and
where may they be called from, what must CRTC enable and disable call, what does
the interrupt handler call, and which device flags change how the counter is
kept? Start from `drm_vblank_init()`, `drm_crtc_vblank_on()` and
`drm_crtc_handle_vblank()`.

## drm.vblank-event-usage: Completion events

- section: Vblank
- relevance: 5 - a lost or double event hangs user space or oopses
- words: 110

When a commit carries a completion event in the CRTC state, what usage of that
event by the driver is unsafe, and what that looks similar is correct? Which
lock must be held, what is the difference between arming and sending, and which
reference must be held when arming? Start from `drm_crtc_arm_vblank_event()` and
`drm_crtc_send_vblank_event()`.

## drm.vblank-timers-work: Vblank timers and work

- section: Vblank
- relevance: 3 - newer helpers that replace driver code
- words: 80

What do the vblank work items and the vblank timer helpers provide, which
initialiser macros wire the timer helpers into a CRTC, and which drivers are
they meant for? Start from `drivers/gpu/drm/drm_vblank_work.c` and
`drivers/gpu/drm/drm_vblank_helper.c`.

## drm.properties-blobs: Properties and blobs

- section: Planes and framebuffers
- relevance: 3 - creation time and blob references
- words: 80

When may properties be created and attached relative to device registration, how
are atomic properties read and written by a driver, and how is a blob property's
lifetime managed when it is stored in a state? Start from
`drivers/gpu/drm/drm_property.c` and `drm_property_replace_blob()`.

## drm.framebuffers-formats: Framebuffers and formats

- section: Planes and framebuffers
- relevance: 4 - the creation callback has gained a parameter
- words: 100

How is a framebuffer created from user space: what does the core check before
the driver's callback runs, what parameters does that callback take, which
helpers build a framebuffer on GEM objects and fill in its structure, and how
does a driver describe a format and its modifiers? Start from
`drm_internal_framebuffer_create()` and `drm_gem_fb_create()`.

## drm.suspend-shutdown: Suspend, resume and shutdown

- section: Planes and framebuffers
- relevance: 3 - every driver needs these and the order matters
- words: 80

Which helpers does a mode setting driver call for system suspend, resume,
shutdown and removal, what does each do to the display state, polling and fbdev,
and what goes wrong if the shutdown helper is left out?

# Connectors, bridges and panels

## drm.connector-lifetime: Connector lifetime

- section: Connectors and probing
- relevance: 4 - hot-pluggable connectors use a different init path
- words: 100

How are connectors initialised, registered and freed, what is different for
connectors created after device registration, how must code walk the connector
list, and which managed variants exist? Start from `drm_connector_init()`,
`drm_connector_dynamic_init()` and `drm_connector_list_iter_begin()`.

## drm.hotplug-probing: Detection and hotplug

- section: Connectors and probing
- relevance: 4 - which lock and which helper for each source of change
- words: 100

How do connector detection, output polling and hotplug interrupts fit together:
which helper does a driver call from a hotplug interrupt for one connector and
for all, what lock does probing run under, what may a detect callback do, and
how is a link failure after a modeset reported to user space? Start from
`drivers/gpu/drm/drm_probe_helper.c`.

## drm.edid: EDID handling

- section: Connectors and probing
- relevance: 4 - an opaque type replaced the raw structure
- words: 90

Which functions should new code use to read an EDID, attach it to a connector
and add its modes, which older functions are deprecated, and who owns and frees
the EDID object? Start from `drm_edid_read()` and `drm_edid_connector_update()`.

## drm.scaling-mode: Scaling mode property

- section: Connectors and probing
- relevance: 2 - a default that distorts the picture is a user-visible bug
- words: 80

What are the values of the standard scaling mode connector property and what
does each do to aspect ratio, how does amdgpu map them to its own scaling
enumeration, and which value does amdgpu choose by itself when a mode needs
scaling and user space asked for none? Start from
`drm_connector_attach_scaling_mode_property()` and `enum amdgpu_rmx_type`.

## drm.bridge-lifetime: Bridge lifetime

- section: Bridges and panels
- relevance: 5 - bridges are now reference counted
- words: 110

How must a bridge driver allocate its bridge, is a bridge reference counted and
if so which lookup and chain-walking functions return a reference the caller
must drop, what happens to the pointer a consumer holds when the bridge driver
unbinds, and is there a guard for hardware access after removal? Start from
`devm_drm_bridge_alloc()` and `drm_bridge_get()`.

## drm.bridge-chain-order: Bridge call order

- section: Bridges and panels
- relevance: 4 - DSI hosts and sinks depend on it
- words: 100

In what order are the pre-enable, enable, disable and post-disable callbacks of
the bridges in a chain called relative to each other, to the encoder and to the
CRTC's enable and disable, which bridge flag changes that order and why, and do
non-atomic forms of those callbacks still exist to be mixed with the atomic
ones? Start from `drm_atomic_bridge_chain_pre_enable()`,
`drm_atomic_bridge_chain_post_disable()` and
`drm_atomic_helper_commit_modeset_enables()`.

## drm.bridge-connector: Bridge connector

- section: Bridges and panels
- relevance: 4 - the attach flag and ops bits decide who makes the connector
- words: 100

What does the no-connector attach flag ask of a bridge, which ops bits does a
bridge set to say what it can do, how does the bridge connector pick a bridge
for each job, and which ops need extra fields filled in on the bridge? Start
from `drm_bridge_connector_init()` and `enum drm_bridge_ops`.

## drm.panel: Panels

- section: Bridges and panels
- relevance: 4 - allocation and the return types have changed
- words: 100

How must a panel driver allocate and register its panel, in what order are the
prepare, enable, disable and unprepare calls made, what do those calls return,
does the core guard against a double call, and what is a panel follower? Start from
`devm_drm_panel_alloc()` and `drm_panel_prepare()`.

## drm.dp-dpcd-access: DPCD access

- section: DisplayPort
- relevance: 4 - two families of helper with different return conventions
- words: 110

What do the DPCD read and write helpers return on success and on a short
transfer, does this tree have more than one family of them with different
conventions and if so which should new code use, does a read probe the sink
first, at which address, and what does the tree say about why? Start from
`drm_dp_dpcd_read()`, `drm_dp_dpcd_read_data()` and `drm_dp_dpcd_probe()`.

## drm.dp-mst: DisplayPort MST

- section: DisplayPort
- relevance: 3 - its state rides in the atomic update as a private object
- words: 100

How is MST bandwidth tracked in an atomic update, which calls must a driver make
in its check and commit paths, which locks protect the topology, and what must
suspend and resume do? Start from `drm_dp_mst_topology_mgr_init()` and
`drm_dp_mst_atomic_check()`.

## drm.clients-fbdev: In-kernel clients and fbdev

- section: Clients
- relevance: 3 - the setup call and the driver hooks have been replaced
- words: 90

How does a driver get fbdev emulation and the other in-kernel clients in this
tree: which call sets them up and when, which driver structure field and macros
select the fbdev flavour, and which older setup functions are gone? Start from
`drm_client_setup()` and `drivers/gpu/drm/clients/`.

## drm.panic-screen: Panic screen

- section: Clients
- relevance: 3 - runs in a context where almost nothing is allowed
- words: 80

How does a driver support the panic screen, what must the plane callback that
describes the scanout buffer do and not do given the context it runs in, and
which lock keeps normal commits from racing with it? Start from
`drivers/gpu/drm/drm_panic.c`.

# amdgpu

## drm.amdgpu-layout: amdgpu layout

- section: amdgpu
- relevance: 4 - the display manager is no longer one file
- words: 100

How is `drivers/gpu/drm/amd/` laid out (core, display core, display manager,
power management, KFD, RAS), is the display manager one file or several and what
is in each, and where are the hardware sequencer functions? A table.

## drm.amdgpu-ip-versions: IP and firmware versions

- section: amdgpu
- relevance: 4 - hardware and firmware are versioned separately
- words: 100

How does amdgpu identify hardware blocks and their versions, and which call
returns a block's version? Is PSP firmware versioned separately from the
hardware block, and if so where is its version held and how does in-tree code
gate a command that only newer firmware understands? Name such code. Start from
`amdgpu_ip_version()` and `drivers/gpu/drm/amd/amdgpu/amdgpu_psp.c`.

## drm.amdgpu-kernel-bo: Kernel buffer objects

- section: amdgpu
- relevance: 4 - the pointer argument is both input and output
- words: 90

What do `amdgpu_bo_create_reserved()` and `amdgpu_bo_create_kernel()` do when the
buffer object pointer they are given already points at something, what must a
caller therefore guarantee about it, and how do the wrappers that allocate
buffers for the ISP driver handle that? Start from `isp_kernel_buffer_alloc()`.

## drm.amdgpu-bo-addresses: Buffer object addresses

- section: amdgpu
- relevance: 3 - two helpers return values in different formats
- words: 80

What is the difference between the value `amdgpu_bo_gpu_offset()` returns and
the value `amdgpu_gmc_pd_addr()` returns for a page directory, which does the
hardware VM root register take, and which does the in-tree debugfs file that
reports a VM's page directory address print?

## drm.amdgpu-ring-fence: Rings and fence sequence numbers

- section: amdgpu
- relevance: 4 - truncation and wrap-around bugs
- words: 100

What are the types of the ring write pointer and of the fence sequence counters
in amdgpu, how is the fence array indexed, and what form of loop over
outstanding sequence numbers is unsafe when the counter wraps, and what that
looks similar is correct? Start from `struct amdgpu_ring`,
`struct amdgpu_fence_driver` and `amdgpu_fence_process()`.

## drm.amdgpu-reset: GPU reset

- section: amdgpu
- relevance: 3 - hardware access must be fenced off during reset
- words: 90

How does amdgpu serialise GPU reset against ioctls and hardware access: what is
a reset domain, which lock do paths take to stay out of a reset, what does the
job timeout handler do, and how does code test that a reset is in progress?
Start from `amdgpu_device_gpu_recover()` and `amdgpu_in_reset()`.

## drm.amdgpu-dc-context: Display core context

- section: amdgpu
- relevance: 4 - some display core paths cannot sleep
- words: 110

In the amdgpu display code, which lock serialises calls into the display core,
what do the floating point start and end macros do to the calling context, which
handlers run in interrupt context, and what usage of sleeping delays in a
hardware sequencer function is unsafe, and what that looks similar is correct?
Start from `DC_FP_START()` and
`drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm_irq.c`.

# xe

## drm.xe-layout: xe device, tiles and GTs

- section: xe
- relevance: 4 - which accessor can return NULL
- words: 100

How are device, tile and GT related in the xe driver, which accessor returns a
GT by index and what does it return for an index with no GT, which returns the
root tile's primary GT, and which iterator macros skip missing GTs? Start from
`drivers/gpu/drm/xe/xe_device.h`.

## drm.xe-system-runtime-pm: xe system and runtime PM

- section: xe
- relevance: 4 - runtime flags must not steer system resume
- words: 100

Which functions handle system suspend and resume and which handle runtime
suspend and resume in xe, what do the capable and allowed D3cold fields mean and
who sets them, and which of the four paths read them? Start from
`drivers/gpu/drm/xe/xe_pm.c`.

## drm.xe-runtime-pm-usage: xe runtime PM references

- section: xe
- relevance: 4 - the wrong getter deadlocks or warns
- words: 100

Which runtime PM getters does xe have, when is each the right one (ioctl entry,
inner code that knows the device is awake, code that must not resume), what
scope-based forms exist, and what usage inside the runtime suspend or resume
callbacks themselves is unsafe? Start from `drivers/gpu/drm/xe/xe_pm.h`.

## drm.xe-forcewake: xe forcewake

- section: xe
- relevance: 4 - the return value is a reference mask, not an error code
- words: 90

What does `xe_force_wake_get()` return, how must a caller check that the domain
it needs woke, what does it pass to the put call, and which scope-based forms
should new code prefer?

## drm.xe-pcode: xe pcode mailbox

- section: xe
- relevance: 3 - packed registers need read-modify-write
- words: 90

How does xe talk to pcode, which read and write calls exist, and when updating
one field of a mailbox value that packs several (such as a power limit with its
enable bit and time window) what usage is unsafe, and what that looks similar is
correct? Start from `drivers/gpu/drm/xe/xe_pcode.c` and
`drivers/gpu/drm/xe/xe_hwmon.c`.

## drm.xe-sriov: xe SR-IOV

- section: xe
- relevance: 4 - a VF cannot reach much of the hardware
- words: 100

How does xe tell whether it runs as a physical function, a virtual function or
neither, which hardware and services does in-tree code skip or refuse on a
virtual function, and how do probe paths for such resources guard themselves?
Name in-tree examples.
Start from `IS_SRIOV_VF()` and `drivers/gpu/drm/xe/xe_sriov.c`.

## drm.xe-guc-ct: xe GuC command transport

- section: xe
- relevance: 3 - debug-only state still needs initialising
- words: 90

What are the initialisation stages of the GuC command transport in xe and what
may each do? If debug code in that file saves stack traces, where is the stack
depot initialised, under which configuration option, and what usage of such a
facility without that step is unsafe? Start from `xe_guc_ct_init_noalloc()` and
`drivers/gpu/drm/xe/xe_guc_ct.c`.

## drm.xe-bo-vm-locking: xe buffer and VM locking

- section: xe
- relevance: 3 - validation now goes through a guard
- words: 90

How does xe lock a VM and its buffer objects for validation and eviction, what
is the validation context and its guard macro for, and how does that relate to
the core helper for locking many objects? Start from
`drivers/gpu/drm/xe/xe_validation.h` and `xe_vm_lock()`.

# Intel display

## drm.intel-display-device: Intel display device

- section: Intel display
- relevance: 4 - one display code base serves two drivers
- words: 100

How is the Intel display code shared between i915 and xe, which structure does
display code take instead of the i915 device, how does it test for a platform,
a subplatform and a display version, and how are registers read and written?
Start from `drivers/gpu/drm/i915/display/intel_display_device.c` and
`to_intel_display()`.

## drm.intel-platform-ids: Platforms and subplatforms

- section: Intel display
- relevance: 3 - a new device id may need more than a table entry
- words: 100

How do PCI ids map to platform descriptors in the i915 display code and in xe,
how is a subplatform declared and matched, and what in the tree decides whether
a variant gets its own id macro and subplatform or just more ids in an existing
macro? Give an in-tree example of a subplatform that changes which PHY a port
uses. Start from
`include/drm/intel/pciids.h`.

## drm.intel-cx0-phy: CX0 PHY access

- section: Intel display
- relevance: 3 - message bus access needs a wake reference and a set-up step
- words: 100

Does code that reads or writes CX0 PHY registers over the message bus have to
be bracketed by anything, and if so which functions take care of that themselves
and which expect the caller to? Does a C10 PHY need an extra step before its
internal registers are accessed, and how does code tell a C10 from a C20 PHY?
Start from `drivers/gpu/drm/i915/display/intel_cx0_phy.c`.

# msm

## drm.msm-context-vm: msm address spaces

- section: msm
- relevance: 3 - the per-context VM is created on first use
- words: 100

When is a context's GPU address space created in the msm driver, which accessor
creates it on demand and what can that return, which code reads the context's
field directly and why is that safe there, and what does display initialisation
do when there is no IOMMU? Start from `msm_context_vm()` and
`msm_kms_init_vm()`.

# General kernel interfaces

## drm.size-helpers: Size helper overflow

- section: General interfaces
- relevance: 2 - not DRM specific, but GPU ioctls size arrays from user input
- words: 70

What do `struct_size()`, `array_size()` and `size_mul()` return when the
arithmetic overflows, what form of overflow check on their result is dead code,
and what that looks similar is correct?

## drm.fwnode-errors: Software node creation errors

- section: General interfaces
- relevance: 1 - one fix written up as a rule
- words: 50

What does `fwnode_create_software_node()` return on failure, and which check of
its result is therefore wrong?

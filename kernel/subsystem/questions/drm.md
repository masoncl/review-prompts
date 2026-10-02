# Questions: DRM

- guide: drm.md
- title: DRM Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/drm-measurement.md` is the wider
set the readers were measured on and `catalogue/drm-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## drm.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## drm.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers have moved between directories and out of the DRM directory

A table and nothing else, job to file or directory: the device and file core; the ioctl
dispatcher; GEM and its helper libraries; PRIME; TTM; the GPU scheduler; GPUVM; the locking helper
for many buffer objects; sync objects; the range and buddy allocators; the atomic core and its
helpers; vblank handling; bridges; panels; the DisplayPort and HDMI helpers; the in-kernel
clients; the panic screen; the compute accelerator core; the Rust abstractions. Where a reader
is likely to look for a file that does not exist in this tree, or that has left the DRM
directory, say so in the row. Start from `drivers/gpu/drm/`, `include/drm/` and
`drivers/dma-buf/`.

## drm.kunit-tests: KUnit tests

- section: Finding your way
- relevance: 3 - a core change usually has a test that pins it

Where do the KUnit tests for the DRM core, the scheduler, TTM and the buddy allocator live, and
what do the helpers for building a mock device and mock mode setting objects provide that a new
test should not rebuild? Start from `drivers/gpu/drm/tests/` and
`include/drm/drm_kunit_helpers.h`.

## drm.size-helpers: struct_size and array_size overflow

- section: Finding your way
- relevance: 2 - not DRM specific, but GPU ioctls size arrays from user input

What do `struct_size()`, `array_size()` and `size_mul()` return when the arithmetic overflows, and
what are the requirements for checking their result for overflow in order to assure safe usage?

# Device lifetime

## drm.device-lifetime: Device references and release

- section: Device lifetime
- relevance: 5 - use after free on unbind is the commonest driver bug

Which reference keeps a `struct drm_device` alive while a file is open after the driver has
unbound, and which driver callback runs when the last reference goes? What are the requirements
for allocating state that hangs off the `struct drm_device` in order to assure safe usage after
unbind? Start from `devm_drm_dev_alloc()`, `drm_dev_register()` and `drm_dev_put()`.

## drm.unplug-usage: Hardware access after unplug

- section: Device lifetime
- relevance: 4 - the guard is easy to leave out of a new path

What does `drm_dev_enter()` guarantee to code between it and `drm_dev_exit()` once the device has
gone away while files are still open, what does `drm_dev_unplug()` wait for, and which entry
points does the core already guard so that a driver need not? Start from `drm_dev_enter()` and
`drm_dev_unplug()`.

## drm.managed-resources: Managed resources

- section: Device lifetime
- relevance: 5 - the wrong lifetime is a use after free the diff does not show

What is the difference in lifetime between memory and actions registered with the `drmm_`
functions and those registered with the `devm_` functions? What are the requirements for an
allocation made with a `devm_` function in a DRM driver in order to assure safe usage? Start from
`drivers/gpu/drm/drm_managed.c`.

# Files, ioctls and debugfs

## drm.node-types: Device nodes and authentication

- section: Files, ioctls and debugfs
- relevance: 4 - decides who may call an ioctl

What may a client do on each kind of device node, and how does a client become authenticated on
the primary node? What does a lease change about what its holder may do? Start from
`drm_ioctl_permit()` and `drivers/gpu/drm/drm_auth.c`.

## drm.file-lifetime: File open and close

- section: Files, ioctls and debugfs
- relevance: 4 - per-client state hangs off this

Which driver callbacks run when a `struct drm_file` is opened and closed, and in what order
relative to the core's own cleanup of handles, framebuffers and events? How is the owning
process tracked when the file descriptor is passed to another process? Start from
`drm_file_alloc()` and `drm_file_free()`.

## drm.ioctl-dispatch: Ioctl dispatch

- section: Files, ioctls and debugfs
- relevance: 5 - size handling and flags are easy to get wrong in a new ioctl

What does `drm_ioctl()` do with the argument when user space and the kernel disagree on the
structure size, and what may a handler therefore assume about it? What does each flag in `enum
drm_ioctl_flags` mean, where a reader's memory may offer flags that are gone? Start from
`DRM_IOCTL_DEF_DRV()` and `enum drm_ioctl_flags`.

## drm.ioctl-errnos: Ioctl error codes

- section: Files, ioctls and debugfs
- relevance: 3 - user space depends on the DRM meanings

Which error codes have a DRM-specific meaning when returned from an ioctl and what does each
mean, going by the documented list and nothing else, and what does user space do with an
interrupted call? Start from the recommended return values section of
`Documentation/gpu/drm-uapi.rst`.

## drm.uapi-rules: New user space interfaces

- section: Files, ioctls and debugfs
- relevance: 4 - a new ioctl that breaks these is rejected or becomes permanent

What does the tree require before a new user space interface is merged, and what does it require
of the argument structure and of the handler of a new ioctl? Start from the open source user space
section of `Documentation/gpu/drm-uapi.rst` and `Documentation/process/botching-up-ioctls.rst`.

## drm.logging-debugfs: Logging and debugfs

- section: Files, ioctls and debugfs
- relevance: 3 - reviewers ask for the device-aware forms

Which logging macros should new DRM code use and which older ones are deprecated? How does a
driver add debugfs files for a device, for a connector and for a CRTC? Start from
`include/drm/drm_print.h` and `include/drm/drm_debugfs.h`.

# Mode setting objects and locks

## drm.kms-objects: Mode object lifetime and lookup

- section: Mode setting objects and locks
- relevance: 4 - some objects are reference counted and most are not

Which mode setting objects live as long as the device and which are reference counted and can
go away while the device is up, and what must code that looks one up by id therefore do with the
result? Which of the allocation helpers for CRTCs, planes, encoders and connectors tie the
object to the right lifetime? Start from `struct drm_mode_object` and `drm_mode_object_find()`.

## drm.framebuffers-formats: Framebuffers and formats

- section: Mode setting objects and locks
- relevance: 4 - the creation callback has gained a parameter

What does the core check and look up before a driver's `fb_create` callback runs, what of that
does it hand to the callback, and which helpers build a framebuffer on GEM objects so that a
driver need not? Start from `drm_internal_framebuffer_create()` and `drm_gem_fb_create()`.

## drm.modeset-locks: Modeset locks

- section: Mode setting objects and locks
- relevance: 4 - the back-off dance is mandatory

What must code do when a modeset lock call returns `-EDEADLK`, which macros wrap the retry loop,
and which older take-everything calls should new code avoid? Start from
`drivers/gpu/drm/drm_modeset_lock.c`.

## drm.modeset-lock-coverage: Modeset lock coverage

- section: Mode setting objects and locks
- relevance: 4 - a path that takes the wrong lock reads state that another thread is changing

Which state do the `mutex` and the `connection_mutex` members of `struct drm_mode_config` each
protect, and which lock protects the state of a CRTC and of a plane? Start from
`drivers/gpu/drm/drm_modeset_lock.c`.

# Atomic commits

## drm.atomic-update-container: Atomic update container

- section: Atomic commits
- relevance: 5 - the structure and its functions have been renamed

What is the structure that carries the set of object states through an atomic update called in
this tree, and what are its allocate, get, put and clear functions called, where a reader's
memory offers older names? Which mode config callbacks let a driver subclass it, and how does
code get the old and the new state of a CRTC, plane or connector from it? Start from
`include/drm/drm_atomic.h`.

## drm.atomic-commit-sequence: Commit sequence

- section: Atomic commits
- relevance: 5 - the order of steps is the contract drivers build on

In what order does `drm_atomic_helper_commit()` run its steps, those of
`drm_atomic_helper_commit_tail()` included? After which step can the commit no longer fail, and
what are the requirements for the steps after it in order to assure safe usage? Start from
`drm_atomic_helper_commit()`.

## drm.commit-tail-rpm: Runtime PM commit tail

- section: Atomic commits
- relevance: 5 - which tail a driver uses decides whether its hardware is enabled when the planes are updated

How does the order of steps in `drm_atomic_helper_commit_tail_rpm()` differ from the order in
`drm_atomic_helper_commit_tail()`, and when must a driver use the first?

## drm.atomic-commit-tracking: Commit ordering and completions

- section: Atomic commits
- relevance: 4 - a missed completion stalls every later commit

What does a later commit on the same CRTC wait for, and who signals each completion in `struct
drm_crtc_commit`? What must a driver with its own commit tail call so that later commits do not
stall? Start from `drm_atomic_helper_setup_commit()`.

## drm.commit-no-vblank: Commits without vblank interrupts

- section: Atomic commits
- relevance: 4 - a CRTC with no vblank interrupt still has to complete its commits, or every later commit stalls

What signals the completions of a commit on a CRTC that has no vblank interrupt, and what must the
driver of such a CRTC do for that to happen? Start from `drm_atomic_helper_setup_commit()`.

## drm.atomic-check-rules: Atomic check

- section: Atomic commits
- relevance: 5 - check runs for test-only commits and may be retried

What are the requirements for an `atomic_check` callback in order to assure safe usage, and how
must it handle `-EDEADLK` from taking more locks? What decides whether a full modeset is allowed?
Start from `drm_atomic_helper_check()` and `drm_atomic_crtc_needs_modeset()`.

## drm.atomic-check-added-objects: Objects added during check

- section: Atomic commits
- relevance: 5 - an object added to the update late misses the checks that ran before it was added

When may an `atomic_check` callback add objects to the update that user space did not ask to
change, and what are the requirements for doing so in order to assure safe usage? Start from
`drm_atomic_helper_check()`.

## drm.atomic-state-subclass: Object state subclassing

- section: Atomic commits
- relevance: 4 - a missed field copy or reference is a leak or stale pointer

How does a driver subclass a CRTC, plane or connector state, which helpers must its reset,
duplicate and destroy callbacks call, and what in the base state holds a reference that
duplicate must take and destroy must drop? Start from
`drivers/gpu/drm/drm_atomic_state_helper.c`.

## drm.plane-prepare-fb: Preparing framebuffers

- section: Atomic commits
- relevance: 4 - pins and fences are taken here and must be undone

When in a commit are the `prepare_fb` and `cleanup_fb` callbacks of a plane called and may they
fail, what are `begin_fb_access` and `end_fb_access` for, and which helper sets up the fence a
plane update waits on? Start from `struct drm_plane_helper_funcs`.

## drm.vblank-api: Vblank counting

- section: Atomic commits
- relevance: 4 - reference and on/off pairing rules

What must CRTC enable and disable call for vblank support to work, what does
`drm_crtc_vblank_get()` return while vblank is off, and which device flags change how the counter
is kept and when the interrupt is switched off? Start from `drm_vblank_init()`,
`drm_crtc_vblank_on()` and `drm_crtc_handle_vblank()`.

## drm.vblank-get-context: Vblank reference context

- section: Atomic commits
- relevance: 4 - drivers take and drop vblank references from interrupt handlers and from commit code

From which contexts may `drm_crtc_vblank_get()` and `drm_crtc_vblank_put()` be called?

## drm.atomic-commit-context: Commit callback context

- section: Atomic commits
- relevance: 5 - atomic names an all-or-nothing update, not a context

In what execution context does the commit tail run for a blocking and for a non-blocking commit?
Which callbacks of a display driver run where sleeping is not allowed, and what are the
requirements for a delay or an allocation in them in order to assure safe usage?

## drm.vblank-event-usage: Vblank completion events

- section: Atomic commits
- relevance: 5 - a lost or double event hangs user space or oopses

When a commit carries a completion event in `struct drm_crtc_state`, what are the requirements for
the driver's handling of the event in order to assure safe usage? What is the difference between
arming and sending, and which lock and which reference must be held for each? Start from
`drm_crtc_arm_vblank_event()` and `drm_crtc_send_vblank_event()`.

# Bridges, panels and connectors

## drm.bridge-lifetime: Bridge lifetime

- section: Bridges, panels and connectors
- relevance: 5 - bridges are now reference counted

How must a bridge driver allocate its bridge in this tree, and which lookup and chain-walking
functions return a reference the caller must drop? What, if anything, keeps a bridge pointer that
a consumer holds valid after the bridge driver unbinds? Start from `devm_drm_bridge_alloc()` and
`drm_bridge_get()`.

## drm.bridge-removal-guard: Bridge access after removal

- section: Bridges, panels and connectors
- relevance: 5 - a bridge that outlives its driver can be called after its hardware has gone

Does the tree provide a guard for hardware access by a bridge after its driver has unbound, and if
so what does the guard guarantee to code inside it and what must the driver call when it unbinds?
Start from `drivers/gpu/drm/drm_bridge.c`.

## drm.bridge-chain-order: Bridge call order

- section: Bridges, panels and connectors
- relevance: 4 - DSI hosts and sinks depend on it, and where the CRTC falls in the order is easy to get backwards

In what order are the pre-enable, enable, disable and post-disable callbacks of the bridges in a
chain called relative to each other, to the encoder and to the CRTC's enable and disable, and
which bridge flag changes that order and why? Do non-atomic forms of those callbacks still exist
to be mixed with the atomic ones? Start from `drm_atomic_bridge_chain_pre_enable()`,
`drm_atomic_bridge_chain_post_disable()` and `drm_atomic_helper_commit_modeset_enables()`.

## drm.bridge-connector: Bridge connector

- section: Bridges, panels and connectors
- relevance: 4 - the attach flag and ops bits decide who makes the connector

What does `DRM_BRIDGE_ATTACH_NO_CONNECTOR` ask of a bridge, how does `drm_bridge_connector_init()`
pick a bridge for each job when several in the chain set the same bit of `enum drm_bridge_ops`,
and which ops need extra members filled in on the bridge? Start from `drm_bridge_connector_init()`
and `enum drm_bridge_ops`.

## drm.panel: Panel allocation and calls

- section: Bridges, panels and connectors
- relevance: 4 - allocation and the return types have changed

How must a panel driver allocate its panel in this tree, what do `drm_panel_prepare()`,
`drm_panel_enable()`, `drm_panel_disable()` and `drm_panel_unprepare()` return, and does the core
guard against a double call? Start from `devm_drm_panel_alloc()` and `drm_panel_prepare()`.

## drm.panel-followers: Panel followers

- section: Bridges, panels and connectors
- relevance: 4 - a follower powers its own device from its callbacks, so when they run decides whether that device has power

When do the callbacks of a panel follower registered with `drm_panel_add_follower()` run relative
to the calls that prepare and unprepare the panel, and what happens when a follower is added to a
panel that is already prepared?

## drm.connector-lifetime: Connector lifetime

- section: Bridges, panels and connectors
- relevance: 4 - hot-pluggable connectors use a different init path

What is different about initialising, registering and freeing a connector created after device
registration, which connectors are reference counted, and how must code walk the connector list?
Start from `drm_connector_init()`, `drm_connector_dynamic_init()` and
`drm_connector_list_iter_begin()`.

## drm.hotplug-probing: Detection and hotplug

- section: Bridges, panels and connectors
- relevance: 4 - which lock and which helper for each source of change

Which helper does a driver call from a hotplug interrupt for one connector and which for all,
what lock does probing run under and what may a detect callback therefore do, and how is a link
failure after a modeset reported to user space? Start from
`drivers/gpu/drm/drm_probe_helper.c`.

## drm.edid: EDID handling

- section: Bridges, panels and connectors
- relevance: 4 - an opaque type replaced the raw structure

Which functions should new code use to read an EDID, attach it to a connector and add its modes,
which older functions are deprecated, and who owns and frees the EDID object? Start from
`drm_edid_read()` and `drm_edid_connector_update()`.

## drm.dp-dpcd-access: DPCD access

- section: Bridges, panels and connectors
- relevance: 4 - two families of helper with different return conventions

What do `drm_dp_dpcd_read()` and `drm_dp_dpcd_write()` return on success and on a short transfer,
what do `drm_dp_dpcd_read_data()` and `drm_dp_dpcd_write_data()` return, and which should new code
use? Does a read probe the sink first, and at which address? Start from `drm_dp_dpcd_read()`,
`drm_dp_dpcd_read_data()` and `drm_dp_dpcd_probe()`.

# Fences and reservation objects

## drm.fence-structure: Fence structure and lock

- section: Fences and reservation objects
- relevance: 5 - the lock and ops members have changed shape

Which lock protects a `struct dma_fence` and how does code reach it, where a reader's memory
offers a plain member? What may be passed as NULL to `dma_fence_init()` and what does that
select, and what is the difference between the 32-bit and 64-bit sequence number forms?

## drm.fence-ops-lifetime: Fence ops and module unload

- section: Fences and reservation objects
- relevance: 5 - a fence can outlive the driver that made it

What, if anything, happens to the ops pointer of a `struct dma_fence` when the fence signals? How
must code read the driver and timeline names, and what must a driver do before its module can be
unloaded? Start from `dma_fence_signal_timestamp_locked()` and `dma_fence_driver_name()`.

## drm.fence-ops-after-signal: Fence callbacks after signalling

- section: Fences and reservation objects
- relevance: 5 - a fence that still calls into its driver after it signalled keeps the module from being unloaded safely

Which callbacks in `struct dma_fence_ops` keep a fence tied to the module that created it after
the fence has signalled? Start from `dma_fence_signal_timestamp_locked()`.

## drm.fence-callbacks: Callbacks and enable signalling

- section: Fences and reservation objects
- relevance: 4 - reference and return-value rules

What does `dma_fence_add_callback()` return when the fence has already signalled and what must
the caller then do, in what context does a callback run and what may it not do, and what must
`enable_signaling` guarantee about references when it returns true?

## drm.resv-usage: Reservation object usage levels

- section: Fences and reservation objects
- relevance: 5 - the wrong level breaks implicit sync or memory management

Who waits on each usage level a fence can be added to a `struct dma_resv` with, and which level
do kernel memory moves, implicit-sync writers and readers, and page table updates use? What must
be called before adding a fence, and with which lock held? Start from `enum dma_resv_usage`.

## drm.resv-iteration: Iterating reservation fences

- section: Fences and reservation objects
- relevance: 4 - the unlocked iterator restarts

What is the difference between iterating the fences of a reservation object with the lock held
and without it, what must a loop using the unlocked iterator cope with, and which helpers wait
on or test all fences of a usage level? Start from `dma_resv_for_each_fence()` and
`dma_resv_for_each_fence_unlocked()`.

## drm.dma-buf-locking: dma-buf locking convention

- section: Fences and reservation objects
- relevance: 4 - the callback and the call an exporter makes when it moves a buffer have been renamed

Which dma-buf operations must an importer call with the buffer's reservation lock held and which
without it? What does the exporter call and the importer supply when the exporter moves a buffer,
where a reader's memory offers older names, and how does a non-dynamic importer differ? Start from
the locking convention comment in `drivers/dma-buf/dma-buf.c`.

## drm.fence-signalling-usage: Fence signalling path

- section: Fences and reservation objects
- relevance: 5 - a deadlock against reclaim that no test shows

What are the requirements for code that must run before a fence can signal in order to assure safe
usage, and how is such a section annotated for lockdep? Start from the cross-driver contract and
the signalling annotation comments in `drivers/dma-buf/dma-fence.c`.

# GEM

## drm.gem-object-lifetime: GEM object lifetime

- section: GEM
- relevance: 5 - two counts with different meanings

What does each of the two counts on a `struct drm_gem_object` keep alive, and what happens when
each reaches zero? Which lock protects the handle count, the global name and the dma-buf
pointer, and which of the put functions remain in this tree? Start from `drm_gem_object_put()`
and `drm_gem_object_handle_put_unlocked()`.

## drm.gem-object-funcs: Object callbacks

- section: GEM
- relevance: 4 - the locking contract differs per callback

Which callbacks in `struct drm_gem_object_funcs` must a driver supply, and which are called with
the object's reservation lock already held as opposed to having to take it themselves?

## drm.gem-lookup: Looking up handles

- section: GEM
- relevance: 4 - the reference rules are what callers get wrong

What do `drm_gem_object_lookup()` and `drm_gem_objects_lookup()` return on success and on
failure, what must the caller release, and can user space reach an ioctl that moves an object
from one handle to another?

## drm.gem-mmap: Mapping objects to user space

- section: GEM
- relevance: 4 - access control and the vm_ops contract live here

How is a client's right to map an object checked when it calls mmap on the device file, what
reference does the mapping hold, and what must a driver's own mmap callback do that the default
path would otherwise do? Start from `drm_gem_mmap()`, `drm_gem_mmap_obj()` and
`drm_vma_node_is_allowed()`.

## drm.gem-shmem: Shmem helper

- section: GEM
- relevance: 4 - most small drivers use it and its counters have changed type

In the shmem GEM helper, which counters track page use, pinning and kernel mappings and what type
are they in this tree, and which of its functions need the reservation lock held as opposed to
taking it themselves? When may the pages of an object that user space has marked purgeable be
freed? Start from `struct drm_gem_shmem_object`.

## drm.prime: PRIME import and export

- section: GEM
- relevance: 4 - reference loops and self-import are the classic bugs

How does importing a dma-buf that this device exported avoid wrapping it twice, what per-file
cache links handles and dma-bufs and what does it hold, and how should code test whether an
object is imported? Start from `drm_gem_prime_handle_to_dmabuf()`, `drm_gem_prime_import_dev()`
and `drm_gem_is_imported()`.

## drm.gem-lru: LRU lists and shrinkers

- section: GEM
- relevance: 3 - the lock moved

Which lock protects a `struct drm_gem_lru` and an object's link to it, and where does that lock
live in this tree? Which locks are held when `drm_gem_lru_scan()` calls the driver's `shrink`
callback, and what may the callback do? Start from `struct drm_gem_lru` and `drm_gem_lru_scan()`.

## drm.exec-locking: drm_exec object locking

- section: GEM
- relevance: 4 - the retry macro hides a jump

What does `drm_exec_until_all_locked()` do on contention, and what are the requirements for code
inside the loop in order to assure safe usage? What does `drm_exec_prepare_obj()` add to
`drm_exec_lock_obj()`? Start from `drm_exec_until_all_locked()` and
`drm_exec_retry_on_contention()`.

## drm.gem-handle-usage: Publishing a handle

- section: GEM
- relevance: 5 - a handle is visible to other threads the moment it exists

In an ioctl that creates an object and returns a handle, what are the requirements for using the
object before and after `drm_gem_handle_create()` in order to assure safe usage? Name in-tree code
that shows it.

# TTM and allocators

## drm.ttm-bo-lifetime: TTM buffer object lifetime

- section: TTM and allocators
- relevance: 4 - the release function has been renamed and the counts are layered

How do a TTM buffer object's own reference count and the embedded GEM object's count relate,
what does a driver call to drop its object in this tree, and what happens to an object that is
still busy when the last reference goes? Start from `ttm_bo_init_reserved()` and
`ttm_bo_fini()`.

## drm.ttm-validate: Placement and validation

- section: TTM and allocators
- relevance: 4 - the context flags decide whether a call may block or evict

What does each field of `struct ttm_operation_ctx` change about what `ttm_bo_validate()` may do,
which error codes can come back and which must be passed to user space for a restart, and what
does pinning forbid?

## drm.range-allocators: Range and buddy allocators

- section: TTM and allocators
- relevance: 3 - the buddy allocator has moved and been renamed

Which allocator does the tree offer for which job (an address range, memory in power-of-two
blocks, short-lived sub-allocations), and where does each live and what is it called, where a
reader's memory offers older names? What locking does each expect from the caller? Start from
`include/drm/drm_mm.h`, `include/drm/drm_buddy.h` and `include/drm/drm_suballoc.h`.

# GPU scheduler

## drm.sched-objects: Run queues and scheduling policies

- section: GPU scheduler
- relevance: 4 - the run queue code has been reworked

How many run queues does a scheduler have in this tree, which entity selection policies exist
and which is the default, and where does each part live, where a reader's memory offers an
older layout? Start from `struct drm_sched_init_args` and `drivers/gpu/drm/scheduler/`.

## drm.sched-backend-ops: Backend callbacks

- section: GPU scheduler
- relevance: 5 - reference and context rules are per callback

For each callback in `struct drm_sched_backend_ops`, in what context is it called, what may it
return, and what reference rule applies to a fence it returns? Which are optional?

## drm.sched-job-lifecycle: Job lifecycle

- section: GPU scheduler
- relevance: 5 - the point of no return is where error paths go wrong

After which of `drm_sched_job_init()`, `drm_sched_job_arm()` and `drm_sched_entity_push_job()` can
submission no longer fail or be undone? What must an error path call before and after that point,
and who frees the job? Start from `drm_sched_job_init()`, `drm_sched_job_arm()` and
`drm_sched_job_cleanup()`.

## drm.sched-flow-control: Credits and work queues

- section: GPU scheduler
- relevance: 3 - decides how many jobs are in flight

How do job credits and the scheduler's credit limit bound the jobs in flight, which work queues
does the scheduler use for submission and for timeouts and what does passing NULL for each
select, and what may work on the submission queue not do?

## drm.sched-timeout: Job timeout handling

- section: GPU scheduler
- relevance: 4 - the return values were renamed and one was added

What values can the timeout callback return and what does the scheduler do for each, what
sequence of scheduler calls does recovery follow for a hardware scheduler and for a firmware
scheduler, and which older recovery helpers are deprecated? Start from
`enum drm_gpu_sched_stat` and `drm_sched_stop()`.

## drm.sched-teardown: Scheduler and entity teardown

- section: GPU scheduler
- relevance: 4 - leaked jobs and unsignalled fences on unload

What do flushing, killing, finishing and destroying an entity each do, to choose between them,
and what does `drm_sched_fini()` do about jobs that are still pending or queued, with and
without the cancel callback? What order must teardown follow?

## drm.sched-tests: Mock scheduler timeout handler

- section: GPU scheduler
- relevance: 2 - a handler that can run twice needs flags that survive it

Can the timeout handler in `drivers/gpu/drm/scheduler/tests/mock_scheduler.c` run more than once
for one job while a test waits, and if so what are the requirements for its handling of the job's
flags in order to assure safe usage? Start from
`drivers/gpu/drm/scheduler/tests/mock_scheduler.c`.

# GPUVM

## drm.gpuvm-objects: GPUVM objects

- section: GPUVM
- relevance: 4 - the manager has three object kinds with separate lifetimes

How is each of `struct drm_gpuvm`, `struct drm_gpuva` and `struct drm_gpuvm_bo` reference counted
or owned, and which functions obtain a `struct drm_gpuvm_bo`, where a reader's memory offers
another name? What do the flags in `enum drm_gpuvm_flags` change? Start from `struct drm_gpuvm`,
`struct drm_gpuva` and `struct drm_gpuvm_bo`.

## drm.gpuvm-locking: GPUVM locking

- section: GPUVM
- relevance: 5 - which lock protects the per-object list depends on a flag

Which lock protects the list of mappings hanging off a GEM object and which protect the VM's lists
of external and evicted objects, and how do the flags in `enum drm_gpuvm_flags` change that? What
are the requirements for code that holds the `gpuva.lock` of a `struct drm_gem_object` in order to
assure safe usage? Start from the `gpuva` member of `struct drm_gem_object` and `enum
drm_gpuvm_flags`.

## drm.gpuvm-split-merge: Map and unmap operations

- section: GPUVM
- relevance: 4 - the callbacks may not fail half way

In which ways can a driver consume the map, remap and unmap steps that `drm_gpuvm_sm_map()` and
`drm_gpuvm_sm_unmap()` split a request into? May a step fail once earlier steps have run, and what
must the driver have allocated before the steps run? Start from `drm_gpuvm_sm_map()` and `struct
drm_gpuvm_map_req`.

# amdgpu

## drm.amdgpu-layout: amdgpu layout

- section: amdgpu
- relevance: 4 - the display manager is no longer one file

A table and nothing else, job to directory or file under `drivers/gpu/drm/amd/`: the core
driver; the display core; the display manager, which a reader may remember as one file; power
management; KFD; RAS; the hardware sequencer functions.

## drm.amdgpu-ip-versions: IP and firmware versions

- section: amdgpu
- relevance: 4 - hardware and firmware are versioned separately

What does `amdgpu_ip_version()` leave out of the value it returns? Where is the version of the PSP
firmware held, and how does in-tree code gate a command that only newer firmware understands? Name
such code. Start from `amdgpu_ip_version()` and `drivers/gpu/drm/amd/amdgpu/amdgpu_psp.c`.

## drm.amdgpu-bo-addresses: Buffer object addresses

- section: amdgpu
- relevance: 3 - two helpers return values in different formats

What is the difference between the value `amdgpu_bo_gpu_offset()` returns and the value
`amdgpu_gmc_pd_addr()` returns for a page directory, which does the hardware VM root register
take, and which does the in-tree debugfs file that reports a VM's page directory address print?

## drm.amdgpu-kernel-bo: Kernel buffer objects

- section: amdgpu
- relevance: 4 - the pointer argument is both input and output

What do `amdgpu_bo_create_reserved()` and `amdgpu_bo_create_kernel()` do when the buffer object
pointer they are given already points at something, what must a caller therefore guarantee about
it, and how do the wrappers that allocate buffers for the ISP driver handle that? Start from
`isp_kernel_buffer_alloc()`.

## drm.scaling-mode: Scaling mode property

- section: amdgpu
- relevance: 2 - a default that distorts the picture is a user-visible bug

What does each value of the standard scaling mode connector property do to aspect ratio, how
does amdgpu map them to its own scaling enumeration, and which value does amdgpu choose by itself
when a mode needs scaling and user space asked for none? Start from
`drm_connector_attach_scaling_mode_property()` and `enum amdgpu_rmx_type`.

## drm.amdgpu-ring-fence: Rings and fence sequence numbers

- section: amdgpu
- relevance: 4 - truncation and wrap-around bugs

What are the types of the ring write pointer and of the fence sequence counters in amdgpu, and how
is the fence array indexed? What are the requirements for a loop over outstanding sequence numbers
in order to assure safe usage when the counter wraps? Start from `struct amdgpu_ring`, `struct
amdgpu_fence_driver` and `amdgpu_fence_process()`.

## drm.amdgpu-dc-context: Display core atomic contexts

- section: amdgpu
- relevance: 4 - some display core paths cannot sleep

In the amdgpu display code, what do `DC_FP_START()` and `DC_FP_END()` do to the calling context,
and which handlers run in interrupt context? What are the requirements for a delay in a hardware
sequencer function in order to assure safe usage? Start from `DC_FP_START()` and
`drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm_irq.c`.

# xe

## drm.xe-layout: xe device, tiles and GTs

- section: xe
- relevance: 4 - which accessor can return NULL

Which accessor returns a GT by index in the xe driver, and what does it return for an index with
no GT? Which accessor returns the root tile's primary GT, and which iterator macros skip missing
GTs? Start from `drivers/gpu/drm/xe/xe_device.h`.

## drm.xe-system-runtime-pm: xe system and runtime PM

- section: xe
- relevance: 4 - runtime flags must not steer system resume

Which functions handle system suspend and resume and which handle runtime suspend and resume in
xe, what do the capable and allowed D3cold fields mean and who sets them, and which of the four
paths read them? Start from `drivers/gpu/drm/xe/xe_pm.c`.

## drm.xe-forcewake: xe forcewake

- section: xe
- relevance: 4 - the return value is a reference mask, not an error code

What does `xe_force_wake_get()` return, how must a caller check that the domain it needs woke, and
what does it pass to `xe_force_wake_put()`?

## drm.xe-forcewake-scoped: Scope-based forcewake

- section: xe
- relevance: 4 - a scope-based form releases the reference when the scope ends, and the caller still has to check which domains woke

Which scope-based forms of taking forcewake does xe provide, and how does code that uses one check
that the domain it needs woke? Start from `drivers/gpu/drm/xe/xe_force_wake.h`.

## drm.xe-sriov: xe SR-IOV

- section: xe
- relevance: 4 - a VF cannot reach much of the hardware

How does xe tell whether it runs as a physical function, a virtual function or neither? What are
the requirements for a probe path that touches hardware or a service that a virtual function
cannot reach, in order to assure safe usage? Name in-tree examples. Start from `IS_SRIOV_VF()` and
`drivers/gpu/drm/xe/xe_sriov.c`.

## drm.xe-guc-ct: xe GuC command transport

- section: xe
- relevance: 3 - debug-only state still needs initialising

What are the initialisation stages of the GuC command transport in xe and what may each do? If
debug code in that file saves stack traces, where is the stack depot initialised and under which
configuration option, and what are the requirements for saving a stack trace to the stack depot in
order to assure safe usage? Start from `xe_guc_ct_init_noalloc()` and
`drivers/gpu/drm/xe/xe_guc_ct.c`.

## drm.xe-runtime-pm-usage: xe runtime PM references

- section: xe
- relevance: 4 - the wrong getter deadlocks or warns

Which of xe's runtime PM getters is the right one in which situation, and what scope-based forms
exist? What are the requirements for taking a runtime PM reference inside the runtime suspend or
resume callbacks themselves in order to assure safe usage? Start from
`drivers/gpu/drm/xe/xe_pm.h`.

## drm.xe-pcode: xe pcode mailbox

- section: xe
- relevance: 3 - packed registers need read-modify-write

When xe updates one field of a pcode mailbox value that packs several, such as a power limit with
its enable bit and time window, what are the requirements for the update in order to assure safe
usage, and which lock must the caller hold? Start from `drivers/gpu/drm/xe/xe_pcode.c` and
`drivers/gpu/drm/xe/xe_hwmon.c`.

# Intel display

## drm.intel-display-device: Intel display device

- section: Intel display
- relevance: 4 - one display code base serves two drivers

How is `struct intel_display` allocated, and how is it reached from each of the two drivers that
share the Intel display code? How does display code test for a platform, a subplatform and a
display version? Start from `drivers/gpu/drm/i915/display/intel_display_device.c` and
`to_intel_display()`.

## drm.intel-register-access: Register access functions

- section: Intel display
- relevance: 4 - the display code is shared by two drivers and has register accessors of its own

Which functions does Intel display code use to read a register, to write one and to wait for a
value in one, where a reader's memory offers older names? Start from
`drivers/gpu/drm/i915/display/intel_de.h`.

## drm.intel-platform-ids: Platforms and subplatforms

- section: Intel display
- relevance: 3 - a new device id may need more than a table entry

How is a subplatform declared and matched in the i915 display code and in xe, and what in the
tree decides whether a variant gets its own id macro and subplatform or just more ids in an
existing macro? Give an in-tree example of a subplatform that changes which PHY a port uses.
Start from `include/drm/intel/pciids.h`.

## drm.intel-cx0-phy: CX0 PHY access

- section: Intel display
- relevance: 3 - message bus access needs a wake reference and a set-up step

Does code that reads or writes CX0 PHY registers over the message bus have to be bracketed by
anything, and if so which functions take care of that themselves and which expect the caller to?
Does a C10 PHY need an extra step before its internal registers are accessed? Start from
`drivers/gpu/drm/i915/display/intel_cx0_phy.c`.

# msm

## drm.msm-context-vm: msm address spaces

- section: msm
- relevance: 3 - the per-context VM is created on first use

What can `msm_context_vm()` return on failure, which code reads the context's address space member
directly and why is that safe there, and what does display initialisation do when there is no
IOMMU? Start from `msm_context_vm()` and `msm_kms_init_vm()`.

# Model gaps

## drm.model-gaps: Other mistakes models make

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

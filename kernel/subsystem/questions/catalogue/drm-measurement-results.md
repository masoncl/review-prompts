# What the drm measurement found

Three models were asked the 100 questions in `drm-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against a
mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C. Reader C
is the most current, reader A is a release or so behind it, and reader B is
several releases behind that; which models they were does not matter here. The
hand-written guide was never checked against current sources, so differences
between it and the built guide are expected and are noted below.

Readers A and C describe the mechanisms correctly nearly everywhere and miss
names, layouts and details. Reader B is out of date on whole mechanisms and had
all but one of its 100 answers rewritten by more than 15%, so the build set was
chosen by importance to a reviewer and not only by dropping what readers know.

The hand-written guide has no map of the DRM core at all. It is twenty
driver-specific rules, most of them one fix written up. The measurement set
therefore covers the core as well as those rules, and the build set spends most
of its words on the core.

## What all three readers got wrong

Mostly names and layouts that have moved. Reader B is wrong on nearly all of
these, sometimes in its own way; where only one of readers A and C slipped, the
item says so.

- **The atomic update container has been renamed.** Every reader wrote
  struct drm_atomic_state and drm_atomic_state_alloc(), _get(), _put() and
  _clear(). None of those exists. The tree has `struct drm_atomic_commit`,
  `drm_atomic_commit_alloc()`, `drm_atomic_commit_get()`,
  `drm_atomic_commit_put()`, `drm_atomic_commit_clear()`,
  `drm_atomic_commit_default_clear()` and
  `drm_atomic_commit_default_release()`. The `atomic_state_alloc`,
  `atomic_state_clear` and `atomic_state_free` hooks in
  `struct drm_mode_config_funcs` and the file `drm_atomic_state_helper.c` kept
  their names. Every callback that took the old structure takes the new one.
- **The buddy allocator has left DRM.** It is `struct gpu_buddy` and
  `gpu_buddy_alloc_blocks()` in `drivers/gpu/buddy.c` and
  `include/linux/gpu_buddy.h`, and its KUnit test is
  `drivers/gpu/tests/gpu_buddy_test.c`. `drivers/gpu/drm/drm_buddy.c` holds only
  `drm_buddy_print()` and `drm_buddy_block_print()`. All three readers gave the
  old names and the old test file.
- **The GEM LRU lock moved.** `struct drm_gem_lru` has only `count` and `list`;
  the lock is `gem_lru_mutex` in `struct drm_device`, and `drm_gem_lru_init()`
  takes just the LRU. All three described a lock pointer supplied by the driver.
- **The dma-buf move callback has been renamed.** There is no
  dma_buf_move_notify() and no move_notify. The exporter calls
  `dma_buf_invalidate_mappings()`, and the importer supplies
  `invalidate_mappings` in `struct dma_buf_attach_ops`. Two readers also had a
  non-dynamic importer pinned at attach; it is pinned at map, and only when the
  exporter has a `pin` operation.
- **Names offered that do not exist.** DRIVER_GEM_GPUVA (all three),
  drm_gpuvm_bo_obtain() (the tree has `drm_gpuvm_bo_obtain_locked()` and
  `drm_gpuvm_bo_obtain_prealloc()`), drm_gpusvm_range_get_pages() and
  drm_gpusvm_range_pages_valid() (`drm_gpusvm_get_pages()`,
  `drm_gpusvm_pages_valid()`), drm_for_each_bridge_in_chain_scoped(),
  drm_debugfs_connector_add_file(), update_job_credits as a scheduler callback,
  intel_de_wait_for_set() (`intel_de_wait_for_set_ms()` and `_us()`).
- **The change-handle ioctl is wired to `drm_invalid_op()`.** Two readers said
  `DRM_IOCTL_GEM_CHANGE_HANDLE` works and one that it does not exist.
  `drm_gem_change_handle_ioctl()` is in the tree and cannot be reached.
- **A short DPCD transfer never comes back as a short count.**
  `drm_dp_dpcd_access()` turns it into `-EPROTO`. All three built their unsafe
  usage on a positive count below the size. The real trap is the two families:
  `drm_dp_dpcd_read()` and `drm_dp_dpcd_write()` return a byte count,
  `drm_dp_dpcd_read_data()`, `drm_dp_dpcd_write_data()`,
  `drm_dp_dpcd_read_byte()` and `drm_dp_dpcd_write_byte()` return 0. The probe
  before a native read is at `DP_TRAINING_PATTERN_SET`, and the only reason the
  tree gives is one monitor (the comment in `dpcd_access_needs_probe()`).
- **Bridges.** `struct drm_bridge_funcs` has no non-atomic pre-enable, enable,
  disable or post-disable hooks, so nothing can be mixed; all three said they
  can. `drm_atomic_helper_commit_modeset_enables()` enables the CRTC first and
  then runs bridge pre-enable and enable, and `disable_outputs()` runs bridge
  disable and post-disable before the CRTC disable. Reader C had the CRTC on the
  other side of pre-enable and post-disable, and so did the checker when it
  corrected reader A, which shows how easy this one is to get backwards. For
  HDMI, audio and CEC a second bridge with the same ops bit makes
  `drm_bridge_connector_init()` return `-EBUSY`; "the last bridge wins" holds
  only for detect, HPD, EDID and modes. All three left out
  `of_drm_get_bridge_by_endpoint()` among the functions that return a reference.
- **The scheduler.** Every reader left `sched_rq.c` out of the file list and
  either missed or doubted `DRM_SCHED_POLICY_FAIR`, under which
  `drm_sched_init()` sets `num_rqs` to 1. A NULL `timeout_wq` means
  `system_percpu_wq`; the header comment that says system_wq is stale and two
  readers repeated it. `free_job` is called from four places, not one.
  `cancel_job` is for jobs on the pending list, which have all been run.
- **Non-blocking commits run on `system_dfl_wq`.** Readers A and C said
  system_unbound_wq.
- **debugfs.** There is no add-file helper for a connector or a CRTC. Connectors
  have the `debugfs_init` hook; CRTC files go in `crtc->debugfs_entry` from
  `late_register`.
- **The ioctl error list.** Each reader's list differed from the recommended
  return values section of `Documentation/gpu/drm-uapi.rst`, which gives DRM
  meanings to ENOENT, ENOSPC, EPERM and EACCES, ENODEV, EOPNOTSUPP, ENXIO, EINTR,
  EIO, EINVAL and ENOTTY and to nothing else.
- **`vblank_disable_immediate`** does not switch the interrupt off at the last
  put, as readers A and C had it. `drm_vblank_put()` skips the timer and
  `drm_handle_vblank()` disables at the next vblank.
- **amdgpu.** `amdgpu_bo_create_reserved()` does not pin a buffer object it was
  handed; it reserves, binds and maps it. `amdgpu_ip_version()` masks off the
  low byte. `amdgpu_job_timedout()` tries `amdgpu_device_ip_soft_reset()` before
  full recovery, and some paths block in `down_read()` on the reset semaphore
  where the readers had only the trylock. `dc_fpu_begin()` calls
  `preempt_disable()` itself and warns outside task context.
- **xe.** `d3cold.capable` is set in `xe_pm_probe()`.
  `xe_pm_runtime_get_ioctl()` is used through `ACQUIRE(xe_pm_runtime_ioctl, ...)`
  and nothing is put when it fails. Most resources a VF cannot reach are guarded
  by device flags that `vf_update_device_info()` clears (`probe_display`,
  `skip_pcode`, `skip_guc_pc`, the HECI flags), not by a VF test in the probe
  function. `xe_hwmon_pcode_rmw_power_limit()` takes no lock; its callers do.
  The stack depot is initialised in `ct_dead_init()` under
  `CONFIG_DRM_XE_DEBUG_GUC`.
- **Intel display.** `struct intel_display` is allocated and reached through a
  pointer in both device structures; reader A had it embedded. The register
  wait helpers two readers named do not exist under those names.
- **msm.** `msm_context_vm()` returns NULL on failure and never an error
  pointer, and teardown paths read `ctx->vm` directly on purpose. With no IOMMU
  `msm_kms_init_vm()` returns `ERR_PTR(-ENODEV)` and display initialisation
  fails; there is no VRAM carveout fallback.
- **`ttm_bo_validate()` cannot return `-EDEADLK`** (the walk turns it into
  `-ENOSPC`), and `-ENOSPC` becomes `-ENOMEM` unless
  `TTM_ALLOCATION_PROPAGATE_ENOSPC` is set. A pinned object that would have to
  move gives `-EINVAL`.
- **Device wedging.** Each reader invented prerequisites; the ones in
  `Documentation/gpu/drm-uapi.rst` are to stop DMA to system memory, signal all
  fences, invalidate mappings and reject new ioctls.

## What readers A and B got wrong as well

- **The fence lock.** `struct dma_fence` has a union of `extern_lock` and
  `inline_lock`, reached through `dma_fence_spinlock()`,
  `dma_fence_lock_irqsave()` and `dma_fence_assert_held()`. Passing NULL to
  `dma_fence_init()` selects the inline lock, which is what new code should do.
  Both wrote fence->lock and said the lock must not be NULL. Both forms of the
  sequence number are stored as 64 bits.
- **Fence ops go away.** `dma_fence_signal_timestamp_locked()` sets `ops` to NULL
  unless the ops have `release` or `wait`, the name functions then return
  placeholder strings, and a module must let a grace period pass before it
  unloads. Reader A was unsure; reader B said the pointer is never cleared.
- **The fence signalling rules.** `GFP_NOFS` and `GFP_NOIO` are forbidden as
  well as `GFP_KERNEL`, and waiting on another fence is not what lockdep flags.
- **TTM.** `ttm_bo_put()` still exists but is internal; drivers call
  `ttm_bo_fini()`. `ttm_device_init()` takes `alloc_flags`. Reader A explained
  the placement flags `TTM_PL_FLAG_DESIRED` and `TTM_PL_FLAG_FALLBACK`
  backwards.
- **`drm_gem_is_imported()` tests `import_attach`**, not the dma-buf pointer.
- **GPUVM.** xe does not use `DRM_GPUVM_IMMEDIATE_MODE`, as reader A had it;
  only panthor does. `drm_gpuvm_bo_evict()` asserts the object's reservation
  lock in both modes.
- **Open and close.** `drm_file_free()` calls `drm_events_release()`; the
  handle and syncobj tables are set up by `drm_gem_open()` and
  `drm_syncobj_open()` (the latter an xarray, `syncobj_xa`); the owner is
  updated by `drm_file_update_pid()` unless `was_master` is set. Both readers
  also listed a DRM_UNLOCKED ioctl flag, which is gone.
- **Panels.** `drm_panel_prepare()`, `drm_panel_enable()`, `drm_panel_disable()`
  and `drm_panel_unprepare()` return void. drm_panel_init() is static, so
  `devm_drm_panel_alloc()` is the only way to make a panel; reader C called the
  old way deprecated.
- **Connectors.** Every connector is reference counted, not only the dynamic
  ones, and `drm_connector_dynamic_init()` does not put the connector on the
  list.
- drm_atomic_set_fence_for_plane() is gone; `drm_gem_plane_helper_prepare_fb()`
  assigns the fence itself. `drm_atomic_private_obj_init()` takes no state; it
  calls `atomic_create_state`.
- DP MST, the asynchronous update checks, the plane `begin_fb_access` timing, the
  xe validation guard and the KUnit helper list all needed several corrections.

## What only reader B got wrong

Reader B describes an older DRM:

- A `preclose` driver callback, a drm_sched_main() kernel thread, a NOMINAL
  timeout status, `drm_sched_entity_push_job()` as the point of no return
  (it is `drm_sched_job_arm()`), a delayed-delete list in TTM, busy and
  preferred placement arrays, a negative `madv` as the purgeable mark.
- Reservation objects: page table updates at the kernel level (they are
  bookkeeping), readers and writers waiting on the wrong levels, a seqcount in
  the unlocked iterator.
- Managed resources: the unsafe and the correct use of `devm_` the wrong way
  round, and `devm_drm_dev_alloc()` "wired into unplug".
- The atomic helpers: `drm_atomic_helper_swap_state()` cannot fail, the default
  tail waits for flip done, the runtime PM tail takes a runtime PM reference.
- xe: tiles embedding their GTs, D3cold allowed decided at suspend time, and
  nearly every name in the PM answers.
- amdgpu: an `rptr` ring field, an atomic `sync_seq`, `fsleep()` offered as the
  safe delay.
- Intel: a lane ownership lock around CX0 accesses, which does not exist.

## What only reader C got wrong

- That the helper commit tail is annotated as a fence signalling section. It is
  not; a few drivers annotate their own tail.
- The panic lock in `struct drm_device`; it is `mode_config.panic_lock`.
- That state destroy frees a completion event the driver left in the CRTC
  state. It is leaked; `drm_atomic_helper_commit_hw_done()` only warns.
- xe: an xe_tile_get_gt() accessor, and a primary GT that may be NULL.
- amdgpu: that `isp_kernel_buffer_alloc()` passes its pointer on uncleared (it
  sets it to NULL first), and amdgpu_device_wb_init().
- The dead-code case for a saturated size: an `int` still compares equal to
  `SIZE_MAX`; the dead case is a 32-bit unsigned on a 64-bit build.

## What the readers already knew

Readers A and C: the entry points, the documentation map, the `drmm_` and
`devm_` rule, the two GEM counts and the handle publishing order, the usage
levels of a reservation object, the rules for atomic check, that commit
callbacks may sleep and which paths may not, the modeset lock back-off, the
order of scheduler job calls, the completion event rules in outline, the EDID
functions, client setup, the amdgpu ring and fence types and the wrap-safe loop,
the xe GT accessors, the two xe PM path pairs and which may read the D3cold
flags, the forcewake reference mask, the Wildcat Lake subplatform example.
Reader C also had the fence structure, the many-object locking helper and TTM
essentially right. Reader B had one answer the checker changed by less than
15%.

## Where the hand-written guide is stale

- **Its first section is wrong.** It lists `drm_atomic_helper_commit_tail()` and
  the CRTC, plane and encoder enable, disable and update callbacks as atomic
  context where sleeping is forbidden. They run in process context: the caller's
  for a blocking commit, a work item on `system_dfl_wq` otherwise, and in-tree
  callbacks sleep (`panel_simple_enable()` calls `msleep()`). What may not sleep
  is narrower: vblank and page-flip interrupt handlers, code under
  `event_lock`, the panic callbacks, and in amdgpu the code between
  `DC_FP_START()` and `DC_FP_END()` and the handlers registered at high
  interrupt context. The fix the section was written from, "use udelay rather
  than fsleep" in a DCN20 hardware sequencer function, is one of those.
- It says `amdgpu_bo_create_kernel()` pins a buffer object it is handed. It
  reserves, binds and maps it and does not pin it. The ISP wrapper it warns
  about, `isp_kernel_buffer_alloc()`, now sets the pointer to NULL.
- It presents "requires an IOMMU" as a property of `drm_gpuvm`. The manager has
  no such requirement; it is msm's display VM that fails without one.
- It calls every direct read of `ctx->vm` in msm a bug. Close and teardown paths
  read it and test for NULL on purpose.
- It tells new CX0 PHY code to call `intel_cx0_phy_transaction_begin()` and
  `intel_cx0_phy_transaction_end()`. Both are static, the wake reference is a
  `struct ref_tracker *`, and the C10 step is now
  `intel_c10_msgbus_access_begin()` and `intel_c10_msgbus_access_commit()`.
- It wants `stack_depot_init()` placed in `xe_guc_ct_init_noalloc()`; it is in
  `ct_dead_init()`, which that function calls.
- It tells xe probe functions to start with a VF test. Most in-tree guards are
  device flags cleared for a VF in `vf_update_device_info()`.
- Its table of DPCD registers that change sink state when read has no support
  in the tree. The probe address is `DP_TRAINING_PATTERN_SET`, the tunnel code
  probes `DP_DPCD_REV`, and the only reason given is one monitor.
- Its scaling mode rule is now the code: `dm_encoder_helper_atomic_check()`
  picks `RMX_ASPECT`, and only for eDP and LVDS.
- Wildcat Lake, its example of ids that need a subplatform, has one:
  `pantherlake_wildcatlake`, which `intel_encoder_is_c10phy()` tests.
- Its `REPORT as bugs` lines are instructions to the reviewer, not facts about
  the code; the built guide states the unsafe usage and the correct one.

Its accounts of the xe system and runtime PM split, `xe_device_get_gt()`
returning NULL, the pcode read-modify-write, the amdgpu write pointer width and
fence wrap-around, the PSP firmware version gate, the mock scheduler flags and
`struct_size()` saturation are still right, and those subjects are kept.

## What was left out of the build set

The hand-written guide is 4,973 words, so the build set is 75 of the 100
questions. It keeps every driver subject of the hand-written guide except one,
and gives the rest of its words to the DRM core, which the hand-written guide
did not cover. Left out, by reason:

- Readers A and C answer them: the entry points, the documentation map, the EDID
  functions, client and fbdev setup.
- The compiler or a warning catches the mistake: the driver feature flags,
  private object initialisation, TTM page backing and pool flags, the GPU SVM
  function names, deferred GPUVM cleanup (which warns outside immediate mode).
- Narrow, and the words were needed elsewhere: events to user space, the wedged
  event, the LRU walk and shrinking in TTM, iterating reservation fences, sync
  objects, GPUVM map and unmap steps, mode setting object lifetimes, asynchronous
  plane updates, vblank timers and work, properties and blobs, suspend and
  shutdown, DP MST, the panic screen, amdgpu reset, the xe validation guard.
- `fwnode_create_software_node()`: one fix written up as a rule, not about DRM,
  and every reader that knows the function knows it returns an error pointer.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 240 corrections, 35% rewritten on average
reader B: 309 corrections, 77% rewritten on average
reader C: 199 corrections, 22% rewritten on average

question                            reader A      reader B      reader C
drm.core-files                      24% ( 5)      91% ( 9)      16% ( 2)
drm.entry-points                     0% ( 0)      14% ( 5)      10% ( 1)
drm.docs                            17% ( 1)      36% ( 1)       2% ( 1)
drm.kunit-tests                     52% ( 2)      78% ( 4)      32% ( 3)
drm.device-lifetime                 10% ( 1)      59% ( 3)      12% ( 1)
drm.managed-resources                0% ( 0)      75% ( 1)       0% ( 0)
drm.unplug-usage                    27% ( 1)      70% ( 2)       1% ( 1)
drm.driver-features                  9% ( 1)      63% ( 2)       8% ( 2)
drm.wedged-event                    48% ( 1)      87% ( 2)      19% ( 1)
drm.file-lifetime                   51% ( 4)      68% ( 4)      25% ( 1)
drm.node-types                      72% ( 4)      85% ( 4)      34% ( 3)
drm.ioctl-dispatch                  43% ( 2)      84% ( 3)      37% ( 1)
drm.uapi-rules                      66% ( 3)      86% ( 3)      33% ( 3)
drm.ioctl-errnos                    72% ( 4)      94% ( 2)      48% ( 2)
drm.events                          67% ( 2)      78% ( 4)       0% ( 0)
drm.logging-debugfs                 45% ( 2)      75% ( 4)      48% ( 4)
drm.gem-object-lifetime              0% ( 0)      76% ( 2)      16% ( 1)
drm.gem-handle-usage                 0% ( 0)      88% ( 1)      29% ( 1)
drm.gem-lookup                      51% ( 3)      74% ( 2)      53% ( 1)
drm.gem-object-funcs                 8% ( 1)      26% ( 1)      10% ( 1)
drm.gem-mmap                        58% ( 3)      84% ( 2)      52% ( 3)
drm.gem-shmem                       28% ( 3)      81% ( 4)      16% ( 4)
drm.gem-lru                         52% ( 2)      78% ( 3)      51% ( 3)
drm.prime                           55% ( 2)      83% ( 5)      18% ( 1)
drm.dma-buf-locking                 50% ( 4)      77% ( 5)      31% ( 4)
drm.ttm-bo-lifetime                 44% ( 4)      85% ( 4)       8% ( 1)
drm.ttm-validate                    40% ( 3)      81% ( 2)      12% ( 2)
drm.ttm-lru                         58% ( 2)      89% ( 2)      25% ( 3)
drm.ttm-tt-pool                     44% ( 2)      80% ( 2)      37% ( 1)
drm.range-allocators                23% ( 2)      40% ( 2)      27% ( 2)
drm.fence-structure                 50% ( 4)      79% ( 4)       4% ( 1)
drm.fence-ops-lifetime              65% ( 3)      81% ( 3)      14% ( 1)
drm.fence-signalling-usage          59% ( 4)      81% ( 1)      25% ( 1)
drm.fence-callbacks                 37% ( 3)      67% ( 2)      21% ( 3)
drm.resv-usage                       4% ( 1)      83% ( 4)       6% ( 1)
drm.resv-iteration                  24% ( 2)      75% ( 3)       0% ( 0)
drm.exec-locking                    38% ( 2)      83% ( 3)      10% ( 2)
drm.syncobj                         52% ( 3)      75% ( 3)      28% ( 2)
drm.sched-objects                   31% ( 4)      69% ( 5)      20% ( 3)
drm.sched-job-lifecycle             12% ( 1)      66% ( 2)      35% ( 1)
drm.sched-backend-ops               54% ( 4)      83% ( 3)      20% ( 3)
drm.sched-timeout                   38% ( 2)      88% ( 3)      20% ( 2)
drm.sched-teardown                  37% ( 3)      78% ( 7)      34% ( 3)
drm.sched-flow-control              22% ( 3)      84% ( 3)       1% ( 1)
drm.sched-tests                     58% ( 2)      82% ( 3)      15% ( 1)
drm.gpuvm-objects                   55% ( 5)      76% ( 5)      13% ( 2)
drm.gpuvm-split-merge               30% ( 3)      91% ( 3)      11% ( 1)
drm.gpuvm-locking                   41% ( 5)      89% ( 3)       9% ( 1)
drm.gpuvm-deferred                  55% ( 4)      86% ( 2)      41% ( 2)
drm.gpusvm                          22% ( 3)      79% ( 3)      14% ( 1)
drm.kms-objects                     19% ( 1)      63% ( 6)      17% ( 6)
drm.atomic-update-container         13% ( 1)      68% ( 3)      23% ( 2)
drm.atomic-check-rules               2% ( 1)      81% ( 3)      35% ( 2)
drm.atomic-commit-sequence          46% ( 1)      82% ( 4)       3% ( 1)
drm.atomic-commit-context            5% ( 2)      68% ( 1)      35% ( 2)
drm.atomic-commit-tracking          24% ( 1)      75% ( 3)      16% ( 1)
drm.atomic-state-subclass           45% ( 4)      64% ( 4)      35% ( 4)
drm.private-objects                 23% ( 2)      89% ( 2)      17% ( 2)
drm.modeset-locks                   18% ( 1)      72% ( 2)       1% ( 1)
drm.plane-prepare-fb                43% ( 3)      88% ( 2)       7% ( 1)
drm.async-updates                   67% ( 2)      82% ( 2)      28% ( 1)
drm.vblank-api                      30% ( 1)      85% ( 4)      29% ( 3)
drm.vblank-event-usage              28% ( 3)      88% ( 3)      26% ( 3)
drm.vblank-timers-work              34% ( 3)      84% ( 3)      38% ( 2)
drm.properties-blobs                58% ( 3)      75% ( 3)      49% ( 1)
drm.framebuffers-formats            37% ( 4)      85% ( 3)      43% ( 2)
drm.suspend-shutdown                51% ( 2)      75% ( 3)      52% ( 2)
drm.connector-lifetime              53% ( 4)      87% ( 4)       4% ( 1)
drm.hotplug-probing                 46% ( 3)      90% ( 4)      37% ( 1)
drm.edid                            24% ( 2)      72% ( 2)       6% ( 1)
drm.scaling-mode                    33% ( 2)      70% ( 3)      34% ( 3)
drm.bridge-lifetime                 54% ( 5)      85% ( 5)      22% ( 5)
drm.bridge-chain-order              58% ( 2)      87% ( 3)      29% ( 2)
drm.bridge-connector                38% ( 4)      83% ( 2)      37% ( 4)
drm.panel                           41% ( 2)      85% ( 5)      30% ( 3)
drm.dp-dpcd-access                  62% ( 5)      76% ( 3)      48% ( 4)
drm.dp-mst                          61% ( 5)      84% ( 5)      29% ( 2)
drm.clients-fbdev                   12% ( 2)      88% ( 4)       0% ( 0)
drm.panic-screen                    48% ( 2)      85% ( 3)      17% ( 2)
drm.amdgpu-layout                    9% ( 1)      38% ( 3)      26% ( 5)
drm.amdgpu-ip-versions              30% ( 3)      77% ( 2)       9% ( 1)
drm.amdgpu-kernel-bo                15% ( 1)      86% ( 2)      31% ( 3)
drm.amdgpu-bo-addresses             41% ( 1)      76% ( 2)      32% ( 1)
drm.amdgpu-ring-fence                0% ( 0)      65% ( 5)      24% ( 1)
drm.amdgpu-reset                    39% ( 4)      87% ( 5)      16% ( 2)
drm.amdgpu-dc-context               38% ( 4)      72% ( 3)      24% ( 2)
drm.xe-layout                       12% ( 1)      66% ( 4)      23% ( 3)
drm.xe-system-runtime-pm            18% ( 1)      97% ( 3)      20% ( 2)
drm.xe-runtime-pm-usage             40% ( 3)      82% ( 4)       6% ( 2)
drm.xe-forcewake                    38% ( 1)      78% ( 2)      14% ( 1)
drm.xe-pcode                        53% ( 2)      79% ( 1)      30% ( 1)
drm.xe-sriov                        42% ( 3)      94% ( 2)      47% ( 3)
drm.xe-guc-ct                       29% ( 2)      84% ( 2)      12% ( 3)
drm.xe-bo-vm-locking                48% ( 2)      88% ( 1)      21% ( 5)
drm.intel-display-device            11% ( 2)      73% ( 5)      26% ( 5)
drm.intel-platform-ids              39% ( 3)      81% ( 3)      41% ( 1)
drm.intel-cx0-phy                   29% ( 2)      93% ( 3)      44% ( 5)
drm.msm-context-vm                  55% ( 4)      79% ( 6)      34% ( 2)
drm.size-helpers                    14% ( 2)      72% ( 1)       4% ( 1)
drm.fwnode-errors                   16% ( 0)      63% ( 1)       0% ( 0)
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `drm.resv-iteration`, `drm.gpuvm-split-merge`, `drm.kms-objects`, `drm.edid`.

## Questions reorganised

- Subjects now: device lifetime; files, ioctls and debugfs; mode setting objects and locks; atomic
  commits; bridges, panels and connectors; fences and reservation objects; GEM; TTM and allocators;
  GPU scheduler; GPUVM; amdgpu; xe; Intel display; msm. 81 questions before and after, ids kept.
- Nothing merged or dropped whole. The three driver layout questions open their driver's subject,
  `drm.kunit-tests` is under Where to look and `drm.sched-tests` is with the scheduler.
- Most questions lost a fourth or fifth ask: lists of members, callbacks, helpers and users, and
  order of steps that is not a contract. Sequences that are the contract (`drm.atomic-commit-sequence`,
  `drm.sched-job-lifecycle`, `drm.bridge-chain-order`) stay.

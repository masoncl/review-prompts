# DRM Subsystem

## Main structures

### Objects and how they relate

- First `->state` of a plane, CRTC or connector: `drm_mode_config_reset()`
  calls the `reset` hook if set, otherwise `atomic_create_state`. A driver
  with `atomic_create_state` and no `reset` is complete, as
  `tidss_crtc_funcs` is.
  `drm_mode_config_create_initial_state()` is the variant that calls no
  `reset` hook and also covers private objects.
- There is no struct drm_atomic_helper. The atomic helpers are functions in
  `drivers/gpu/drm/drm_atomic_helper.c` plus the helper vtables in
  `include/drm/drm_modeset_helper_vtables.h`.
- `drm_atomic_helper_check()`: does not check in pipeline order. It runs
  `drm_atomic_helper_check_modeset()` (connectors, encoders, bridges, CRTC
  modes) first, then `drm_atomic_helper_check_planes()`.
- `struct drm_colorop` (`include/drm/drm_colorop.h`): one colour operation on
  one plane, and a mode object (`DRM_MODE_OBJECT_COLOROP`).
  - Colorops chain through `next` into a pipeline;
    `drm_plane_state.color_pipeline` points at the first one of the active
    pipeline.
  - `struct drm_colorop_state` has its own array in
    `struct drm_atomic_commit`.
- `struct drm_mode_object`: base of planes, CRTCs, encoders, connectors,
  colorops, properties, blobs and framebuffers only. `struct drm_bridge`,
  `struct drm_panel` and `struct drm_private_obj` have no object id.
- `struct drm_bridge`: embeds a `struct drm_private_obj` as `base`, and
  `struct drm_bridge_state` embeds a `struct drm_private_state`. Bridge state
  therefore travels in the `private_objs` array of the commit.
  - `drm_bridge_attach()` calls `drm_atomic_private_obj_init()` for every
    bridge; there is no drm_bridge_is_atomic() test and no atomic_reset hook.
  - Allocated only by `devm_drm_bridge_alloc()`.
  - `drm_bridge_add()` (global list) and `drm_bridge_attach()` (encoder chain)
    each hold their own reference.
- `struct drm_minor`: a device has either the accel minor alone, or the
  primary minor plus an optional render minor; see `drm_dev_init()` in
  `drivers/gpu/drm/drm_drv.c`.
  - `DRIVER_COMPUTE_ACCEL` together with `DRIVER_RENDER` or `DRIVER_MODESET`:
    `drm_dev_init()` returns `-EINVAL`.
  - Accel nodes are not under `/dev/dri/`: they use `ACCEL_MAJOR` and the
    devnode "accel/%s", see `drivers/accel/drm_accel.c`.
- Leases: there is no struct drm_lease. A lease is a `struct drm_master` whose
  `lessor` points at the owning master (`include/drm/drm_auth.h`).
- `struct drm_crtc_commit`: progress of one commit on one CRTC (`hw_done`,
  `flip_done`, `cleanup_done`). Plane, CRTC and connector states each hold a
  reference in their `commit` field; later commits wait on it, which is what
  orders nonblocking commits.
- `struct drm_client_dev`: an in-kernel KMS user with its own internal
  `struct drm_file`, opened on the primary minor and kept on
  `drm_device.filelist_internal`. For example the "fbdev" and "drm_log"
  clients in `drivers/gpu/drm/clients/`; search for `drm_client_init()` for
  the rest.
- `struct drm_gpusvm` (`include/drm/drm_gpusvm.h`): mirror of part of a CPU
  `struct mm_struct` into a GPU address space, built from
  `struct drm_gpusvm_notifier` (an MMU interval notifier) holding
  `struct drm_gpusvm_range` entries. Not refcounted; it lives inside the
  driver's VM object. Ranges are refcounted.
- `struct drm_pagemap` (`include/drm/drm_pagemap.h`): refcounted wrapper
  around a `struct dev_pagemap` of device-private memory.
  `struct drm_pagemap_devmem` is one device memory allocation that belongs
  to it.

## Where to look

**Core files**

| Job | Where in this tree | Easy to miss |
|---|---|---|
| Buddy allocator | `drivers/gpu/buddy.c`, `include/linux/gpu_buddy.h`, `CONFIG_GPU_BUDDY` | The API is `struct gpu_buddy`, `gpu_buddy_init()`, `gpu_buddy_alloc_blocks()`. `drivers/gpu/drm/drm_buddy.c` and `include/drm/drm_buddy.h` still exist but hold only `drm_buddy_print()` and `drm_buddy_block_print()`. There is no drm_buddy_init() and no struct drm_buddy. |
| Compute accelerator core | `drivers/accel/drm_accel.c`, `include/drm/drm_accel.h` | No drm_accel.c under `drivers/gpu/drm/`; `drivers/gpu/drm/Makefile` links the file into `drm.o` under `CONFIG_DRM_ACCEL`. |
| Atomic core | `drivers/gpu/drm/drm_atomic.c`, `include/drm/drm_atomic.h` | There is no struct drm_atomic_state here; the type is `struct drm_atomic_commit`, with `drm_atomic_commit_alloc()` and `drm_atomic_commit_put()`. |
| GPU scheduler | `drivers/gpu/drm/scheduler/` | Run-queue code, for example `drm_sched_rq_add_entity()` and `drm_sched_rq_select_entity()`, is defined in `sched_rq.c`; `sched_main.c` and `sched_entity.c` only call it. |
| Locking helper for many buffer objects | `drivers/gpu/drm/drm_exec.c` | `drivers/gpu/drm/ttm/ttm_execbuf_util.c` still exists beside it. |
| Vblank handling | `drivers/gpu/drm/drm_vblank.c`, `drm_vblank_work.c` | `drm_vblank_helper.c` is a third file, built into `drm_kms_helper`, with the vblank-timer and atomic enable/disable helpers. |
| In-kernel clients | `drivers/gpu/drm/drm_client.c` and `drivers/gpu/drm/clients/` | `drm_client_sysrq.c` is built with the other `drm_client` files under `CONFIG_DRM_CLIENT`. |
| Panic screen | `drivers/gpu/drm/drm_panic.c`, `drm_panic_qr.rs` | Drawing primitives are in `drm_draw.c` (`CONFIG_DRM_DRAW`), shared with `clients/drm_log.c`. |
| Rust abstractions | `rust/kernel/drm/` | Includes `gpuvm/` and `gem/shmem.rs`. The buddy binding is outside it, in `rust/kernel/gpu/buddy.rs`. C shims are `rust/helpers/drm.c`, `rust/helpers/drm_gpuvm.c` and `rust/helpers/gpu.c`. `drivers/gpu/drm/nova/` is built from `drivers/gpu/Makefile`, not `drivers/gpu/drm/Makefile`. |

**KUnit tests**

- Buddy allocator tests: `drivers/gpu/tests/gpu_buddy_test.c`, with
  `gpu_random.c` beside it, built by `CONFIG_GPU_BUDDY_KUNIT_TEST`; there is
  no drm_buddy_test.c in `drivers/gpu/drm/tests/`.
- Atomic tests: `drm_atomic_test.c` and `drm_atomic_commit_test.c`; there is
  no drm_atomic_state_test.c.
- `drm_panic_test.c` and `drm_client_modeset_test.c`: not in
  `drivers/gpu/drm/tests/Makefile`; `drm_panic.c` and `drm_client_modeset.c`
  `#include` them, so they can reach static functions. The guard is
  `#ifdef CONFIG_DRM_KUNIT_TEST`, which is false when the option is `m`.
- `CONFIG_DRM_KUNIT_TEST_HELPERS`: has no prompt, so only a `select` turns it
  on, as `CONFIG_DRM_TTM_KUNIT_TEST` does.
- `drm_kunit_helper_alloc_device()`: registers a KUnit-bus device with
  `kunit_device_register()`, not a platform device.
- `__drm_kunit_helper_alloc_drm_device_with_driver()`: also calls
  `drmm_mode_config_init()` and sets `mode_config.funcs` to
  `drm_atomic_helper_check()` and `drm_atomic_helper_commit()`.
- Mock `struct drm_device`: the helpers call neither `drm_dev_register()` nor
  `drm_mode_config_reset()`; a test that needs either calls it itself, as
  `drm_atomic_commit_test.c` does for the reset.
- `drm_kunit_helper_atomic_state_alloc()`: returns
  `struct drm_atomic_commit *`; the KUnit action calls
  `drm_atomic_commit_put()`, so the test must not.
- Acquire context: there is no drm_kunit_helper_acquire_ctx_alloc() or other
  helper for it; a test calls `drm_modeset_acquire_init()`, passes the
  context to `drm_kunit_helper_atomic_state_alloc()`, retries through
  `drm_modeset_backoff()` on `-EDEADLK`, then calls
  `drm_modeset_drop_locks()` and `drm_modeset_acquire_fini()`.
- `drm_kunit_helper_enable_crtc_connector()`: can return `-EDEADLK`; the
  caller owns the retry.
- Encoders and connectors: no helper builds them; tests call
  `drmm_encoder_init()` and `drmm_connector_init()` directly.

**struct_size and array_size overflow**

- Arguments of `size_mul()`, `size_add()` and `size_sub()`: are `size_t`
  parameters, so a `u64` count is truncated on 32-bit before the overflow
  test runs.
- `kmalloc_objs()`, `kzalloc_objs()`, `kvmalloc_objs()`, `kzalloc_flex()` and
  relatives in `include/linux/slab.h`: used for arrays in DRM core, beside
  `kmalloc_array()`; they call `size_mul()` or `struct_size_t()` and hand the
  result, saturated or not, to the allocator.
- `kmalloc_array()` and `kvmalloc_array()`: return NULL from
  `check_mul_overflow()` without calling the allocator.
- **Potentially unsafe usage**: relying on the allocator to reject a size
  built from a count that userspace controls.
  - Unsafe: without `__GFP_NOWARN`, when nothing bounds the count first;
    `__kvmalloc_node_noprof()` in `mm/slub.c` hits `WARN_ON_ONCE()` for a
    size above `INT_MAX`, and `alloc_order_allowed()` in `mm/page_alloc.c`
    hits `WARN_ON_ONCE_GFP()` for an order above `MAX_PAGE_ORDER`.
  - Safe: with `__GFP_NOWARN`, which both tests honour, as `submit_create()`
    in `drivers/gpu/drm/msm/msm_gem_submit.c` does.
- **Potentially unsafe usage**: passing the result to code that rounds it up
  before any size test.
  - Unsafe: through `PAGE_ALIGN()`, `ALIGN()` or `round_up()` when nothing
    bounds the count first; they turn `SIZE_MAX` into 0.
    `drm_gem_shmem_create()`, in `__drm_gem_shmem_create()`, and
    `drm_gem_dma_create()` round their `size` argument this way first.
  - Safe: through `kmalloc_size_roundup()`, which returns a size above
    `KMALLOC_MAX_SIZE` unchanged, as `dma_resv_list_alloc()` in
    `drivers/dma-buf/dma-resv.c` does.
  - Safe: when the count is already bounded, as in `swiotlb_init_remap()` in
    `kernel/dma/swiotlb.c`, which has allocated `nslabs << IO_TLB_SHIFT`
    bytes before it calls `PAGE_ALIGN()` on `array_size()` of `nslabs` slots.
- **Potentially unsafe usage**: passing the result to a sink that is not an
  allocator and then adds to it.
  - Unsafe: when the sink does plain `+` on the length with no bound before
    it; `SIZE_MAX` wraps to a small value.
  - Safe: when the sink bounds the length first, as
    `drm_property_create_blob()` does with `length > INT_MAX -
    sizeof(struct drm_property_blob)`; `drm_plane_add_size_hints_property()`
    passes it `array_size()`.

## Device lifetime

**Device references and release**

- `drm_file_free()`: does not drop the open file's device reference.
  `drm_minor_release()` drops it as the last step of `drm_release()` and
  `drm_release_noglobal()`, so `struct drm_driver.postclose` and
  `drm_lastclose()` still run with the reference held.
- `accel_open()` in `drivers/accel/drm_accel.c`: takes the same reference
  through `drm_minor_acquire()`.
- Open files are not the only holders after unbind: search `drm_dev_get(`; for
  example `drm_gem_dmabuf_export()` holds one until `drm_gem_dmabuf_release()`.
- `devm_drm_dev_alloc()` does not go through `drm_dev_alloc()`. The chain is
  `__devm_drm_dev_alloc()` -> `devm_drm_dev_init()` -> `drm_dev_init()`.
- `drm_dev_alloc()` and `__drm_dev_alloc()`: register no devres action; the
  driver drops the initial reference itself with `drm_dev_put()`.
- `drm_dev_init()` and `devm_drm_dev_init()` are static in
  `drivers/gpu/drm/drm_drv.c`; a driver cannot initialise a
  `struct drm_device` inside memory it allocated itself.
- Container from `__devm_drm_dev_alloc()`: plain `kzalloc()`, not on the
  `drmm_` list. `drm_dev_release()` frees it with
  `kfree(dev->managed.final_kfree)` after `drm_managed_release()` returns, so
  `struct drm_driver.release` and every `drmm_` action may still use fields
  embedded in it.

**Hardware access after unplug**

- `drm_dev_enter()` returning true: `drm_dev_unplug()` has not returned and
  will not before `drm_dev_exit()`. Only what the driver releases after
  `drm_dev_unplug()` returns is protected; anything `remove()` tears down
  before that call is not.
- `drm_dev_unregister()` does not set `dev->unplugged`. In a driver whose
  `remove()` calls only that, `drm_dev_enter()` keeps returning true after
  unbind and no core unplug check fires for files already open.
- `drm_dev_register()` failure: the `err_minors` path calls
  `drm_dev_synchronize_unplug()`, so `drm_dev_enter()` returns false in the
  driver's probe error unwinding.
- `drm_dev_unplug()` sets the flag before `drm_dev_unregister()`. Disable
  callbacks guarded by `drm_dev_enter()` are skipped when
  `drm_atomic_helper_shutdown()` runs afterwards, and the hardware can stay
  on.
- Core entry points with a check; search `drm_dev_enter` and
  `drm_dev_is_unplugged` under `drivers/gpu/drm` for the rest:

  | Entry point | Kind | After unplug |
  |---|---|---|
  | `drm_ioctl()`, `drm_ioctl_kernel()` | point check | `-ENODEV` |
  | `drm_minor_acquire()`, so `drm_open()` and `accel_open()` | point check | `-ENODEV` |
  | `drm_gem_mmap()`, in `drm_gem_object_lookup_at_offset()` | point check | `-ENODEV` |
  | `drm_show_fdinfo()`, including `struct drm_driver.show_fdinfo` | section | prints nothing |
  | `ttm_bo_vm_fault()` | section | calls `ttm_bo_vm_dummy_page()` |

- Point check: `drm_dev_is_unplugged()` leaves the section before it returns.
  The ioctl handler or `mmap` callback runs outside any section and can
  overlap `drm_dev_unplug()`; it needs its own `drm_dev_enter()` around
  hardware access.
- `drm_read()`, `drm_poll()`, `drm_release()` and `drm_file_free()`: no unplug
  check. `struct drm_driver.postclose` runs after unplug.
- There is no drm_mmap in this tree.
- `drivers/gpu/drm/drm_gem_shmem_helper.c`,
  `drivers/gpu/drm/drm_simple_kms_helper.c`, `drivers/gpu/drm/drm_fb_helper.c`,
  `drivers/gpu/drm/drm_sysfs.c` and `drivers/gpu/drm/drm_debugfs.c`: contain no
  `drm_dev_enter()`. fbdev clients, minors and debugfs entries are removed by
  `drm_dev_unregister()`, not guarded.
- There is no mipi_dbi_pipe_update() here. `mipi_dbi_fb_dirty()` has no guard
  of its own; its caller `drm_mipi_dbi_plane_helper_atomic_update()` in
  `drivers/gpu/drm/drm_mipi_dbi.c` takes the section.
- `drm_dev_enter()` says nothing about a bridge whose own device goes away.
  That has a separate flag and SRCU domain: `drm_bridge_enter()`,
  `drm_bridge_exit()`, `drm_bridge_unplug()` in `drivers/gpu/drm/drm_bridge.c`.
- **Potentially unsafe usage**: sleeping inside a `drm_dev_enter()` section
  until the device answers.
  - Unsafe: when nothing wakes the sleeper once the device is gone;
    `synchronize_srcu()` in `drm_dev_synchronize_unplug()` never returns and
    `remove()` hangs.
  - Safe: when `remove()` wakes the waiters before `drm_dev_unplug()` and the
    wait condition tests that, as `virtio_gpu_remove()` does with
    `virtio_gpu_release_vqs()` for the wait in `virtio_gpu_queue_ctrl_sgs()`.

**Managed resources**

- `drm_dev_enter()` protects a `devm_` resource only in a driver that calls
  `drm_dev_unplug()`. `dev->unplugged` is set nowhere else except the
  `drm_dev_register()` error path.
- `devm_drm_dev_init_release()`: only calls `drm_dev_put()`. It is not a
  hardware teardown hook and runs no driver code unless that put is the last.
- Devres is released in reverse order, see `release_nodes()` in
  `drivers/base/devres.c`. Every `devm_` resource acquired on the same device
  after `devm_drm_dev_alloc()` is gone before `struct drm_driver.release` and
  the `drmm_` actions can run.
- `devm_drm_bridge_alloc()` and `devm_drm_panel_alloc()`: the memory is
  `kzalloc()` plus a kref. The devres action only drops one reference, so the
  object is not freed at unbind while `drm_bridge_get()` or `drm_panel_get()`
  holders remain.
- `drm_managed_release()` frees a `drmm_kzalloc()` block before it runs any
  action registered earlier. An action must not touch `drmm_` memory allocated
  after the action was added.
- `drmm_mode_config_init()` is such an earlier action. It runs
  `drm_mode_config_cleanup()`, which calls `->destroy` on every encoder,
  colorop, plane and CRTC still on the lists.
- `drmm_crtc_alloc_with_planes()`, `drmm_crtc_init_with_planes()`,
  `drmm_encoder_alloc()`, `drmm_encoder_init()`,
  `drmm_universal_plane_alloc()` and `drmm_connector_init()`: each registers
  its own cleanup action after it initialises the object; the action unlinks
  the object before `drmm_` memory allocated earlier is freed.
- Those `drmm_` helpers warn when `->destroy` is set. `drm_crtc_init_with_planes()`,
  `drm_encoder_init()`, `drm_universal_plane_init()` and `drm_connector_init()`
  warn when it is not.
- **Potentially unsafe usage**: `drmm_kzalloc()` for a KMS object that is
  initialised with a non-`drmm_` init function.
  - Unsafe: when `drmm_mode_config_init()` was called before the allocation
    and nothing removes the object earlier; `drm_mode_config_cleanup()` then
    calls `->destroy` on freed memory.
  - Safe: allocation made before `drmm_mode_config_init()`, as
    `virtio_gpu_init()` does for the outputs in `struct virtio_gpu_device`;
    `drm_managed_release()` runs the later `drm_mode_config_cleanup()` action
    before it frees the earlier block.
  - Safe: `drmm_kzalloc()` followed by the `drmm_` init function, or the
    `drmm_` alloc helper, as `__drmm_crtc_alloc_with_planes()` does; the
    cleanup action is added after the allocation, so `drm_managed_release()`
    runs it before it frees the block.
  - Safe: object embedded in the `devm_drm_dev_alloc()` container, as
    `gm12u320_usb_probe()` does; `drm_dev_release()` frees the container
    after `drm_managed_release()`.
- Action registered with `data` `NULL`: the callback receives `NULL`, and
  `drmm_release_action()` with `data` `NULL` matches the earliest added
  entry with that function.

## Files, ioctls and debugfs

**Device nodes and authentication**

- `drm_ioctl_permit()` in `drivers/gpu/drm/drm_ioctl.c`: tests `DRM_ROOT_ONLY`,
  `DRM_AUTH`, `DRM_MASTER`, then the render rule; every failure is `-EACCES`.
- Accel node: `drm_is_render_client()` is false for it, so `DRM_RENDER_ALLOW`
  is not needed and `DRM_AUTH` is not waived.
- Accel node and `DRM_MASTER`: the ioctl fails; `drm_open_helper()` calls
  `drm_master_open()` only for primary files, so `is_master` stays false.
- Control node: `DRM_MINOR_CONTROL` is still a value of `enum drm_minor_type`
  in `include/drm/drm_file.h`, but `drm_dev_init()` allocates no such minor.
- `create_compat_control_link()` in `drivers/gpu/drm/drm_drv.c`: adds only a
  sysfs symlink named controlD<n> to the primary minor, for `DRIVER_MODESET`.
- `authenticated`: written only in `drm_file_alloc()` (to
  `capable(CAP_SYS_ADMIN)`), `drm_new_set_master()`, `drm_authmagic()` and
  `drm_mode_create_lease_ioctl()`; nothing clears it, so a file that drops
  master stays authenticated.
- `drm_getmagic()` and `drm_authmagic()`: each uses the calling file's own
  `master->magic_map`, so authentication works only when both files point at
  the same `struct drm_master`; `drm_authmagic()` returns `-EINVAL` for a
  magic that is not in the caller's map.
- `drm_authmagic()`: replaces the entry with NULL, so a magic works once; the
  id is freed in `drm_master_release()`.
- `drm_setmaster_ioctl()`: does not take master from another holder; it
  returns `-EBUSY` while `dev->master` is set and the caller is not the
  current master.
- `drm_master_check_perm()`: passes without `CAP_SYS_ADMIN` only when
  `was_master` is set and the caller's tgid equals `file_priv->pid`.
- Lease owner: not blocked from leased objects; `_drm_lease_held_master()`
  returns true for a master with no `lessor`.
- Double leasing: `drm_lease_create()` returns `ERR_PTR(-EBUSY)` when
  `_drm_has_leased()` finds the object in another lessee.
- Lessee and the lease ioctls: all four are `DRM_MASTER`, which a lessee
  passes while its owner is `dev->master`; `drm_mode_create_lease_ioctl()`
  then returns `-EINVAL` for a lessee; `drm_mode_get_lease_ioctl()` returns
  the caller's own leased ids.
- `drm_mode_revoke_lease_ioctl()`: empties the lessee's `leases`; the lessee
  file stays master and authenticated, but every CRTC, connector and plane
  lookup by that file then fails.
- `drm_lease_revoke()`: is the close path, called from `drm_master_release()`
  for a file with `is_master` on a `DRIVER_MODESET` device.
- Lessee and master switching: both ioctls call `drm_master_check_perm()`
  first; once it passes, `drm_dropmaster_ioctl()` returns `-EINVAL` for a
  master with a `lessor`, and `drm_setmaster_ioctl()` does the same when the
  device has no master.

**File open and close**

- `struct drm_driver` in `include/drm/drm_drv.h`: has `open` and `postclose`
  only; there is no preclose or lastclose member.
- `drm_lastclose()` in `drivers/gpu/drm/drm_file.c`: core-only; calls
  `drm_client_dev_restore()` when `dev->open_count` reaches zero.
- `drm_file_free()` order: `drm_debugfs_clients_remove()`,
  `drm_events_release()`, `drm_fb_release()` and
  `drm_property_destroy_user_blobs()`, `drm_syncobj_release()`,
  `drm_gem_release()`, `drm_master_release()`, `postclose`,
  `drm_prime_destroy_file_private()`, `put_pid()`.
- `drm_events_release()`: frees events not yet read; pending events are only
  unlinked and get `file_priv = NULL`, and `drm_send_event_helper()` frees
  them later.
- Inside `open`: `file->filp` and `file->master` are both NULL;
  `drm_open_helper()` sets them after `drm_file_alloc()` returns.
- `drm_master_open()` failure in `drm_open_helper()`: calls `drm_file_free()`,
  so `postclose` runs although the open syscall fails.
- In-kernel clients: `drm_client_open()` calls `drm_file_alloc()` on
  `dev->primary`, so `open` and `postclose` run for a file whose `filp` stays
  NULL and that sits on `dev->filelist_internal`.
- Lease fds: `drm_mode_create_lease_ioctl()` uses `file_clone_open()`, so the
  driver `open` runs again for the lessee file.
- `drm_file_update_pid()`: called from `drm_ioctl_kernel()`, before
  `drm_ioctl_permit()`; it can sleep in `synchronize_rcu()`.
- `drm_show_fdinfo()`: prints `client_id`, not the pid; `drm_clients_info()`
  in `drivers/gpu/drm/drm_debugfs.c` prints the pid.

**Ioctl dispatch**

- Copy-in: `drm_ioctl()` copies the full user `in_size`, also when it is larger
  than the kernel structure; `ksize` is the largest of the three sizes.
- Longer user structure: the handler sees its own structure at the start of
  `data`; with `IOC_IN` and `IOC_OUT` both set, bytes beyond it are copied
  back unchanged.
- Copy-out: `copy_to_user()` of `out_size` bytes runs whatever
  `drm_ioctl_kernel()` returned, so what a failing handler wrote to `data`
  reaches user space.
- Direction bits: `in_size` or `out_size` becomes 0 unless both the user `cmd`
  and `ioctl->cmd` have `IOC_IN` or `IOC_OUT`; with `in_size` 0 the whole
  buffer is zeroed.
- Unknown ioctl: `-ENOTTY` only when `DRM_IOCTL_TYPE(cmd)` is not
  `DRM_IOCTL_BASE`; a number past the table or an entry with no `func` gives
  `-EINVAL`.
- `DRIVER_LEGACY`: only a value of `enum drm_driver_feature`; `drm_ioctl()`
  has no legacy test and there is no legacy ioctl flag.
- `DRM_ROOT_ONLY`: a plain `capable(CAP_SYS_ADMIN)` test; nothing in the tree
  marks it deprecated.
- `DRM_ROOT_ONLY` kerneldoc in `include/drm/drm_ioctl.h`: names SETMASTER and
  DROPMASTER, but `drm_ioctls[]` gives both flags 0 and the handlers call
  `drm_master_check_perm()`.

**Ioctl error codes**

- `ENOSPC`: out of VRAM or another limited GPU resource used for rendering, as
  opposed to `ENOMEM` for kernel memory; the error-code list in
  `Documentation/gpu/drm-uapi.rst` names no modeset or bandwidth use.
- `EDEADLK`: sometimes used for resource allocation or reservation failures in
  command submission ioctls.
- `ENXIO`: remote failure, either a hardware transaction such as i2c, or a
  dma-buf or fence exporter that lacks a needed feature.
- `EIO`: the GPU died and reset could not recover it; modeset hardware failure
  goes through the "link status" connector property instead.
- `ENOTTY`: "this IOCTL does not exist"; the list says nothing about feature
  probing.
- `ETIME`, `EFAULT`, `EBUSY`, `ENOTTY`: named as keeping their common meaning.
- `ERANGE` and `EAGAIN`: not on the list.
- Interrupted call: the list names `EINTR` only; any ioctl can return it and
  user space restarts with the parameters unchanged.

**New user space interfaces**

- Acked-by: the user-space reviewer should give one on the kernel uAPI patch;
  `Documentation/gpu/drm-uapi.rst` does not ask for a link in the commit.
- Canonical upstream: the user-space patches must be against it, not a vendor
  fork.
- Merge order: the kernel patch goes to drm-next or drm-misc-next before the
  user-space patches land.
- IGT: not named as the user, which must not be a toy or test application;
  IGT testcases are a separate requirement, for cross-driver uAPI, under
  "Testing Requirements for userspace API".
- Structure size: padded to a multiple of 64 bits if the structure holds
  64-bit types.
- Variable-sized array: must not be the last member, because `drm_ioctl()`
  zero-extends; see the DOC comment in `drivers/gpu/drm/drm_ioctl.c`.
- Time values: `__s64` seconds plus `__u64` nanoseconds; the handler rejects
  values that are not normalized.
- Code path that cannot restart: must at least be killable.
- sysfs and debugfs: `Documentation/process/botching-up-ioctls.rst` recommends
  considering them instead of an ioctl; it does not forbid them.
- Driver ioctl number: must lie between `DRM_COMMAND_BASE` and
  `DRM_COMMAND_END`, and its name must start with DRM_IOCTL_.

**Logging and debugfs**

- `_ratelimited` forms: of the macros that are not deprecated, only
  `drm_err_ratelimited()`, `drm_dbg_ratelimited()` and
  `drm_dbg_kms_ratelimited()` exist; info, notice and warn have `_once` forms
  only.
- No device, debug: `include/drm/drm_print.h` deprecates `DRM_DEBUG_KMS()` and
  its siblings in favour of `drm_dbg_kms(NULL, ...)` and so on.
- No device, other levels: `DRM_ERROR()`, `DRM_WARN()`, `DRM_INFO()` and
  `DRM_NOTE()` are deprecated in favour of `pr_err()` and its siblings.
- `DRM_DEV_ERROR()` and `DRM_DEV_INFO()`: deprecated in favour of `drm_err()`
  or `dev_err()`, and `drm_info()` or `dev_info()`.
- `DRM_DEV_DEBUG()`, `DRM_DEV_DEBUG_DRIVER()` and `DRM_DEV_DEBUG_KMS()`:
  deprecated in favour of `drm_dbg_core()`, `drm_dbg()` and `drm_dbg_kms()`.
- `drm_debugfs_add_file()`: creates the file at once under
  `dev->debugfs_root`, which `drm_dev_init()` has already made.
- `drm_debugfs_entry_open()`: returns `-ENODEV` until the minor is registered.
- `drm_debugfs_add_files()`: does not test `driver_features` of `struct
  drm_debugfs_info`; `drm_debugfs_create_files()` tests it for `struct
  drm_info_list`.
- Device directory: named `dev->unique` under dri, or under accel for
  `DRIVER_COMPUTE_ACCEL`; `drm_debugfs_register()` adds a symlink named by
  minor index.
- `debugfs_init` of `struct drm_driver`: not called for the render minor, nor
  for an accel device.
- Connector: `debugfs_init` is called from `drm_debugfs_connector_add()`,
  before `late_register`; there is no drm_debugfs_connector_init() here.
- CRTC: `struct drm_crtc_funcs` has no `debugfs_init`; create files under
  `crtc->debugfs_entry` from `late_register`.
- `drm_crtc_register_all()`: makes `crtc->debugfs_entry` just before it calls
  `late_register`.
- Plane: no `debugfs_init` hook.
- Bridge: `debugfs_init` of `struct drm_bridge_funcs` is called only from
  `drm_bridge_connector_debugfs_init()`, with the connector's directory as
  root.

## Mode setting objects and locks

**Mode object lifetime and lookup**

- Every `struct drm_connector` is reference counted, static ones included:
  `drm_connector_init_only()` in `drivers/gpu/drm/drm_connector.c` always
  installs `drm_connector_free()` as `free_cb`, so a connector returned by
  `drm_connector_lookup()` always needs `drm_connector_put()`.
- Hotplugged connector (DP MST): `drm_connector_dynamic_init()`, then
  `drm_connector_dynamic_register()`; removed with
  `drm_connector_unregister()` then `drm_connector_put()`.
- `drm_connector_init()`, `drm_connector_init_with_ddc()` and
  `drmm_connector_init()` put the connector on `connector_list` at once;
  `drm_connector_dynamic_init()` does not.
- `drm_connector_unregister()` leaves the id in the idr, so a lookup still
  returns the connector until the last reference goes; test with
  `drm_connector_is_unregistered()`.
- `struct drm_colorop` (`DRM_MODE_OBJECT_COLOROP`, `drm_colorop_find()`) is a
  mode object with device lifetime, not reference counted, like planes, CRTCs
  and encoders.
- Device lifetime is enforced by a `WARN_ON()` in `__drm_mode_object_add()` and
  `drm_mode_object_unregister()`: an object without `free_cb` added or removed
  once `dev->registered` is set warns, unless the driver has `load`.
- Lease check in `__drm_mode_object_find()`: `_drm_lease_held()`, not
  `drm_lease_held()`; applied only to the types in
  `drm_mode_object_lease_required()`; passes when `file_priv` is NULL.
- There is no drmm_plane_init() here; the only managed plane helper is
  `drmm_universal_plane_alloc()`.
- `drm_universal_plane_alloc()` is unmanaged: plain `kzalloc()`, the driver
  frees it with `kfree()`.
- **Potentially unsafe usage**: plain `drm_crtc_init_with_planes()`,
  `drm_universal_plane_init()` or `drm_encoder_init()` on memory the driver
  does not `kfree()` itself.
  - Unsafe: when the memory is freed before `drm_mode_config_cleanup()` runs,
    which calls `funcs->destroy` on every object still listed.
  - Safe: object embedded in the structure from `devm_drm_dev_alloc()`, with
    `destroy` set to the cleanup function only, as `gm12u320_usb_probe()` does
    through `drm_simple_display_pipe_init()`; `drm_dev_release()` frees
    `managed.final_kfree` after `drm_managed_release()`.
- **Unsafe usage**: a drmm-initialised object still on its `mode_config` list
  when `drm_mode_config_cleanup()` runs; it calls `funcs->destroy` with no
  NULL check.
  - Safe: `drmm_mode_config_init()` called before the drmm object helper, and
    no direct call of `drm_mode_config_cleanup()`, as `vkms_modeset_init()`
    does; `drm_managed_release()` releases in reverse order, so the object's
    cleanup action unlinks it first.
- **Unsafe usage**: dropping the last reference of a connector made with
  `drmm_connector_init()`; `drm_connector_free()` calls `funcs->destroy`,
  which is NULL.
  - Safe: dropping the last reference of a connector from
    `drm_connector_dynamic_init()`, which returns `-EINVAL` without
    `funcs->destroy`, as `drm_dp_delayed_destroy_port()` does.

**Framebuffers and formats**

- `fb_create` in `struct drm_mode_config_funcs` takes four arguments:
  `dev`, `file_priv`, `const struct drm_format_info *info`,
  `const struct drm_mode_fb_cmd2 *mode_cmd`.
- `drm_get_format_info()` takes `(dev, pixel_format, modifier)`; the core
  passes `r->modifier[0]`, and the `get_format_info` hook gets no `dev`.
- `framebuffer_check()` runs against the info from `drm_get_format_info()`,
  which is the driver's when `get_format_info` returns one, so plane count and
  block sizes are then the driver's.
- `drm_internal_framebuffer_create()` never calls
  `drm_any_plane_has_format()`.
- `drm_gem_fb_init_with_funcs()` calls `drm_any_plane_has_format()`, only when
  `drm_drv_uses_atomic_modeset()`; an `fb_create` that does not go through
  this helper gets no such check from the core.
- There is no allow_fb_modifiers here; the field is
  `mode_config.fb_modifiers_not_supported`.
- `drm_mode_addfb2()` puts the fb on `file_priv->fbs`;
  `drm_internal_framebuffer_create()` does not, and
  `drm_mode_cursor_universal()` calls it directly.
- Pitch check in `framebuffer_check()`: skipped when
  `info->char_per_block[i]` is 0; such a plane is rejected with
  `DRM_FORMAT_MOD_LINEAR` instead.
- Unused planes in `framebuffer_check()`: modifier must always be 0; handle,
  pitch and offset must be 0 only when `DRM_MODE_FB_MODIFIERS` is set.
- Size check in `drm_gem_fb_init_with_funcs()`: object size at least
  `(height - 1) * pitch + drm_format_info_min_pitch() + offset`, with plane
  width and height.
- `drm_gem_fb_init_with_funcs()` ends in `drm_framebuffer_init()`: the fb is
  visible to lookups when it returns.
- `drm_framebuffer_init()`: returns `-EINVAL` with a warning when `fb->dev` is
  not `dev` or `fb->format` is NULL; `drm_helper_mode_fill_fb_struct()` sets
  both.
- `drm_gem_fb_afbc_init()`: reads `afbc_fb->base.obj`, so it runs after
  `drm_gem_fb_init_with_funcs()`; on failure the caller puts the objects.

**Modeset locks**

- Retry order with atomic state: `drm_atomic_commit_clear()`, then
  `drm_modeset_backoff()`, then retry; see `drm_mode_atomic_ioctl()`.
- **Potentially unsafe usage**: returning `-EDEADLK` from a modeset lock call
  without `drm_modeset_backoff()`.
  - Unsafe: in the function that called `drm_modeset_acquire_init()` on the
    context; `drm_modeset_drop_locks()` warns while `ctx->contended` is set,
    and the error leaves the retry loop.
  - Safe: in a function that got the context from its caller; it returns
    `-EDEADLK` unchanged, as `drm_modeset_lock_all_ctx()`,
    `drm_atomic_get_crtc_state()` and `drm_atomic_helper_set_config()` do.
- `drm_modeset_backoff()` can fail only for a context made with
  `DRM_MODESET_ACQUIRE_INTERRUPTIBLE`; then return its error, do not retry.
- `drm_modeset_backoff()` on a context with flags 0: always 0;
  `drm_helper_probe_detect_ctx()` ignores the result.
- `drm_modeset_lock_all()`: handles `-EDEADLK` itself in a backoff loop and
  returns void.
- `drm_modeset_lock_all()` is brittle because its context is stored in
  `mode_config.acquire_ctx` and it takes `mode_config.mutex` first; a nested
  call blocks on that mutex before it reaches `WARN_ON(config->acquire_ctx)`.
- `DRM_MODESET_LOCK_ALL_BEGIN()`: takes `mode_config.mutex` only when
  `drm_drv_uses_atomic_modeset()` is false; `DRM_MODESET_LOCK_ALL_END()`
  releases it under the same test.
- `DRM_MODESET_LOCK_ALL_END()`: leaves `ret` alone unless it is `-EDEADLK`;
  then `ret` becomes the result of `drm_modeset_backoff()`.

**Modeset lock coverage**

- `mode_config.mutex` does not protect the object lists.
- `crtc_list`, `plane_list`, `encoder_list`, `property_list`: no lock, fixed
  once the device is registered.
- `connector_list`: `connector_list_lock`; `fb_list`: `fb_lock`.
- `mode_config.mutex` protects connector probe state: `connector->status`,
  `connector->modes`, `connector->probed_modes`, and use of
  `mode_config.acquire_ctx`.
- Asserts on `mode_config.mutex`: for example `check_connector_changed()` and
  `drm_helper_probe_single_connector_modes()` in
  `drivers/gpu/drm/drm_probe_helper.c`; search `mutex_is_locked(` for the
  rest.
- `connection_mutex` does not cover `connector->status`;
  `check_connector_changed()` writes it after `drm_helper_probe_detect()` has
  dropped `connection_mutex`.
- `drm_modeset_lock_all_ctx()` order: `connection_mutex`, every CRTC, every
  plane, every `struct drm_private_obj`; no `mode_config.mutex`.
- `drm_warn_on_modeset_not_all_locked()`: checks the CRTC locks,
  `connection_mutex` and `mode_config.mutex` only, not plane or private
  object locks.
- `drm_warn_on_modeset_not_all_locked()` after `drm_modeset_lock_all_ctx()`
  alone: warns, because `mode_config.mutex` is not held.
- `drm_modeset_is_locked()`: `ww_mutex_is_locked()`, true when any task holds
  the lock; `drm_modeset_lock_assert_held()` is the lockdep check for the
  caller.
- `struct drm_colorop` state: protected by the owning plane's `mutex`; see
  `drm_atomic_get_colorop_state()`.

## Atomic commits

**Atomic update container**

- The container is `struct drm_atomic_commit`, defined in
  `include/drm/drm_atomic.h`; no struct named drm_atomic_state exists in this
  tree.

| Name from memory | Name in this tree |
|---|---|
| drm_atomic_state_alloc() | `drm_atomic_commit_alloc()` |
| drm_atomic_state_get() | `drm_atomic_commit_get()` |
| drm_atomic_state_put() | `drm_atomic_commit_put()` |
| drm_atomic_state_clear() | `drm_atomic_commit_clear()` |
| drm_atomic_state_init() | `drm_atomic_commit_init()` |
| drm_atomic_state_default_clear() | `drm_atomic_commit_default_clear()` |
| drm_atomic_state_default_release() | `drm_atomic_commit_default_release()` |
| __drm_atomic_state_free() | `__drm_atomic_commit_free()` |

- `drm_atomic_commit()` is a function (check, then commit, blocking); it is
  not a constructor for the struct of the same name.
- `struct drm_crtc_commit` is the per-CRTC completion tracker, not the
  container.
- Not renamed: the hooks `atomic_state_alloc`, `atomic_state_clear` and
  `atomic_state_free`; the iterators such as
  `for_each_oldnew_crtc_in_state()`; `drm_atomic_helper_swap_state()`; the
  back pointer field `state` in each object state; and most variables of the
  container type, which are still called `state`.
- Array entries for planes, CRTCs, connectors and private objects hold `ptr`,
  `state_to_destroy`, `old_state` and `new_state`; only
  `struct __drm_colorops_state` still has a field named `state`.
- `state_to_destroy`: equals `new_state` until
  `drm_atomic_helper_swap_state()`, equals `old_state` after it;
  `drm_atomic_commit_default_clear()` destroys that one.
- Back pointer after swap: `new_state->state` is NULL and `old_state->state`
  points at the container, so a commit hook cannot reach the container through
  a new state.
- During check, `obj->state` of an object in the update is the same pointer as
  its `old_state`; the getters store it under the modeset lock they take.
- `drm_atomic_helper_commit_planes()` reads `crtc->state` itself, in
  `plane_crtc_active()`; when that is valid in commit code is under "Commit
  sequence".

**Commit sequence**

- Async path (`async_update` set): `drm_atomic_helper_prepare_planes()`,
  `drm_atomic_helper_async_commit()`, `drm_atomic_helper_unprepare_planes()`,
  return 0. It runs no setup, no swap and no `commit_tail()`.
- Fence waits: a blocking commit calls `drm_atomic_helper_wait_for_fences()`
  before the swap with `pre_swap` true; `commit_tail()` calls it again for
  every commit with `pre_swap` false.
- Nonblocking commits are queued as `commit_work` on `system_dfl_wq`, not on
  `system_unbound_wq`.
- `drm_atomic_helper_commit_tail()` passes flags 0 to
  `drm_atomic_helper_commit_planes()`; the default tail never passes
  `DRM_PLANE_COMMIT_ACTIVE_ONLY`.
- **Unsafe usage**: dereferencing a new object state after
  `drm_atomic_helper_commit_hw_done()`, through `new_state` in the container
  or through `obj->state`.
  - Unsafe: a later commit only stalls for `hw_done` in
    `drm_atomic_helper_swap_state()`; once it finishes it destroys this
    commit's new states as its own `state_to_destroy`.
  - Safe: before `drm_atomic_helper_commit_hw_done()`, when the swap ran with
    `stall` true, as `plane_crtc_active()` does for
    `drm_atomic_helper_commit_planes()`.
  - Safe: old states at any point of the tail, as
    `drm_atomic_helper_cleanup_planes()` does.
  - Safe: a value copied out before the hook runs, as `commit_tail()` does
    with `new_self_refresh_mask`.
  - Safe: `state->crtcs[i].commit`, which holds its own reference, as
    `drm_atomic_helper_wait_for_flip_done()` does.

**Runtime PM commit tail**

- Order in `drm_atomic_helper_commit_tail_rpm()`: modeset disables, modeset
  enables, then planes with `DRM_PLANE_COMMIT_ACTIVE_ONLY`; planes never run
  first.
- Planes skipped while their CRTC was inactive are not lost:
  `drm_atomic_helper_check_modeset()` calls `drm_atomic_add_affected_planes()`
  for every CRTC that needs a modeset, so their `atomic_update` runs after the
  enable.
- With `DRM_PLANE_COMMIT_ACTIVE_ONLY`, planes on a CRTC that goes inactive in
  the same commit get no `atomic_disable` or `atomic_update`:
  `plane_crtc_active()` reads the CRTC's current state, which is already the
  new one.
- With `DRM_PLANE_COMMIT_ACTIVE_ONLY`, `atomic_begin` and `atomic_flush` are
  skipped as well for a CRTC whose new state is inactive.
- Nothing in the helpers tests which tail a driver uses.

**Commit ordering and completions**

- `drm_atomic_helper_setup_commit()` stores the new commit in
  `new_crtc_state->commit` but does not put it on `crtc->commit_list`;
  `drm_atomic_helper_swap_state()` adds it under `commit_lock`.
- Private object states get no commit: `struct drm_private_state` has no such
  member. A driver orders them itself through `atomic_commit_setup` in
  `struct drm_mode_config_helper_funcs`, as `vc4_atomic_commit_setup()` does.

| Where | Waits for | Result |
|---|---|---|
| `stall_checks()` | `flip_done` of the newest commit on the CRTC | nonblocking: `-EBUSY`; blocking: no wait here |
| `stall_checks()` | `cleanup_done` of the second-newest commit | both modes; interruptible, 10 s; a timeout only logs |
| `drm_atomic_helper_setup_commit()` | `flip_done` of the commit in an old plane or connector state | nonblocking: `-EBUSY` |
| `drm_atomic_helper_swap_state()`, `stall` true | `hw_done` of commits in old CRTC, connector, plane states | interruptible, no timeout |
| `drm_atomic_helper_wait_for_dependencies()` | `hw_done`, then `flip_done`, via `drm_crtc_commit_wait()` | 10 s each; a timeout only logs |

- `flip_done` is completed in `drm_send_event_helper()` in
  `drivers/gpu/drm/drm_file.c` when the event is delivered.
- `fake_commit` (planes and connectors with no CRTC): `hw_done` and
  `flip_done` are completed by `drm_atomic_helper_commit_hw_done()`,
  `cleanup_done` by `drm_atomic_helper_commit_cleanup_done()`.
- An `atomic_commit_tail` hook under `drm_atomic_helper_commit()` must call
  `drm_atomic_helper_commit_hw_done()` and consume every
  `new_crtc_state->event`; `commit_tail()` does the dependency wait before
  the hook and the cleanup_done call after it.
- `drm_atomic_helper_commit_cleanup_done()` takes the commit from
  `old_crtc_state->commit`, which `drm_atomic_helper_commit_hw_done()` fills;
  without hw_done first it hits `WARN_ON(!commit)` or completes an older
  commit.
- **Potentially unsafe usage**: a driver calling
  `drm_atomic_helper_commit_cleanup_done()` itself.
  - Unsafe: from an `atomic_commit_tail` hook; `commit_tail()` calls it again
    after the hook, and each call does `list_del()` on `commit_entry`.
  - Safe: in a driver with its own `atomic_commit` that never enters
    `commit_tail()`, as `nv50_disp_atomic_commit_tail()` does.

**Commits without vblank interrupts**

- `drm_atomic_helper_fake_vblank()` acts only on a CRTC whose new state has
  `no_vblank` set and a non-NULL `event`; it completes `flip_done` only.
- `hw_done` and `cleanup_done` are signalled as for any other commit.
- `no_vblank` is written by `drm_atomic_helper_check_modeset()` for every CRTC
  in the update, on every call: true when `drm_dev_has_vblank()` is false.
- `drm_dev_has_vblank()` is per device, not per CRTC; it is true once
  `drm_vblank_init()` ran.
- **Potentially unsafe usage**: a driver writing `no_vblank` itself.
  - Unsafe: before a call of `drm_atomic_helper_check_modeset()`, which
    overwrites the value.
  - Safe: in a plane or CRTC `atomic_check` hook when no later call of
    `drm_atomic_helper_check_modeset()` follows; `drm_atomic_helper_check()`
    runs these hooks from `drm_atomic_helper_check_planes()` after
    check_modeset, as `vc4_txp_atomic_check()` relies on.
- A driver may send the event itself and set `new_crtc_state->event` to NULL;
  the helper then skips that CRTC.
- A custom `atomic_commit_tail` gets no fake vblank unless it calls
  `drm_atomic_helper_fake_vblank()` before hw_done, as
  `vkms_atomic_commit_tail()` does.
- An event still set at `drm_atomic_helper_commit_hw_done()` trips its
  `WARN_ON(new_crtc_state->event)`; no helper sends the event after that
  point.
- Alternative with `drm_vblank_init()`: the vblank timer helpers in
  `drivers/gpu/drm/drm_vblank_helper.c`; `no_vblank` stays false and
  `drm_crtc_vblank_atomic_flush()` arms or sends the event. In
  `include/drm/drm_vblank_helper.h`, `DRM_CRTC_VBLANK_TIMER_FUNCS` drives
  `drm_crtc_handle_vblank()` from an hrtimer, started by
  `drm_crtc_vblank_start_timer()`, and `DRM_CRTC_HELPER_VBLANK_FUNCS`
  supplies the matching `atomic_enable`, `atomic_disable` and `atomic_flush`.

**Atomic check**

- `allow_modeset` is a field of `struct drm_atomic_commit`, not of
  `struct drm_crtc_state`.
- `drm_atomic_check_only()` enforces it, after the driver's `atomic_check`
  returned 0: `-EINVAL` if any CRTC in the update needs a modeset.
  `drm_atomic_helper_check_modeset()` never tests it.
- `drm_atomic_commit_init()` sets `allow_modeset` true, so in-kernel commits
  allow modesets by default; `page_flip_common()` clears it for the legacy
  page flip.
- `drm_self_refresh_helper_alter_state()`, the last step of
  `drm_atomic_helper_check()`, sets `allow_modeset` true when an old CRTC
  state has `self_refresh_active`.
- `drm_atomic_helper_check()` calls `drm_atomic_helper_check_modeset()` once;
  a driver that sets `mode_changed` later calls it again itself.
- `drm_atomic_helper_check()` does not call
  `drm_atomic_helper_check_plane_state()`; plane `atomic_check` hooks do.
- `drm_atomic_helper_check_modeset()` only sets `mode_changed`,
  `active_changed` and `connectors_changed`; it never clears them, so a flag
  the driver cleared comes back on a second call if the cause remains.
- After `-EDEADLK`, the `contended` field of
  `struct drm_modeset_acquire_ctx` is set; any further `drm_modeset_lock()`
  on that context hits `WARN_ON(ctx->contended)` in `modeset_lock()`.
- `DRM_MODESET_LOCK_ALL_END()` does not call `drm_atomic_commit_clear()`; it
  backs off and jumps back to `DRM_MODESET_LOCK_ALL_BEGIN()`, so the block
  between them runs again from its first line.

**Objects added during check**

- `drm_atomic_check_only()` compares the CRTC mask before and after the
  driver's `atomic_check`; a difference logs at debug level and, with
  `allow_modeset` clear, also triggers `WARN()`.
- Both masks count only CRTCs whose new state has `enable` set; adding a
  disabled CRTC never trips the WARN.
- `drm_atomic_get_plane_state()` and `drm_atomic_get_connector_state()` also
  add the CRTC the object is currently on, so adding a plane or connector of
  another enabled CRTC counts as adding that CRTC.
- `checked` in `struct drm_atomic_commit` is set at the end of a successful
  `drm_atomic_check_only()`; from then on the CRTC, plane, connector and
  private object getters hit `drm_WARN_ON()`, and still proceed.
- `drm_atomic_get_colorop_state()` does not test `checked`.
- `drm_atomic_commit_default_clear()` resets `checked`.
- **Potentially unsafe usage**: adding an object from inside a helper's check
  loop.
  - Unsafe: when the loop already passed that object's index and its
    `atomic_check` hook has to run for this update; the hook never runs.
  - Safe: add before the loop starts, as `drm_atomic_helper_check_modeset()`
    does with `drm_atomic_add_affected_planes()` ahead of
    `drm_atomic_helper_check_planes()`; `for_each_oldnew_plane_in_state()`
    walks the array by index once.
  - Safe: loop again over what was added, as
    `drm_atomic_helper_check_modeset()` does with its second connector loop.
- A private object does not trip the CRTC WARN, and gets no commit ordering
  either: setup and the swap stall cover only CRTC, plane and connector
  states. See `atomic_commit_setup` under "Commit ordering and completions".

**Object state subclassing**

- `atomic_create_state`: hook in `struct drm_crtc_funcs`,
  `struct drm_plane_funcs` and `struct drm_connector_funcs`, an alternative
  to `reset`. It returns a new state; the core assigns `obj->state`.
- Subclassed `atomic_create_state`: allocate the driver struct zeroed, then
  call `__drm_atomic_helper_crtc_state_init()`,
  `__drm_atomic_helper_plane_state_init()` or
  `__drm_atomic_helper_connector_state_init()` on the embedded base; see
  `tidss_crtc_create_state()`.
- `atomic_create_state` failure: `ERR_PTR()`. The callers in
  `drivers/gpu/drm/drm_mode_config.c` test `IS_ERR()` only, so NULL is
  installed as the state. `atomic_duplicate_state` fails with NULL.
- `drm_mode_config_reset()`: calls `reset` when set; otherwise, when
  `atomic_create_state` is set, it destroys the current state with
  `atomic_destroy_state` and installs a new one.
- `drm_mode_config_create_initial_state()`: fills only objects whose `state`
  is NULL and calls no `reset` hook.
- `drm_crtc_vblank_reset()`: `__drm_atomic_helper_crtc_reset()` calls it;
  `__drm_atomic_helper_crtc_state_init()` does not, and
  `drm_mode_config_crtc_create_state()` calls it instead. Both only when
  `drm_dev_has_vblank()`.
- Plane property defaults: there is no __drm_atomic_helper_plane_state_reset()
  here; `__drm_atomic_helper_plane_state_init()` sets them and
  `__drm_atomic_helper_plane_reset()` calls it.
- Base-state fields that the duplicate helper clears instead of taking a
  reference, for example in `__drm_atomic_helper_plane_duplicate_state()`,
  and what the destroy helper does with them:

| Field | Duplicate helper | Destroy helper |
|---|---|---|
| `commit` (CRTC, plane, connector) | sets NULL | `drm_crtc_commit_put()` |
| plane `fence` | sets NULL | `dma_fence_put()` |
| plane `fb_damage_clips` | sets NULL | `drm_property_blob_put()` |
| connector `writeback_job` (not refcounted) | sets NULL | `drm_writeback_cleanup_job()` |

- Connector `hdr_output_metadata`:
  `__drm_atomic_helper_connector_duplicate_state()` takes a reference with
  `drm_property_blob_get()` and
  `__drm_atomic_helper_connector_destroy_state()` drops it with
  `drm_property_blob_put()`.
- `commit` reference: set in `drm_atomic_helper_setup_commit()`, not in
  duplicate.
- **Potentially unsafe usage**: installing a state allocated by a default
  helper, for example `drm_atomic_helper_plane_reset()`, on an object whose
  driver converts the state with `container_of()` to a larger struct.
  - Unsafe: when a hook can read or write a driver field of that state; the
    default helpers allocate `sizeof` the base state only, see
    `kzalloc_obj()` in `drm_atomic_helper_plane_reset()`.
  - Safe: every hook that allocates does so for the driver struct, as
    `tidss_crtc_create_state()` and `tidss_crtc_duplicate_state()` do.
  - Safe: every access to a driver field is behind a test that the default
    state fails, as `virtio_gpu_plane_prepare_fb()` and
    `virtio_gpu_plane_cleanup_fb()` return for a NULL `fb`, which
    `kzalloc_obj()` in `drm_atomic_helper_plane_reset()` leaves NULL.

**Preparing framebuffers**

- `drm_atomic_helper_prepare_planes()`: two passes. `prepare_fb` runs on
  every plane in the commit, then `begin_fb_access` runs on every plane.
- `prepare_fb` failure: `cleanup_fb` on the planes before the failing one;
  no `end_fb_access` call.
- `begin_fb_access` failure: `end_fb_access` on the planes before the
  failing one, then `cleanup_fb` on every plane in the commit.
- Planes whose new state has `fb == NULL`: get all four hooks too; the loops
  have no fb test.
- No `prepare_fb` hook: `drm_gem_plane_helper_prepare_fb()` is called when
  the driver has `DRIVER_GEM`; a `cleanup_fb` without `prepare_fb` hits
  `WARN_ON_ONCE()`.
- `begin_fb_access`: called only from `drm_atomic_helper_prepare_planes()`,
  before the swap, never from the commit tail.
- `end_fb_access` in the tail: last step of
  `drm_atomic_helper_commit_planes()`, after `atomic_flush` and before
  `drm_atomic_helper_commit_hw_done()`.
- `end_fb_access` on abort: `drm_atomic_helper_unprepare_planes()` and the
  failure path of `drm_atomic_helper_prepare_planes()` pass the new state.
- `drm_atomic_helper_commit_planes_on_crtc()`: does not call
  `end_fb_access`.
- Async update (`state->async_update` in `drm_atomic_helper_commit()`):
  prepare, `drm_atomic_helper_async_commit()`, then
  `drm_atomic_helper_unprepare_planes()` at once. `cleanup_fb` gets the
  commit's plane state, into which `atomic_async_update` must have swapped
  the old fb; see the `WARN_ON_ONCE()` in `drm_atomic_helper_async_commit()`.
- Fence storage: there is no drm_atomic_set_fence_for_plane() here;
  `drm_gem_plane_helper_prepare_fb()` writes `state->fence` itself.
- `drm_gem_plane_helper_prepare_fb()` with `state->fence` already set: adds
  only `DMA_RESV_USAGE_KERNEL` fences, chained to the explicit fence.
  Without one it takes `DMA_RESV_USAGE_WRITE` fences.
- `drm_gem_plane_helper_prepare_fb()` errors: `-EINVAL` when a framebuffer
  plane has no GEM object, `-ENOMEM` when the chain allocation or
  `dma_resv_get_singleton()` fails.
- Fence wait on a blocking commit: `drm_atomic_helper_commit()` calls
  `drm_atomic_helper_wait_for_fences()` before the swap, interruptibly; an
  error unprepares the planes and fails the commit. The call in
  `commit_tail()` then finds `fence` already NULL.

**Vblank counting**

- `enable_vblank` and `disable_vblank`: `drivers/gpu/drm/drm_vblank.c` calls
  only the `struct drm_crtc_funcs` hooks; `struct drm_driver` has none.
  Without `enable_vblank`, `__enable_vblank()` returns `-EINVAL`.
- `drm_crtc_vblank_get()` returns `-EINVAL` and takes no reference:
  - without `drm_vblank_init()`
  - after `drm_crtc_vblank_off()` or `drm_crtc_vblank_reset()`, until
    `drm_crtc_vblank_on()`
- CRTC that was never reset or turned off after `drm_vblank_init()`:
  `drm_crtc_vblank_get()` calls `enable_vblank` and can return 0 with the
  CRTC disabled.
- `drm_atomic_helper_commit_crtc_disable()`: after the CRTC disable hook it
  calls `drm_crtc_vblank_get()` and WARNs "driver forgot to call
  drm_crtc_vblank_off()" unless the result is `-EINVAL`.
- `new_crtc_state->self_refresh_active`: the same check WARNs if the get
  fails, so the disable hook must leave vblank on in that case.
- `drm_crtc_vblank_on()`: copies `drm_vblank_offdelay` and
  `dev->vblank_disable_immediate` into `vblank->config`. A later change of
  either takes effect at the next `drm_crtc_vblank_on()`.
- `drm_crtc_vblank_on_config()`: takes a `struct drm_vblank_crtc_config`
  with `offdelay_ms` and `disable_immediate` for one CRTC.
- When the interrupt is switched off after the last
  `drm_crtc_vblank_put()`:

| `offdelay_ms` | `disable_immediate` | What happens |
|---|---|---|
| 0 | either | never; `drm_crtc_vblank_on_config()` also enables it at once |
| < 0 | either | `drm_vblank_put()` calls `vblank_disable_fn()` synchronously |
| > 0 | false | `disable_timer` is armed for `offdelay_ms` |
| > 0 | true | nothing at put; the next `drm_handle_vblank()` that sees refcount 0 disables it after sending events |

- `disable_immediate`: `drivers/gpu/drm/drm_vblank.c` has no check that the
  counter or timestamp is accurate; that is left to the driver.
- `max_vblank_count`: `drm_max_vblank_count()` uses the per-CRTC value if
  non-zero, else `dev->max_vblank_count`.
- Non-zero `max_vblank_count` without `get_vblank_counter`:
  `drm_vblank_no_hw_counter()` WARNs.
- `max_vblank_count` 0 and no usable timestamp (`get_vblank_timestamp`
  fails or `framedur_ns` is 0): `drm_update_vblank_count()` adds 1 per
  interrupt and nothing for the time the interrupt was off.
- `drm_crtc_set_max_vblank_count()`: WARNs if `dev->max_vblank_count` is
  non-zero or if vblank is not off (`inmodeset` clear).

**Vblank reference context**

- `drm_crtc_vblank_put()`: takes no lock itself. Only with
  `offdelay_ms < 0` does the last put run `vblank_disable_fn()`, and with it
  `disable_vblank`, in the caller's context; that path uses
  `spin_lock_irqsave()` and is safe from hard interrupt context.
- `drm_crtc_vblank_get()`: on the first reference it runs the driver's
  `enable_vblank` in the caller's context, under `dev->vbl_lock` and
  `dev->vblank_time_lock`.
- Inside `enable_vblank`, `disable_vblank`, `get_vblank_counter` and
  `get_vblank_timestamp`: `drm_crtc_vblank_get()` must not be called;
  `drm_vblank_get()` takes `dev->vbl_lock`, which `drm_vblank_enable()` and
  `drm_vblank_disable_and_save()` assert is already held. A last
  `drm_crtc_vblank_put()` with `offdelay_ms < 0` takes the same lock in
  `vblank_disable_fn()`.
- Lock order: `dev->event_lock`, then `dev->vbl_lock`, then
  `dev->vblank_time_lock`; see `drm_crtc_vblank_off()`.
- Under `dev->event_lock`: both calls are allowed, as
  `drm_crtc_vblank_atomic_flush()` and `drm_handle_vblank_events()` do.

**Commit callback context**

- `commit_tail()` and `drm_atomic_helper_commit_tail()`: do not call
  `dma_fence_begin_signalling()`, so lockdep does not flag a `GFP_KERNEL`
  allocation in a tail callback on the helper path.
- A driver's own `atomic_commit_tail` can add the annotation, for example
  `komeda_kms_commit_tail()`; callbacks run inside it are then checked.
- `handle_vblank_timeout` in `struct drm_crtc_helper_funcs`: runs from the
  hrtimer callback `drm_vblank_timer_function()`.
- `get_scanout_buffer` and `panic_flush` in `struct drm_plane_helper_funcs`
  (`CONFIG_DRM_PANIC`): run during a panic under `drm_panic_trylock()`, a
  raw spinlock with interrupts off; see `drivers/gpu/drm/drm_panic.c`.
- `get_vblank_timestamp`: also called with no lock held, from
  `drm_crtc_next_vblank_start()`; it still must not sleep because the other
  callers hold `dev->vblank_time_lock`.
- Tail callbacks can be atomic by the driver's own choice: for example
  `vkms_crtc_atomic_begin()` takes a spinlock with `spin_lock_irq()` that
  `vkms_crtc_atomic_flush()` releases, so that driver's plane
  `atomic_update` runs with interrupts off.
- **Potentially unsafe usage**: a synchronous runtime-PM resume, such as
  `pm_runtime_resume_and_get()`, in `enable_vblank`.
  - Unsafe: when the device can be suspended at that point; the resume
    sleeps under `dev->vbl_lock` with interrupts off.
  - Safe: when the device is already `RPM_ACTIVE` whenever vblank can be
    enabled, as in `tidss_crtc_enable_vblank()`:
    `tidss_crtc_atomic_enable()` takes the runtime-PM reference before
    `drm_crtc_vblank_on()` and `tidss_crtc_atomic_disable()` drops it after
    `drm_crtc_vblank_off()`. `might_sleep_if()` in `__pm_runtime_resume()`
    defines the condition.

**Vblank completion events**

- Where the event comes from: user space, for example through
  `prepare_signaling()` in `drivers/gpu/drm/drm_atomic_uapi.c` for events
  and out-fences, or `page_flip_common()` for the legacy page flip; else
  `drm_atomic_helper_setup_commit()` allocates one.
- `drm_atomic_helper_setup_commit()` installs no event when old and new
  CRTC state are both inactive, or on `legacy_cursor_update`; it completes
  `flip_done` at once. `crtc_state->event` can be NULL in the tail.
- After the swap the driver is the only owner:
  `drm_atomic_helper_swap_state()` clears `commit->event`, so state destroy
  no longer frees the event.
- After send or arm the event belongs to the core: `drm_send_event_helper()`
  frees it or moves it to the file's event list.
- **Unsafe usage**: leaving `crtc_state->event` set after sending or arming
  it, on a commit set up by `drm_atomic_helper_setup_commit()`.
  - Safe: set it to NULL before `drm_atomic_helper_commit_hw_done()`, as
    `drm_crtc_vblank_atomic_flush()` does.
    `drm_atomic_helper_commit_hw_done()` has a `WARN_ON()` for it, and
    `__drm_atomic_helper_crtc_destroy_state()` does an extra
    `drm_crtc_commit_put()` when `state->event` is non-NULL and
    `abort_completion` is set.
- `drm_crtc_send_vblank_event()`: the lock is asserted in
  `drm_send_event_helper()`, not in the function itself.
- `drm_crtc_send_vblank_event()` without `drm_vblank_init()`: sends
  sequence 0 and `ktime_get()`.
- `drm_crtc_arm_vblank_event()`: the target is the vblank count at the call
  plus 1; nothing ties it to the hardware latch. An interrupt handled
  between the register write and the arm delays the event by one frame.
- Armed event without a vblank reference: on delivery `drm_vblank_put()`
  either WARNs and returns (count 0) or drops a reference owned by someone
  else.
- Armed events are delivered, and their reference dropped, by
  `drm_handle_vblank_events()` or by `drm_crtc_vblank_off()`.
- `drm_crtc_vblank_off()`: takes `dev->event_lock` itself with
  `spin_lock_irq()`; call it outside the lock and with interrupts enabled,
  and send `crtc->state->event` in a separate locked section.

## Bridges, panels and connectors

**Bridge lifetime**

- Chain iterators: there is no drm_for_each_bridge_in_chain_scoped() here;
  `drm_for_each_bridge_in_chain()` and `drm_for_each_bridge_in_chain_from()`
  in `include/drm/drm_bridge.h` declare the cursor themselves and drop the
  reference on any exit from the loop.
- Both iterators hold `encoder->bridge_chain_mutex` for the whole walk, so the
  body must not start another walk or attach a bridge on the same encoder.
- Lookups, by what the caller gets:

  | Function | Returned bridge |
  |---|---|
  | `of_drm_find_and_get_bridge()` | counted, NULL on failure |
  | `of_drm_get_bridge_by_endpoint()` | counted, `ERR_PTR()` on failure |
  | `of_drm_find_bridge()` | not counted (gets, then puts) |
  | `drm_of_find_panel_or_bridge()` | not counted |
  | `devm_drm_of_get_bridge()` | not counted |
  | `drmm_of_get_bridge()` | not counted |

- `drm_of_find_panel_or_bridge()`: the panel it returns is counted, drop it
  with `drm_panel_put()`; a NULL `panel` argument returns `-EINVAL`.
- `bridge->next_bridge`: `__drm_bridge_free()` puts it after `destroy`, so the
  driver must store a counted reference there and must not put it itself
  unless it also clears or replaces the pointer, as
  `drm_bridge_clear_and_put()` does.
- **Potentially unsafe usage**: storing a looked-up bridge in
  `bridge->next_bridge`.
  - Unsafe: when the pointer came from a lookup that does not count, since
    `__drm_bridge_free()` then drops a reference nobody took.
  - Safe: from `of_drm_find_and_get_bridge()`, as `tpd12s015_probe()` in
    `drivers/gpu/drm/bridge/ti-tpd12s015.c` does.
  - Safe: wrapped in `drm_bridge_get()`, as `imx93_pdfc_bridge_probe()` in
    `drivers/gpu/drm/bridge/imx/imx93-pdfc.c` does for the result of
    `devm_drm_of_get_bridge()`.
- `drm_bridge_add()` and `drm_bridge_attach()` on a bridge without
  `bridge->container`: only `DRM_WARN()`, then they carry on.
- `drm_bridge_attach()`: calls `funcs->atomic_create_state` with no NULL
  test, so every bridge that is attached needs it, with
  `atomic_duplicate_state` and `atomic_destroy_state`.
- `drm_bridge_detach()`: not exported; only `drm_encoder_cleanup()` calls it,
  so the attach reference lasts until the encoder is cleaned up.
- `drm_bridge_remove()`: moves the bridge to `bridge_lingering_list` and
  destroys `hpd_mutex` and `hpd_state_mutex`; a held reference keeps the
  memory, not those mutexes.
- `devm_drm_put_bridge()`: drops the allocation reference early; its
  kerneldoc marks it a temporary workaround, used by
  `drm_panel_bridge_remove()`.

**Bridge access after removal**

- `drm_bridge_enter()`: returns `bool`; the index comes back through its
  `int *idx` argument.
- `drm_bridge_unplug()`: sets `bridge->unplugged`, waits with
  `synchronize_srcu()`, then calls `drm_bridge_remove()`; the driver calls it
  in place of `drm_bridge_remove()`.
- `drm_bridge_remove()` alone never sets `unplugged`, so after it
  `drm_bridge_enter()` still returns true.
- Guarantee inside a section: `drm_bridge_unplug()` has not returned; only
  what the driver releases after that call is still present.
- `drm_bridge_unplug_srcu`: one domain for all bridges, so unplugging one
  bridge waits for the open sections of every bridge.
- The core never enters the guard and never tests `unplugged`: the chain
  helpers and the bridge connector still call the callbacks of an unplugged
  bridge that is attached.
- Each callback, work item and interrupt handler must enter the guard itself;
  see `drivers/gpu/drm/bridge/ti-sn65dsi83.c`, the only user.
- **Unsafe usage**: `devm_drm_bridge_add()` together with
  `drm_bridge_unplug()`; both call `drm_bridge_remove()`, which puts once per
  call for the single get in `drm_bridge_add()`.
  - Safe: `drm_bridge_add()` in probe and `drm_bridge_unplug()` in remove, as
    `sn65dsi83_remove()` does.

**Bridge call order**

- Disable, in `disable_outputs()` in `drivers/gpu/drm/drm_atomic_helper.c`:
  1. `drm_atomic_helper_commit_encoder_bridge_disable()`: bridges
     `atomic_disable`, then the encoder disable
  2. `drm_atomic_helper_commit_encoder_bridge_post_disable()`
  3. `drm_atomic_helper_commit_crtc_disable()`
- Enable, in `drm_atomic_helper_commit_modeset_enables()`:
  1. `drm_atomic_helper_commit_crtc_enable()`
  2. `drm_atomic_helper_commit_encoder_bridge_pre_enable()`
  3. `drm_atomic_helper_commit_encoder_bridge_enable()`: the encoder enable,
     then bridges `atomic_enable`
- Each stage loops over every connector in the commit, or every CRTC for the
  two CRTC stages, before the next stage starts; the order is not per
  encoder.
- The stages are exported, and a driver may order them differently:
  `tidss_atomic_commit_tail()` in `drivers/gpu/drm/tidss/tidss_kms.c` runs
  pre_enable before the CRTC enable and post_disable after the CRTC disable.
- A bridge driver therefore cannot assume the CRTC state in
  `atomic_pre_enable` or `atomic_post_disable`.
- `pre_enable_prev_first` on a bridge: the previous bridge's
  `atomic_pre_enable` runs before this bridge's, and this bridge's
  `atomic_post_disable` runs before the previous bridge's.
- Non-atomic callbacks: `struct drm_bridge_funcs` has no `pre_enable`,
  `enable`, `disable` or `post_disable` member; the chain helpers call only
  the `atomic_` ones, with no fallback.
- `mode_fixup` and `mode_set` are the non-atomic members that remain.
- Atomic callback argument: `struct drm_atomic_commit *`.
- State hooks: there is no atomic_reset member; `atomic_create_state` takes
  its place, see `drm_atomic_helper_bridge_create_state()`.
- `drm_atomic_bridge_chain_pre_enable()`, `drm_atomic_bridge_chain_enable()`,
  `drm_atomic_bridge_chain_disable()` and
  `drm_atomic_bridge_chain_post_disable()` hold `encoder->bridge_chain_mutex`
  while they call the callbacks, so a callback must not walk the chain with
  `drm_for_each_bridge_in_chain()` or attach a bridge to that encoder.

**Bridge connector**

- How `drm_bridge_connector_init()` picks, per op:

  | Op bit | Several bridges set it |
  |---|---|
  | `DRM_BRIDGE_OP_HPD`, `DRM_BRIDGE_OP_DETECT` | last in chain wins |
  | `DRM_BRIDGE_OP_EDID`, `DRM_BRIDGE_OP_MODES` | picked as a pair, see below |
  | `DRM_BRIDGE_OP_HDMI` | second one: `-EBUSY` |
  | `DRM_BRIDGE_OP_HDMI_AUDIO`, `DRM_BRIDGE_OP_DP_AUDIO` | second of either: `-EBUSY` |
  | `DRM_BRIDGE_OP_HDMI_CEC_NOTIFIER`, `DRM_BRIDGE_OP_HDMI_CEC_ADAPTER` | second of either: `-EBUSY` |

- EDID and MODES pair: a later bridge that sets either bit clears both
  earlier picks, so a MODES-only bridge after an EDID bridge leaves no EDID
  bridge.
- CEC: one bridge that sets both CEC bits also gets `-EBUSY`, since both use
  `bridge_hdmi_cec`.
- Connector type: taken from the last bridge in the chain only
  (`drm_bridge_is_last()`); `DRM_MODE_CONNECTOR_Unknown` there returns
  `-EINVAL`.
- `drm_connector_attach_encoder()`: called by `drm_bridge_connector_init()`
  itself.
- `DRM_BRIDGE_OP_HPD`: `hpd_enable` and `hpd_disable` are optional;
  `drm_bridge_hpd_enable()` tests them for NULL.
- `detect`, `edid_read`, `get_modes`: not checked at init and called with no
  NULL test once the op bit is set.
- Infoframes: `struct drm_bridge_funcs` has one write and one clear callback
  per type, for example `hdmi_write_avi_infoframe`.
  - AVI and HDMI pairs: required with `DRM_BRIDGE_OP_HDMI`, else `-EINVAL`.
  - Audio pair: required when the same bridge sets `DRM_BRIDGE_OP_HDMI_AUDIO`.
  - HDR and SPD pairs: required with `DRM_BRIDGE_OP_HDMI_HDR_DRM_INFOFRAME`
    and `DRM_BRIDGE_OP_HDMI_SPD_INFOFRAME`.
- Optional callbacks: `hdmi_tmds_char_rate_valid`, `hdmi_audio_startup`,
  `hdmi_audio_mute_stream`, `hdmi_cec_init` and the `dp_audio_` equivalents.
- Audio ops: `-EINVAL` unless `hdmi_audio_max_i2s_playback_channels` or
  `hdmi_audio_spdif_playback` is set, and unless prepare and shutdown exist.
- `DRM_BRIDGE_OP_HDMI` chain, checked in `drmm_connector_hdmi_init()`:
  - last bridge `type` must be `DRM_MODE_CONNECTOR_HDMIA` or
    `DRM_MODE_CONNECTOR_HDMIB`
  - `vendor` and `product` must be non-NULL and no longer than
    `DRM_CONNECTOR_HDMI_VENDOR_LEN` and `DRM_CONNECTOR_HDMI_PRODUCT_LEN`
  - `supported_formats` must include RGB444; zero is replaced by RGB444 only
  - `connector->ycbcr_420_allowed` must equal the YCbCr 4:2:0 bit of
    `supported_formats`
  - `max_bpc` must be 8, 10 or 12; zero is replaced by 8
- `drm_bridge_add()`: for an HDMI bridge it sets `ycbcr_420_allowed` from
  `supported_formats`, so `ops` and `supported_formats` must be set first.
- EDID with an HDMI bridge: read from `drm_bridge_connector_detect()`, only
  if some bridge sets `DRM_BRIDGE_OP_DETECT`, and from
  `drm_bridge_connector_force()`; `drm_bridge_connector_get_modes()` then
  only adds modes.
- `DRM_BRIDGE_ATTACH_NO_CONNECTOR` absent: bridges that cannot create a
  connector fail attach with `-EINVAL`, for example `anx7625_bridge_attach()`.

**Panel allocation and calls**

- `drm_panel_prepare()`, `drm_panel_enable()`, `drm_panel_disable()`,
  `drm_panel_unprepare()`: return `void`; a callback failure is not reported
  to the caller.
- NULL panel: the four calls return silently.
- `drm_panel_init()`: `static` in `drivers/gpu/drm/drm_panel.c`; drivers
  cannot call it, `devm_drm_panel_alloc()` is the only way to initialise.
- Double call: skipped with `dev_warn()` in all four; the test of
  `prepared`/`enabled` runs before `follower_lock` is taken.
- `unprepare` or `disable` callback fails: the flag stays true, so the next
  prepare or enable is skipped; the followers were already called, and in
  `drm_panel_disable()` the backlight was already turned off.
- `enable` callback fails: backlight is not enabled.

**Panel followers**

- `struct drm_panel_follower_funcs`: has `panel_prepared`,
  `panel_unpreparing`, `panel_enabled` and `panel_disabling`; each is
  optional.
- `panel_enabled`: runs in `drm_panel_enable()` after the `enable` callback
  and after `backlight_enable()`.
- `panel_disabling`: runs in `drm_panel_disable()` before
  `backlight_disable()` and before the `disable` callback.
- `drm_panel_add_follower()` on a prepared or enabled panel: calls
  `panel_prepared` if the panel is prepared, then `panel_enabled` if it is
  enabled, and returns 0 even if they fail.
- `drm_panel_add_follower()`: keeps a panel reference and a device reference
  until `drm_panel_remove_follower()`.

**Connector lifetime**

- `drm_connector_put()` dropping the last reference: calls `funcs->destroy`
  at once, in the caller's context.
- `connector_free_work`: used only when the list iterator drops the last
  reference, since it puts under `connector_list_lock`.
- Static connectors with `destroy`: `drm_mode_config_cleanup()` drops their
  initial reference with `drm_connector_put()`; an extra reference leaves
  them on the list and triggers the "leaked" error.
- `drmm_connector_init()` connectors: `drm_connector_cleanup_action()` cleans
  them up at device release whatever the count; a reference does not keep
  them alive.
- `drm_connector_dynamic_init()`: takes a fifth `ddc` argument and returns
  `-EINVAL` without `funcs->destroy`, so it cannot be combined with drmm.
- `drm_connector_register()`: returns 0 and does nothing before the device is
  registered; it acts only in `DRM_CONNECTOR_INITIALIZING`, so an
  unregistered connector cannot be registered again.
- `drm_connector_unregister()`: leaves the connector on
  `mode_config.connector_list`; only `drm_connector_cleanup()` removes it.
- List iterator: skips only connectors whose count is zero, so it returns
  unregistered ones; test with `drm_connector_is_unregistered()`.
- **Potentially unsafe usage**: walking `mode_config.connector_list` with
  `list_for_each_entry()`.
  - Unsafe: while another task can run `drm_connector_dynamic_register()` or
    `drm_connector_cleanup()`, which change the list under
    `connector_list_lock` only.
  - Safe: with `connector_list_lock` held, as
    `drm_helper_move_panel_connectors_to_head()` does around its
    `list_for_each_entry_safe()`.
  - Safe: with `drm_connector_list_iter_begin()`,
    `drm_for_each_connector_iter()` and `drm_connector_list_iter_end()`.
  - Safe: on the commit path of a driver that has no dynamic connectors, as
    `omap_encoder_mode_set()` does; the list then changes only when
    connectors are initialised or cleaned up.

**Detection and hotplug**

- `drm_connector_helper_hpd_irq_event()`: one connector;
  `drm_helper_hpd_irq_event()`: all with `DRM_CONNECTOR_POLL_HPD`. Both run
  detect.
- `drm_kms_helper_connector_hotplug_event()` and
  `drm_kms_helper_hotplug_event()`: only send the event, no detect.
- `drm_helper_hpd_irq_event()`: returns false and does nothing unless
  `mode_config.poll_enabled`, which `drm_kms_helper_poll_init()` sets.
- `drm_connector_helper_hpd_irq_event()`: has no `poll_enabled` test.
- Locks: both hpd helpers and the poll worker hold `mode_config.mutex`, and
  `drm_helper_probe_detect()` takes `connection_mutex` on every path.
- A detect callback therefore must not take `mode_config.mutex` or call the
  hpd helpers.
- Both hpd helpers and the poll worker call detect with `force` false;
  `drm_helper_probe_single_connector_modes()` passes true.
- `drm_helper_probe_detect()` with a ctx: returns `-EDEADLK` to the caller
  without retrying and does not write `connector->status`.
- `drm_helper_probe_detect()` with NULL ctx: retries `-EDEADLK` itself.
- `drm_connector_set_link_status_property()`: takes `connection_mutex`
  itself and sends no event; the driver sends the hotplug event.
- Link status back to GOOD: the kernel resets it only in
  `update_output_state()` in `drivers/gpu/drm/drm_atomic.c`, which
  `__drm_atomic_helper_set_config()` calls for legacy SETCRTC and for
  in-kernel clients.
- Atomic user space must write the property; the kernel accepts only a change
  away from BAD, see `drivers/gpu/drm/drm_atomic_uapi.c`.

**EDID handling**

- There is no drm_do_get_edid() here; `_drm_do_get_edid()` is static and
  `drm_edid_read_custom()` is the exported form.
- Still defined and usable on raw `struct edid`: `drm_get_edid()`,
  `drm_get_edid_switcheroo()`, `drm_edid_duplicate()`,
  `drm_add_edid_modes()`, `drm_connector_update_edid_property()`,
  `drm_edid_is_valid()`, `drm_detect_hdmi_monitor()`,
  `drm_detect_monitor_audio()`.
- Kerneldoc marks only `drm_add_edid_modes()` and
  `drm_connector_update_edid_property()` as deprecated.
- `drm_edid_read()`: warns and returns NULL when `connector->ddc` is NULL.
- `drm_edid_read_ddc()`: returns NULL before looking at override or firmware
  EDID when the connector is not forced and `drm_probe_ddc()` fails.
- That case is covered by `drm_edid_override_connector_update()`, called from
  `drm_helper_probe_get_modes()` when `get_modes` returned 0 and the
  connector status is connected.
- `drm_edid_read_custom()`: does not test `connector->force` and does not
  probe.
- `drm_edid_connector_update()`: copies the bytes into
  `connector->edid_blob_ptr`; the connector keeps no pointer to the
  `struct drm_edid` passed in.
- `drm_edid_connector_add_modes()`: parses that blob again.

**DPCD access**

- `drm_dp_dpcd_read()`: returns `size` or a negative errno, never a smaller
  positive count.
- Short transfer on a local aux: `drm_dp_dpcd_access()` turns it into
  `-EPROTO` and retries, up to 32 tries.
- Short read on a remote aux: `drm_dp_send_dpcd_read()` returns `-EPROTO`.
- `drm_dp_dpcd_write()` on a local aux: same, `size` or negative.
- Error returned after the retries: the first one seen, not the last.
- `aux->powered_down`: `-EBUSY` at once, no transfer; set by
  `drm_dp_dpcd_set_powered()`.
- Probe: on a local aux `drm_dp_dpcd_read()` reads one byte at
  `DP_TRAINING_PATTERN_SET` before every read, not only the first; a remote
  aux (`is_remote`) is never probed.
- Probe failure: `drm_dp_dpcd_read()` returns that error without the real
  read.
- Probe is on by default; `drm_dp_dpcd_set_probe()` with false turns it off
  for one aux.
- `drm_dp_dpcd_read_data()`: after any negative result it reads again byte by
  byte with `drm_dp_dpcd_readb()` and returns 0 if every byte succeeds.
- `drm_dp_dpcd_write_data()`: no such fallback.

## Fences and reservation objects

**Fence structure and lock**

- `struct dma_fence` has no member named lock: it holds an anonymous union
  of `extern_lock` (`spinlock_t *`) and `inline_lock` (`spinlock_t`);
  `DMA_FENCE_FLAG_INLINE_LOCK_BIT` in `flags` says which one is valid.
- `dma_fence_spinlock()` in `include/linux/dma-fence.h` returns the right
  lock; `dma_fence_lock_irqsave()`, `dma_fence_unlock_irqrestore()` and
  `dma_fence_assert_held()` wrap it.
- Kerneldoc in `include/linux/dma-fence.h` and `drivers/dma-buf/dma-fence.c`
  still writes `&dma_fence.lock`; it means the lock `dma_fence_spinlock()`
  returns.
- `lock` argument NULL to `dma_fence_init()` or `dma_fence_init64()`:
  `__dma_fence_init()` initialises `inline_lock` and sets
  `DMA_FENCE_FLAG_INLINE_LOCK_BIT`.
- `ops` NULL, or `ops` without `get_driver_name` or `get_timeline_name`:
  `BUG_ON()` in `__dma_fence_init()`.
- Non-NULL `lock`: its memory must stay valid until the last reference to the
  fence is dropped, not only until the fence signals; the core locks signalled
  fences too, for example in `dma_fence_remove_callback()` and
  `dma_fence_get_status()`.
- **Potentially unsafe usage**: reading `fence->extern_lock` directly.
  - Unsafe: on a fence initialised with a NULL lock; the union then holds the
    spinlock itself, so the value read is not a pointer.
  - Safe: where every fence of that ops table is initialised with a non-NULL
    lock, as `dma_fence_parent()` in `drivers/dma-buf/sync_debug.h` relies on;
    `dma_fence_spinlock()` defines which member is valid.
- Inline locks all share one lockdep class, from the `spin_lock_init()` in
  `__dma_fence_init()`; code that holds one fence's lock while taking another
  fence's lock needs its own class, as `dma_fence_array_init()` and
  `dma_fence_chain_init()` set with `lockdep_set_class()`.
- `seqno` is stored as `u64` by both init functions; only the comparison in
  `__dma_fence_is_later()` differs.

**Fence ops and module unload**

- `dma_fence_signal_timestamp_locked()`: sets `fence->ops` to NULL only when
  the ops table has neither `release` nor `wait`; otherwise the pointer stays
  for the life of the fence.
- The clearing happens before the callback list is run, so a `dma_fence_cb`
  callback can already see `fence->ops` as NULL.
- `fence->ops` is `__rcu`: read it with `rcu_dereference()` under
  `rcu_read_lock()` and handle NULL; `rcu_access_pointer()` only to compare.
- **Potentially unsafe usage**: dereferencing `fence->ops`, or testing a
  fence's type by comparing `fence->ops` with an ops table, without a NULL
  check.
  - Unsafe: when the ops table sets neither `release` nor `wait` and the fence
    may have signalled; the pointer is NULL, so the dereference faults and the
    comparison is false for a fence of that type.
  - Safe: when the ops table sets `release` or `wait`, as
    `dma_fence_is_array()` relies on for `dma_fence_array_ops`; the test in
    `dma_fence_signal_timestamp_locked()` defines this.
  - Safe: under the fence lock before the pointer is cleared, as the
    `trace_dma_fence_signaled()` call in
    `dma_fence_signal_timestamp_locked()`; its event class `dma_fence_ops` in
    `include/trace/events/dma_fence.h` dereferences `fence->ops` directly.
- `dma_fence_driver_name()` and `dma_fence_timeline_name()`: do not take
  `rcu_read_lock()`; the caller must hold it across the call and every use of
  the string.
- Return type of both is `const char __rcu *`; pass it through
  `rcu_dereference()` to use it, as `sync_file_get_name()` in
  `drivers/dma-buf/sync_file.c` does.
- Missing `rcu_read_lock()` around the name helpers: caught only by
  `rcu_dereference()`, under `CONFIG_PROVE_RCU`.
- Placeholder strings are `"detached-driver"` and `"signaled-timeline"`; both
  helpers return them whenever the signalled bit is set, also for a fence
  whose ops stay attached.
- Module reference: the core takes none for fence ops; nothing stops an
  unload while fences exist.
- Ops with `release` or `wait`: the module must stay loaded until every such
  fence has been freed, not only signalled.
- External lock: see "Fence structure and lock"; a lock in driver memory keeps
  the driver tied to the fence until the fence is freed.

**Fence callbacks after signalling**

- `wait` on a signalled fence: still called; `dma_fence_wait_timeout()` makes
  no signalled test before `ops->wait`, and calls it after
  `rcu_read_unlock()`.
- Every other callback except `release`, on a fence whose ops stay attached:
  the core tests the signalled bit first and does not call it; see
  `dma_fence_driver_name()`, `__dma_fence_enable_signaling()`,
  `dma_fence_is_signaled()` and `dma_fence_set_deadline()`.
- Exception: `trace_dma_fence_signaled()` in
  `dma_fence_signal_timestamp_locked()`, when that tracepoint is enabled,
  calls `get_driver_name` and `get_timeline_name` right after the signalled
  bit is set, still inside the signalling call.
- There are no fence_value_str or timeline_value_str members in
  `struct dma_fence_ops` here.
- Ops without `release`: `dma_fence_release()` calls `dma_fence_free()`, which
  is `kfree_rcu()` on the `struct dma_fence` pointer, so that pointer must be
  the start of the allocation, as in `drm_crtc_create_fence()`.

**Callbacks and enable signalling**

- `dma_fence_add_callback()` returning `-EINVAL`: NULL `fence` or NULL
  `func`, with a `WARN_ON()`.
- `cb->node`: initialised on `-ENOENT`, not on `-EINVAL`; only after
  `-ENOENT` or success is a later `dma_fence_remove_callback()` defined.
- `-ENOENT` is also returned when `enable_signaling` returns false during
  this call; the core then signals the fence inside
  `dma_fence_add_callback()`, and callbacks other users installed run in the
  caller's context.
- When a callback runs: the signalled bit is set, `fence->cb_list` is already
  overwritten by `timestamp`, and `fence->ops` may be NULL.
- `cb->node` is re-initialised before `func` is called, so `func` may free or
  reuse the structure that embeds `cb`.
- **Unsafe usage**: from a callback, calling a function that takes the fence
  lock (`dma_fence_remove_callback()`, `dma_fence_signal()`,
  `dma_fence_get_status()`, `dma_fence_enable_signaling()`) on the signalling
  fence, or one of those or `dma_fence_add_callback()` on another fence
  initialised with the same external lock.
  - Safe: queue an `irq_work` and do it there, as `dma_fence_chain_cb()`
    does; `dma_fence_spinlock()` shows which fences share a lock.
- Reference taken in `enable_signaling`: the core never drops it;
  `dma_fence_signal()` puts nothing. The driver's signalling path must drop
  it, as `dma_fence_array_cb_func()` and `irq_dma_fence_array_work()` do for
  the references `dma_fence_array_enable_signaling()` takes.

**Reservation object usage levels**

- `dma_resv_usage_rw()`: gives the level to query or wait on, not the level
  to add at; a writer adds at `DMA_RESV_USAGE_WRITE` and waits on
  `dma_resv_usage_rw(true)`, which is `DMA_RESV_USAGE_READ`. Compare
  `dma_buf_import_sync_file()` and `dma_buf_export_sync_file()` in
  `drivers/dma-buf/dma-buf.c`.
- `dma_resv_reserve_fences()`: returns `-ENOMEM` when it cannot allocate.
- `dma_resv_reserve_fences()` with `num_fences` 0: `WARN_ON()` and
  `-EINVAL`.
- `dma_resv_add_fence()` with no free slot: `BUG_ON()`; on an object that
  never had `dma_resv_reserve_fences()` called, it dereferences a NULL list.
- Reserved slots after `dma_resv_unlock()`: dropped only under
  `CONFIG_DEBUG_MUTEXES`, by `dma_resv_reset_max_fences()`; code must reserve
  again after every relock to pass that check.
- `dma_resv_add_fence()` reuses a slot instead of taking a new one when the
  old fence has signalled, or when it has the same context, the new fence is
  later or the same, and the old usage is equal or weaker (`old_usage >=
  usage`).
- Same context with a weaker new usage: no replacement; both fences stay and
  a reserved slot is consumed.

**Iterating reservation fences**

- `dma_resv_for_each_fence()`: returns signalled fences too; it filters by
  usage only, see `dma_resv_iter_next()`.
- `dma_resv_for_each_fence_unlocked()`: skips signalled fences, see
  `dma_resv_iter_walk_unlocked()`.
- Unlocked restart: happens only when `obj->fences` points to another list
  (after `dma_resv_reserve_fences()` reallocates or `dma_resv_copy_fences()`
  replaces it) or when `dma_fence_get_rcu()` fails on an entry.
- A fence that `dma_resv_add_fence()` writes into an already reserved slot
  during an unlocked walk: no restart, and the walk may miss it; the result is
  not a snapshot.
- `dma_resv_iter_is_restarted()`: true for the first fence of every walk,
  locked or unlocked; `dma_resv_get_fences()` uses that branch to allocate as
  well as to reset.
- Unlocked loop body: runs with a reference on the current fence and without
  the RCU read lock, which is held only inside
  `dma_resv_iter_first_unlocked()` and `dma_resv_iter_next_unlocked()`; the
  body may sleep, as in `dma_resv_wait_timeout()`.
- `dma_resv_describe()`: uses the locked iterator, so it needs the lock held,
  and it lists fences up to `DMA_RESV_USAGE_READ` only.

**dma-buf locking convention**

- There is no dma_buf_move_notify() and no move_notify member here; the
  exporter calls `dma_buf_invalidate_mappings()` with the reservation lock
  held (asserted), and the importer supplies `invalidate_mappings` in
  `struct dma_buf_attach_ops`.
- Driver functions keep the old word in their names, for example
  `amdgpu_dma_buf_move_notify()` is installed as `.invalidate_mappings`.
- There is no CONFIG_DMABUF_MOVE_NOTIFY; `dma_buf_pin_on_map()` is true when
  the exporter has a `pin` op and the attachment has no `importer_ops`.
- Dynamic means `importer_ops` is non-NULL, even when `invalidate_mappings`
  is NULL; `dma_buf_attach_revocable()` tests for the callback itself.
- `dma_buf_attachment_is_dynamic()` is `static` in
  `drivers/dma-buf/dma-buf.c`; drivers cannot call it.
- Lock rule for `dma_buf_map_attachment()`, `dma_buf_unmap_attachment()`,
  `dma_buf_vmap()` and `dma_buf_vunmap()`: applies to every importer, dynamic
  or not; each asserts the lock unconditionally.
- `dma_buf_pin()` and `dma_buf_unpin()`: `WARN_ON()` for a non-dynamic
  attachment.
- Non-dynamic importer: the core calls the exporter's `pin` in
  `dma_buf_map_attachment()` and `unpin` in `dma_buf_unmap_attachment()`, not
  at attach time; the `pin` kerneldoc in `include/linux/dma-buf.h` says
  otherwise.
- The core caches no sg_table: `struct dma_buf_attachment` has no member for
  one, and each map call reaches `map_dma_buf`.
- Non-dynamic importer: `dma_buf_map_attachment()` waits interruptibly for the
  `DMA_RESV_USAGE_KERNEL` fences before it returns; a dynamic importer gets no
  wait and must wait itself.
- `dma_buf_dynamic_attach()` and `dma_buf_detach()`: take the lock only around
  the attachment list update; the exporter's `attach` and `detach` run outside
  it.
- `dma_buf_begin_cpu_access()` and `dma_buf_end_cpu_access()`: only
  `might_lock()` the reservation lock; they do not take it.

**Fence signalling path**

- **Unsafe usage**: between making a fence visible and signalling it, taking
  a lock that `dma_resv_lockdep()` in `drivers/dma-buf/dma-resv.c` holds when
  it calls `__dma_fence_might_wait()`: `mmap_lock`, any `struct dma_resv`
  lock, or entering reclaim through an allocation.
  - Safe: allocate before the fence is visible and only initialise inside the
    section, as `dma_fence_array_alloc()` followed by
    `dma_fence_array_init()` allows.
  - Safe: an allocation mask without `__GFP_DIRECT_RECLAIM`, with the failure
    handled, as `xe_guc_log_snapshot_alloc()` does with `GFP_ATOMIC` when
    `devcoredump_snapshot()` reaches it inside the section;
    `__need_reclaim()` in `mm/page_alloc.c` defines this.
- Any `struct dma_resv` lock is covered, not only one held across an
  allocation: all share `reservation_ww_class`.
- `GFP_NOFS` and `GFP_NOIO` are forbidden too: under `CONFIG_MMU_NOTIFIER`
  `fs_reclaim_acquire()` takes `__mmu_notifier_invalidate_range_start_map`
  whenever `__need_reclaim()` is true, with or without `__GFP_FS`.
- For a `struct dma_resv`, the section starts at `dma_resv_add_fence()`,
  before `dma_resv_unlock()`: `dma_resv_for_each_fence_unlocked()` reads
  without the lock.
- `dma_fence_begin_signalling()` returns a `bool`: false when it acquired
  `dma_fence_lockdep_map`, true when it did nothing; pass that value to the
  matching `dma_fence_end_signalling()`, which releases only on false.
- `dma_fence_begin_signalling()` does nothing when the section is already
  open or when `in_atomic()` is true, so a section in atomic context is not
  recorded.
- Without `CONFIG_LOCKDEP`, `dma_fence_begin_signalling()`,
  `dma_fence_end_signalling()` and `__dma_fence_might_wait()` are stubs.
- Only `dma_fence_signal()` annotates itself; `dma_fence_signal_timestamp()`,
  `dma_fence_signal_locked()`, `dma_fence_signal_timestamp_locked()`,
  `dma_fence_check_and_signal()` and `dma_fence_check_and_signal_locked()`
  do not.
- Wait side: only `dma_fence_wait_timeout()` calls
  `__dma_fence_might_wait()`; `dma_fence_wait_any_timeout()` and a direct
  `dma_fence_default_wait()` do not.
- A fence wait inside a signalling section is not reported:
  `__dma_fence_might_wait()` drops the section's hold on the map before it
  takes the map; nothing checks for a cycle between fences.
- No file under `drivers/gpu/drm/scheduler/` calls
  `dma_fence_begin_signalling()`; drivers annotate their own paths, for
  example `drivers/gpu/drm/panfrost/panfrost_job.c`.

## GEM

**GEM object lifetime**

- `handle_count`: all handles together hold one `refcount` reference, not one
  each. `drm_gem_object_handle_get()` takes it on 0 -> 1 and
  `drm_gem_object_handle_put_unlocked()` drops it on 1 -> 0.
- `handle_count` also counts framebuffers: `drm_framebuffer_init()` takes one
  handle reference per plane with
  `drm_gem_object_handle_get_if_exists_unlocked()`, recorded in
  `DRM_FRAMEBUFFER_HAS_HANDLE_REF()`, and `drm_framebuffer_cleanup()` drops it.
- Closing every user handle while a framebuffer holds a handle reference:
  `obj->name` and `obj->dma_buf` stay set.
- `drm_gem_object_handle_put_unlocked()`: takes `dev->object_name_lock`
  itself, so the caller must not hold it. `drm_gem_handle_delete()` has only
  replaced the idr slot with NULL by then, and `drm_gem_release()` calls it
  with the entry still in `object_idr`.
- Put functions in `include/drm/drm_gem.h`: `drm_gem_object_put()`, which
  accepts NULL, and `__drm_gem_object_put()`, which does not.
- drm_gem_object_put_locked: named in the kerneldoc of `refcount`, defined
  nowhere.

**Object callbacks**

- `free`: mandatory. Without it `drm_gem_object_free()` warns and returns, and
  the object is never freed.
- `obj->funcs`: must be set. `drm_gem_object_free()`,
  `drm_gem_handle_create_tail()` and `drm_gem_mmap_obj()` dereference it
  without a NULL test.
- `vm_ops`: required when `mmap` is unset; `drm_gem_mmap_obj()` otherwise
  returns `-EINVAL`.
- `pin`, `unpin`: there is no drm_gem_pin_locked or drm_gem_pin here. The
  only callers are `drm_gem_map_attach()` and `drm_gem_map_detach()` in
  `drivers/gpu/drm/drm_prime.c`, which lock `obj->resv` around the call.
- `get_sg_table`: `drm_gem_map_dma_buf()` takes no lock itself; `resv` is
  held on that path because `dma_buf_map_attachment()` asserts it before
  calling `map_dma_buf`.
- `status`, `rss`: called by `drm_show_memory_stats()` under the spinlock
  `file->table_lock`, without `resv`; they must not sleep.
- `evict`: `drm_gem_evict_locked()` asserts `resv`, but nothing in this tree
  installs `evict` or calls `drm_gem_evict_locked()`; drm_gem_object_evict,
  named in the kerneldoc, does not exist.

**Looking up handles**

- `drm_gem_objects_lookup()` on failure: drops the references it took, frees
  the array and leaves `*objs_out` NULL; the caller releases nothing.
- `drm_gem_objects_lookup()` with `count == 0`: returns 0 with `*objs_out`
  NULL.
- `DRM_IOCTL_GEM_CHANGE_HANDLE`: defined in `include/uapi/drm/drm.h`, but the
  table in `drivers/gpu/drm/drm_ioctl.c` routes it to `drm_invalid_op()`,
  which returns `-EINVAL`.
- `drm_gem_change_handle_ioctl()`: still defined in
  `drivers/gpu/drm/drm_gem.c`, with no caller; user space cannot move an
  object between handles.

**Mapping objects to user space**

- Lookup and access check: in static `drm_gem_object_lookup_at_offset()` in
  `drivers/gpu/drm/drm_gem.c`, not in the body of `drm_gem_mmap()`.
- `drm_gem_object_lookup_at_offset()`: returns `-ENODEV` first if
  `drm_dev_is_unplugged()`; `drm_gem_get_unmapped_area()` calls it too.
- `drm_gem_mmap_obj()`: takes the reference and sets `vm_private_data` and
  `vma->vm_ops = obj->funcs->vm_ops` before it calls `funcs->mmap`.
- `funcs->mmap` callback: owes `vm_flags` and `vm_page_prot`.
  `drm_gem_mmap_obj()` sets them only when `mmap` is unset, and warns if
  `VM_DONTEXPAND` is missing after the callback.
- Kerneldoc of `mmap` in `include/drm/drm_gem.h`: says the callback must set
  `vma->vm_ops`; the code pre-sets it on both paths.
- `vm_pgoff` on callback entry: includes the fake offset through
  `drm_gem_mmap()` and through `drm_gem_prime_mmap()`, which adds it first.
  `drm_gem_dma_mmap()` subtracts it.
- `drm_gem_prime_mmap()` with a `mmap` callback: makes no access check, and
  sets `vm_private_data` after the callback returns.
- **Potentially unsafe usage**: a `mmap` callback that drops the object
  reference taken by `drm_gem_mmap_obj()`.
  - Unsafe: when the callback returns an error; `drm_gem_mmap_obj()` then
    calls `drm_gem_object_put()` again.
  - Safe: on success only, when something else keeps the mapping alive, as
    `drm_gem_ttm_mmap()` does after `ttm_bo_mmap_obj()` took its own
    reference, and `drm_gem_shmem_mmap()` does after `dma_buf_mmap()` moved
    the vma to the dma-buf file.

**Shmem helper**

- `pages_use_count`, `pages_pin_count`, `vmap_use_count`: all `refcount_t`.
- `drm_gem_shmem_vmap()`, `drm_gem_shmem_vunmap()`,
  `drm_gem_shmem_madvise()`, `drm_gem_shmem_purge()`: built only under
  `IS_ENABLED(CONFIG_KUNIT)` and exported with `EXPORT_SYMBOL_IF_KUNIT()`.
  Drivers have only the `_locked` forms.
- `drm_gem_shmem_get_pages_locked()`: static. A driver gets pages for example
  through `drm_gem_shmem_pin()` or `drm_gem_shmem_get_pages_sgt()`.
- `drm_gem_shmem_object_pin()`, `drm_gem_shmem_object_unpin()`: call the
  `_locked` forms and need `resv` held, although their kerneldoc names the
  locking forms.
- `drm_gem_shmem_get_sg_table()`: no lock assertion, but reads
  `shmem->pages`; `drm_gem_shmem_get_pages_sgt_locked()` and the
  `get_sg_table` path through `drm_gem_map_dma_buf()` call it with `resv`
  held.
- `drm_gem_shmem_is_purgeable()`: tests `madv > 0`, not a particular value,
  and also requires `sgt` to be set.
- A user mapping does not block a purge: `pages_use_count` is not tested.
  `drm_gem_shmem_purge_locked()` zaps the mapping with `drm_vma_node_unmap()`.
- `drm_gem_shmem_purge_locked()`: only warns when the object is not
  purgeable, then purges anyway; the caller must test first.

**PRIME import and export**

- `drm_gem_is_imported()`: returns `!!obj->import_attach`. It does not look
  at `obj->dma_buf`.
- An import whose driver left `import_attach` NULL: tests as not imported.
- `if (obj->import_attach)`: same result as `drm_gem_is_imported()` here;
  `drm_gem_prime_handle_to_dmabuf()` tests the field directly.
- **Unsafe usage**: testing `obj->dma_buf` to decide whether an object is
  imported. `export_and_register_object()` sets it for exports,
  `drm_gem_prime_fd_to_handle()` sets it for imports, and
  `drm_gem_object_exported_dma_buf_free()` clears it at last handle close.
  - Safe: `drm_gem_is_imported()`, as `drm_gem_shmem_vmap_locked()` does;
    `import_attach` is set once at import, for example in
    `drm_gem_prime_import_dev()`.
- Self-import test: `drm_gem_is_prime_exported_dma_buf()` in
  `drivers/gpu/drm/drm_prime.c`, exported; `drm_gem_prime_import_dev()` and
  `drm_gem_shmem_prime_import_no_map()` call it.
- A driver whose `export` uses its own `struct dma_buf_ops`: fails that test,
  since it compares against `drm_gem_prime_dmabuf_ops`. Such a driver needs
  its own check, as `amdgpu_gem_prime_import()` has.

**LRU lists and shrinkers**

- `struct drm_gem_lru`: has only `count` and `list`; there is no lock field.
- The lock: `gem_lru_mutex` in `struct drm_device`, one mutex for every LRU of
  the device. It protects `obj->lru` and `obj->lru_node` too.
- `drm_gem_lru_init()`: takes only the LRU. `drm_gem_lru_scan()`: takes the
  device as its first argument.
- `drm_gem_lru_scan()`: takes `resv` with
  `ww_mutex_trylock(&obj->resv->lock, ticket)` whether or not a ticket is
  given; it never blocks on `resv`.
- `ticket`: every in-tree caller passes NULL. The callbacks take other
  reservations with `dma_resv_trylock()` only, for example `with_vm_locks()`
  in `drivers/gpu/drm/msm/msm_gem_shrinker.c`.
- The callback may sleep: `panthor_gem_try_evict()` waits in
  `dma_resv_wait_timeout()`.
- **Unsafe usage**: calling `drm_gem_lru_move_tail_locked()` from the `shrink`
  callback without taking `gem_lru_mutex`; its
  `lockdep_assert_held_once()` fails, because `drm_gem_lru_scan()` dropped
  the mutex.
  - Safe: `drm_gem_lru_move_tail()` or `drm_gem_lru_remove()`, as
    `panthor_gem_update_reclaim_state_locked()` does.
  - Safe: take `dev->gem_lru_mutex`, then call the `_locked` form, as
    `update_lru()` in `drivers/gpu/drm/msm/msm_gem.c` does.

**drm_exec object locking**

- `drm_exec_lock_obj()` on `-EDEADLK`: only takes a reference and stores the
  object in `exec->contended`. It unlocks nothing.
- `drm_exec_cleanup()`, the loop condition: unlocks and puts everything.
- The slow lock: taken by `drm_exec_lock_contended()` at the start of the
  next `drm_exec_lock_obj()`, whichever object that call asks for.
- `drm_exec_retry`: a plain function-scope label reached by a plain `goto`.
  A second loop in one function needs `__label__ drm_exec_retry;` in its
  enclosing block, as in `drivers/gpu/drm/tests/drm_exec_test.c`.
- `drm_exec_retry_on_contention()`: compiles only lexically inside the loop,
  because it reads `__drm_exec_loop`. A helper returns `-EDEADLK` and the
  loop body calls the macro.
- **Unsafe usage**: a retry pass through the loop body that makes no lock
  call. Only `drm_exec_lock_contended()` clears a contended object from
  `exec->contended`, so `drm_exec_cleanup()` returns true forever.
  - Safe: every pass calls `drm_exec_lock_obj()` or `drm_exec_prepare_obj()`
    at least once, as `drm_gpuvm_exec_lock()` does.
  - Safe: `drm_exec_prepare_array()` with zero objects; it calls
    `drm_exec_lock_contended()` itself.
- `drm_exec_retry()`: restarts the loop unconditionally. It warns unless
  `exec->contended` is `DRM_EXEC_DUMMY`, so the caller must run
  `drm_exec_fini()` and `drm_exec_init()` first.

**Publishing a handle**

- A concurrent close drops only the handle's reference. The ioctl's creation
  reference keeps the object alive until the ioctl's own
  `drm_gem_object_put()`.
- **Potentially unsafe usage**: dereferencing the object after
  `drm_gem_handle_create()`.
  - Unsafe: after the ioctl has dropped its creation reference;
    `drm_gem_handle_delete()` from another thread can then free the object.
  - Safe: between `drm_gem_handle_create()` and the put, as
    `panthor_gem_create_with_handle()` reads `bo->base.size`.
  - Safe: copy the value before the handle exists, as `i915_gem_publish()`
    does.
- `drm_gem_dma_create_with_handle()`: reads nothing from the object, and
  returns the pointer after the put. Its two callers only pass it to
  `PTR_ERR_OR_ZERO()`.
- **Potentially unsafe usage**: relying on per-handle state created by
  `funcs->open` after `drm_gem_handle_create()` returns.
  - Unsafe: when the code assumes the state exists; a close that guessed the
    handle has already run `funcs->close`.
  - Safe: look the state up and handle its absence, as
    `panfrost_ioctl_create_bo()` returns `-EINVAL` when
    `panfrost_gem_mapping_get()` finds nothing.

## TTM and allocators

**TTM buffer object lifetime**

- Two counts: `kref` in `struct ttm_buffer_object` and `base.refcount` of the
  embedded GEM object. Drivers, handles and dma-bufs hold the GEM count; the
  GEM object as a whole owns one `kref`.
- `ttm_bo_fini()` in `drivers/gpu/drm/ttm/ttm_bo.c`: the exported drop; it is
  one `ttm_bo_put()`, which puts `bo->kref` with `ttm_bo_release()`.
- `ttm_bo_put()`, `ttm_bo_get()`, `ttm_bo_get_unless_zero()`: TTM-internal,
  in `drivers/gpu/drm/ttm/ttm_bo_internal.h`; `ttm_bo_put()` is not exported.
- Driver drop path: `drm_gem_object_put()`; the driver's
  `struct drm_gem_object_funcs` `.free` calls `ttm_bo_fini()`, for example
  `amdgpu_gem_object_free()`.
- After `ttm_bo_fini()` the `.free` callback must not free the object:
  `ttm_bo_release()` calls `bo->destroy`, at once or later, normally from
  `bdev->wq`, and `destroy` frees the containing struct.
- GEM count zero with `bo->kref` non-zero is a normal state: TTM's LRU walk
  and ghost objects hold `bo->kref` only. A driver callback that needs
  GEM-level state first tries `kref_get_unless_zero()` on `base.refcount`, as
  `xe_bo_get_unless_zero()` does.
- `ttm_bo_init_reserved()`: does not initialise the embedded GEM object. It
  reads `bo->base.size`, uses `bo->base.vma_node`, overwrites `bo->base.resv`
  and, with a NULL `resv`, trylocks `bo->base._resv`.
  `drm_gem_private_object_init()` prepares those; `nouveau_bo_new()` sets
  them by hand and leaves `bo->base.dev` NULL.
- `ttm_bo_release()` defers destruction when any of these holds: unsignalled
  `DMA_RESV_USAGE_BOOKKEEP` fences on `bo->base._resv`;
  `want_init_on_free()` and `bo->ttm` set; `ttm_bo_type_sg`; trylock of
  `bo->base.resv` fails. An idle BO is therefore deferred too under
  init-on-free.
- There is no ttm_bo_cleanup_refs() and no delayed-destroy list; each zombie
  queues its own `bo->delayed_delete` work, `ttm_bo_delayed_delete()`.
- A zombie stays on the LRU. `ttm_bo_evict_cb()`, `ttm_bo_swapout_cb()` and
  `ttm_bo_evict_first()` test `bo->deleted` and call
  `ttm_bo_cleanup_memtype_use()` early; `ttm_bo_delayed_delete()` calls it
  again, so `delete_mem_notify` can run twice, the second time with
  `bo->resource == NULL`.
- **Potentially unsafe usage**: calling `ttm_bo_fini()` outside the GEM
  `.free` callback.
  - Unsafe: on a BO whose GEM object has a `.free` callback that can still
    run; GEM holders keep using the BO, and `.free` later puts `bo->kref` a
    second time.
  - Safe: on a BO that never had a GEM object initialised, so no `.free`
    exists for it, as `nouveau_bo_unpin_del()` does for BOs from
    `nouveau_bo_new()`; `ttm_bo_fini()` is the single put of the `kref_init()`
    in `ttm_bo_init_reserved()`.
  - Safe: after the GEM count reached zero, from work that the `.free`
    callback queued, as `i915_ttm_delayed_free()` does; it is reached only
    through `i915_gem_free_object()`.
  - Safe: on a BO whose GEM object has no `funcs`, so no `.free` exists for
    it, as the KUnit test `ttm_bo_init_reserved_sys_man()` does; the
    `kref_init()` in `ttm_bo_init_reserved()` is the only reference.
- **Unsafe usage**: passing a NULL `destroy` to `ttm_bo_init_reserved()` or
  `ttm_bo_init_validate()`; the kerneldoc promises `kfree()`, but
  `ttm_bo_release()` calls `bo->destroy(bo)` with no NULL test.
  - Safe: always pass a function; `amdgpu_bo_create()` substitutes
    `amdgpu_bo_destroy()` when its parameter is NULL.

**Placement and validation**

- `struct ttm_operation_ctx` in `include/drm/ttm/ttm_bo.h`: six fields; it
  has no `force_alloc` member.
- `no_wait_gpu` during allocation does not produce `-EBUSY`: busy eviction
  victims are skipped, the LRU walk only trylocks, and a place whose manager
  has an unsignalled eviction fence is passed over for the next place. When
  nothing fits the result is `-ENOMEM`. See
  `ttm_bo_add_pipelined_eviction_fences()` and `__ttm_bo_lru_cursor_next()`.
- `-EBUSY` reaches the caller from `ttm_bo_wait_ctx()`, typically inside the
  driver's `move` callback. Without `no_wait_gpu` it still returns `-EBUSY`
  after a 15 second wait.
- `-EDEADLK` is not returned by TTM's eviction locking:
  `ttm_lru_walk_ticketlock()` turns it into `-ENOSPC`, which ends as
  `-ENOMEM`.
- `-EINTR` can come back with `interruptible` set:
  `ttm_lru_walk_ticketlock()` returns the result of
  `dma_resv_lock_interruptible()` unconverted, unlike `ttm_bo_reserve()`.
  `ttm_bo_evict()` skips its "Buffer eviction failed" message for both
  `-EINTR` and `-ERESTARTSYS`.
- `-ERESTARTSYS` is the restart code, from interruptible fence waits; pass
  it up unchanged.
- `-EAGAIN` from the dmem cgroup charge in `ttm_resource_try_charge()`:
  `ttm_bo_alloc_at_place()` converts it to `-EBUSY` or `-ENOSPC` before it
  can leave.
- `-ENOSPC` at the end of `ttm_bo_validate()` becomes `-ENOMEM` unless
  `bdev->alloc_flags` has `TTM_ALLOCATION_PROPAGATE_ENOSPC`; no driver in this
  tree sets that flag. `ttm_bo_bounce_temp_buffer()` failures are returned
  unconverted.
- Placement naming only absent or unused managers: those places are skipped
  in `ttm_bo_alloc_resource()`, giving `-ENOMEM`, not `-EINVAL`.
- `-EINVAL` from `ttm_bo_validate()` itself means a pinned BO would have to
  move.
- Pinned BO and `TTM_PL_FLAG_FALLBACK`: the compatibility test before the pin
  test runs with `evicting == false`, which ignores fallback places. A pinned
  BO sitting in a place the placement lists only as fallback gets `-EINVAL`.
- Pinned BOs are moved to the `bdev->unevictable` list by
  `ttm_resource_move_to_lru_tail()`, not unlinked;
  `ttm_device_clear_dma_mappings()` still walks them.
- Pinning also makes `ttm_bo_shrink_suitable()` return false.

**Range and buddy allocators**

| Job | Type | Core code | Config |
|---|---|---|---|
| Address range | `struct drm_mm` | `drivers/gpu/drm/drm_mm.c` | part of the DRM core |
| Power-of-two blocks | `struct gpu_buddy` | `drivers/gpu/buddy.c`, `include/linux/gpu_buddy.h` | `CONFIG_GPU_BUDDY` |
| Short-lived, fenced | `struct drm_suballoc_manager` | `drivers/gpu/drm/drm_suballoc.c` | `CONFIG_DRM_SUBALLOC_HELPER` |

- There is no struct drm_buddy, drm_buddy_alloc_blocks() or
  DRM_BUDDY_RANGE_ALLOCATION here. The calls are `gpu_buddy_init()`,
  `gpu_buddy_alloc_blocks()`, `gpu_buddy_free_list()`,
  `gpu_buddy_block_trim()`, with flags such as `GPU_BUDDY_RANGE_ALLOCATION`.
- `include/drm/drm_buddy.h` and `drivers/gpu/drm/drm_buddy.c` hold only
  `drm_buddy_print()` and `drm_buddy_block_print()`, which take
  `struct gpu_buddy`. `CONFIG_DRM_BUDDY` selects `CONFIG_GPU_BUDDY`.
- Buddy locking: none inside. A driver can register its lock with
  `gpu_buddy_driver_set_lock()`; exported calls such as
  `gpu_buddy_alloc_blocks()` and `gpu_buddy_free_list()` then assert it
  through `gpu_buddy_driver_lock_held()`. `gpu_buddy_init()`,
  `gpu_buddy_fini()` and `gpu_buddy_block_print()` do not assert.
- `gpu_buddy_driver_lock_held()` checks nothing without `CONFIG_LOCKDEP`, or
  when no lock was registered; in this tree only
  `drivers/gpu/drm/xe/xe_ttm_vram_mgr.c` registers one.
- The buddy caller's lock must allow sleeping: `gpu_block_alloc()` allocates
  with `GFP_KERNEL` when a block is split, and `gpu_buddy_free_list()` calls
  `cond_resched()` per block.
- `drm_mm_scan_init()` exists, as a static inline in `include/drm/drm_mm.h`
  that calls `drm_mm_scan_init_with_range()`.
- `struct amdgpu_sa_manager` and `struct radeon_sa_manager` still exist; each
  embeds `struct drm_suballoc_manager` as `base`, and `amdgpu_sa_bo_new()`
  calls `drm_suballoc_new()`.
- Suballoc two-step form: `drm_suballoc_alloc()` allocates the object, then
  `drm_suballoc_insert()` places it; `drm_suballoc_new()` is both.
  `drm_suballoc_free()` on an object that was never inserted just frees it.
- Suballoc locking: `sa_manager->wq.lock`, taken with plain `spin_lock()`,
  which does not disable interrupts. `drm_suballoc_manager_fini()` takes no
  lock.

## GPU scheduler

**Run queues and scheduling policies**

- Run queue count: `struct drm_sched_init_args.num_rqs` is stored as
  `num_user_rqs`; `num_rqs` in `struct drm_gpu_scheduler` is that value for
  FIFO and RR, and 1 for `DRM_SCHED_POLICY_FAIR`. See `drm_sched_init()` in
  `drivers/gpu/drm/scheduler/sched_main.c`.
- `sched_rq` array: allocated with `args->num_rqs` slots, but only the first
  `num_rqs` are filled; under FAIR every slot above 0 is NULL.
- Policies: three, `DRM_SCHED_POLICY_RR` (0), `DRM_SCHED_POLICY_FIFO` (1) and
  `DRM_SCHED_POLICY_FAIR` (2), defined in
  `drivers/gpu/drm/scheduler/sched_internal.h`.
- Default: `drm_sched_policy` is initialised to `DRM_SCHED_POLICY_FIFO`; there
  is no DRM_SCHED_POLICY_DEFAULT. The parameter text calls FAIR experimental.
- Selection: all three policies pick from the rb-tree `rb_tree_root` through
  one `drm_sched_rq_select_entity()`; inside a run queue they differ only in
  the key written to `entity->oldest_job_waiting`.
  - FIFO: `submit_ts` of the entity's next job.
  - RR: a fake timestamp, `rr_ts`, bumped in `drm_sched_rq_pop_entity()`.
    There is no list walk and no current_entity field.
  - FAIR: a virtual runtime kept in `struct drm_sched_entity_stats`
    (`sched_internal.h`), scaled per priority by `vruntime_shift[]`.
- `entities` list in `struct drm_sched_rq`: still maintained, but not used for
  selection; for example `drm_sched_increase_karma()` walks it.
- Entity fields: `priority` is the user priority, `rq_priority` is the index
  into `sched_rq[]`. Under FAIR `rq_priority` is
  `DRM_SCHED_PRIORITY_KERNEL`.
- `rq_priority`: written only by `drm_sched_entity_init()`;
  `drm_sched_entity_set_priority()` changes `priority` alone.
- `drm_sched_entity_init()`: compares the priority with `num_user_rqs`, not
  `num_rqs`, and the clamp rewrites `entity->priority`.
- `drm_sched_select_entity()`, the loop over run queues: stays in
  `sched_main.c`.

**Backend callbacks**

- `struct drm_sched_backend_ops`: five members, `prepare_job`, `run_job`,
  `timedout_job`, `free_job`, `cancel_job`. There is no update_job_credits
  callback in this tree.
- NULL tests: the scheduler tests only `prepare_job` and `cancel_job` for NULL.
- `free_job`: required even with `cancel_job`;
  `drm_sched_cancel_remaining_jobs()` calls `free_job` right after
  `cancel_job`.
- `free_job` contexts: not only `submit_wq`.

  | Caller | Context |
  |---|---|
  | `drm_sched_free_job_work()` | `submit_wq` |
  | `drm_sched_stop()` | its caller, for example the timeout handler |
  | `drm_sched_job_timedout()`, when `free_guilty` is set | `timeout_wq` |
  | `drm_sched_cancel_remaining_jobs()` | caller of `drm_sched_fini()` |
  | `drm_sched_entity_kill_jobs_work()` | work queued by `schedule_work()` |

- `free_job` from the kill path: the job never ran, so `s_fence->parent` is
  NULL and `run_job` was never called for it.
- `run_job` returning NULL: the job is finished at once with result 0, which
  sets no error on the finished fence; an `ERR_PTR()` sets its errno.
- `run_job` fence reference: `drm_sched_run_job_work()` drops the returned
  reference as soon as the completion callback is added.
  `drm_sched_fence_set_parent()` takes a separate reference for
  `s_fence->parent`.
- `run_job` second call: from the scheduler only through
  `drm_sched_resubmit_jobs()`, in the context of its caller; a driver can
  also call `ops->run_job` itself, as `xe_sched_resubmit_jobs()` does.
- `prepare_job`: called from `drm_sched_job_dependency()` once the job's
  `dependencies` are used up, and called again until it returns NULL.
  `drm_sched_entity_kill()` does not call it for the jobs it pops.
- `cancel_job`: called for each job on `pending_list`, newest first. Those
  jobs were all passed to `run_job` already; the kerneldoc's "have not been
  executed" does not match `drm_sched_cancel_remaining_jobs()`.
- `cancel_job` implementations: only `mock_sched_cancel_job()` in
  `drivers/gpu/drm/scheduler/tests/mock_scheduler.c`; no driver sets it.
- **Potentially unsafe usage**: leaving `timedout_job` NULL.
  - Unsafe: when `work_tdr` can run with a job on `pending_list`;
    `drm_sched_job_timedout()` calls the pointer with no NULL test. A finite
    `timeout`, `drm_sched_fault()`, `drm_sched_tdr_queue_imm()` and
    `drm_sched_resume_timeout()` all queue that work.
  - Safe: with `timeout` set to `MAX_SCHEDULE_TIMEOUT` and none of those
    calls, as `msm_ringbuffer_new()` sets up; `drm_sched_start_timeout()`
    then never queues `work_tdr`.

**Job lifecycle**

- `drm_sched_job_init()`: fails only with `-EINVAL` for zero credits and
  `-ENOMEM` for the fence allocation. It tests neither `entity` nor
  `entity->rq`, and does not return `-ENOENT`, although its kerneldoc says so.
- `drm_sched_job_arm()`: does `BUG_ON(!entity)` and then dereferences
  `entity->rq`, which `drm_sched_entity_select_rq()` sets to NULL when
  `drm_sched_pick_best()` finds no ready scheduler.
- `drm_sched_entity_push_job()` on a killed entity: cannot report it.
  `drm_sched_rq_add_entity()` logs "Trying to push to a killed entity" after
  the job is already in `job_queue`; the job stays there until the next
  `drm_sched_entity_kill()`, for example from `drm_sched_entity_fini()`,
  finishes it with `-ESRCH`.
- After `drm_sched_entity_push_job()` returns: the job may already be freed.
  Take what is needed between arm and push, as `panfrost_job_push()` does
  with `s_fence->finished`.

**Credits and work queues**

- Credit callback: none in this tree. A job's `credits` change only when
  `drm_sched_can_queue()` truncates them to `credit_limit`.
- Head job does not fit: `drm_sched_rq_select_entity()` returns
  `ERR_PTR(-ENOSPC)` and `drm_sched_select_entity()` stops there. No other
  entity and no lower run queue is tried until credits come back.
- Credits during recovery: `drm_sched_stop()` subtracts the credits of every
  job it detaches from its hardware fence; `drm_sched_start()` adds the
  credits of every job on `pending_list` back.
- `timeout_wq` NULL: selects `system_percpu_wq`, not `system_wq`.
- Driver-supplied `submit_wq`: `drm_sched_init()` checks neither that it is
  ordered nor that it has `WQ_MEM_RECLAIM`.
- `drm_sched_wqueue_stop()`: runs `cancel_work_sync()` on `work_run_job` and
  `work_free_job`, so `drm_sched_stop()` and `drm_sched_fini()` wait for a
  running `run_job` or `free_job`. Those callbacks must not block on anything
  the caller of the two functions holds.
- `drm_sched_run_job_queue()` and `drm_sched_run_free_queue()`: queue nothing
  while `pause_submit` is set.

**Job timeout handling**

- `drm_sched_job_timedout()`: tests the return value only against
  `DRM_GPU_SCHED_STAT_NO_HANG` and `DRM_GPU_SCHED_STAT_ENODEV`.
  `DRM_GPU_SCHED_STAT_NONE` takes the same path as
  `DRM_GPU_SCHED_STAT_RESET`.
- `DRM_GPU_SCHED_STAT_RESET`: the scheduler re-arms the timer and does not put
  the job back on `pending_list`. Only `drm_sched_stop()` with the job as
  `bad` puts it back.
- Handler that returns RESET without `drm_sched_stop()` on the job: the
  scheduler never calls `free_job` for it; the handler frees it, as
  `mock_sched_timedout_job()` does.
- `DRM_GPU_SCHED_STAT_NO_HANG`: handled by
  `drm_sched_job_reinsert_on_false_timeout()`, which does the same
  `list_add()` as `drm_sched_stop()` does for `bad`; both for one job adds it
  twice.
- `free_guilty`: when `drm_sched_stop()` set it, `free_job` runs on the job
  after the callback, whatever the callback returned.
- `drm_sched_stop()`: drops the parent reference and sets `s_fence->parent` to
  NULL for every job it detaches.
- `drm_sched_start()`: finishes each job without a parent with
  `errno ?: -ECANCELED`. After `drm_sched_stop()` that is every remaining job,
  unless something set the parent again, as `drm_sched_resubmit_jobs()` does.
- `drm_sched_start()` with errno 0: the remaining jobs still end with
  `-ECANCELED`.
- Recovery sequences: stated only in the kerneldoc of `timedout_job` in
  `include/drm/gpu_scheduler.h`; no code enforces them.
  - Firmware scheduler: `drm_sched_stop()`, remove the ring, kill the entity
    and its scheduler. There is no `drm_sched_start()` step.
  - Hardware scheduler: `drm_sched_stop()` on all affected schedulers, kill
    the entity of the faulty job, reset, resubmit to live entities,
    `drm_sched_start()`.
- Deprecated: `drm_sched_resubmit_jobs()` (kerneldoc in `sched_main.c`) and
  `hang_limit` (kerneldoc of `struct drm_sched_init_args`). In-tree drivers
  still call the first.
- `drm_sched_increase_karma()`: carries no deprecation note.
- Not in this tree: drm_sched_resubmit_jobs_ext and drm_sched_job_recovery.
- Replacement named by the kerneldoc: `drm_sched_for_each_pending_job()` after
  stopping the scheduler. It and `drm_sched_job_is_signaled()` do `WARN_ON()`
  unless `drm_sched_is_stopped()` is true.

**Scheduler and entity teardown**

- `drm_sched_entity_kill()`: exported and declared in
  `include/drm/gpu_scheduler.h`, not static. Use it instead of a flush when
  queued jobs should not be waited for.
- `drm_sched_entity_flush()` timeout: used only when the caller has
  `PF_EXITING`. Otherwise it uses `wait_event_killable()` with no time bound
  and returns `timeout` unchanged.
- `drm_sched_entity_flush()` waits for `drm_sched_entity_is_idle()`: the job
  queue is empty, or the entity is stopped or off its run queue. It does not
  wait for jobs to finish on the hardware.
- `drm_sched_entity_flush()` kills only when the caller's thread group leader
  is the entity's `last_user`, the caller has `PF_EXITING`, and its exit code
  is `SIGKILL`.
- `drm_sched_entity_kill()` does not wait for the killed jobs to be freed.
  Each job is finished and passed to `free_job` from
  `drm_sched_entity_kill_jobs_work()`, queued with `schedule_work()` once the
  previous job and the dependencies have signalled.
- `drm_sched_fini()` and entities: it does not mark entities stopped or take
  them off the run queues. It frees each run queue with `kfree()`.
- `drm_sched_fini()` stops work with `drm_sched_wqueue_stop()`; the kerneldoc
  of `drm_sched_stop()` says not to use that one for teardown.
- `drm_sched_fini()` warning: "Tearing down scheduler while jobs are
  pending!" prints only if `pending_list` is not empty at the end, so not
  after `cancel_job` ran.
- **Potentially unsafe usage**: calling `drm_sched_fini()` while an entity is
  still attached to the scheduler.
  - Unsafe: when a job was pushed to the entity, or the entity is later
    passed to `drm_sched_entity_flush()` or `drm_sched_entity_destroy()`;
    `entity->rq` then points to freed memory; `drm_sched_entity_flush()`
    reads `entity->rq->sched`, and `drm_sched_entity_kill()` takes `rq->lock`
    for an entity on the list.
  - Safe: `drm_sched_entity_fini()` afterwards on an entity that never had a
    job pushed, as `pvr_queue_destroy()` does on the context creation failure
    path; `drm_sched_rq_remove_entity()` returns on
    `list_empty(&entity->list)` before it touches the run queue.
  - Safe: finish every entity first, then the scheduler, then destroy a
    driver-owned `submit_wq`, as `nouveau_sched_fini()` does.

**Mock scheduler timeout handler**

- Handler: `mock_sched_timedout_job()`; there is no
  drm_mock_sched_job_timedout.
- Flags: `DRM_MOCK_SCHED_JOB_DONE`, `DRM_MOCK_SCHED_JOB_TIMEDOUT`,
  `DRM_MOCK_SCHED_JOB_DONT_RESET` and `DRM_MOCK_SCHED_JOB_RESET_SKIPPED`, in
  `drivers/gpu/drm/scheduler/tests/sched_tests.h`. `flags` is a plain
  `unsigned long`.
- Repeat runs: happen only for a job with `DRM_MOCK_SCHED_JOB_DONT_RESET`,
  where the handler returns `DRM_GPU_SCHED_STAT_NO_HANG`.
- `drm_sched_skip_reset()` in
  `drivers/gpu/drm/scheduler/tests/tests_basic.c`: waits `2 * MOCK_TIMEOUT` on
  a scheduler whose timeout is `MOCK_TIMEOUT`, so the handler can run twice
  before the test looks at the flags.
- Reset path: runs at most once per job. The handler returns
  `DRM_GPU_SCHED_STAT_RESET` without `drm_sched_stop()`, so the job never
  returns to `pending_list`.
- Reset path cleanup: the handler drops the `hw_fence` reference and calls
  `drm_sched_job_cleanup()` itself, because `free_job` will not be called.
- `DRM_MOCK_SCHED_JOB_DONE` and `DRM_MOCK_SCHED_JOB_TIMEDOUT`: set under
  `lock` of `struct drm_mock_scheduler`. The tests read `flags` without it.
- **Unsafe usage**: clearing `DRM_MOCK_SCHED_JOB_DONT_RESET` in the handler.
  - Unsafe: the next run for the same job takes the reset path, signals
    `hw_fence` with `-ETIMEDOUT` and cleans the job up, while the test still
    expects `drm_mock_sched_advance()` to complete it.
  - Safe: leave the request flag set and OR in
    `DRM_MOCK_SCHED_JOB_RESET_SKIPPED`, as `mock_sched_timedout_job()` does;
    `drm_sched_skip_reset()` asserts on that flag.

## GPUVM

**GPUVM objects**

- There is no drm_gpuvm_bo_obtain() here; `drm_gpuvm_bo_obtain_locked()` in
  `drivers/gpu/drm/drm_gpuvm.c` is the find-or-create function. Comments in
  that file still use the old name.
- Functions that create or look up a `struct drm_gpuvm_bo`, each returning
  one reference for the caller:

  | Function | GEM list lock | On failure | VM mode |
  |---|---|---|---|
  | `drm_gpuvm_bo_create()` | none; vm_bo is on no list | `NULL` | any |
  | `drm_gpuvm_bo_find()` | caller holds | `NULL` if none | any |
  | `drm_gpuvm_bo_obtain_locked()` | caller holds | `ERR_PTR(-ENOMEM)` | `drm_WARN_ON()` if immediate |
  | `drm_gpuvm_bo_obtain_prealloc()` | takes `gpuva.lock` itself | cannot fail | `drm_WARN_ON()` if not immediate |

- `drm_gpuvm_bo_obtain_prealloc()`, when a vm_bo already exists: drops the
  preallocated one through `drm_gpuvm_bo_destroy_not_in_lists()`, which
  calls `vm_bo_free` if the driver set it and puts the VM and the GEM
  object.
- `drm_gpuvm_bo_obtain_prealloc()` call site: at prepare time, before the
  walk, for example `panthor_vm_prepare_map_op_ctx()`;
  `panthor_gpuva_sm_step_map()` later calls no obtain function, only
  `drm_gpuva_link()` and `drm_gpuvm_bo_put_deferred()` on that vm_bo.
- `struct drm_gpuva`: holds a `struct drm_gpuvm` reference while in the
  tree; `drm_gpuva_insert()` takes it and `drm_gpuva_remove()` drops it.
  `kernel_alloc_node` is the one va that holds none.
- `drm_gpuva_remove()`: may therefore be the final VM put and run
  `vm_free`.
- vm_bo after a deferred final put (`drm_gpuvm_bo_put_deferred()`,
  `drm_gpuva_unlink_defer()`): off the GEM list at once, but still
  allocated on `bo_defer` in `struct drm_gpuvm`, holding its VM and GEM
  references, until `drm_gpuvm_bo_deferred_cleanup()` runs.
- With `DRM_GPUVM_RESV_PROTECTED`, such a vm_bo also stays on the extobj
  and evict lists with refcount zero until then; the list walkers skip it
  with `drm_gpuvm_bo_is_zombie()`.
- `DRM_GPUVM_IMMEDIATE_MODE`: no GPUVM function changes behaviour on it.
  It selects the lock that `drm_gem_gpuva_assert_lock_held()` checks, and
  which functions `drm_WARN_ON()`: `drm_gpuvm_bo_obtain_locked()` when set;
  `drm_gpuvm_bo_obtain_prealloc()`, `drm_gpuvm_bo_put_deferred()` and
  `drm_gpuva_unlink_defer()` when clear.

**GPUVM locking**

- `gpuva.lock`: a `struct mutex` embedded in every `struct drm_gem_object`,
  initialised by `drm_gem_private_object_init()`. It is not a pointer and
  no driver supplies it; drm_gem_gpuva_set_lock() is defined nowhere,
  though the kerneldoc of `drm_gem_gpuva_init()` in
  `include/drm/drm_gem.h` and `Documentation/gpu/drm-vm-bind-locking.rst`
  still name it.
- Without `DRM_GPUVM_IMMEDIATE_MODE`: the GEM's dma-resv protects
  `gpuva.list` and `gpuva.lock` is unused.
- `drm_gem_gpuva_assert_lock_held()`: takes the VM as first argument and
  picks the lock from that VM's flag; empty without `CONFIG_LOCKDEP`.
- One GEM mapped by several VMs: the list is shared and the lock is picked
  per VM, so all those VMs must have the same `DRM_GPUVM_IMMEDIATE_MODE`
  setting; nothing checks this.
- Who takes the GEM list lock:

  | Caller must hold it | Takes `gpuva.lock` itself |
  |---|---|
  | `drm_gpuva_link()`, `drm_gpuva_unlink()` | `drm_gpuva_unlink_defer()` |
  | `drm_gpuvm_bo_find()`, `drm_gpuvm_bo_obtain_locked()` | `drm_gpuvm_bo_obtain_prealloc()` |
  | final `drm_gpuvm_bo_put()` | `drm_gpuvm_bo_put_deferred()` |
  | `drm_gpuvm_bo_unmap_ops_create()`, `drm_gpuvm_bo_gem_evict()` | |

- `drm_gpuvm_bo_put()`: takes no GEM list lock; `drm_gpuvm_bo_destroy()`
  asserts it. It calls `might_sleep()`.
- With `DRM_GPUVM_RESV_PROTECTED`: a final `drm_gpuvm_bo_put()` and
  `drm_gpuvm_bo_extobj_add()` also assert the VM's resv.
- `drm_gpuvm_bo_deferred_cleanup()` with `DRM_GPUVM_RESV_PROTECTED`: calls
  `dma_resv_lock()` on the VM's resv itself, so the caller must not hold
  it; `panthor_vm_cleanup_op_ctx()` skips the call on its `vm_bo_validate`
  path for that reason.
- `drm_gpuvm_bo_evict()`: asserts the GEM's dma-resv in every mode, so
  `drm_gpuvm_bo_gem_evict()` on an immediate-mode VM needs the dma-resv
  and `gpuva.lock`.
- `drm_gpuvm_bo_evict()` with `DRM_GPUVM_RESV_PROTECTED` on an external
  object: only sets `evicted`; `drm_gpuvm_prepare_objects()` puts the
  vm_bo on the evict list later.
- Without `DRM_GPUVM_RESV_PROTECTED`: `drm_gpuvm_prepare_objects()` and
  `drm_gpuvm_validate()` are safe against concurrent list insertion and
  removal but not against a second concurrent call on the same VM; each
  list has one `local_list` pointer.
- Lock order where both are held: dma-resv first, then `gpuva.lock`, as in
  `panthor_vm_bo_free()`. GPUVM core defines no order.
- **Unsafe usage**: calling `drm_gpuvm_bo_obtain_prealloc()`,
  `drm_gpuva_unlink_defer()`, or a `drm_gpuvm_bo_put_deferred()` that may
  drop the last reference, with `gpuva.lock` held; each locks the mutex
  again.
  - Safe: `drm_gpuva_link()` under `gpuva.lock`, then unlock, then the
    deferred put, as `panthor_gpuva_sm_step_map()` does through
    `panthor_vma_link()`.
- **Unsafe usage**: a `drm_gpuvm_bo_put()` or `drm_gpuva_unlink()` that may
  drop the last vm_bo reference while `gpuva.lock` is held and the vm_bo's
  GEM reference may be the last; `drm_gpuvm_bo_destroy_not_in_lists()` then
  frees the GEM object that contains the held mutex.
  - Safe: `drm_gpuva_unlink_defer()` or `drm_gpuvm_bo_put_deferred()`
    without the lock held, as `panthor_vma_unlink()` does;
    `drm_gpuvm_bo_defer_free()` unlocks before it queues the vm_bo.
- **Unsafe usage**: allocating memory that can enter reclaim while holding
  `gpuva.lock`; the mutex is taken inside the fence signalling section
  (`panthor_vm_bind_run_job()`), and `drm_gpuvm_bo_obtain_locked()` warns
  on immediate-mode VMs for this reason.
  - Safe: allocate first, lock after: `drm_gpuvm_bo_create()` followed by
    `drm_gpuvm_bo_obtain_prealloc()`, as `panthor_vm_prepare_map_op_ctx()`
    does.
  - Safe: `drm_gpuvm_bo_unmap_ops_create()`, which allocates under the
    asserted list lock, on a VM without `DRM_GPUVM_IMMEDIATE_MODE`, where
    that lock is the dma-resv, as `vm_bind_ioctl_ops_create()` in
    `drivers/gpu/drm/xe/xe_vm.c` does.
- **Potentially unsafe usage**: taking a dma-resv while holding
  `gpuva.lock`.
  - Unsafe: a blocking `dma_resv_lock()`; it inverts the order used by
    `panthor_vm_bo_free()`.
  - Safe: `dma_resv_trylock()` with back-off, as
    `panthor_gem_try_evict_no_resv_wait()` does.

**Map and unmap operations**

- `struct drm_gpuvm_map_req`: its only member is `map`.
- A failing step: the walk stops and `drm_gpuvm_sm_map()` or
  `drm_gpuvm_sm_unmap()` returns the callback's error; core rolls nothing
  back. For example `panthor_vm_bind_run_job()` then marks the VM unusable,
  through `panthor_vm_exec_op()` and `panthor_vm_declare_unusable()`.
- Preallocation is not a core requirement: it is needed only when the walk
  runs where allocation is forbidden. `msm_gem_vm_sm_step_map()` allocates
  inside the callback, because `vm_bind_job_prepare()` runs the walk at
  ioctl time and queues only the page-table updates.
- Preallocation for a walk inside the fence signalling section: see
  `panthor_vm_op_ctx_prealloc_vmas()` (three vas for map, two for unmap)
  and `panthor_vm_prepare_map_op_ctx()` (vm_bo, page tables).
- `drm_gpuvm_sm_map()` sequence: never empty on success; the map step for
  the request is always issued last. An identical existing mapping yields
  an unmap step followed by the map step, contrary to the kerneldoc.
- `drm_gpuvm_sm_unmap()` sequence: empty when nothing overlaps.
- `drm_gpuva_map()` and `drm_gpuva_remap()`: return void and discard the
  result of `drm_gpuva_insert()`, which can be `-EINVAL` or `-EEXIST`; on
  failure the va is not in the tree and holds no VM reference.
- `struct drm_gpuva_op` passed to a callback: lives on the stack of
  `op_map_cb()`, `op_remap_cb()` or `op_unmap_cb()`, and a remap's `prev`,
  `next` and `unmap` point at locals of the walker. A driver that keeps a
  step for later must copy all of them, as `drm_gpuva_sm_step()` does.
- Ops list: its ops hold bare `struct drm_gpuva` pointers with no
  reference, so the driver must keep each named va allocated until the ops
  are used.
- Ops-list creation failure: returns an `ERR_PTR`, frees the partial list
  and leaves the VM untouched.
- `drm_gpuvm_madvise_ops_create()`: exists, in ops-list form only. It emits
  no unmap steps, only remap and map steps, and skips every existing va
  that has a GEM object; `xe_vm_alloc_vma()` in
  `drivers/gpu/drm/xe/xe_vm.c` is its caller.

## amdgpu

**amdgpu layout**

| Job | Under `drivers/gpu/drm/amd/` |
|---|---|
| Core driver | `amdgpu/` |
| Display core | `display/dc/` |
| Display manager | `display/amdgpu_dm/`, a directory; `amdgpu_dm.c` is one file of many. Connector and scaling code is in `amdgpu_dm_connector.c`, interrupt handlers and their registration in `amdgpu_dm_irq.c` |
| Power management | `pm/` (`pm/swsmu/`, `pm/powerplay/`, `pm/legacy-dpm/`) |
| KFD | `amdkfd/` |
| RAS | two places: `amdgpu/amdgpu_ras.c`, and the top-level `ras/` with `ras/core/` and `ras/ras_mgr/`, which `amdgpu/Makefile` includes |
| Hardware sequencer functions | `display/dc/hwss/`, one subdirectory per generation; the hook table is `struct hw_sequencer_funcs` in `display/dc/hwss/hw_sequencer.h` |

**IP and firmware versions**

- `amdgpu_ip_version()` in `drivers/gpu/drm/amd/amdgpu/amdgpu.h`: masks off the
  low 8 bits of `adev->ip_versions[ip][inst]`, which are the variant (bits 7:4)
  and the sub-revision (bits 3:0).
- Instance: not left out; it is the `inst` argument.
- PSP firmware version: `adev->psp.sos.fw_version`, a `struct psp_bin_desc`
  member of `struct psp_context`.
- `sos_fw_version` is not a field; that name is only a sysfs attribute in
  `amdgpu_ucode.c` that reads `psp.sos.fw_version`.
- Gate pattern: test the IP version, then compare `fw_version` with a literal
  minimum for that IP.

| Function in `amdgpu_psp.c` | IP tested | Firmware tested | When the gate fails |
|---|---|---|---|
| `psp_update_fw_reservation()` | `MP0_HWIP` | `sos.fw_version` | returns 0, sends nothing |
| `amdgpu_ptl_perf_monitor_ctrl()` | `GC_HWIP` | `sos.fw_version` | returns `-EOPNOTSUPP` |
| `psp_load_p2s_table()` | `MP0_HWIP` | `sos.fw_version` | returns 0, skips the load |
| `psp_xgmi_peer_link_info_supported()` | `MP0_HWIP` | XGMI TA `bin_desc.fw_version` | returns `false` |

- Minimum versions are per IP: in `psp_update_fw_reservation()` the threshold
  for MP0 14.0.3 is lower than the one for 14.0.2.
- `psp_xgmi_peer_link_info_supported()`: also true for any MP0 at or above
  `IP_VERSION(13, 0, 6)`, with no firmware version test.
- `psp_xgmi_peer_link_info_supported()` does not test capability flags.
- XGMI TA capability flags: `psp_xgmi_initialize()` stores them in
  `xgmi_ta_caps` and, except on an SR-IOV VF, derives
  `supports_ext_link_info` from them; `psp_xgmi_get_topology_info()` uses the
  latter to choose between two commands.
- `psp_cmd_submit_buf()`: returns 0 when the firmware answers with a non-zero
  `resp.status`, except on timeout or for a ucode load on an SR-IOV VF.
- A caller that needs to know the command was rejected has to read
  `cmd->resp.status`, as `psp_get_fw_reservation_info()` does for
  `PSP_ERR_UNKNOWN_COMMAND`.

**Buffer object addresses**

- `amdgpu_bo_gpu_offset()` for VRAM: `vram_start` plus the resource offset, an
  MC address; `vram_base_offset` is not part of it.
- `amdgpu_bo_gpu_offset()` for GTT: the AGP aperture address when
  `amdgpu_gmc_agp_addr()` finds one, otherwise `gart_start` plus the offset.
- `amdgpu_bo_gpu_offset()` warning for an unlocked, unpinned BO: does not fire
  for `ttm_bo_type_kernel`.
- `amdgpu_gmc_pd_addr()` at `CHIP_VEGA10` and later: a PDE, the address from
  `amdgpu_gmc_get_pde_for_bo()` with flag bits in the low bits.
- `amdgpu_gmc_pd_addr()` below `CHIP_VEGA10`: returns `amdgpu_bo_gpu_offset()`
  unchanged.
- PDE address for a VRAM page directory: the MC address minus `vram_start`
  plus `vram_base_offset`; for example `gmc_v9_0_get_vm_pde()` calls
  `amdgpu_gmc_vram_mc2pa()` for it, and `gmc_v12_0_get_vm_pde()` open-codes
  the same sum.
- PDE address for a GTT page directory: `dma_address[0]`, not a GART address.
- PDE flags: come from `amdgpu_ttm_tt_pde_flags()`, which overwrites the
  `AMDGPU_PTE_VALID` that `amdgpu_gmc_pd_addr()` starts with; GTT adds
  `AMDGPU_PTE_SYSTEM`.
- Debugfs: the per-client file `vm_pagetable_info`, read by
  `amdgpu_pt_info_read()` in `amdgpu_debugfs.c`, prints `pd_address` as
  `amdgpu_gmc_pd_addr()` of the root BO.
- `pd_address` in that file at `CHIP_VEGA10` and later: has flag bits set and
  is not an MC address.
- `amdgpu_amdkfd_gpuvm_get_process_page_dir()`: returns the stored
  `amdgpu_gmc_pd_addr()` value, shifted right by `AMDGPU_GPU_PAGE_SHIFT` below
  `CHIP_VEGA10`.

**Kernel buffer objects**

- Existing BO in `*bo_ptr`: `amdgpu_bo_create_reserved()` reserves it, binds
  GART, reads the address and maps it; it does not pin it again.
- `amdgpu_bo_pin()`: called only for a BO this call created.
- `size`, `align` and `domain`: not compared with the existing BO.
- `size == 0`: `amdgpu_bo_create_reserved()` calls `amdgpu_bo_unref(bo_ptr)` and
  returns 0, so an existing BO loses a reference without being unpinned and
  `*bo_ptr` becomes NULL.
- Success with `*bo_ptr == NULL` is therefore possible;
  `amdgpu_bo_create_kernel()` and `amdgpu_bo_create_kernel_at()` test for it.
- **Potentially unsafe usage**: calling either function with `*bo_ptr` not
  NULL.
  - Unsafe: when the target is uninitialised or points at a freed BO;
    `amdgpu_bo_reserve()` then dereferences it.
  - Safe: when it is the live BO from an earlier call, as in
    `gfx_v10_0_cp_gfx_load_pfp_microcode()`, whose `pfp_fw_obj` is set to NULL
    by `amdgpu_bo_free_kernel()` when that frees the BO.
  - Safe: when the wrapper clears it first, as `isp_kernel_buffer_alloc()` does.
- `isp_kernel_buffer_alloc()` in `amdgpu_isp.c`: writes `*bo = NULL` through the
  caller's `buf_obj` before calling `amdgpu_bo_create_kernel()`; it uses no
  local pointer.
- A BO the caller's handle held on entry to `isp_kernel_buffer_alloc()`: is
  overwritten, not freed.
- `isp_user_buffer_alloc()`: passes the address of an uninitialised local;
  `amdgpu_bo_create_isp_user()` assigns `*bo` before reading it.

**Scaling mode property**

- amdgpu's own choice: `RMX_ASPECT`, not full screen.
- `dm_encoder_helper_atomic_check()` in
  `drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm_connector.c`: for eDP and
  LVDS, when the adjusted mode differs in size from the native mode and the
  state holds `RMX_OFF`, it writes `RMX_ASPECT` into the new connector state.
- After that rewrite `amdgpu_dm_connector_atomic_get_property()` reports
  `DRM_MODE_SCALE_ASPECT`, since it reads the same `scaling` field.
- `amdgpu_dm_update_stream_scaling_settings()`: puts `RMX_OFF` and `RMX_ASPECT`
  in the same branch; `RMX_FULL` keeps the full addressable area; `RMX_CENTER`
  sets destination equal to source.
- There is no update_stream_scaling_settings() here;
  `amdgpu_dm_update_stream_scaling_settings()` in `amdgpu_dm_connector.c` does
  that.
- `amdgpu_dm_connector_atomic_set_property()`: is in `amdgpu_dm_connector.c`,
  not `amdgpu_dm.c`.
- amdgpu does not call `drm_connector_attach_scaling_mode_property()`; it
  attaches the device-wide `mode_config.scaling_mode_property` from
  `drm_mode_create_scaling_mode_property()`.
- `scaling_mode` in `struct drm_connector_state`: not written for amdgpu; the
  value is `scaling` in `struct dm_connector_state`.
- Legacy path in `amdgpu_connectors.c`: LVDS and eDP attach the property with
  default `DRM_MODE_SCALE_FULLSCREEN`; other connector types that attach it use
  `DRM_MODE_SCALE_NONE`.

**Rings and fence sequence numbers**

| Field | Type |
|---|---|
| `wptr` in `struct amdgpu_ring` | `u64` |
| `sync_seq` in `struct amdgpu_fence_driver` | `uint32_t` |
| `last_seq` in `struct amdgpu_fence_driver` | `atomic_t` |

- Ring index: `wptr & buf_mask`; `ptr_mask` only limits the stored `wptr`.
- `ptr_mask` with `support_64bit_ptrs`: all ones, so `wptr` is a running dword
  count and not a ring index.
- Slot reuse: `amdgpu_fence_emit()` waits on an unsignalled fence still in the
  slot; `amdgpu_fence_emit_polling()` waits for `seq - num_fences_mask`.
- **Potentially unsafe usage**: a masked `do`/`while (last_seq != seq)` walk
  over the fence array; it visits every slot when both masked values are equal
  on entry.
  - Unsafe: when the unmasked counters can be equal on entry and the body acts
    on a fence without testing it; `dma_fence_signal()` then runs on fences
    the hardware has not reached.
  - Safe: return before the loop when the unmasked values are equal, as
    `amdgpu_fence_process()` does; it signals every fence it visits.
  - Safe: test each fence with `dma_fence_is_signaled()` before acting on it,
    as `amdgpu_ring_find_guilty_fence()` does.
  - Safe: walk the whole array from 0 to `num_fences_mask` under
    `fence_drv.lock` and test each fence, as `amdgpu_fence_driver_set_error()`
    does; that form does not depend on the counters.

**Display core atomic contexts**

- `DC_FP_START()` and `DC_FP_END()`: defined in
  `drivers/gpu/drm/amd/display/amdgpu_dm/dc_fpu.h`, which `dc/os_types.h`
  includes under `CONFIG_DRM_AMD_DC_FP`.
- In a file built with `_LINUX_FPU_COMPILATION_UNIT`: both macros are
  `BUILD_BUG()`.
- `dc_fpu_begin()`: calls `preempt_disable()` itself, then `kernel_fpu_begin()`
  at depth 1; `dc_fpu.c` has no per-architecture branches.
- `dc_fpu_begin()` outside task context: `WARN_ON_ONCE(!in_task())` fires and
  the function carries on, so an interrupt handler must not open an FP
  section.
- `DC_RUN_WITH_PREEMPTION_ENABLED()` in `dc_fpu.h`: closes an open FP section
  around one statement and reopens it; `dml2_allocate_memory()` uses it for
  `vzalloc()`.

| Handler | Registered by | Context |
|---|---|---|
| `dm_vupdate_high_irq()` | DCE (only when `dc_supports_vrr()`) and DCN | interrupt |
| `dm_crtc_high_irq()` | `amdgpu_dm_dce110_register_irq_handlers()` only | interrupt |
| `dm_pflip_high_irq()` | `amdgpu_dm_dce110_register_irq_handlers()` only | interrupt |
| `dm_dcn_vertical_interrupt0_high_irq()` | DCN, under `CONFIG_DRM_AMD_SECURE_DISPLAY` | interrupt |
| `handle_hpd_irq()`, `handle_hpd_rx_irq()`, `dm_dmub_outbox1_low_irq()` | `INTERRUPT_LOW_IRQ_CONTEXT` | work item |

- DCN: `dm_vupdate_high_irq()` calls `dm_crtc_high_irq_handler()`, which
  handles vblank and delivers page-flip completion.
- DRR update from the interrupt handlers: `schedule_dc_vmin_vmax()` queues
  `dm_handle_vmin_vmax_update()`, which calls `dc_stream_adjust_vmin_vmax()`
  under the `dc_lock` mutex.
- The `set_drr` hook is still reached with the `event_lock` spinlock held, from
  `amdgpu_dm_commit_planes()` and `amdgpu_dm_update_freesync_state_on_stream()`.
- `generic_reg_wait()`: calls `msleep()` when `delay_between_poll_us` is 1000 or
  more, `udelay()` below that.
- **Unsafe usage**: a sleeping delay (`msleep()`, `usleep_range()`, `fsleep()`)
  in a hardware sequencer function that has a caller holding a spinlock,
  running from an `INTERRUPT_HIGH_IRQ_CONTEXT` handler or inside
  `DC_FP_START()`.
  - Safe: `udelay()`, or `generic_reg_wait()` with an interval below 1000.
  - Safe: defer the call to a work item, as `schedule_dc_vmin_vmax()` does.

## xe

**xe device, tiles and GTs**

- `xe_device_get_gt()`: an id at or above
  `xe->info.tile_count * xe->info.max_gt_per_tile` returns NULL with no
  warning; the only `xe_assert()` is for a slot other than 0 or 1.
- GT id to tile: divided by `xe->info.max_gt_per_tile` (per platform, set
  in `xe_pci.c`), not by `XE_MAX_GT_PER_TILE`.
- There is no xe_tile_get_gt() in this tree.
- `for_each_gt_on_tile()`: wraps `for_each_gt()` over the whole device and
  keeps GTs with `gt->tile == tile`; `id__` is the device-wide GT id, not a
  slot within the tile.
- `for_each_gt_with_type()`: in `xe_device.h`; wraps `for_each_gt()` and
  filters on a mask of `BIT(gt->info.type)`.
- `xe->info.gt_count`: number of GTs present, counted with `for_each_gt()`
  in `xe_pci.c`; it is not the bound of GT ids, which is
  `xe->info.tile_count * xe->info.max_gt_per_tile`; with
  `max_gt_per_tile` 2, a tile with no media GT leaves its second id unused.

**xe system and runtime PM**

- `xe->d3cold.capable`: set in `xe_pm_probe()`, which `xe_pci_probe()` calls
  before `xe_device_probe()`; `xe_pm_init()` only reads it.
- `xe->d3cold.allowed`: written only by `xe_pm_d3cold_allowed_toggle()`,
  called only from `xe_pci_runtime_idle()`.
- `xe_pm_d3cold_allowed_toggle()`: inputs are `capable` and total VRAM in
  use below `xe->d3cold.vram_threshold`; it reads no other setting.

| Path | reads `allowed` | reads `capable` |
|---|---|---|
| `xe_pm_suspend()`, `xe_pm_resume()` | no | not in the function body |
| `xe_pci_suspend()`, `xe_pci_resume()` | no | yes, in `d3cold_toggle()` |
| `xe_pm_runtime_suspend()`, `xe_pm_runtime_resume()` | yes | in the function body, only to pick the lockdep map, via `xe_rpm_reclaim_safe()` |
| `xe_pci_runtime_suspend()` | yes | yes, in `d3cold_toggle()` |
| `xe_pci_runtime_resume()` | yes | not in the function body |

- `display/xe_display.c`: `xe_display_pm_runtime_suspend()`,
  `xe_display_pm_runtime_suspend_late()`,
  `xe_display_pm_runtime_resume_early()` and
  `xe_display_pm_runtime_resume()` also branch on `allowed`.
- Runtime path with `allowed` false: calls `xe_gt_runtime_suspend()` and
  `xe_gt_runtime_resume()`; with `allowed` true it calls `xe_gt_suspend()`
  and `xe_gt_resume()`, as the system path does.
- `xe_rpm_reclaim_safe()`: returns `!xe->d3cold.capable`; it selects which
  lockdep map the runtime callbacks and the getters acquire.

**xe forcewake**

- `domains` argument of `xe_force_wake_get()`: one domain bit or
  `XE_FORCEWAKE_ALL`; the function asserts `is_power_of_2(domains)`.
- `XE_FORCEWAKE_ALL`: a separate bit, `BIT(XE_FW_DOMAIN_ID_COUNT)`, not the
  OR of the domain bits.
- Returned mask: the domains whose refcount this call raised and still
  holds, including domains that were already awake.
- `XE_FORCEWAKE_ALL` bit in the result: set by `xe_force_wake_get()` only
  when the held set equals `fw->initialized_domains`;
  `xe_force_wake_ref_has_domain()` itself is a plain `fw_ref & domain`.
- Single-domain request: a nonzero result means that domain is held, so
  `if (!fw_ref)` is a sufficient test; only an `XE_FORCEWAKE_ALL` request
  can return a partial nonzero mask.
- `xe_force_wake_put()` with 0: returns at once, so it is safe to call on
  any return value.
- **Potentially unsafe usage**: passing a constant instead of the returned
  reference to `xe_force_wake_put()`.
  - Unsafe: `XE_FORCEWAKE_ALL` after a get whose result lacks the
    `XE_FORCEWAKE_ALL` bit; put expands that bit to
    `fw->initialized_domains` and drops references that were never taken
    (`xe_gt_assert(gt, domain->ref)` catches it only under
    `CONFIG_DRM_XE_DEBUG` and only when the count is already 0).
  - Safe: `XE_FORCEWAKE_ALL` when the matching get returned a reference
    with the `XE_FORCEWAKE_ALL` bit, as `forcewake_release()` in
    `xe_debugfs.c` does for GTs that `forcewake_open()` fully woke.

**Scope-based forcewake**

- Three forms exist in `xe_force_wake.h`; there is no `DEFINE_GUARD()` form
  and no scope-specific has-domain helper.

| Form | Use |
|---|---|
| `CLASS(xe_force_wake, fw_ref)(fw, domains)` | get now, put at end of enclosing scope |
| `xe_with_force_wake(fw_ref, fw, domains)` | same, bound to the next statement or block |
| `CLASS(xe_force_wake_release_only, fw_ref)(ref)` | put only; the get happened in another function |

- `CLASS(xe_force_wake_release_only, ...)`: takes a
  `struct xe_force_wake_ref` by value and skips the put when `.fw` is NULL.
- `xe_force_wake_constructor()`: returns the `struct xe_force_wake_ref` to
  hand to the release-only class; see `force_wake_get_any_engine()` in
  `xe_drm_client.c`.
- Check after a single-domain request: in-tree code uses either
  `!fw_ref.domains` or
  `xe_force_wake_ref_has_domain(fw_ref.domains, domain)`; after an
  `XE_FORCEWAKE_ALL` request only the latter, with `XE_FORCEWAKE_ALL`,
  shows that every domain woke.

**xe SR-IOV**

- VF detection: `test_is_vf()` reads MMIO register `VF_CAP_REG`, not PCI
  config, and only when `xe->info.has_sriov`.
- PF detection: `xe_sriov_pf_readiness()` in `xe_sriov_pf.c`; needs
  `dev_is_pf()` and a non-zero minimum of `xe_configfs_get_max_vfs()` and
  the PCI total VFs; without `CONFIG_PCI_IOV` it is a stub returning false.
- `xe_configfs_get_max_vfs()`: the configfs value, falling back to the
  `max_vfs` module parameter.
- `XE_SRIOV_MODE_NONE` is 1; `xe->sriov.__mode == 0` means not probed yet.
- `vf_update_device_info()` in `xe_device.c`: runs in
  `xe_device_probe_early()` after `xe_sriov_probe_early()`; sets
  `xe->info.skip_pcode` and `xe->info.skip_guc_pc` and clears
  `probe_display` and other feature flags. There is no xe_pcode_init().
- `xe_wa_process_device_oob()` runs before `xe_sriov_probe_early()`, so
  device OOB workaround rules cannot match on VF mode; see the FIXME in
  `wa_14026539277()` in `xe_gt.c`.
- **Unsafe usage**: testing `IS_SRIOV_VF()` before
  `xe_sriov_probe_early()` has run.
  - Unsafe: `xe_device_sriov_mode()` asserts only under
    `CONFIG_DRM_XE_DEBUG`; otherwise the test silently returns false on a
    VF.
  - Safe: after `xe_sriov_probe_early()` has set `xe->sriov.__mode`, as
    the test before `vf_update_device_info()` in
    `xe_device_probe_early()`.
- **Potentially unsafe usage**: a probe step that reads or writes a
  register a VF cannot reach.
  - Unsafe: with no `IS_SRIOV_VF()` test and the value used for a
    decision; `xe_mmio_read32()` does no MMIO on a VF for a register
    without `XE_REG_OPTION_VF`, it returns 0 from `xe_gt_sriov_vf_read32()`
    when the PF did not supply the register, and `xe_mmio_write32()` drops
    the write; both warn only under `CONFIG_DRM_XE_DEBUG`.
  - Safe: return early for a VF before the access, as
    `xe_hwmon_register()`, `detect_preproduction_hw()` and
    `probe_has_flat_ccs()` do.
  - Safe: the register is defined with `XE_REG_OPTION_VF`, as `VF_CAP_REG`
    is.
  - Safe: forcewake; `__domain_ctl()` and `__domain_wait()` in
    `xe_force_wake.c` do nothing on a VF, so the get reports success.
  - Safe: the caller has excluded a VF and the callee only asserts it with
    `xe_gt_assert(gt, !IS_SRIOV_VF(...))`, as
    `xe_gt_mcr_unicast_read_any()` under `probe_has_flat_ccs()`; the assert
    is compiled out without `CONFIG_DRM_XE_DEBUG`.
- **Potentially unsafe usage**: calling `xe_pcode_read()` on a path a VF
  can reach.
  - Unsafe: when the output is used without being initialised first; with
    `xe->info.skip_pcode` `pcode_mailbox_rw()` returns 0 and leaves the
    output untouched.
  - Safe: the output is initialised before the call, as `max_freq_show()`
    in `xe_vram_freq.c` does.
  - Safe: the caller is never reached on a VF, as the hwmon callbacks,
    since `xe_hwmon_register()` returns early for a VF.
- Setup skipped for a VF needs the same test in its teardown:
  `xe_pm_runtime_init()` and `xe_pm_runtime_fini()` both return early.

**xe GuC command transport**

- `xe_guc_ct_init_noalloc()`: allocates no BO, but does allocate: it calls
  `alloc_ordered_workqueue()` and registers drm-managed actions, so it can
  fail with `-ENOMEM`.
- `xe_guc_ct_init()`: creates two BOs, `ct->ctbs.h2g.bo` and
  `ct->ctbs.g2h.bo`, in system memory, and registers
  `guc_action_disable_ct()` as a devm action.
- `xe_guc_ct_init_post_hwconfig()`: moves only the H2G BO to VRAM, only
  when `IS_DGFX()`; the G2H BO stays in system memory.
- `xe_guc_init_post_hwconfig()` returns through the VF branch first, so
  `xe_guc_ct_init_post_hwconfig()` is not called on a VF.
- `xe_guc_ct_restart()`: same as `xe_guc_ct_enable()` but skips the CTB
  re-initialisation, the registration with the GuC and
  `guc_ct_control_toggle()`; `xe_guc_ct_runtime_resume()` uses it.
- `stack_depot_init()`: called in `ct_dead_init()`, which
  `xe_guc_ct_init_noalloc()` calls; compiled only under
  `CONFIG_DRM_XE_DEBUG_GUC` nested inside `CONFIG_DRM_XE_DEBUG`.
- `fast_req_stack_save()`: the only caller of `stack_depot_save()` in xe;
  `ct_dead_capture()` saves no stack trace.
- `fast_req_stack_save()` runs from `h2g_write()`, which asserts
  `ct->lock` (a mutex) is held.
- **Potentially unsafe usage**: calling `stack_depot_save()` from xe code.
  - Unsafe: in code built without `CONFIG_DRM_XE_DEBUG_GUC`; xe has not
    called `stack_depot_init()`, and `stack_depot_save_flags()` in
    `lib/stackdepot.c` tests `stack_depot_disabled` but not `stack_table`
    for NULL before it indexes `stack_table`.
  - Safe: under `#if IS_ENABLED(CONFIG_DRM_XE_DEBUG_GUC)`, the same guard
    as the init and as the `stack` field of `struct xe_fast_req_fence`, as
    `fast_req_stack_save()` does.
- **Unsafe usage**: a GFP mask that allows direct reclaim for
  `stack_depot_save()` on the CT send path.
  - Unsafe: `primelockdep()` declares `ct->lock` as taken inside
    `fs_reclaim`, so reclaim under `ct->lock` is a lock inversion.
  - Safe: `GFP_NOWAIT`, as `fast_req_stack_save()` uses; `fast_req_dump()`
    prints a fallback when the handle is 0.

**xe runtime PM references**

- `xe_pm_runtime_resume_and_get()`: returns bool; false means no reference
  is held.
- `xe_pm_runtime_get_ioctl()`: returns int, negative on failure; on the
  normal path it is `pm_runtime_get_sync()`, which raises the count even
  on failure.
- `xe_pm_runtime_get_noresume()`: takes the reference even when it warns
  "Missing outer runtime PM protection", so a put is always owed.
- Callback-task tracking (`xe->pm_callback_task`, written at entry and
  exit of `xe_pm_runtime_suspend()` and `xe_pm_runtime_resume()`) is
  unconditional, not debug-only.

| Scope-based form | Wraps |
|---|---|
| `guard(xe_pm_runtime)(xe)` | `xe_pm_runtime_get()` |
| `guard(xe_pm_runtime_noresume)(xe)` | `xe_pm_runtime_get_noresume()` |
| `ACQUIRE(xe_pm_runtime_ioctl, pm)(xe)` | `xe_pm_runtime_get_ioctl()`; test `ACQUIRE_ERR(xe_pm_runtime_ioctl, &pm)` |
| `guard(xe_pm_runtime_release_only)(xe)` | put only; get was done elsewhere |

- `scoped_guard()` works with the `guard()` forms; see
  `scoped_guard(xe_pm_runtime, xe)` in `xe_guc_submit.c`.
- No scope-based form exists for `xe_pm_runtime_get_if_active()`,
  `xe_pm_runtime_get_if_in_use()` or `xe_pm_runtime_resume_and_get()`.
- **Potentially unsafe usage**: taking a runtime PM reference in code
  reached from `xe_pm_runtime_suspend()` or `xe_pm_runtime_resume()`.
  - Unsafe: `xe_pm_runtime_get_ioctl()`; on the callback task it WARNs and
    returns `-ELOOP` without taking a reference.
  - Unsafe: relying on `xe_pm_runtime_get_if_active()`; it has no
    callback-task test and returns false while the status is not
    `RPM_ACTIVE`.
  - Unsafe: from another task the callback waits for; only
    `current == xe->pm_callback_task` is treated as inside the callback,
    any other task goes on to `pm_runtime_resume()`.
  - Unsafe: calling `pm_runtime_get_sync()` or `pm_runtime_resume()`
    directly; that bypasses the callback-task test. All such calls in xe
    are inside `xe_pm.c`.
  - Safe: `xe_pm_runtime_get()`, `xe_pm_runtime_get_if_in_use()`,
    `xe_pm_runtime_get_noresume()` and `xe_pm_runtime_resume_and_get()` on
    the callback task; each tests `xe_pm_read_callback_task(xe) == current`
    and only raises the count, and `xe_pm_runtime_put()` then uses
    `pm_runtime_put_noidle()`. `xe_bo_move()` relies on this when
    `xe_bo_evict_all()` runs from `xe_pm_runtime_suspend()`.
  - Safe: work that must run while a callback is in progress pairs
    `xe_pm_runtime_get_if_active()` with a
    `xe_pm_read_callback_task(xe) == NULL` test and puts only if the get
    succeeded, as `receive_g2h()` in `xe_guc_ct.c` does.

**xe pcode mailbox**

- Power-limit mailbox value: two dwords, PL1 in the first and PL2 in the
  second; `attr` (`PL1_HWMON_ATTR` or `PL2_HWMON_ATTR`) selects which one
  `xe_hwmon_pcode_rmw_power_limit()` modifies.
- `xe_hwmon_pcode_read_power_limit()`: not a raw read; for
  `PL1_HWMON_ATTR` or `PL2_HWMON_ATTR` it returns one dword, and 0 unless
  `PWR_LIM_EN` is set in it.
- `xe_hwmon_pcode_rmw_power_limit()`: computes `(val & ~clr) | set`; `set`
  is not masked with `clr`.
- `hwmon->hwmon_lock`: taken with `mutex_lock()` by the sysfs callers of
  `xe_hwmon_pcode_rmw_power_limit()`; neither helper has a lockdep
  assertion, so a missing lock is not caught at run time.
- Platforms without `xe->info.has_mbx_power_limits`: the same fields live
  in a register and are updated with `xe_mmio_rmw32()` under the same
  `hwmon->hwmon_lock`.
- **Unsafe usage**: writing the two-dword power-limit value
  (`WRITE_PACKAGE_POWER_LIMIT`, `WRITE_PSYSGPU_POWER_LIMIT`) with
  `xe_pcode_write()` or `xe_pcode_write_timeout()`.
  - Unsafe: the single-dword writers pass a NULL `data1`, so
    `__pcode_mailbox_rw()` writes 0 to `PCODE_DATA1`, the PL2 dword.
  - Safe: `xe_pcode_read()` of both dwords succeeds, one field is changed,
    then `xe_pcode_write64_timeout()` sends both, the sequence in
    `xe_hwmon_pcode_rmw_power_limit()`.
  - Safe: a single-dword command, as `xe_hwmon_pcode_write_i1()` sends
    `POWER_SETUP_SUBCOMMAND_WRITE_I1` with `xe_pcode_write()`;
    `xe_hwmon_pcode_read_i1()` reads that value with a NULL second dword.
- **Potentially unsafe usage**: calling `xe_hwmon_pcode_rmw_power_limit()`
  without `hwmon->hwmon_lock`.
  - Unsafe: once the hwmon device is registered; `tile->pcode.lock` is
    dropped between the read and the write, so a concurrent sysfs store to
    another field of the same value is lost.
  - Safe: under `mutex_lock(&hwmon->hwmon_lock)`, as
    `xe_hwmon_power_max_write()` and
    `xe_hwmon_power_max_interval_store()` do.
  - Safe: before `devm_hwmon_device_register_with_info()`, as
    `xe_hwmon_get_preregistration_info()` does.
- Runtime PM for these paths: `xe_hwmon_read()` and `xe_hwmon_write()`
  take `guard(xe_pm_runtime)`; the interval show and store functions take
  their own, before `hwmon->hwmon_lock`.

## Intel display

**Intel display device**

- Allocation: `intel_display_device_probe()` uses `kzalloc_obj()`; nothing in
  xe allocates the struct itself.
- i915 caller: `i915_driver_probe()`, right after `i915_driver_create()`
  returns; not inside `i915_driver_create()`.
- xe caller: `xe_display_probe()` in `drivers/gpu/drm/xe/display/xe_display.c`;
  the free is the drmm action `display_device_remove()`. There is no
  xe_display_create().
- Probe precondition: it takes `pci_get_drvdata(pdev)` as the
  `struct drm_device *`, so the driver must have set drvdata first.
- Probe return: `ERR_PTR(-ENOMEM)` is the only error. Unknown device id,
  IVB Q, or an unrecognised GMD_ID still return a valid struct whose info is
  `no_display`; test `HAS_DISPLAY()` or `intel_display_device_present()`, not
  the pointer. For an id absent from `intel_display_ids[]` the probe logs
  "Unknown device ID" with `drm_dbg_kms()`.
- xe with `xe->info.probe_display` false at `xe_display_probe()`: probe is
  not called and `xe->display` stays NULL. The member exists only under
  `CONFIG_DRM_XE_DISPLAY`.
- Second probe argument: `const struct intel_display_parent_interface *`
  (`include/drm/intel/display_parent_interface.h`), kept in `display->parent`.
  Each driver passes its own static `parent`.
- `to_intel_display()`: does not accept `struct drm_i915_private *` or
  `struct xe_device *`. It does accept `struct device *` and
  `struct pci_dev *`, both through drvdata.
- `IS_TIGERLAKE()`-style macros: still defined in
  `drivers/gpu/drm/i915/i915_drv.h`, take i915, and have no users under
  `drivers/gpu/drm/i915/display/`. They do not take `display`.
- Version with release: `DISPLAY_VERx100()` and
  `IS_DISPLAY_VERx100(display, from, until)`; the latter build-fails when
  `from` is below 200. There is no DISPLAY_VER_FULL() or
  IS_DISPLAY_VER_FULL().
- Group bits: `display->platform.dgfx`, `display->platform.mobile` and
  `display->platform.g4x` are set by `PLATFORM_GROUP()` alongside the
  platform bit.
- `display->platform.haswell_ult` and `display->platform.broadwell_ult`: also
  set on ULX parts (`SUBPLATFORM_GROUP()`), so test the `_ulx` bit first when
  the two differ. Other platforms' `_ult` bits do not cover ULX.

**Register access functions**

- Wait names: every one carries a unit. intel_de_wait(),
  intel_de_wait_custom(), intel_de_wait_for_set(), intel_de_wait_for_clear()
  and intel_de_wait_fw() are not in this tree.

| Function | Reads with | Context |
|---|---|---|
| `intel_de_wait_us()`, `intel_de_wait_ms()` | `intel_de_read()` | may sleep |
| `intel_de_wait_for_set_us()`, `intel_de_wait_for_set_ms()` | `intel_de_read()`, no out value | may sleep |
| `intel_de_wait_for_clear_us()`, `intel_de_wait_for_clear_ms()` | `intel_de_read()`, no out value | may sleep |
| `intel_de_wait_fw_ms()` | `intel_de_read_fw()` | may sleep |
| `intel_de_wait_fw_us_atomic()` | `intel_de_read_fw()` | busy-waits |

- `intel_de_wait_for_register()`: exists, but is static in
  `drivers/gpu/drm/i915/display/intel_de.c`; callers use the functions above.
- `intel_wait_for_register()` and `__intel_wait_for_register()`: exist in
  `drivers/gpu/drm/i915/intel_uncore.h` for i915 core only;
  `drivers/gpu/drm/xe/compat-i915-headers/intel_uncore.h` has no wait helper,
  so display code cannot use them.
- `wait_for()`: lives in `drivers/gpu/drm/i915/i915_wait_util.h` and has no
  users under `drivers/gpu/drm/i915/display/`; display polls arbitrary
  conditions with `poll_timeout_us()` from `include/linux/iopoll.h`.
- Register type: `intel_reg_t` (typedef of `i915_reg_t` in
  `drivers/gpu/drm/i915/display/intel_display_reg_defs.h`), with
  `intel_reg_offset()` in place of `i915_mmio_reg_offset()`.
- First argument: `struct intel_display *` for every `intel_de_` function;
  none accepts i915.
- DMC wakelock: not taken by `intel_de_read_fw()`, `intel_de_write_fw()`,
  `intel_de_rmw_fw()`, `intel_de_read_notrace()`, `intel_de_write_notrace()`,
  `intel_de_read8()`, `intel_de_write8()`, `intel_de_read16()`,
  `intel_de_wait_fw_ms()` or `intel_de_wait_fw_us_atomic()`.
- `intel_de_write_dsb()` with a NULL `dsb`: falls back to
  `intel_de_write_fw()`, not `intel_de_write()`.
- I915_READ, I915_WRITE and POSTING_READ: not in this tree.

**Platforms and subplatforms**

- Names: the RPL-U macro is `INTEL_RPLU_IDS()`; the display descriptor type
  is `struct subplatform_desc`. There is no INTEL_ADLP_RPLU_IDS() or
  struct intel_subplatform_info.
- `struct xe_subplatform_desc`: defined in
  `drivers/gpu/drm/xe/xe_pci_types.h`.
- Nested id macro (for example `INTEL_MTL_U_IDS()` inside `INTEL_MTL_IDS()`,
  `INTEL_DG2_G10_IDS()` inside `INTEL_DG2_IDS()`): new ids reach every table
  that expands the platform macro.
- Sibling id macro (for example `INTEL_WCL_IDS()`, `INTEL_RPLU_IDS()`,
  `INTEL_ADLN_IDS()`): needs its own line in each table that should match
  it: `intel_display_ids[]`, `pciidlist[]` in `drivers/gpu/drm/xe/xe_pci.c`,
  and where relevant `drivers/gpu/drm/i915/i915_pci.c`,
  `arch/x86/kernel/early-quirks.c` and `drivers/vfio/pci/xe/main.c`.
- Reason for a display subplatform: either code tests the subplatform bit in
  `display->platform`, for example `display->platform.meteorlake_u`, or the
  entry carries its own `STEP_INFO()` map, which `get_pre_gmdid_step()`
  prefers over the platform's. For example `alderlake_p_raptorlake_p` and
  `dg2_g10` have a step map and no `display->platform.` test in the tree.
- Own id macro without a subplatform: `INTEL_ARL_H_IDS()` and
  `INTEL_ARL_S_IDS()` have none in display; only `INTEL_ARL_U_IDS()` is
  folded into `meteorlake_u`.
- Display and xe sets differ:

| Variant | Display | xe |
|---|---|---|
| WCL | subplatform `pantherlake_wildcatlake` | plain `ptl_desc`, no subplatform |
| ADL-N | subplatform `alderlake_p_alderlake_n` | own platform, `adl_n_desc` |
| RPL-P | subplatform `alderlake_p_raptorlake_p` | `adl_p_desc`, no subplatform |
| MTL-U, ARL-U | subplatform `meteorlake_u` | plain `mtl_desc` |
| BMG G21 | none | `XE_SUBPLATFORM_BATTLEMAGE_G21` |

- PHY example: `intel_encoder_is_c10phy()` in
  `drivers/gpu/drm/i915/display/intel_cx0_phy.c` returns true for
  `phy <= PHY_B` on `display->platform.pantherlake_wildcatlake` and only for
  `PHY_A` on other `display->platform.pantherlake`.
- WCL display IP: also has its own `gmdid_display_map[]` entry (30.02), so
  in-tree code tests either the subplatform bit or
  `DISPLAY_VERx100(display) == 3002`.

**CX0 PHY access**

- `intel_cx0_phy_transaction_begin()`: calls `intel_psr_pause()`, takes
  `POWER_DOMAIN_DC_OFF`, and programs the message bus timer on both lanes. It
  returns a `struct ref_tracker *`.
- Both transaction helpers are static in
  `drivers/gpu/drm/i915/display/intel_cx0_phy.c`. Code in another file that
  calls `intel_cx0_read()`, `intel_cx0_write()` or `intel_cx0_rmw()` needs its
  own bracket, as `intel_lt_phy_transaction_begin()` in
  `drivers/gpu/drm/i915/display/intel_lt_phy.c` provides (no timer
  programming there).
- Bracket themselves: `intel_cx0_phy_set_signal_levels()`,
  `intel_cx0pll_enable()`, `intel_cx0pll_disable()`,
  `intel_c10pll_readout_hw_state()`, `intel_c20pll_readout_hw_state()`,
  `intel_lnl_mac_transmit_lfps()`.
- Bracketed only through a callee: `intel_cx0pll_readout_hw_state()`,
  `intel_mtl_pll_enable()`, `intel_mtl_pll_disable()`,
  `intel_cx0_pll_power_save_wa()`. The `mtl_pll_funcs` hooks in
  `drivers/gpu/drm/i915/display/intel_dpll_mgr.c` call the first three and
  add no bracket of their own.
- Expect the caller to bracket: `intel_cx0_read()`, `intel_cx0_write()`,
  `intel_cx0_rmw()`, `intel_c20_sram_read()`, `intel_c20_sram_write()`,
  `intel_readout_lane_count()`, `intel_c10_pll_program()`,
  `intel_c20_pll_program()`, `intel_cx0_program_phy_lane()`,
  `intel_c20_readout_vdr_params()`, `intel_c20_program_vdr_params()`.
- **Unsafe usage**: a message bus access without `POWER_DOMAIN_DC_OFF` held.
  - Safe: between begin and end, as `intel_c20pll_readout_hw_state()` does;
    `__intel_cx0_read()` and `__intel_cx0_write()` check it with
    `assert_dc_off()`, a `drm_WARN_ON()`. PSR pause is not asserted.
- C10 step: `intel_c10_msgbus_access_begin()` before touching C10 registers;
  the programming paths, for example `intel_c10_pll_program()` and
  `intel_cx0_program_phy_lane()`, call `intel_c10_msgbus_access_commit()`
  after their writes. There is no intel_c10_msgbus_access_end().
- The transaction helpers do not call the C10 helpers;
  `intel_c10_msgbus_access_begin()` is a separate call inside the
  transaction, as in `intel_c10pll_readout_hw_state()`.
- Both C10 helpers return at once when `intel_encoder_is_c10phy()` is false,
  so shared C10/C20 paths call them unconditionally.
- `intel_c10_msgbus_access_commit()` with `master_lane` true: also sets
  `C10_VDR_CTRL_MASTER_LANE`; only `intel_c10_pll_program()` passes true.
- Read-only C10 access: `intel_c10pll_readout_hw_state()` calls begin and no
  commit.

## msm

**msm address spaces**

- `msm_context_vm()`: defined in `drivers/gpu/drm/msm/msm_drv.c`; returns NULL
  on failure, never an `ERR_PTR()`.
- `IS_ERR()` on its result: passes the NULL through; callers test `!vm`, as
  `msm_ioctl_gem_submit()` and `msm_ioctl_vm_bind()` do before
  `to_msm_vm(vm)->unusable`.
- Errno of the failure: lost. Callers return `UERR(ENOMEM, ...)` "no VM";
  `msm_gem_new_handle()` returns `-EINVAL`; `adreno_get_param()` accepts NULL.
- A failed creation is not cached: `ctx->vm` stays NULL and the next call
  tries again.
- Creation lock: `ctx->ctxlock` held for write, not a static mutex. The static
  `init_lock` in the same file belongs to `load_gpu()`.
- `msm_gpu_create_private_vm()` fallback to `gpu->vm`: only when
  `kernel_managed` is true. For a VM_BIND context a failing
  `create_private_vm` hook yields NULL from `msm_context_vm()`.
- `priv->gpu == NULL`: `msm_gpu_create_private_vm()` returns NULL, so callers
  may call `msm_context_vm()` before they test `priv->gpu`.
- `MSM_PARAM_EN_VM_BIND`: handled in `adreno_set_param()` in
  `drivers/gpu/drm/msm/adreno/adreno_gpu.c`, not in `msm_ioctl_set_param()`.
  The `-EINVAL` in that case tests for a missing `create_private_vm` hook; it
  does not compare `ctx->vm` with `gpu->vm`.
- **Potentially unsafe usage**: reading `ctx->vm` directly instead of calling
  `msm_context_vm()`.
  - Unsafe: on a path that needs a VM and can run before the first
    `msm_context_vm()` call on that context; the pointer is NULL and
    `to_msm_vm()` users dereference it.
  - Safe: `adreno_set_param()` for `MSM_PARAM_EN_VM_BIND`; it must not create
    the VM, and it holds `ctx->ctxlock` for read, which excludes creation
    under the write lock in `msm_context_vm()`.
  - Safe: `a6xx_set_pagetable()`; a `struct msm_gem_submit` exists only after
    `msm_ioctl_gem_submit()` got a non-NULL VM for the same context, and the
    queue holds a context reference from `msm_submitqueue_create()`.
  - Safe: `msm_gem_close()`; NULL means the context has no VM and so nothing
    to unmap. The NULL test is required: `put_iova_spaces()` with a NULL `vm`
    matches every VM and tears down other contexts' mappings.
  - Safe: `msm_submitqueue_close()`; it returns when `ctx->vm` is NULL, and
    it runs from `msm_postclose()`, after which no ioctl can create the VM.
  - Safe: `__msm_context_destroy()`; last reference, and `drm_gpuvm_put()`
    accepts NULL.
- `msm_kms_init_vm()` with no IOMMU on the MDP/DPU device or `mdss_dev`: logs
  "no IOMMU, bailing out" and returns `ERR_PTR(-ENODEV)`.
- `msm_kms_init_vm()` has no NULL return; every failure is an `ERR_PTR()`.
- Display init without IOMMU fails: the callers return `PTR_ERR(vm)`, dpu
  from `hw_init` (`dpu_kms_hw_init()`), mdp4 and mdp5 from `kms_init`
  (`mdp4_kms_init()`, `mdp5_kms_init()`); `msm_drm_kms_init()` fails, and
  `msm_drm_init()` unwinds through `msm_drm_uninit()`.
- No fallback to physically contiguous scanout: nothing under
  `drivers/gpu/drm/msm` has a vram carveout member or allocator.
- `kms->vm` NULL tests in the kms destroy paths (for example
  `mdp4_destroy()`'s `if (kms->vm)`): cover destroy after `kms_init` or
  `hw_init` failed before the VM was stored, not a running no-IOMMU mode.
- MMU constructor for display: `msm_iommu_disp_new()`, which wraps
  `msm_iommu_new()` and installs the display fault handler.

## Model gaps

### Other mistakes models make

- Models take the HDMI `supported_formats` and `display_info.color_formats`
  bits to be `enum hdmi_colorspace` values or DRM_COLOR_FORMAT_RGB444-style
  masks. Here each bit is `BIT()` of an `enum drm_output_color_format` value
  from `include/drm/drm_connector.h`, for example
  `BIT(DRM_OUTPUT_COLOR_FORMAT_RGB444)`; 4:4:4 and 4:2:2 are in the opposite
  order to `enum hdmi_colorspace`, and DRM_COLOR_FORMAT_RGB444 is defined
  nowhere.
- Models take any `struct file_operations` with `drm_open()` to be enough.
  Here `drm_open_helper()` in `drivers/gpu/drm/drm_file.c` fails with
  `-EINVAL` unless `fop_flags` has `FOP_UNSIGNED_OFFSET`; `DRM_GEM_FOPS` sets
  it.
- Models take an allocation call with no GFP argument to be an error. Here
  `kzalloc_obj()`, `kmalloc_objs()`, `kzalloc_flex()` and `kvmalloc_objs()` in
  `include/linux/slab.h` default to `GFP_KERNEL` through `default_gfp()`.
- Models take `drm_atomic_private_obj_init()` to receive the initial state and
  return nothing. Here it takes `dev`, `obj` and `funcs`, returns int, and
  calls `funcs->atomic_create_state` without testing it for NULL.
- Models take `dma_fence_signal()` to return an error for a fence that has
  already signalled. Here it returns void; `dma_fence_check_and_signal()`
  returns true when the fence was signalled before the call.
- Models take HDMI infoframes to go through one write and one clear callback
  of the connector. Here `struct drm_connector_hdmi_funcs` has one
  `struct drm_connector_infoframe_funcs` per type.
- Models take the legacy plane colour properties to apply to every commit.
  Here `drm_mode_atomic_ioctl()` sets `plane_color_pipeline` in
  `struct drm_atomic_commit` for a client with
  `DRM_CLIENT_CAP_PLANE_COLOR_PIPELINE`; no core helper reads it. The only
  reader is `fill_plane_color_attributes()` in
  `drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c`, which skips
  `color_encoding` and `color_range` when the flag is set and
  `plane_state->state` is non-NULL.

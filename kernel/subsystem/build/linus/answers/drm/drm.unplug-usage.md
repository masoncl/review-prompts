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

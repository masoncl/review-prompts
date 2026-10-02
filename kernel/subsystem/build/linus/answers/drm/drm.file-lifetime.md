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

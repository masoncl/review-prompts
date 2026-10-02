- `kfree(us->extra)`: done by `usb_stor_release_resources()` on every path,
  with or without a destructor.
  - `init_usbat()` in `drivers/usb/storage/shuttle_usbat.c` sets `us->extra`
    and no destructor.
- Destructor: frees only what the data points to, never the data itself.
- `us->extra_destructor`: called whenever it is non-NULL; `us->extra` is not
  tested.
  - After `init_realtek_cr()` fails through `INIT_FAIL` it is called with
    NULL, and `realtek_cr_destructor()` returns early.
  - After `rio_karma_init()` fails with `-EIO` it is called with fully
    allocated data.
- **Unsafe usage**: an init function that frees the data on its error path
  and leaves `us->extra` pointing at it.
  - Unsafe: `usb_stor_probe2()` then calls `release_everything()`, which runs
    any destructor on freed memory and frees the data again.
  - Safe: free before `us->extra` is assigned, as `isd200_init_info()` does.
  - Safe: free and set `us->extra` to NULL, with a destructor that accepts
    NULL, as `init_realtek_cr()` does.
  - Safe: free nothing and return the error, as `init_usbat()` does.
- There is no del_timer_sync() in this tree; `include/linux/timer.h` has
  `timer_delete_sync()` and `timer_shutdown_sync()`.
- Self re-arming timer: allowed; `rts51x_suspend_timer_fn()` re-arms itself,
  and `mod_timer()` does nothing once `timer_shutdown_sync()` has run.
- `timer_setup()` in `init_realtek_cr()`: comes right after `us->extra` is
  assigned and before any step that can fail, so the destructor never sees a
  non-NULL pointer with an uninitialised timer.
- `rts51x_suspend_timer_fn()`: takes neither `us->dev_mutex` nor the host
  lock and does not test `US_FLIDX_DISCONNECTING`; it reaches `us` through
  `chip->us`, which is valid until `scsi_host_put()`.
- Work items: no sub-driver in `drivers/usb/storage/` keeps one in
  `us->extra`; the core stops its own `us->scan_dwork` with
  `cancel_delayed_work_sync()` in `quiesce_and_remove_host()`.

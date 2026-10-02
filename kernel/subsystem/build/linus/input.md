# Input Subsystem

## Main structures

### Objects and how they relate

- `drivers/input/misc/uinput.c`: an event source, not a consumer; it registers
  a `struct input_dev` and has no `struct input_handler`.
- `dev->grab`: written under `dev->mutex`, read under RCU; `event_lock` does
  not protect it.
- With `dev->grab` set: `input_pass_values()` calls the grabbing handle only;
  filter handles, for example sysrq, are skipped as well.
- `struct evdev` has its own `grab` and `open`: `dev->grab` picks the handle,
  `evdev->grab` picks one `struct evdev_client` of that handle;
  `evdev_open_device()` calls `input_open_device()` for the first file only.
- `dev->open()` and `dev->close()`: not tied to first and last handle open
  alone. The first open of an inhibited device does not call `dev->open()`;
  `input_inhibit_device()` calls `dev->close()` and `input_uninhibit_device()`
  calls `dev->open()` while handles stay open.
- Handler-to-device direction: `input_inject_event()` goes through the same
  `input_handle_event()`, so an injected `EV_LED` reaches `dev->event()` while
  `dev->ready` is set and is passed to handles like a driver event, back to
  the injecting handle too; it is dropped when another handle holds the grab.
- `struct input_handle` memory: owned by the handler. The core does not
  allocate or free it, and `input_register_handle()` takes no reference on the
  device.
- Handle that outlives `disconnect()`: `evdev_disconnect()` does not free the
  `struct evdev`, it drops a reference with `put_device()`; `evdev_free()`
  frees the `struct evdev` after the last file closes, so `evdev_connect()`
  holds the device with `input_get_device()`.
- `connect()` need not create a handle: `kgdboc_reset_connect()` in
  `drivers/tty/serial/kgdboc.c` resets the device and returns `-ENODEV`.
- `struct ff_device`: the `event` and `flush` callbacks that
  `input_ff_create()` installs on the device are `input_ff_event()` and
  `input_ff_flush()` in `drivers/input/ff-core.c`.

## Where to look

### Core files

| Job | File | Easy to miss |
|---|---|---|
| `struct input_device_id`, its match flags such as `INPUT_DEVICE_ID_MATCH_BUS`, its limits such as `INPUT_DEVICE_ID_KEY_MAX` | `include/linux/device-id/input.h` | `include/linux/mod_devicetable.h` holds no definition of them, only `#include "device-id/input.h"`; `include/linux/input.h` includes `<linux/device-id/input.h>` directly, not `include/linux/mod_devicetable.h` |
| `struct serio_device_id`, `SERIO_ANY` | `include/linux/device-id/serio.h` | included by `include/linux/serio.h`; not defined in `include/linux/mod_devicetable.h` |
| uinput kernel-side state: `struct uinput_device`, `struct uinput_request` | `drivers/input/misc/uinput.c` | there is no include/linux/uinput.h in this tree; the only uinput header is `include/uapi/linux/uinput.h` |
| Touchscreen overlay helpers, such as `touch_overlay_map()` and `touch_overlay_process_contact()` | `drivers/input/touch-overlay.c`, `include/linux/input/touch-overlay.h` | separate from `drivers/input/touchscreen.c`; the only driver that includes the header is `drivers/input/touchscreen/st1232.c` |
| What `input-core.o` contains | `input-core-y` in `drivers/input/Makefile` | seven objects: `input.o`, `input-compat.o`, `input-mt.o`, `input-poller.o`, `ff-core.o`, `touchscreen.o`, `touch-overlay.o`; none has a Kconfig symbol of its own, all are built with `CONFIG_INPUT` |
| Declarations private to the input core | `drivers/input/input-core-private.h` | declares `input_mt_release_slots()` and `input_handle_event()`; included only by `drivers/input/input.c` and `drivers/input/input-mt.c` |
| Compat conversion of `struct input_event` (both directions) and `struct ff_effect` (from user only) | `drivers/input/input-compat.c`, `drivers/input/input-compat.h` | also defines `input_bits_to_string()`; the header is included by `drivers/input/input.c`, `drivers/input/evdev.c` and `drivers/input/misc/uinput.c` |
| Vivaldi function-row map helper | `drivers/input/vivaldi-fmap.c`, `include/linux/input/vivaldi-fmap.h` | built under `CONFIG_INPUT_VIVALDIFMAP`, beside the sparse and matrix keymap libraries |

## Open, close, inhibit and readiness

**Output events and readiness**

- `dev->ready` in `struct input_dev` (`include/linux/input.h`) is the gate:
  `input_event_dispose()` calls `dev->event()` only when the disposition has
  `INPUT_PASS_TO_DEVICE`, `dev->event` is set and `dev->ready` is true.
- `dev->ready` is not `input_device_enabled()`; it is a stored flag, true only
  between a successful `open()` and the matching `close()`.
- `event()` is therefore never called before the first `open()`, after the
  last `close()`, after a failed `open()`, or while inhibited.
- Gate opens in `input_start_device()` and `input_uninhibit_device()`:
  `open()` returns 0, then `ready = true`, then `input_dev_toggle(dev, true)`.
- Gate shuts in `input_close_device()` and `input_inhibit_device()`:
  `input_dev_toggle(dev, false)`, then `ready = false`, then `close()`.
- Device with no `open()` callback: `ready` is still set on the first user.
- `input_uninhibit_device()` with `dev->users == 0`: `ready` stays false and
  nothing is pushed.
- `input_dev_toggle()` calls only `dev->event()`; it does not release keys and
  does not touch the poller.
- `input_dev_toggle(dev, true)`: sends `REP_PERIOD` and `REP_DELAY` whenever
  `EV_REP` is in `dev->evbit`, whatever the values.
- `input_dev_toggle()` itself returns when `!dev->ready`, so
  `input_dev_suspend()`, `input_dev_resume()`, `input_dev_poweroff()` and
  `input_reset_device()` push nothing to a closed or inhibited device.
- Output event while not ready and not inhibited: `input_get_disposition()`
  still records it in `dev->led`, `dev->snd` or `dev->rep` and handlers still
  see it; only the driver call is skipped.
- Replay at gate open covers LED, SND and REP only; `EV_FF`, `EV_MSC`,
  `EV_PWR` and `SYN_CONFIG` sent while not ready are lost to the driver.

**Open and close callbacks**

- `input_start_device()` in `drivers/input/input.c` holds the user count and
  the `open()` call; `input_open_device()` calls it under `dev->mutex`.
- Handler with `passive_observer` set: `handle->open` is counted, but
  `input_start_device()` and the `--dev->users` branch are skipped, so such a
  handle never causes `open()` or `close()`.
- `passive_observer`: no handler in this tree sets it.
- `input_close_device()`: its first step is `__input_release_device()`.
- `synchronize_rcu()` in `input_close_device()`: runs when `--handle->open`
  reaches 0, not on list removal.
- `open()` error: `dev->users--` in `input_start_device()`, then
  `handle->open--` and `synchronize_rcu()` in `input_open_device()`;
  `handler->start()` is not called.
- Unregister: `input_disconnect_device()` zeroes every `handle->open` but
  leaves `dev->users`, so `close()` still runs from the handlers'
  `disconnect()` via `input_close_device()`, if the device is not inhibited.

**Flush callback**

- There is no evdev_flush() here and `evdev_fops` has no `.flush`;
  `input_flush_device()` is called from `evdev_release()`, `evdev_revoke()`
  and `evdev_cleanup()` in `drivers/input/evdev.c`.
- `evdev_release()`: the `.release` operation, so once per open file, not on
  every `close()` of a descriptor; it skips the flush when `evdev->exist` is
  clear or the client is revoked.
- `evdev_revoke()`: on the `EVIOCREVOKE` ioctl, with `evdev->mutex` held by
  `evdev_ioctl_handler()`.
- `evdev_cleanup()`: at handler disconnect when `evdev->open` is non-zero,
  with `file == NULL`, just before `input_close_device()`; on device
  unregistration `going_away` is already set.
- `file == NULL`: `input_ff_flush()` erases every effect whatever its owner;
  `uinput_dev_flush()` returns 0 without doing anything.
- `input_flush_device()` tests none of `users`, `inhibited`, `ready` or
  `going_away`; `flush()` can run on an inhibited device, after `close()`.
- `input_close_device()` does not call `flush()`.
- Return value: all three callers ignore it; on `-EINTR` `flush()` did not
  run.

**Inhibiting a device**

- Both `input_inhibit_device()` and `input_uninhibit_device()` return
  `-ENODEV` when `dev->going_away` is set; the test comes before the
  "already in that state" test, and `inhibited_store()` returns it to the
  writer.
- Release step: `input_mt_release_slots()`, `input_dev_release_keys()` and
  `SYN_REPORT` run after `close()`, also when `dev->users` is 0.
- `dev->inhibited = true`: set last, in the same `event_lock` section as the
  releases, so the release events still reach handlers.
- `input_uninhibit_device()`: clears `dev->inhibited` before calling `open()`
  and sets it back on error, so events the driver reports from inside
  `open()` are not dropped.
- Events while inhibited: `input_get_disposition()` returns
  `INPUT_IGNORE_EVENT` before any state update; this covers injected output
  events too, so an LED change requested while inhibited is not recorded in
  `dev->led` and `input_dev_toggle()` does not replay it on uninhibit.
- `input_repeat_key()`: stops repeating while `dev->inhibited` is set.

**Device mutex**

- `dev->mutex` also protects `dev->h_list` changes
  (`input_register_handle()`, `input_unregister_handle()`) and `dev->grab`
  changes.
- `dev->ready`: written with both `dev->mutex` and `dev->event_lock` held.
- `dev->inhibited`: set by `input_inhibit_device()` under both locks;
  `input_uninhibit_device()` clears it, and sets it back when `open()` fails,
  under `dev->mutex` only.
- `handle->open`: counted under `dev->mutex`, but zeroed by
  `input_disconnect_device()` under `dev->event_lock` only.
- `input_dev_set_poll_interval()` in `drivers/input/input-poller.c` takes the
  mutex but calls neither `open()` nor `close()`.
- Poll function: the first call, from `input_dev_poller_start()`, runs with
  `dev->mutex` held; later calls from the work item do not.
- Poll function must not take `dev->mutex`: `input_dev_poller_stop()` and the
  sysfs `poll` store call `cancel_delayed_work_sync()` with it held.
- `event()`: runs with `dev->mutex` held as well as `event_lock` when
  `input_dev_toggle()` calls it from open, close, inhibit, uninhibit or
  `input_reset_device()`; `input_event()`, `input_inject_event()` and the
  input PM callbacks do not take `dev->mutex`.
- Driver state read in `open()` or `close()` can be written under
  `input->mutex` from elsewhere; for example `ad7879_suspend()` sets
  `suspended`, which `ad7879_open()` reads.
- Driver sysfs store that reprograms hardware: takes `input->mutex` to
  exclude `open()` and `close()`, as `kxtj9_set_poll()` does.

**Polled devices**

- `input_setup_polling()` only allocates `struct input_dev_poller` and sets
  `dev->poller`; it does not set or wrap `dev->open` or `dev->close`.
- A polled device may have its own `open()` and `close()`; the core calls
  `input_dev_poller_start()` and `input_dev_poller_stop()` around them.
- Start, in `input_start_device()` and `input_uninhibit_device()`: after
  `open()` succeeded, after `ready = true` and after the LED/SND/REP replay.
- Stop, in both `input_close_device()` and `input_inhibit_device()`: before
  `input_dev_toggle(dev, false)` and before `close()`.
- Suspend: `input_dev_suspend()` and `input_dev_resume()` do not touch the
  poller; the only suspend handling is that the work is queued on
  `system_freezable_wq`.
- Maximum: `input_dev_poller_finalize()` sets `poll_interval_max` to the
  interval when the driver set none, so user space cannot set an interval
  above the one at registration.
- Minimum: defaults to 0, and interval 0 disables polling;
  `input_dev_poller_start()` then neither polls nor queues.
- Sysfs `poll` write on an enabled device: cancels and requeues the work; it
  does not call the poll function at once.
- `dev->poller`: freed by `input_dev_release()`; there is no devm variant of
  `input_setup_polling()`.

**Checking for an active device**

- Inside `open()`: `input_device_enabled()` is true, on first open and on
  uninhibit.
- Inside `close()`: false on the last close (`dev->users` is already 0), true
  on inhibit (`dev->inhibited` is set only after `close()` returns).
- `dev->mutex` is the outer lock: the core calls `open()` and `close()` with
  it held, so a suspend or resume callback must take it before any driver
  lock that `open()` or `close()` takes.
- Driver stop in suspend changes none of `dev->users`, `dev->inhibited` or
  `dev->ready`; the core still treats the device as open and may call
  `event()`.
- `lockdep_assert_held()` in `input_device_enabled()`: the only check; without
  lockdep an unlocked call races silently.
- **Unsafe usage**: calling `input_device_enabled()` on a path where nothing
  holds `dev->mutex`.
  - Safe: the callback takes `input->mutex` itself and keeps it across the
    hardware action, as `gpio_keys_suspend()` does; `input_device_enabled()`
    asserts the lock.
  - Safe: a helper that does not lock, when every caller already holds the
    mutex, as `samsung_keypad_toggle_wakeup()` called from
    `samsung_keypad_suspend()` and `samsung_keypad_resume()`.

## Registering and unregistering a device

**Setup before registration**

- `input_device_tune_vals()` at registration: only grows `dev->vals`, when
  `hint_events_per_packet + 2` exceeds `max_vals`.
- `input_allocate_device()`: does not set `dev->dev.groups`; the attribute
  groups come from `input_dev_type` in `drivers/input/input.c`.
- `input_cleanse_bitmasks()`: zeroes each whole per-type bitmap whose `EV_`
  bit is clear in `evbit`; it does not touch `propbit`.
- Softrepeat: `input_register_device()` calls
  `input_enable_softrepeat(dev, 250, 33)` whenever `rep[REP_DELAY]` and
  `rep[REP_PERIOD]` are both 0; it does not test `EV_REP` and does not set
  it.
- Driver-handled autorepeat: set either `rep[]` value non-zero before
  registering, otherwise `input_repeat_key()` is installed in `dev->timer`.
- `input_register_device()` also fills in `getkeycode` and `setkeycode`
  defaults and, when `dev->poller` is set, calls
  `input_dev_poller_finalize()`.
- `input_setup_polling()`, `input_mt_init_slots()` and `input_ff_create()`
  belong before registration: poller sysfs visibility, `dev->vals` sizing and
  `EV_FF` are evaluated there.
- The only precondition `input_register_device()` checks is `EV_ABS` with
  `dev->absinfo` NULL; a missing `name`, `id` or parent is accepted.

**Absolute axis information**

- `input_set_abs_params()`: sets `EV_ABS` and the `absbit` bit before it
  calls `input_alloc_absinfo()`; on allocation failure both bits stay set and
  registration then fails with `-EINVAL`.
- `input_set_capability()` with `EV_ABS`: also calls
  `input_alloc_absinfo()`, so it alone is enough to pass the registration
  check; min, max, fuzz, flat and resolution stay 0.
- Registration returns `-EINVAL` when `EV_ABS` was set in `evbit` by hand
  (`__set_bit()`) and no allocating helper was called, or when the
  allocation failed.
- The registration test looks at `EV_ABS` in `evbit`, not at `absbit`.

**Callbacks during registration**

- First `event()` call: `input_dev_toggle(dev, true)` in
  `input_start_device()`, straight after `open()`, under `event_lock` with
  interrupts off; it sends the state of every LED in `ledbit`, every sound in
  `sndbit` and, with `EV_REP`, both repeat values.
- `getkeycode()` and `setkeycode()`: not gated by `dev->ready`;
  `input_get_keycode()` and `input_set_keycode()` call them under
  `event_lock`, from evdev ioctls and from `drivers/tty/vt/keyboard.c`.
- During `input_register_device()`, `open()` called from a handler's connect
  runs in the registering thread, with `input_mutex` and `dev->mutex` held.

**Registration failure**

- Undone by the core: `device_del()` on the `-EINTR` path only, and
  `devres_free()` of the unregister devres it allocated for a managed device.
- Not on any list: the device is added to `input_dev_list` only after the
  last failure point.
- `dev->vals` is not freed on failure; `input_dev_release()` frees it.
- The poller is not touched on failure; `input_dev_poller_finalize()` only
  fills in default intervals.
- Left changed when `device_add()` fails or on the `-EINTR` path: `EV_SYN`,
  `KEY_RESERVED`, the cleansed bitmaps, softrepeat settings, default keycode
  callbacks.
- Left changed when `input_device_tune_vals()` fails: `EV_SYN`,
  `KEY_RESERVED` and the cleansed bitmaps, but not softrepeat or the keycode
  defaults.
- No handler was attached on any failure path, so `open()` and `event()`
  have not been called.

**Unregistration steps**

- Order in `__input_unregister_device()`:
  1. `input_disconnect_device()`: `going_away`, key-up events, every
     `handle->open = 0`.
  2. Under `input_mutex`: `disconnect()` for each handle,
     `timer_delete_sync(&dev->timer)`, `list_del_init(&dev->node)`, wake
     procfs readers.
  3. `dev->ff->stop()`, outside `input_mutex`.
  4. `device_del()`.
- There is no del_timer_sync in this tree; the call is
  `timer_delete_sync()`.
- Poller: `__input_unregister_device()` does not call
  `input_dev_poller_stop()`; the poller stops only when a handler's
  disconnect reaches `input_close_device()` and `dev->users` drops to 0.
- `dev->timer` is deleted, not shut down; see "Callbacks after
  unregistration" for what re-arms it.

**Callbacks after unregistration**

- There is no __input_close_device() here; `evdev_disconnect()` calls
  `evdev_cleanup()`, which calls `input_close_device()` when `evdev->open` is
  non-zero. `evdev_mark_dead()` only clears `evdev->exist`.
- `input_dev_toggle(dev, false)` calls `event()` with value 0 for each LED
  and sound that is on, so `event()` runs during unregistration, before
  `close()`.
- `close()` is skipped when `dev->inhibited` is set; `input_inhibit_device()`
  already called it if the device had users.
- During unregistration `close()`, `flush()` and `event()` run in the
  thread that unregisters, with `input_mutex` held.
- `input_event()` afterwards: nothing in the event path tests `going_away`;
  `input_get_disposition()` still updates `dev->key`, `dev->sw` and
  `absinfo` values.
- `input_event()` afterwards does not call `dev->event()`: `dev->ready` is
  clear once the device was closed or inhibited.
- A key press reported and synced afterwards on a device with `EV_REP`,
  `EV_KEY` and softrepeat re-arms `dev->timer` through
  `input_start_autorepeat()`; `input_dev_release()` does not delete that
  timer.

**Event device after disconnect**

- `evdev->exist` is the only thing that stops writes and ioctls after
  disconnect; `input_inject_event()`, `input_ff_upload()` and
  `input_set_keycode()` use `handle->dev` and do not test whether the handle
  is still registered.
- `evdev_write()` and `evdev_ioctl_handler()` test `exist` under
  `evdev->mutex`, so `evdev_mark_dead()` waits for one already running.
- `evdev_read()` and `evdev_poll()` test `exist` without `evdev->mutex`;
  neither calls into the driver.
- `evdev_disconnect()` calls `cdev_device_del()` before `evdev_cleanup()`.
- `evdev_poll()` with events still buffered: returns `EPOLLIN |
  EPOLLRDNORM` as well as `EPOLLHUP | EPOLLERR`; `evdev_read()` still returns
  `-ENODEV`.

**Reference counting**

- `input_register_handle()` takes no reference; a handler that needs the
  device after disconnect calls `input_get_device()` in its connect, as
  `evdev_connect()` does, and puts it in its release (`evdev_free()`).
- `kbd_connect()` takes no reference; its handle is freed in
  `kbd_disconnect()`.
- Initial reference: from `device_initialize()` in
  `input_allocate_device()`; dropped by `input_unregister_device()` for an
  unmanaged device, by `devm_input_device_release()` for a managed one.
- Unregistration uses `device_del()`, not `device_unregister()`.
- `input_dev_release()` also frees `dev->poller` and calls
  `module_put(THIS_MODULE)`.
- `ff->destroy()` and the `kfree()` of `ff->private` run at the last put,
  which can be after the driver's remove has returned, for example when an
  evdev file is still open.

**Freeing and unregistering**

- **Unsafe usage**: `input_unregister_device()` followed by
  `input_free_device()` on the same unmanaged device, or
  `input_free_device()` on a registered device.
  - Unsafe: unmanaged `input_unregister_device()` ends with
    `input_put_device()`, so the second call puts a reference that is gone.
  - Safe: `input_free_device()` only where registration never succeeded, as
    the `fail1` label of `atkbd_connect()` does.
  - Safe: a flag records success and selects one call, as
    `snd_jack_dev_disconnect()` in `sound/core/jack.c` does with
    `jack->registered`.
  - Safe: the pointer is set to NULL after `input_unregister_device()` and
    before the error path falls through to `input_free_device()`, as
    `sony_laptop_setup_input()` does with `key_dev`; `input_free_device()`
    does nothing for NULL.
- `input_free_device()` on a managed device: removes the allocation devres
  entry and puts; `WARN_ON()` fires only if the entry is not found.
- `input_unregister_device()` has no NULL check and dereferences `dev`;
  `psmouse_disconnect()` tests `psmouse->dev` first.

**Timers and work at teardown**

- **Potentially unsafe usage**: an IRQ handler, timer or work item that calls
  `input_event()` can still run when `input_unregister_device()` is called.
  - Unsafe: unmanaged device; `input_unregister_device()` ends with
    `input_put_device()`, which frees the device unless another reference is
    held.
  - Safe: unmanaged device with the source stopped first, as
    `palmas_pwron_remove()` in `drivers/input/misc/palmas-pwrbutton.c` does
    with `free_irq()` and `cancel_delayed_work_sync()`.
  - Safe: managed device with the source registered with devres after
    `devm_input_allocate_device()`; the struct stays allocated until
    `devm_input_device_release()` runs, as in `gpio_keys_probe()`. For the
    autorepeat timer see "Callbacks after unregistration".
- **Potentially unsafe usage**: a devres-managed source that uses the input
  device, registered before `devm_input_allocate_device()`.
  - Unsafe: when the source is live outside `open()` and `close()`;
    `release_nodes()` in `drivers/base/devres.c` runs entries in reverse, so
    `devm_input_device_release()` puts the device while the source is still
    live.
  - Safe: allocate first, then `devm_add_action()` and the IRQ request, as
    `gpio_keys_setup_key()` does.
  - Safe: an IRQ requested with `IRQF_NO_AUTOEN` that only `open()` enables
    and `close()` disables with `disable_irq()`, as in
    `wacom_w9000_probe()`; `input_close_device()` calls `close()` from the
    unregister entry, which runs before the release entry.
- **Potentially unsafe usage**: cancelling work or URBs that `event()` starts
  before `input_unregister_device()`.
  - Unsafe: when an LED or sound is on; `input_dev_toggle(dev, false)` calls
    `event()` during unregistration and queues the work again before private
    data is freed.
  - Safe: cancel after unregistering, as `usb_kbd_disconnect()` in
    `drivers/hid/usbhid/usbkbd.c` kills `kbd->led` after the call.
- A source started in `open()` and stopped synchronously in `close()` is
  stopped when unregistration returns; `close()` is skipped only when no
  `open()` is outstanding.
- A source started in probe is not stopped by `close()` when the device was
  never opened.

**Serio teardown**

- `serio_pause_rx()`: `spin_lock_irq()`, not irqsave;
  `serio_continue_rx()` enables interrupts unconditionally, so the pair is
  for callers with interrupts on.
- **Potentially unsafe usage**: `input_unregister_device()` before
  `serio_close()`.
  - Unsafe: unmanaged device, `interrupt()` reports unconditionally and the
    driver holds no extra reference; a byte arriving before `serio_close()`
    reaches `input_event()` on a freed device.
  - Safe: a flag cleared under `serio_pause_rx()` first, tested before any
    `input_event()`, as `atkbd_disable()` and `atkbd_receive_byte()` do for
    `atkbd_disconnect()`.
  - Safe: `input_get_device()` before unregistering and `input_put_device()`
    after `serio_close()`, as `elo_disconnect()` in
    `drivers/input/touchscreen/elo.c` does.
  - Safe: `serio_close()` first, as `nkbd_disconnect()` does.
- **Potentially unsafe usage**: cancelling work that `event()` queues before
  `input_unregister_device()`.
  - Unsafe: when an LED is on; unregistration calls `event()` and the work is
    queued again, then runs after `kfree()`.
  - Safe: `cancel_delayed_work_sync()` after unregistering and before
    `serio_close()`, as `atkbd_disconnect()` does; `atkbd_event_work()` only
    reschedules itself while `enabled` is clear.
- `atkbd_disconnect()` unregisters before `serio_close()`; it is not an
  example of close-first. `psmouse_disconnect()` is.

## Managed devices

**Managed allocation and teardown**

- Unregistration point in the devres stack: the end of a successful
  `input_register_device()`, not the allocation.
- Managed resource acquired between `devm_input_allocate_device()` and
  `input_register_device()`: released after the device is unregistered and
  before its reference is dropped.
- Managed resource acquired after `input_register_device()`: released before
  the device is unregistered.
- `devm_input_device_release()`: drops one reference; it frees only when that
  is the last one.
- `input_dev_release()` frees on the last put, which can come after unwinding;
  for example `evdev_connect()` takes a reference that only `evdev_free()`
  drops.

**Manual calls on managed devices**

- `devres_managed` in `struct input_dev`: the flag both calls test; only
  `devm_input_allocate_device()` sets it.
- `WARN_ON(devres_destroy(...))` in `input_free_device()` and
  `input_unregister_device()`: a missing entry only warns, the call then still
  puts or unregisters.
- Second `input_unregister_device()` on the same managed device: warns and
  runs `__input_unregister_device()` again.
- Second `input_free_device()` on the same managed device: drops a reference
  the caller no longer owns; the first put may already have freed the struct,
  otherwise the call warns.
- `input_unregister_device()` then `input_free_device()` on a managed device:
  each removes a different entry, one put in total, no warning.
- After a manual `input_unregister_device()` alone: the release entry still
  holds the reference, so the struct stays allocated until the parent unbinds.
- Driver that unregisters and re-creates managed devices while bound, as
  `cyapa_update_fw_store()` does: each old struct stays allocated until unbind.
- `input_free_device()` on a managed device that was never registered, or
  whose registration failed: supported; see `wacom_setup_inputs()` and
  `hidpp_connect_event()`.

**Parent of a managed device**

- `input_register_device()`, `input_unregister_device()` and
  `input_free_device()` read `dev->dev.parent` at call time to find the devres
  list; nothing else records the device given to
  `devm_input_allocate_device()`.
- Parent changed before registration: the unregister entry goes on the new
  parent, the release entry stays on the owner.
- Owner unbind with a changed parent: the reference is dropped while the
  device is still registered.
- `input_unregister_device()` with a parent changed before registration: finds
  its entry on the new parent, no warning.
- `input_free_device()` with a changed parent: misses the release entry, warns,
  puts; the entry left on the owner puts again at unbind.
- **Unsafe usage**: assigning a different device to `dev.parent` of a managed
  input device.
  - Safe: assigning the same device that was passed to
    `devm_input_allocate_device()`, as `gpio_keys_probe()` does; the devres
    calls in `drivers/input/input.c` then use the owner.
- Helpers with `dev.parent` NULL:

| Helper | Behaviour |
|---|---|
| `matrix_keypad_build_keymap()` | `WARN_ON()`, returns `-EINVAL` |
| `touchscreen_parse_properties()` | no check; `dev_fwnode()` dereferences NULL |
| `touch_overlay_map()` | no check; `dev_fwnode()` dereferences NULL |
| `input_setup_polling()` | works; parent only used for `dev_err()`, falls back to `&dev->dev` |
| `sparse_keymap_setup()` | works; managed keymap copy is attached to `&dev->dev` |

- `drivers/input/ff-memless.c`: does not use the parent or devres.

**Mixing managed and unmanaged resources**

- `probe()` error path after a successful `input_register_device()`: same
  rules as `remove()`; the device stays registered until devres is released
  after `probe()` returns, in `device_unbind_cleanup()` or, for an I2C or HID
  driver, in the `devres_release_group()` of `i2c_device_probe()` or
  `__hid_device_probe()`.
- **Potentially unsafe usage**: releasing a resource by hand in `remove()` of
  a driver whose input device is from `devm_input_allocate_device()`.
  - Unsafe: when the device is left to devres and `open()`, `close()`,
    `flush()`, `event()` or the poll function uses that resource; the device
    is still registered and `close()` runs later, from
    `devm_input_device_unregister()`.
  - Safe: `input_unregister_device()` first, then the teardown, as
    `sun4i_ts_remove()` does; `release_nodes()` in `drivers/base/devres.c`
    runs only after `remove()`.
  - Safe: teardown added as a devres action before `input_register_device()`,
    as `gpio_keys_setup_key()` does with `gpio_keys_quiesce_key()`;
    `release_nodes()` runs it after the unregister entry.
- **Potentially unsafe usage**: acquiring a managed resource after
  `input_register_device()`.
  - Unsafe: when `open()`, `close()`, `flush()`, `event()` or the poll
    function uses it; `release_nodes()` releases it before the unregister
    entry runs.
  - Safe: when it only feeds events and the device has no callback that uses
    it, as the IRQs in `rt5120_pwrkey_probe()`; the release entry keeps the
    device allocated until after the IRQ is freed.
- Explicit `input_unregister_device()` is required when:
  - `remove()` goes on to change state that the callbacks use.
  - The device has to go away while the driver stays bound, as in
    `cyapa_update_fw_store()`.
- Explicit `input_unregister_device()` is redundant when everything the
  callbacks use is managed and acquired before `input_register_device()`;
  `drivers/input/keyboard/gpio_keys.c` has no `remove()`.
- After an explicit `input_unregister_device()` in `remove()`: the driver's
  pointer stays valid until the release entry runs, so a managed IRQ requested
  after `devm_input_allocate_device()` that is still live does not see a freed
  device.

## Reporting events

**Path of an event**

- `handle->handle_events` precedence: `handler->filter` gives
  `input_handle_events_filter()`, else `handler->event` gives
  `input_handle_events_default()`, else `handler->events` is installed
  directly, else `input_handle_events_null()`.
- `input_handle_event()`: not static, declared in
  `drivers/input/input-core-private.h`; core paths and
  `drivers/input/input-mt.c` call it with `dev->event_lock` already held,
  without going through `input_event()`; it asserts `dev->event_lock` and
  makes no test of the event type against `dev->evbit` itself.
- `input_set_keycode()`: calls `input_event_dispose()` directly, so the
  key-up it sends for a removed keycode skips `input_get_disposition()`.

**Events the core drops**

- `dev->inhibited`: first test in `input_get_disposition()`; every event is
  dropped, `SYN_REPORT` included.
- `EV_KEY` value 2: passed to handlers whenever the code is in `dev->keybit`;
  `dev->key` is neither tested nor changed.
- `input_report_key()`: applies `!!value`, so it cannot send 2; a repeat needs
  `input_event()` directly.
- `EV_KEY` that passes: `INPUT_PASS_TO_HANDLERS` only, never `dev->event()`.
- `EV_SND`: dropped only when the code is not in `dev->sndbit`; an unchanged
  value still passes, `dev->snd` is just updated.
- `EV_FF`: dropped only when value < 0; value 0 passes; the core makes no
  `dev->ffbit` test here.
- `EV_MSC`: dropped only when the code is not in `dev->mscbit`; no code is
  special-cased.
- `EV_ABS` codes for which `input_is_mt_value()` is true (this excludes
  `ABS_MT_SLOT`), on a device with no `dev->mt`: no defuzz and no unchanged
  test, every value passes; see `input_handle_abs_event()`.
- Types with no case in the switch, for example `EV_FF_STATUS`: always
  dropped, so `input_report_ff_status()` reaches no handler.
- Passed with an unchanged value: accepted `EV_SYN` codes, `EV_KEY` value 2,
  non-zero `EV_REL`, `EV_MSC`, `EV_SND`, `EV_FF`, `EV_PWR`, and `EV_ABS`
  codes for which `input_is_mt_value()` is true without `dev->mt`.

**Frames and synchronisation**

- Driver that never syncs: `input_event_dispose()` appends `input_value_sync`
  and then calls `input_pass_values()`, so handlers do get a sync at the cut.
- Flush threshold: `dev->num_vals >= dev->max_vals - 2`, tested after each
  queued value; there is no INPUT_MAX_VALS in this tree.
- `dev->max_vals`: 10 from `input_allocate_device()`;
  `input_device_tune_vals()` raises it, never lowers it, and runs only from
  `input_register_device()`.
- `input_set_events_per_packet()` after registration: does not resize
  `dev->vals`.
- Synthetic sync: value 1; `input_sync()` sends value 0.
- `input_value_sync`: used only for the overflow flush; other core syncs pass
  a literal 1, for example `input_repeat_key()`.
- Value 1 is a convention the core does not enforce: `drivers/tty/sysrq.c`
  injects syncs with value 1 and `uinput_inject_events()` forwards whatever
  value userspace wrote.
- `evdev_pass_values()`: copies the sync value to the client unchanged.

**Events before registration**

- `dev->vals`: allocated by `input_allocate_device()` with `dev->max_vals` 10,
  so a pre-registration value is queued like any other.
- Many seeded values: the threshold flush at 8 queued values keeps the array
  from overflowing; it delivers to an empty `dev->h_list`.
- `input_sync()` before registration: dropped in `input_event()` unless the
  driver set `EV_SYN` in `dev->evbit`; `input_register_device()` is what sets
  it.
- `dev->num_vals`: written only in `input_event_dispose()`;
  `input_register_device()` does not reset it.
- `dev->event()`: not called before registration, because `dev->ready` is
  false; `dev->led`, `dev->snd` and `dev->rep` are still updated.
- `input_register_device()`: sends no event and no sync to handlers for the
  seeded state; handlers read the cached bitmaps and values instead.
- `EV_ABS` before registration: `input_handle_abs_event()` dereferences
  `dev->absinfo` with no NULL test; the test in `input_register_device()` has
  not run yet.
- `input_alloc_absinfo()` failure: only logged, and `input_set_abs_params()`
  has set the `dev->absbit` bit by then.

**Events sent to the device**

- `input_dev_toggle()`: static in `drivers/input/input.c`; see "Output events
  and readiness" for its callers.
- `input_dev_toggle()`: calls `dev->event()` directly under
  `dev->event_lock`, skipping `input_get_disposition()`, so the callback sees
  values that did not change.
- Types passed down include `EV_MSC` and `EV_SYN` with `SYN_CONFIG`; both are
  `INPUT_PASS_TO_ALL`.
- `ff->upload()` and `ff->erase()`: called from `input_ff_upload()` and
  `erase_effect()` under `ff->mutex`, outside `dev->event_lock`; they do not
  go through `input_ff_event()`.

**Reporting context and locks**

- `dev->event_lock`: a `spinlock_t`, not a `raw_spinlock_t`; `input_event()`
  takes it with `guard(spinlock_irqsave)`.
- Lock scope: one `input_event()` call, not one frame; concurrent callers are
  safe, but their values interleave in `dev->vals`.
- `input_repeat_key()`: takes the lock for its key and sync together, so an
  autorepeat frame can land inside a driver's open frame.
- Callbacks that the core calls under `dev->event_lock`: `dev->event()`,
  handler `event()`, `events()` and `filter()`, `ff->playback()`,
  `ff->set_gain()`, `ff->set_autocenter()`, `dev->getkeycode()`,
  `dev->setkeycode()`, and `play_effect()` of `drivers/input/ff-memless.c`.
- **Potentially unsafe usage**: a callback from the list above takes a driver
  spinlock.
  - Unsafe: when the driver also holds that lock across `input_event()`;
    `input_event_dispose()` calls `dev->event()` with `dev->event_lock`
    held, so the two orders deadlock.
  - Safe: when the lock is never held across a report, as `usb_kbd_event()`
    does with `leds_lock`; `usb_kbd_irq()` reports without it.
  - Safe: when the callback only records the request and schedules work, as
    `atkbd_event()` does.
- **Potentially unsafe usage**: calling `input_event()` from a handler
  callback or from `dev->event()`.
  - Unsafe: on the same device; `dev->event_lock` is already held and
    `input_event()` takes it again.
  - Safe: on another device, as `mac_hid_emumouse_filter()` in
    `drivers/macintosh/mac_hid.c` does; `mac_hid_emumouse_connect()` refuses
    to bind to that device, and `mac_hid_create_emumouse()` gives its lock
    its own class with `lockdep_set_class()`.

## Multitouch

**Initialising slots**

- Flags are in `include/linux/input/mt.h`; `INPUT_MT_DIRECT` and
  `INPUT_MT_DROP_UNUSED` are left out of the table.

| Flag | What the core does |
|---|---|
| `INPUT_MT_POINTER` | `BTN_TOOL_TRIPLETAP`, `BTN_TOOL_QUADTAP`, `BTN_TOOL_QUINTTAP` are set only when `num_slots` is at least 3, 4, 5 |
| `INPUT_MT_SEMI_MT` | sets `INPUT_PROP_SEMI_MT`, and makes `input_mt_sync_frame()` skip finger counting even with `INPUT_MT_POINTER` |
| `INPUT_MT_TRACK` | allocates `mt->red` and nothing else; does not turn on `INPUT_MT_DROP_UNUSED` behaviour |
| `INPUT_MT_TOTAL_FORCE` | sets no bit at init; `input_mt_report_pointer_emulation()` reports `ABS_PRESSURE` as the sum of `ABS_MT_PRESSURE` over active slots instead of the oldest contact's value |

- `ABS_MT_TRACKING_ID`: set to 0..`TRKID_MAX` unconditionally, replacing any
  range the driver set earlier.
- Order matters only with `INPUT_MT_POINTER` or `INPUT_MT_DIRECT`; with
  neither flag nothing is copied to the single-touch axes.
- MT axis declared after the call: `copy_abs()` skips an axis whose bit is not
  yet in `dev->absbit`, so `ABS_X`, `ABS_Y` or `ABS_PRESSURE` stays undeclared
  (not zero-ranged) unless the driver declares it itself, and the core drops
  the emulated events for an undeclared axis.
- `touchscreen_parse_properties()` with multitouch true may rewrite and swap
  the MT absinfo; run after the call, it leaves the single-touch copy with the
  earlier ranges.
- `copy_abs()` replaces the whole single-touch absinfo and forces fuzz to 0; a
  driver that wants its own `ABS_X`/`ABS_Y` parameters sets them after the
  call, as `drivers/input/mouse/synaptics.c` does for semi-mt pads.
- Too many slots: the limit is the literal 1024 in `input_mt_init_slots()`;
  there is no MT_SLOT_ABS_MAX in this tree.
- Second call: 0 when `num_slots` equals `dev->mt->num_slots` or is 0,
  `-EINVAL` for any other value; the flags of the second call are ignored.

**Reporting a frame of contacts**

- `input_mt_report_pointer_emulation()`: takes `ABS_X`, `ABS_Y` from the
  oldest active contact (wrap-aware compare of tracking ids), not from the
  lowest-numbered active slot.
- `input_mt_report_slot_state()` with a changed `tool_type` on an active slot:
  keeps the tracking id; the kerneldoc above it says a new id is assigned, the
  body assigns one only when the stored id is negative.
- `input_mt_sync_frame()` with `INPUT_MT_DROP_UNUSED`, and
  `input_mt_drop_unused()`: leave `mt->slot` at the last slot they dropped, so
  the next frame has to call `input_mt_slot()` before
  `input_mt_report_slot_state()`.
- `mt->frame` advances only in `input_mt_sync_frame()`,
  `input_mt_drop_unused()` and `input_mt_release_slots()`.
- `input_mt_get_slot_by_key()` with a driver that calls neither
  `input_mt_sync_frame()` nor `input_mt_drop_unused()`: while `mt->frame` does
  not advance, a slot that was reported once is not handed out again after
  release, since only slots that are inactive and not stamped with the
  current `mt->frame` are taken.

**Releasing contacts**

- `input_inhibit_device()` in `drivers/input/input.c` is the only caller of
  `input_mt_release_slots()`; it is reached by writing to the `inhibited`
  sysfs attribute.
- `input_dev_suspend()`, `input_dev_freeze()`, `input_disconnect_device()` and
  `input_reset_device()`: call `input_dev_release_keys()` and not
  `input_mt_release_slots()`, so `BTN_TOUCH` and the `BTN_TOOL_FINGER` family
  go up while every slot keeps its tracking id.
- `input_close_device()`: releases neither keys nor slots.
- `input_mt_release_slots()`: has no `EXPORT_SYMBOL()` and is declared only in
  `drivers/input/input-core-private.h`; drivers cannot call it.
- `input_mt_release_slots()`: does not call
  `input_mt_report_pointer_emulation()` and sends no `SYN_REPORT`; it sends
  `ABS_PRESSURE` 0 itself, and `input_inhibit_device()` follows it with
  `input_dev_release_keys()` and the `SYN_REPORT`.
- On every path except inhibit (system suspend and resume, controller reset,
  close) the core lifts no contact; where the hardware loses contacts there,
  only the driver can release them. For example `mms114_suspend()` in
  `drivers/input/touchscreen/mms114.c` and `mt_reset_resume()` in
  `drivers/hid/hid-multitouch.c`.
- Driver-side release: loop `input_mt_slot()` plus
  `input_mt_report_slot_inactive()` over all slots, then
  `input_mt_sync_frame()` or `input_mt_report_pointer_emulation()`, then
  `input_sync()`; see `mt_release_contacts()`.
- `input_mt_drop_unused()`: lifts only slots not reported since `mt->frame`
  last advanced, and does no pointer emulation, so `BTN_TOUCH` and
  `ABS_PRESSURE` stay as they were until emulation is run.

**Slot numbers from the device**

- `input_handle_abs_event()` on an out-of-range `ABS_MT_SLOT`: no warning, no
  error to the driver; it does not call `pr_warn_once()`.
- After an out-of-range slot: `mt->slot` keeps its previous value, so the
  following `input_mt_report_slot_state()` and `ABS_MT_POSITION_X` and other
  MT values activate, release or move the previously selected contact.
- `input_mt_get_value()`, `input_mt_is_active()`, `input_mt_is_used()`: take a
  slot pointer and check nothing; they are no safer than indexing
  `mt->slots[]` directly.
- `input_mt_assign_slots()`: on `-ENXIO` or `-EINVAL` it leaves `slots[]`
  unwritten; on success `input_mt_set_slots()` starts each entry at -1 and
  overwrites it only when a match or a free slot is found.
- **Potentially unsafe usage**: indexing a driver array or bitmap, or
  `dev->mt->slots[]`, with a slot number from the device.
  - Unsafe: when nothing before the access limits the number to the array
    size; the range test in `input_handle_abs_event()` guards only the core's
    `mt->slot`, and the driver never sees its result.
  - Safe: checked against the count that sizes the array and was passed to
    `input_mt_init_slots()`, and the contact skipped on failure, as
    `mt_process_slot()` does with `td->maxcontacts`; `mt_compute_slot()` can
    return the raw contact id, so the upper bound is needed there.
  - Safe: an "id minus one" number checked at both ends, as
    `process_packet_head_v4()` in `drivers/input/mouse/elantech.c` does
    against `ETP_MAX_FINGERS`, the size of `etd->mt[]`, or compared as
    unsigned, as `focaltech_process_abs_packet()` does against
    `FOC_MAX_FINGERS`, the size of `state->fingers[]`.
  - Safe: when the field width cannot exceed the array, as in
    `cyttsp_report_tchdata()`: ids are 4 bits and `CY_MAX_ID` (16) sizes both
    the bitmap and the slot count.
- **Potentially unsafe usage**: passing a slot number from the device to
  `input_mt_slot()` without a range check.
  - Unsafe: when the number can be negative or reach the declared slot count;
    memory stays intact, but the contact's data lands in the previously
    selected slot.
  - Safe: checked first and the contact skipped, as
    `goodix_berlin_report_state()` does against `GOODIX_BERLIN_MAX_TOUCH`,
    the same count it passes to `input_mt_init_slots()`.
  - Safe: when the field width cannot reach the slot count, as in
    `cyttsp_report_tchdata()`.

## Force feedback

**Creating a force-feedback device**

- `max_effects` upper limit: `FF_MAX_EFFECTS`, which is `FF_GAIN` (0x60) in
  `include/uapi/linux/input.h`; there is no FF_EFFECTS_MAX.
- `-EINVAL`: returned only for `max_effects == 0` and
  `max_effects > FF_MAX_EFFECTS`.
- Empty `dev->ffbit`: not checked by `input_ff_create()`.
- Size overflow: no separate test; the allocations are `kzalloc_flex()` and
  `kzalloc_objs()`, and a failure returns `-ENOMEM`.
- `upload` and `playback`: both mandatory; `input_ff_upload()` calls
  `ff->upload`, and `erase_effect()` and `input_ff_event()` call
  `ff->playback`, with no NULL test.
- `stop`: a further optional callback of `struct ff_device`, NULL-checked in
  `__input_unregister_device()`; see "Memoryless helper timer".
- `dev->event` and `dev->flush`: overwritten unconditionally by
  `input_ff_create()`; a driver that needs its own installs them after the
  call, as `uinput_create_device()` does.
- Driver-owned `dev->event`: `EV_FF` events reach `ff->playback`,
  `ff->set_gain` and `ff->set_autocenter` only if that handler calls
  `input_ff_event()`, as `hidinput_input_event()` does.
- `dev->ffbit` at registration: `input_cleanse_bitmasks()` zeroes it when
  `EV_FF` is not set in `dev->evbit`, so bits set with `set_bit()` alone,
  without a later `input_ff_create()` before `input_register_device()`, are
  lost; `input_set_capability()` sets `EV_FF` itself.

**Freeing the ff device**

- `ff->private`: freed by `input_ff_destroy()` itself with `kfree()`, after
  `ff->destroy` returns; `ff->destroy` frees only what hangs off it, as
  `hidpp_ff_destroy()` does.
- `EV_FF`: cleared by `input_ff_destroy()` first, also when `dev->ff` is NULL.
- `dev->event` and `dev->flush`: not reset by `input_ff_destroy()`.
- Second call: a no-op for the free, since `dev->ff` is NULL; the call from
  `input_dev_release()` always follows a driver's own call.
- Explicit call before `input_free_device()`: redundant;
  `input_dev_release()` runs `input_ff_destroy()`.
- **Potentially unsafe usage**: a driver calling `input_ff_destroy()` itself.
  - Unsafe: on a device that is or will be registered while `dev->flush` is
    still `input_ff_flush()`; `input_flush_device()` calls `dev->flush`
    whenever it is set, and `input_ff_flush()` dereferences `dev->ff` with no
    `EV_FF` test.
  - Safe: on the error path where `input_register_device()` has not
    succeeded and `input_free_device()` follows, as `xpad_init_input()` and
    `uinput_create_device()` do; no handle exists to call
    `input_flush_device()`.

**Memoryless helper timer**

- `ff->stop`: set to `ml_ff_stop()` by `input_ff_create_memless()`; it runs
  `timer_shutdown_sync()` on `ml->timer`.
- Caller of `ff->stop`: `__input_unregister_device()` in
  `drivers/input/input.c`, after the handlers are disconnected and before
  `device_del()`; both `input_unregister_device()` and
  `devm_input_device_unregister()` go through it.
- After `input_unregister_device()` returns: the timer cannot fire or be
  re-armed; `mod_timer()` on a shut-down timer is ignored.
- `ff->destroy`: `ml_ff_destroy()` runs `timer_shutdown_sync()` again at
  release; this is the only stop for a device that was never registered.
- `ff->playback` with value 0: reaches `ml_schedule_timer()`, which calls
  `timer_delete()` (not synchronous) once no started effect has a future
  event; `erase_effect()` and `input_ff_flush()` stop the timer only this way.
- `ff->erase`: not set by the helper; there is no ml_ff_erase() or
  ml_ff_flush().
- `dev->close`, suspend, inhibit: no helper hook; `input_inhibit_device()`
  calls `dev->close` but not `dev->flush`, so effects stay started and the
  timer keeps calling `play_effect`.
- Left to the driver: stopping the hardware and its own work or URBs at
  close, suspend and unbind; see "Deferred effect playback".

**Memoryless helper data**

- `data` after success: owned by the helper; `ml_ff_destroy()` runs
  `kfree(ml->private)` at release of the input device, which can be later
  than unbind.
- Probe failure after a successful call: `data` is freed with the input
  device, through `input_free_device()` or `input_ff_destroy()`.
- Callers that free `data` on failure: for example `pl_input_configured()`
  in `drivers/hid/hid-pl.c`, `lg2ff_init()` in `drivers/hid/hid-lg2ff.c` and
  `gc_n64_init_ff()` in `drivers/input/joystick/gamecon.c`; there is no
  plff_init() here.
- `xpad_init_ff()`, `gpio_vibrator_probe()` and `drivers/hid/hid-lg4ff.c`:
  pass NULL, so they have nothing to free.
- **Unsafe usage**: passing `data` that `kfree()` must not free, or that
  something else also frees (devm memory, the driver's main state, a static).
  - Unsafe: `ml_ff_destroy()` runs `kfree()` on `data` at release.
  - Safe: pass NULL and fetch state with `input_get_drvdata()` in
    `play_effect`, as `winwing_init_ff()` and `winwing_play_effect()` do;
    `ml_ff_destroy()` then frees nothing.
  - Safe: pass a dedicated `kzalloc_obj()` block and free it only when
    `input_ff_create_memless()` fails, as `zp_input_configured()` in
    `drivers/hid/hid-zpff.c` does; on failure the helper has not taken
    `data`.
- **Unsafe usage**: using a saved copy of `data` after the driver has dropped
  its reference to the input device.
  - Unsafe: `ml_ff_destroy()` frees `data` at release of the input device.
  - Safe: use `data` only through the `play_effect` argument, as
    `hid_plff_play()` does; `ml_play_effects()` passes `ml->private`, which
    lives as long as the `struct ff_device`.

**Deferred effect playback**

- Lock held around `play_effect`: `dev->event_lock`; `struct ml_device` has
  no timer_lock field.
- `erase_effect()` in `drivers/input/ff-core.c`: calls `ff->playback`
  directly under `dev->event_lock`, not through `dev->event`, so it reaches
  `play_effect` when `dev->ready` is false or `dev->inhibited` is set.
- `input_ff_event()` path: reached only while `dev->ready` is set
  (`input_event_dispose()`) and `dev->inhibited` is clear
  (`input_get_disposition()`).
- After `input_unregister_device()` returns: the helper no longer calls
  `play_effect` from the timer (see "Memoryless helper timer"), so work
  stopped after that point is not re-queued.
- `play_effect` after `dev->close`: possible on an inhibited device, from the
  timer and from `erase_effect()`.
- Suspend: the helper does not stop the timer, so `play_effect` can queue
  work after the suspend callback has cancelled it.
- `regulator_haptic_suspend()`: does not call `cancel_work_sync()`; it sets
  `haptic->suspended` under `haptic->mutex`, which `regulator_haptic_work()`
  tests.
- `isa1200_suspend()`: when `input_device_enabled()` is true, sets
  `isa->suspended`, which `isa1200_vibrator_play_effect()` tests before
  `schedule_work()`.
- **Potentially unsafe usage**: stopping deferred work only in `dev->close`.
  - Unsafe: when the work uses data freed at unbind and nothing stops the
    work after `input_unregister_device()`; on a device inhibited through
    sysfs the flush at unregister calls `play_effect`, and `dev->close` does
    not run.
  - Safe: stop the work or URBs after `input_unregister_device()` and before
    freeing, as `xpad_disconnect()` does with `xpad_stop_output()`;
    `ml_ff_stop()` has shut the timer down by then.
- **Potentially unsafe usage**: `cancel_work_sync()` before the input device
  is unregistered.
  - Unsafe: when nothing stops `play_effect` from queuing the work again.
  - Safe: set a flag under a lock that the queuing path tests, then cancel,
    as `bigben_remove()` and `bigben_schedule_work()` do.

## Handlers

**Handler event methods**

- `input_handle_setup_event_handler()`: static in `drivers/input/input.c`;
  `handle->handle_events`, which it sets, is the only pointer
  `input_pass_values()` calls.
- A handler may set at most one of `filter()`, `event()` and `events()`:
  `input_handler_check_methods()` makes `input_register_handler()` return
  `-EINVAL` otherwise.
- A handler that sets none of the three is accepted, for example
  `kgdboc_reset_handler` in `drivers/tty/serial/kgdboc.c`; a handle of such a
  handler gets `input_handle_events_null()`.
- `events()` returning 0: ends the walk of `dev->h_list`, so no later handle
  sees the packet; `evdev_events()` returns `count` unchanged.
- `filter()` returning `true`: `input_handle_events_filter()` removes that one
  value and passes the rest of the packet on; the walk stops only when no
  value is left.
- With `dev->grab` set: `input_pass_values()` calls only the grabbing handle,
  so filters on the device do not see the events, and `handle->open` of the
  grabber is not tested.

**Connect and disconnect**

- On device removal, `disconnect()` runs after `input_disconnect_device()`,
  which has already set `dev->going_away` and written 0 to `handle->open` on
  every handle of the device.
- `input_close_device()` in `disconnect()` is still needed on that path to
  drop `dev->users`; it leaves `handle->open` at -1.
- **Potentially unsafe usage**: calling `input_open_device()` on a
  `struct input_handle` that an earlier `disconnect()` already closed.
  - Unsafe: when `handle->open` is left at -1; the open brings it to 0, so
    `input_pass_values()` skips the handle and `start()` is not called.
  - Safe: a handle from a zeroing allocation, as in `kbd_connect()` in
    `drivers/tty/vt/keyboard.c`; `input_open_device()` then brings
    `handle->open` from 0 to 1.
  - Safe: an embedded handle whose `handle->open` is reset to 0 first, as in
    `appletb_kbd_inp_connect()` in `drivers/hid/hid-appletb-kbd.c`.
- `handler->id_table`, `handler->connect` and `handler->disconnect`: used with
  no NULL test, in `input_match_device()`, `input_attach_handler()`,
  `__input_unregister_device()` and `input_unregister_handler()`.

**Start callback**

- `input_register_handle()`: does not call `start()`.
- `input_attach_handler()`: has no `start()` call of its own; it reaches
  `start()` only when `connect()` calls `input_open_device()`.
- `start()` has three call sites, all in `drivers/input/input.c`, all with
  `dev->mutex` held:

| Call site | Called for | When |
|---|---|---|
| `input_open_device()` | the handle being opened | `handle->open` just became 1 |
| `__input_release_device()` | every handle on `dev->h_list` with `handle->open` non-zero | the caller held the grab; after `synchronize_rcu()` |
| `input_uninhibit_device()` | every handle on `dev->h_list` with `handle->open` non-zero | end of uninhibit |

- `__input_release_device()`: reached from `input_release_device()` and from
  `input_close_device()`; in the second it runs before `handle->open` is
  decremented, so a closing handle that held the grab gets `start()` too.
- `input_mutex`: held in `start()` when `input_open_device()` is called from
  `connect()`, as `kbd_connect()` does; not held when `start()` comes from
  `input_uninhibit_device()` or from the `input_release_device()` in
  `evdev_ungrab()`.
- A handle that is never opened never gets `start()`.
- `input_open_device()` calls `start()` even when `dev->inhibited` is set;
  `input_get_disposition()` drops events injected then, and
  `input_uninhibit_device()` calls `start()` again.
- `rfkill_connect()` in `net/rfkill/input.c`: its comment says
  `input_register_handle()` causes `rfkill_start()`; the call comes from the
  `input_open_device()` that follows.
- **Unsafe usage**: `start()` calling anything that takes `dev->mutex` of the
  same device, for example `input_open_device()`, `input_close_device()`,
  `input_grab_device()`, `input_release_device()` or
  `input_unregister_handle()`; the calling thread already holds that mutex,
  so the call blocks on it.
  - Safe: `input_inject_event()`, which takes only `dev->event_lock`, as
    `kbd_update_leds_helper()` called from `kbd_start()` does when
    `CONFIG_INPUT_LEDS` or `CONFIG_LEDS_TRIGGERS` is off.
  - Safe: taking `dev->event_lock` with `spin_lock_irq()`, as `rfkill_start()`
    does; no `start()` call site holds `dev->event_lock`.

## Core locking and other users

**Lock order**

- One chain nests four of the locks: `evdev_release()` holds `evdev->mutex` →
  `input_flush_device()` takes `dev->mutex` → `input_ff_flush()` takes
  `ff->mutex` → `erase_effect()` takes `dev->event_lock`.
- `ff->mutex` nests inside `dev->mutex`: `input_flush_device()` holds
  `dev->mutex` across `dev->flush()`, so `ff->erase()` may sleep under both.
- `input_ff_upload()` and `input_ff_erase()` from `evdev_do_ioctl()`: entered
  with `evdev->mutex` held and without `dev->mutex`.
- `input_disconnect_device()`: holds `dev->mutex` only while it sets
  `dev->going_away`, releases it, then takes `dev->event_lock`; the two are
  not nested there.
- `dev->event_lock` under `dev->mutex`: `input_reset_device()`,
  `input_start_device()`, `input_close_device()`, `input_inhibit_device()` and
  `input_uninhibit_device()`; the last four take it to change `dev->ready`.
- `handler->disconnect()`: called under `input_mutex`;
  `__input_unregister_device()` holds neither `dev->mutex` nor
  `dev->event_lock` when it takes `input_mutex`.
- evdev disconnect path: `evdev_mark_dead()` releases `evdev->mutex` before
  `evdev_cleanup()` calls `input_flush_device()` and `input_close_device()`;
  the path gives `input_mutex` → `evdev->mutex` and `input_mutex` →
  `dev->mutex`, not `input_mutex` → `evdev->mutex` → `dev->mutex`.
- PM callbacks `input_dev_suspend()`, `input_dev_resume()`,
  `input_dev_freeze()`, `input_dev_poweroff()`: take only `dev->event_lock`,
  not `dev->mutex`.
- `input_enable_softrepeat()`: takes no lock.
- `input_register_handle()`: does not call `synchronize_rcu()`.
- `input_unregister_handle()`: calls `synchronize_rcu()` after it has released
  `dev->mutex`.
- `handle->h_node`: added and removed outside `dev->mutex`; the only
  serialization is `input_mutex`, held by the core around `connect()` and
  `disconnect()`.
- `ff->stop()`: called by `__input_unregister_device()` after `input_mutex` is
  released, with no core lock held; `ml_ff_stop()` waits for a timer whose
  handler `ml_effect_timer()` takes `dev->event_lock`.
- Handler spinlock from process context: `evdev_handle_get_val()` and
  `joydev_0x_read()` take `dev->event_lock` first, then `client->buffer_lock`,
  the same order as the event path.
- mousedev: `mousedev_mix->mutex` → `mousedev->mutex` → `dev->mutex`, in
  `mixdev_open_devices()` and `mixdev_add_device()`; the latter runs from
  `mousedev_connect()`, so under `input_mutex`. The mixdev mutex has lockdep
  subclass `SINGLE_DEPTH_NESTING`.
- uinput: `state_lock` in `struct uinput_device` is outside
  `dev->event_lock`; `uinput_request_send()` takes it, then
  `dev->event_lock`.
- uinput: `udev->mutex` is outside `input_mutex`; `uinput_ioctl_handler()`
  holds it across `input_register_device()` and `input_unregister_device()`.
- `uinput_dev_flush()`: skips `input_ff_flush()` when `file` is NULL;
  `UI_DEV_DESTROY` reaches it with `udev->mutex` held, and the reply to an
  erase request (`UI_END_FF_ERASE`) needs that mutex.

**Changing the core**

- There is no input_to_handler() here; `input_pass_values()` in
  `drivers/input/input.c` calls `handle->handle_events()` with no NULL test.
- `handle->handle_events`: set by `input_handle_setup_event_handler()` at the
  top of `input_register_handle()`, before the handle goes on `dev->h_list`.
- `handle_events()` return value: the number of values left; the walk stops
  when it is 0, and the autorepeat loop after the walk uses the same count.
- `handler->events()`: returns `unsigned int` and must return the count it
  was given unless it drops values; `evdev_events()` is the only in-tree one.
- `input_handle_events_filter()`: compacts `vals` in place, so later handles
  see the filtered array.
- `handle->open`: `input_disconnect_device()` zeroes it for every handle under
  `dev->event_lock` alone, with no `dev->mutex` and no grace period; the walk
  relies on `dev->event_lock` for this, which `input_pass_values()` asserts.
- RCU read section in the event path of `drivers/input/input.c`: opened in
  `input_pass_values()` and `input_inject_event()`, not in `input_event()`.
- `dev->event()` called from `input_event()`: runs under `dev->event_lock`
  outside the RCU read section; called from `input_inject_event()` it runs
  inside it.
- `synchronize_rcu()` in `drivers/input/input.c`: four calls, in
  `__input_release_device()`, the error path of `input_open_device()`,
  `input_close_device()` and `input_unregister_handle()`; the first three run
  under `dev->mutex`.
- There is no INPUT_COMPAT_TEST in this tree.
- Compat test for events (`input_event_size()`, `input_event_from_user()`,
  `input_event_to_user()`), under `CONFIG_COMPAT`:
  `in_compat_syscall() && !COMPAT_USE_64BIT_TIME`.
- Compat test for effects (`input_ff_effect_from_user()`,
  `uinput_ff_upload_to_user()`, `uinput_ff_upload_from_user()`), under
  `CONFIG_COMPAT`: `in_compat_syscall()` alone.
- `input_ff_effect_from_user()`, compat branch: copies
  `sizeof(struct ff_effect_compat)` bytes into the native `struct ff_effect`
  through a cast, then rewrites only `u.periodic.custom_data`, and only for
  `FF_PERIODIC` with `FF_CUSTOM`.
- uinput upload helpers: `memcpy()` of `sizeof(struct ff_effect_compat)`
  between the native and compat structs, with no pointer fix-up.
- Both copies rely on every field before `custom_data` having the same offset
  in `struct ff_effect` and `struct ff_effect_compat`, and on `custom_data`
  being last.
- `haptic` (`struct ff_haptic_effect`): in the union of `struct ff_effect`,
  absent from `struct ff_effect_compat`; the bulk copy carries it because it
  holds no pointer or `long` and is smaller than
  `struct ff_periodic_effect_compat`.
- `EVIOCSFF`: matched with `EVIOC_MASK_SIZE()`, which ignores the size bits;
  `input_ff_effect_from_user()` then requires `size` to equal the struct size
  exactly and returns `-EINVAL` otherwise, which `evdev_do_ioctl()` reports
  as `-EFAULT`.
- Changing `sizeof(struct ff_effect)`: makes `EVIOCSFF` from existing native
  binaries fail that equality test; compat callers are compared against
  `sizeof(struct ff_effect_compat)`.
- `EVIOCSFF` write-back: `evdev_do_ioctl()` stores `effect.id` through
  `&((struct ff_effect __user *)p)->id` for compat callers too, so `id` must
  keep the same offset in both structs.
- There is no tools/testing/selftests/input/ directory in this tree.
- `tools/testing/selftests/bpf/test_lirc_mode2_user.c`: the only file under
  `tools/` that names `struct input_event`; it reads
  `sizeof(struct input_event)` bytes from an evdev node.
- `struct ff_effect` and `EVIOCSFF`: named by no file under `tools/`.
- `tools/testing/selftests/hid/`: creates devices through uhid and reads
  them with the Python libevdev module; it does not use uinput.
- `drivers/input/tests/input_test.c`: sends no event and touches neither
  struct.
- Size assertions: `drivers/input/evdev.c`, `drivers/input/input-compat.c`,
  `drivers/input/input-compat.h` and `drivers/input/misc/uinput.c` contain no
  `BUILD_BUG_ON()` or `static_assert()`, so a layout change builds cleanly.

## Maintainer conventions

**Error variables and cleanup guards**

- Written style rules: none specific to input; the nearest thing is the
  example driver in `Documentation/input/input-programming.rst`, which uses
  `int error` with `goto err_free_dev` / `err_free_irq` labels and no cleanup
  helper.
- `Documentation/input/input-programming.rst`: has no text on `devm_`
  (managed) allocation.
- Guard conversion is per file, not core-wide:

| Files under `drivers/input/` | Locking style |
|---|---|
| `input.c`, `ff-core.c`, `ff-memless.c`, `input-mt.c`, `input-poller.c`, `serio/serio.c` | `guard()`, `scoped_guard()`, `scoped_cond_guard()` |
| `evdev.c`, `joydev.c`, `mousedev.c`, `misc/uinput.c` | open-coded lock/unlock pairs with `goto out`; no cleanup helper anywhere in the file |

- `drivers/input/input.c`, the open-coded exception:
  `input_devices_seq_start()` and `input_handlers_seq_start()` call
  `mutex_lock_interruptible(&input_mutex)` and `input_seq_stop()` unlocks,
  because the lock spans two seq_file callbacks; `mutex_acquired` in
  `struct input_seq_state` records whether to unlock.
- `input_register_device()`: combines
  `scoped_cond_guard(mutex_intr, goto err_device_del, &input_mutex)` with the
  `err_device_del` and `err_devres_free` labels; both labels sit after the
  guarded block and no `goto` jumps into it.
- `input_register_device()`: sets `error = -EINTR` on the line before the
  `scoped_cond_guard()`, since the fail statement is a `goto`, not a
  `return -EINTR`.
- `__free()` in the top-level files: ownership is handed over only with
  `no_free_ptr()`, as in `input_ff_create()` and `input_mt_init_slots()`;
  `retain_and_null_ptr()` and `return_ptr()` are not used there.
- `DEFINE_FREE()` / `DEFINE_GUARD()`: the only one in the input headers or
  under `drivers/input/` is the `serio_pause_rx` guard in
  `include/linux/serio.h`; there is no `__free()` class for
  `struct input_dev`.
- `error` is the dominant name but not the only one for a pure errno in the
  core:
  - `retval`: `evdev_open_device()`, `joydev_open_device()`,
    `mousedev_open_device()`, all holding only 0 or a negative errno.
  - `err`: `input_init()`, `input_dev_set_poll_interval()` in
    `drivers/input/input-poller.c`, and the `INPUT_ADD_HOTPLUG_VAR()` macro
    family in `drivers/input/input.c`.
- `retval` in `input_handler_for_each_handle()`: holds whatever the callback
  returned, not necessarily an errno.

## Model gaps

### Other mistakes models make

- Models take `handler->start()` to reach `dev->event()` before `dev->open()`
  has run; `input_open_device()` calls `start()` after
  `input_start_device()` has returned 0 (that call is skipped for a handler
  with `passive_observer`), and an event injected from `start()` reaches
  `dev->event()` only while `dev->ready` is set.
- Models take `input_register_device()` to test `EV_REP` before it installs
  soft repeat; `EV_REP` is tested later, in `input_start_autorepeat()`.
- Models write the core's allocations as `kzalloc()`, `kcalloc()` and
  `struct_size()`; `drivers/input/input.c`, `drivers/input/ff-core.c` and
  `drivers/input/input-mt.c` use `kzalloc_obj()`, `kzalloc_objs()` and
  `kzalloc_flex()` from `include/linux/slab.h`, for example in
  `input_allocate_device()` and `input_ff_create()`.
- Models name from_timer(); it is not defined in this tree. The core uses
  `timer_container_of()`, for example in `input_repeat_key()`.

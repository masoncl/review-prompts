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

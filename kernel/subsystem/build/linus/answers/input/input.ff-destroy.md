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

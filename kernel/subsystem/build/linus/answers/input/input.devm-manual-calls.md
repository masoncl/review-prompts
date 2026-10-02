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

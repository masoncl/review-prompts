- `report_fixup`: called only from `hid_open_report()`, which returns
  `-EBUSY` while `HID_STAT_PARSED` is set, so it does not run again in a
  binding once a parse succeeded.
- `devm_kzalloc()` on `&hdev->dev` inside the fixup: lands in the devres group
  that `__hid_device_probe()` opens, released by `devres_release_group()` on
  probe failure and in `hid_device_remove()`; it does not accumulate.
- `asus_report_fixup()` in `drivers/hid/hid-asus.c` and
  `gembird_report_fixup()` in `drivers/hid/hid-gembird.c`: allocate that way,
  never free explicitly, and return the passed buffer if allocation fails.
- `drivers/hid/hid-uclogic-core.c`: `uclogic_probe()` fills
  `drvdata->desc_ptr` with `uclogic_params_get_desc()`, a `krealloc()`
  buffer, before `hid_parse()`; `uclogic_report_fixup()` returns it;
  `uclogic_remove()` frees it with `kfree(drvdata->desc_ptr)`. The `failure:`
  label of `uclogic_probe()` calls only `uclogic_params_cleanup()`, so the
  buffer is not freed when `hid_parse()` or `hid_hw_start()` fails; that is
  the first Unsafe case below, not a model to copy.
- `uclogic_params_cleanup()` in `drivers/hid/hid-uclogic-params.c`: frees
  `params->desc_ptr`, a different buffer from the `drvdata->desc_ptr` that
  `uclogic_report_fixup()` returns.
- **Unsafe usage**: a replacement from `kmalloc()` or `krealloc()` that is
  freed only in the driver's `remove`.
  - Unsafe: when probe fails after the allocation; `__hid_device_probe()`
    then runs `devres_release_group()` and `hid_close_report()`, not
    `remove`.
  - Safe: a devm allocation on `&hdev->dev`, as `asus_report_fixup()` does;
    `devres_release_group()` in `__hid_device_probe()` covers probe failure.
- **Unsafe usage**: `kmalloc()` or `kmemdup()` inside `report_fixup` with the
  result only returned, not stored or devm-managed.
  - Safe: `devm_kzalloc()` on `&hdev->dev`, as `gembird_report_fixup()` does;
    `hid_open_report()` copies the result and drops the pointer.

- `mfd_get_cell()`: returns `pdev->mfd_cell`; it does not read
  `dev_get_platdata()`.
- Platform device not created by `mfd_add_device()`: the result is `NULL`,
  never a pointer to some other structure.
- Main use in this tree: a boolean "is this an MFD child" test, as in
  `mipi_i3c_hci_pci_is_mfd()` and `keyboard_led_is_mfd_device()`; neither
  dereferences the result.
- Reading a member: only `id` is read through the accessor outside the core,
  in `drivers/regulator/da9052-regulator.c`.
- `platform_data`, `name`, `of_compatible`: no caller reads them through
  `mfd_get_cell()`.
- `pdev->mfd_cell` is also read directly, without the accessor, and those
  reads do take `name` and `platform_data`; search for `->mfd_cell` as well as
  for `mfd_get_cell` when looking for users.

- `MFD_CELL_ALL()` argument order: `_name, _res, _pdata, _pdsize, _id, _compat,
  _of_reg, _use_of_reg, _match`; see `include/linux/mfd/core.h`.
- `_pdsize`: follows `_pdata` in `MFD_CELL_ALL()`, `MFD_CELL_OF_REG()`,
  `MFD_CELL_OF()`, `MFD_CELL_ACPI()` and `MFD_CELL_BASIC()`; the caller
  supplies it, nothing derives it from `_pdata`.
- `MFD_CELL_OF_REG()`: the only wrapper that sets `use_of_reg`; every other
  wrapper passes `false` and `of_reg` 0.
- `num_resources`: computed by `MFD_RES_SIZE()`, a `sizeof` division, not by
  `ARRAY_SIZE()`.
- `_res` given as `NULL` or as a pointer: compiles and yields `num_resources`
  0, so a pointer to resources silently registers a child with none.
- `MFD_CELL_OF()` with `_compat` `NULL`: same cell as `MFD_CELL_BASIC()`;
  `mfd_add_device()` skips the OF lookup when `of_compatible` is `NULL`.
- Members no macro sets: `level`, `swnode`, `suspend`, `resume`,
  `ignore_resource_conflicts`, `pm_runtime_no_callbacks`, `parent_supplies`,
  `num_parent_supplies`; a cell that needs one sets it by name, for example
  with a designated initialiser.
- `MFD_DEP_LEVEL_NORMAL` and `MFD_DEP_LEVEL_HIGH`: defined in the same header;
  they are values for `level`, not initialisers.

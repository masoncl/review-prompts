- `its_force_quiescent()` timeout: returns `-EBUSY`.
- `its_force_quiescent()`: returns 0 at once if the ITS is already disabled
  and quiescent; otherwise clears `GITS_CTLR_ENABLE` and `GITS_CTLR_ImDe`,
  then polls `GITS_CTLR_QUIESCENT`.
- Probe: `its_map_one()` calls `its_force_quiescent()`, not
  `its_probe_one()`; `its_node_init()` and `its_reset_one()` reach it.
- Reset pass: `its_reset_one()` writes 0 to every `GITS_BASER` of every ITS
  before any ITS is probed, from `its_of_probe()` and `its_acpi_reset()`.
- There is no ITS_FLAGS_SAVE_SUSPEND_STATE in this tree;
  `its_save_disable()` and `its_restore_enable()` walk every entry of
  `its_nodes`, and `its_init()` registers them without testing a flag.
- `its_save_disable()`: saves `GITS_CTLR` and `GITS_CBASER` only;
  `GITS_BASER` is restored from the cached `baser->val`.
- `its_restore_enable()` when the ITS fails to quiesce: skips that ITS and
  restores nothing, so it stays disabled.
- Re-issued on resume: `its_cpu_init_collection()` for the CPU that runs the
  hook only, and only if its `col_id` is below `GITS_TYPER_HCC()`.
- `its_cpu_init_collection()`: sends MAPC, then INVALL; with
  `ITS_FLAGS_WORKAROUND_CAVIUM_23144` it returns first for a CPU on another
  node.
- No other command is replayed by `its_restore_enable()`.

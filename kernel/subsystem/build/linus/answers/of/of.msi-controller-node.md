- `msi_np` NULL: accepted; the caller gets the ID only, as
  `fsl_mc_get_msi_id()` in `drivers/bus/fsl-mc/fsl-mc-msi.c` does.
- `*msi_np` non-NULL on entry, match through `msi-map`: `of_msi_xlate()`
  drops the lookup reference; the caller's count is unchanged.
- `msi-parent`: absent `#msi-cells` means 0 cells, so the same controller
  node counts as 1 cell under `msi-map` and 0 under `msi-parent`.
- `msi-map` result: `of_msi_xlate()` uses `args[0]` only, and only when
  `args_count > 0`; with 0 cells the node is still handed back and the ID
  stays `id_in`.

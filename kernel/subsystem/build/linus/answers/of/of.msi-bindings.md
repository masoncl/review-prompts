- Properties read: `msi-map` with `msi-map-mask`, and `msi-parent`; no file
  under `drivers/of/` reads `msi-controller`.
- Walk: `of_msi_xlate()` follows `dev->parent`, not device tree parents.
- Return: `u32`; `id_in` unchanged when nothing translates; there is no
  error return.
- Order at each level: `of_map_msi_id()` on `parent_dev->of_node`; only on a
  non-zero return, `of_check_msi_parent()`.
- `msi-map` present with no matching entry: `of_map_msi_id()` returns 0, so
  the walk ends there with the ID unchanged; `msi-parent` on that node is
  not tried.
- Non-zero from `of_map_msi_id()`: any error, for example a NULL `of_node`
  or a malformed map, moves on to `msi-parent` and then up.
- `msi-parent`: accepted only when entry 0 has zero argument cells; with
  cells `of_check_msi_parent()` returns `-EINVAL` and the walk continues up.
- `msi-parent` never changes the ID.
- `msi_np` NULL: `msi-parent` is not read, and a node without `msi-map` also
  ends the walk; the walk goes up only past a device for which
  `of_map_msi_id()` returns an error, for example a NULL `of_node`.
- `of_msi_get_domain()`: no walk and no `msi-map`; it iterates every
  `msi-parent` entry of the given node and returns the first domain
  `irq_find_matching_host()` finds for the token.

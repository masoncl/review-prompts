- `of_overlay_fdt_apply()`: has a fourth parameter, `base`, the node that a
  fragment's `target-path` is resolved against; NULL for the root.
- `*ret_ovcs_id`: 0 on entry, set to the id after every call to
  `of_overlay_apply()`, whatever it returned.
- Non-zero id after an error: says only that the overlay is still registered
  in `ovcs_idr` and holds its memory, not that the tree changed.
- Cases with a non-zero id: every error from `of_overlay_apply()`, for
  example `of_resolve_phandles()` or `init_overlay_changeset()` failed, an
  `OF_OVERLAY_PRE_APPLY` notifier refused, `build_changeset()` failed, the
  entries were applied and rolled back, or a notifier failed with the overlay
  fully applied.
- Zero id after an error: `free_overlay_changeset()` already ran, or nothing
  was allocated.
- **Unsafe usage**: returning from an `of_overlay_fdt_apply()` error without
  calling `of_overlay_remove()` on the id; the error path skips
  `free_overlay_changeset()`, so the overlay stays registered and possibly
  applied.
  - Safe: call `of_overlay_remove()` on every error, as
    `imx8mp_hdmi_tx_connector_fixup_init()` does; with an id of 0 it returns
    0 and does nothing.
- `OF_OVERLAY_PRE_APPLY` and `OF_OVERLAY_POST_APPLY` notifiers: run from
  `overlay_notify()` with `of_overlay_phandle_mutex` and `of_mutex` both
  held.
- Refusal state: `devicetree_corrupt()` tests the static
  `devicetree_state_flags` in `drivers/of/overlay.c`; there is no
  devicetree_state_flags_corrupt().
- `DTSF_APPLY_FAIL`: set in `of_overlay_apply()` when
  `__of_changeset_apply_entries()` fails and reports a rollback error in
  `ret_revert`.
- `DTSF_REVERT_FAIL`: set in `of_overlay_remove()` when
  `__of_changeset_revert_entries()` fails and reports a re-apply error.
- Plain `of_changeset_apply()` and `of_changeset_revert()` never set either
  bit.
- After `DTSF_APPLY_FAIL`: the `of_overlay_remove()` that the caller owes
  returns `-EBUSY` as well, so that overlay stays registered and its memory
  is never freed.

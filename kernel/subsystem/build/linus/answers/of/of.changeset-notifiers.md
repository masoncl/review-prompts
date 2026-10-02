- Timing: `__of_changeset_apply()` applies every entry first, then
  `__of_changeset_apply_notify()` sends one notification per entry in list
  order; a callback sees the whole changeset applied, not only its entry.
- `of_changeset_revert()`: same shape; `__of_changeset_revert_notify()` walks
  the entries in reverse and sends the inverted action.
- Locks: `__of_changeset_apply_notify()` unlocks `of_mutex` before the loop
  and relocks it after; callbacks run with neither `of_mutex` nor
  `devtree_lock` held.
- During an overlay apply the callbacks still run under
  `of_overlay_phandle_mutex`.
- Notifier error: logged by `__of_changeset_entry_notify()`, the remaining
  entries are still notified, and the last non-zero error becomes the return
  value of `of_changeset_apply()`.
- A non-zero return from `of_changeset_apply()` can therefore mean "every
  entry applied, a notifier failed"; nothing is rolled back in that case.
- Property entries: `of_property_notify()` sends nothing when the node is not
  in sysfs (`of_node_is_attached()` in `drivers/of/kobj.c`).

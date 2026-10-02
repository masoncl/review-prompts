- `of_changeset_destroy()`: never reverts; an applied changeset stays in the
  tree for good, and only the entries and their node references go.
- Destroy after apply is the normal way to make a change permanent, as
  `dlpar_hp_dt_add()` does; to undo, call `of_changeset_revert()` first, as
  `of_pci_remove_node()` does.
- `of_changeset_destroy()`: calls `device_link_wait_removal()` first, which
  flushes a workqueue, so it may sleep.
- References: `of_changeset_action()` takes one `of_node_get()` on the
  entry's node; none on the parent, none on the property.
- Properties: `__of_changeset_entry_destroy()` frees no property.
- `of_changeset_add_prop_helper()`: links the new property on `deadprops`
  when it is queued, so that it is freed with the node even if never applied;
  `__of_add_property()` unlinks it from `deadprops` on apply.
- Rollback result is lost: `__of_changeset_apply()` passes a local
  `ret_revert` and discards it, and `__of_changeset_revert()` does the same
  with `ret_reply`; the caller of `of_changeset_apply()` or
  `of_changeset_revert()` gets the entry's error and cannot tell whether the
  tree was restored.
- Actions that can fail in `__of_changeset_entry_apply()`, which revert also
  uses with the inverted action: of the five `OF_RECONFIG_` actions only
  `OF_RECONFIG_ADD_PROPERTY` (`-EEXIST`, name already on the node) and
  `OF_RECONFIG_REMOVE_PROPERTY` (`-ENODEV`, property not on the node's list);
  `__of_attach_node()` and `__of_detach_node()` return void and
  `__of_update_property()` returns 0.

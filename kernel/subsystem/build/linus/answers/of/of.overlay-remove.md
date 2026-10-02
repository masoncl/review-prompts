- `*ovcs_id == 0`: `of_overlay_remove()` returns 0 at once.
- Refusals that leave the overlay registered and `*ovcs_id` unchanged:
  `devicetree_corrupt()` (`-EBUSY`, tested before `of_mutex` is taken), id
  not in `ovcs_idr` (`-ENODEV`), `overlay_removal_is_ok()` fails (`-EBUSY`),
  an `OF_OVERLAY_PRE_REMOVE` notifier error, an entry revert error (the
  entries already reverted are re-applied, best effort); there is no other
  state test.
- `overlay_removal_is_ok()`: tests overlap, not order; it refuses when a
  node in this overlay's changeset is the same as, an ancestor of, or a
  descendant of a node in the changeset of a later-applied overlay (see
  `node_overlaps_later_cs()`); an older overlay with no such overlap can be
  removed.
- Once the entries are reverted nothing refuses: `*ovcs_id` is zeroed and
  `free_overlay_changeset()` runs even if a reconfig or
  `OF_OVERLAY_POST_REMOVE` notifier returns an error.
- An overlay has two kinds of memory with different lifetimes:

| Memory | Allocated by | Freed |
|---|---|---|
| overlay's own tree, `overlay_mem` and `new_fdt`; `nd.overlay` in an overlay notifier points here | `of_overlay_fdt_apply()` | `kfree()` in `free_overlay_changeset()`, right after the `OF_OVERLAY_POST_REMOVE` notifiers; no refcount is looked at |
| nodes added to the live tree, and their properties | `__of_node_dup()` and `__of_prop_dup()` | `of_node_release()`, on the last `of_node_put()` |

- `free_overlay_changeset()`: both of its callers reach it with
  `notify_state` at `OF_OVERLAY_INIT` or `OF_OVERLAY_POST_REMOVE`, so the
  "do not free" branch is not taken.
- Pointer into the overlay's own tree: must be gone when the
  `OF_OVERLAY_POST_REMOVE` notifier returns; nothing checks it.
- `np->name` of a node the overlay added: `add_changeset_node()` points it at
  the "name" property of the overlay's own tree, so it dangles after removal
  even if the node itself is still referenced.
- Properties the overlay added to a pre-existing node: moved to that node's
  `deadprops` on removal, and freed only if that node is ever released.
- Refcount check: in `__of_changeset_entry_destroy()`, only for
  `OF_RECONFIG_ATTACH_NODE` entries on `OF_OVERLAY` nodes; the expected count
  is 1, the entry's own reference.
- `of_overlay_remove()` still returns success on a mismatch, and
  `overlay_mem` and `new_fdt` are freed anyway.
- Reference on an added node: must be dropped before
  `__of_changeset_entry_destroy()` reads the count, that is by the time the
  `OF_OVERLAY_POST_REMOVE` notifiers have returned and
  `device_link_wait_removal()` has finished.

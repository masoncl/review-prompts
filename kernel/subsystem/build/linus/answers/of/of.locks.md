- `of_overlay_phandle_mutex`: third lock, a static `struct mutex` in
  `drivers/of/overlay.c`, taken only through `of_overlay_mutex_lock()`; there
  is no object named of_overlay_mutex.
- `of_mutex`: taken with `mutex_lock(&of_mutex)` directly; there is no
  of_mutex_lock() helper.
- Order in `of_overlay_fdt_apply()`: `of_overlay_phandle_mutex`, then
  `of_mutex`, then `devtree_lock`; `of_fdt_unflatten_mutex` in
  `drivers/of/fdt.c` is also taken while `of_mutex` is held.
- `of_overlay_remove()`: takes `of_mutex` only, not
  `of_overlay_phandle_mutex`.
- Reconfig notifiers do not run under `of_mutex`: `of_attach_node()`,
  `of_detach_node()`, `of_add_property()`, `of_remove_property()` and
  `of_update_property()` notify after the change and after
  `mutex_unlock(&of_mutex)`, and discard the notifier's return value, so a
  notifier cannot veto.
- `of_alias_get_id()` and `of_alias_get_highest_id()`: take `of_mutex`, so
  they may sleep, unlike the node and property lookups.
- `__of_find_property()`, `__of_get_next_child()`,
  `__of_device_is_compatible()`, `__of_device_is_available()` are `static` in
  `drivers/of/base.c`, and `__of_attach_node()` is `static` in
  `drivers/of/dynamic.c`; the `__` forms with a locking rule that other files
  can call are those declared in `drivers/of/of_private.h`, plus
  `__of_find_all_nodes()` and the macro `for_each_of_allnodes()` in
  `include/linux/of.h`.
- The `__` prefix does not mean one locking rule; for example:

| Kind | For example | Caller must |
|---|---|---|
| read-only | `__of_get_property()`, `__of_find_node_by_path()`, `__of_find_all_nodes()` | hold `devtree_lock` or `of_mutex`, or own the tree |
| modifying | `__of_add_property()`, `__of_remove_property()`, `__of_update_property()`, `__of_detach_node()` | hold `of_mutex` unless no other task can reach the node, not hold `devtree_lock`, be able to sleep |
| changeset notify | `__of_changeset_apply_notify()`, `__of_changeset_revert_notify()` | hold `of_mutex` on entry; they unlock and relock it |

- Modifying `__` forms: take `devtree_lock` themselves for the list change,
  release it, then call the sysfs helpers in `drivers/of/kobj.c`.
- **Unsafe usage**: calling a modifying `__` form with `devtree_lock` held;
  the raw spinlock is taken again and the sysfs step may sleep.
  - Safe: hold `of_mutex` only, as `of_add_property()` does.
- **Potentially unsafe usage**: calling a read-only `__` form without
  `devtree_lock`.
  - Unsafe: on a node reachable from `of_root`, with `of_mutex` not held
    either; `__of_add_property()`, `__of_remove_property()`,
    `__of_update_property()` and `__of_detach_node()` relink `properties`,
    `deadprops`, `child` and `sibling` under `devtree_lock`.
  - Safe: with `devtree_lock` held, as `of_find_compatible_node()` does.
  - Safe: with `of_mutex` held, as `of_core_init()` does with
    `for_each_of_allnodes()`; every caller of a modifying `__` form on the
    live tree holds `of_mutex`.
  - Safe: on a tree that is not attached to the live tree, as
    `add_changeset_node()` does with `__of_get_property()` on the overlay's
    own unflattened tree.
- **Potentially unsafe usage**: calling a modifying `__` form without
  `of_mutex`.
  - Unsafe: on a node in the live tree; the sysfs update runs after
    `devtree_lock` is dropped and only `of_mutex` orders it against another
    writer.
  - Safe: on a newly allocated node that no other task can reach, as
    `__of_node_dup()` does with `__of_add_property()`.

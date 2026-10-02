- Removal or replacement: never frees; the pointer stays valid after the
  property has left `np->properties`.
- `of_node_release()` in `drivers/of/dynamic.c`: the only place the core frees
  `properties` and `deadprops`; it runs when the last node reference drops.
- `of_node_release()` returns without freeing when `OF_DETACHED` is clear,
  when `OF_DYNAMIC` is clear, or when the node has `OF_OVERLAY` without
  `OF_OVERLAY_FREE_CSET`.
- Without `CONFIG_OF_DYNAMIC`: `of_node_release()` is an empty function in
  `drivers/of/kobj.c` and `of_node_put()` is an empty inline; the core frees
  no property.
- `__of_prop_free()`: calls `kfree()` on `name`, `value` and the
  `struct property` separately, for every entry of both lists; the property's
  own `OF_DYNAMIC` flag is not tested.
- `__of_add_property()` and `__of_update_property()`: first take the incoming
  property off `np->deadprops`, so that list is walked long after a removal.
- **Unsafe usage**: freeing a `struct property`, or its `name` or `value`,
  while it is on `np->properties` or `np->deadprops`; the next walk of the
  list and `of_node_release()` touch freed memory.
  - Safe: freeing a property that was never linked to the node, as
    `of_changeset_add_prop_helper()` does when `of_changeset_add_property()`
    fails.
  - Safe: leaving a removed property allocated, as `ima_free_kexec_buffer()`
    in `drivers/of/kexec.c` does after `of_remove_property()`.

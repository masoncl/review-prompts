- `of_node_release()` on a node without `OF_DETACHED`: prints "ERROR:
  of_node_release() detected bad of_node_put() on" plus the parent path and
  `full_name`; no "Bad of_node_put()" string exists in this tree.
- Stack dump and the second error line: skipped when `CONFIG_OF_UNITTEST` is
  set and the parent's `full_name` is "testcase-data".
- Order of checks in `of_node_release()`: `OF_DETACHED`, then `OF_DYNAMIC`,
  then `OF_OVERLAY` with `OF_OVERLAY_FREE_CSET`.
- Detached node without `OF_DYNAMIC` (a boot node after `of_detach_node()`):
  release returns silently, nothing printed, nothing freed.
- Freed nodes: `OF_DETACHED` and `OF_DYNAMIC`, and either no `OF_OVERLAY` or
  `OF_OVERLAY_FREE_CSET` set.
- Overlay node with children, or with properties left: release prints an
  error and frees the node anyway.
- Count reaching zero on an attached node (boot or overlay):
  `kobject_cleanup()` in `lib/kobject.c` removes the node from
  `/sys/firmware/devicetree`, frees the kobject name and puts the parent
  kobject; the `struct device_node` memory stays.
- Overlay node, missing put: `__of_changeset_entry_destroy()` sees a count
  above 1, prints "ERROR: memory leak, expected refcount 1 instead of", and
  does not set `OF_OVERLAY_FREE_CSET`.
- Overlay node after that message: never freed, even if the late put arrives;
  release then prints "ERROR: memory leak before free overlay changeset".
- Overlay removal does not fail on a bad count; nothing in
  `drivers/of/overlay.c` reads the count.
- Overlay node, extra put, no other holder: the count reaches zero before
  `OF_OVERLAY_FREE_CSET` is set; error printed, node leaked, and the changeset's
  own put then gives a `refcount_t` underflow warning.
- Overlay node, extra put, another holder present: the count is 1 at
  changeset destroy, the node is freed, and the holder has a use-after-free.

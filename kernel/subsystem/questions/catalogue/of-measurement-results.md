# What the of measurement found

Three models were asked the 36 questions in `of-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.12 to 6.19), reader A close behind it (6.8 to 6.17), and
reader B older (6.9 to 6.12) and much less sure of itself, with names it made
up and several rules stated backwards. The hand-written guide was never checked
against current sources, so differences between it and the built guide are
expected and are noted near the end.

Readers A and C know this code well: the file map, which lookups return a
reference, that the find and step functions consume their `from` or `prev`
argument, the scoped iterators, the status values, the interrupt return values.
What all three get wrong is the ID map and MSI code, which has been rewritten
under names that stayed the same, and a set of details about locks, flags and
error paths in the dynamic and overlay code. Reader B gets the basics of
reference counting wrong in ways that would change a review verdict, so the
build set keeps those questions even though two readers answer them.

## What all three readers got wrong

- **`of_map_id()` has a different interface.** Every reader gave the older
  six-argument form with a target pointer and an output ID (reader B had it
  returning a node). The tree's `of_map_id()` takes np, id, map_name,
  cells_name, map_mask_name, filter_np and arg: the result is a
  `struct of_phandle_args`,
  the number of output cells is read from the target's `cells_name` property
  (one if absent), a multi-cell output with a range longer than one is
  `-EINVAL`, `arg->np` is set only on a match and then holds a reference,
  and a missing map is `-ENODEV` only when `filter_np` is given. Callers use
  the wrappers `of_map_iommu_id()` and `of_map_msi_id()`. Two readers said
  they were unsure whether the output had become multi-cell; none knew.
- **`of_msi_xlate()` follows from that.** It calls `of_map_msi_id()`; the
  first `msi-map` found on the way up stops the walk even when no entry
  matches; `msi-parent` is looked at only when the map is absent and `msi_np`
  is non-NULL; `of_check_msi_parent()` accepts only an entry with no argument
  cells; `*msi_np` receives a reference only when it was NULL on entry and is
  a filter otherwise. An absent `#msi-cells` means one output cell for an
  `msi-map` target and none for `msi-parent`. One reader guessed that an
  `msi-parent` with one cell supplies the ID; it is rejected.
- **An integer read of an empty property returns `-EOVERFLOW`.** All three
  said `-ENODATA`. `of_find_property_value_of_size()` returns that only for a
  NULL `value`, and both `populate_properties()` and `__of_prop_dup()` give an
  empty property a non-NULL one. `of_property_read_string()` tests the length
  and does return `-ENODATA`.
- **`for_each_compatible_node_scoped()`** was missing from every reader's
  table of iterators, and only reader C knew that
  `for_each_child_of_node_with_prefix()` declares its variable with
  `__free(device_node)` although nothing in its name says so. Readers A and C
  gave `devtree_lock` as the lock for `for_each_of_allnodes()`;
  `of_core_init()` walks it under `of_mutex`.
- **Who takes the device's node reference.** All three said
  `of_device_alloc()` calls `of_node_get()` and the device core puts it. It
  goes through `platform_device_set_of_node()`, which takes a firmware-node
  reference that `platform_device_release()` drops; the generic device release
  never puts `of_node`.
- **Platform population.** Recursion into children is decided by the caller's
  `matches` argument, and only after the node's own device was created.
  of_default_bus_match_table, named by two readers, is gone from the code (it
  survives in `Documentation/devicetree/usage-model.rst`); the table is local
  to `of_platform_default_populate()`. `of_platform_depopulate()` clears only
  the parent's `OF_POPULATED_BUS`; `of_platform_device_destroy()` clears both
  flags on each child.
- **`of_link_property()` stops at the first table entry whose parser
  matches.** No reader said so. Reader A named a node_not_dev member and
  reader B a name member of `struct supplier_bindings`; it has `parse_prop`,
  `get_con_dev`, `optional` and `fwlink_flags`.
- **Overlay apply details.** Each reader had the outline and each had a step
  wrong: where the id is allocated, which of `DTSF_APPLY_FAIL` and
  `DTSF_REVERT_FAIL` is set by which failure, that `of_mutex` is dropped
  around the reconfiguration notifiers, that `overlay_fw_devlink_refresh()`
  runs before `OF_OVERLAY_POST_APPLY`.
- **What else a change must keep building.** Every reader missed something:
  that x86 OLPC also selects `OF_PROMTREE`, that `drivers/of/overlay_test.c`
  has its own option, that the stubs in `include/linux/of_address.h` and
  `include/linux/of_irq.h` hang off `CONFIG_OF_ADDRESS` and `CONFIG_OF_IRQ`
  (so sparc uses them with `CONFIG_OF` on), or the `EXPECT_NOT` markers.

## What only some readers got wrong

Reader B, and nobody else. The first five would change a verdict:

- The find functions "leave `from` alone". `of_find_node_by_name()`,
  `of_find_node_by_type()`, `of_find_compatible_node()`,
  `of_find_node_with_property()` and `of_find_matching_node_and_match()` all
  put it, which is what the iterator macros built on them rely on.
- To keep a node after a loop, take `of_node_get()` before `break`. A plain
  iterator does not put on `break`, so that leaks;
  `of_get_child_by_name()` just breaks and returns the child. It also called
  `for_each_child_of_node()` self-cleaning.
- Without `CONFIG_OF_DYNAMIC` "the same kobject calls still run".
  `of_node_get()` returns its argument and `of_node_put()` is empty.
- `of_get_parent()` gives a borrowed pointer. It returns a counted reference.
- On an error from `of_overlay_fdt_apply()` the id is zero and the core has
  unwound. Once the inner apply has run the id is set, the changeset may be
  partly applied, and the caller has to call `of_overlay_remove()`.
- `of_property_for_each_u32()` with five arguments (it takes three);
  `of_property_read_bool()` as a header wrapper that does not warn; CPU
  iteration skipping every CPU that is not okay (only failed ones); no
  `reserved` state.
- `of_changeset_destroy()` reverts an applied changeset, notifiers run per
  entry under `of_mutex`, only attach and detach entries hold a reference, a
  failed revert carries on. None of these is so.
- More than `MAX_PHANDLE_ARGS` cells is `-EINVAL`
  (`of_phandle_iterator_args()` warns and truncates); the reconfiguration
  chain is a raw notifier that can veto; population recurses into every child;
  the populated flags live in the firmware node.
- Names that exist nowhere: of_find_node_by_full_name(),
  for_each_child_of_port(), fwnode_is_of(), a ce_list member.

Readers A and B:

- An unknown phandle in a list is always `-EINVAL`. With no cells name
  (`of_parse_phandle_with_fixed_args()`) the entry succeeds with `np` NULL.
- The forms with two leading underscores need the caller to hold
  `devtree_lock` and to update sysfs. `__of_attach_node()`,
  `__of_add_property()` and the rest take `devtree_lock` themselves and do
  the sysfs update; the outer functions take only `of_mutex`.
- Changeset notifiers are sent with `of_mutex` held and their errors only
  logged. `__of_changeset_apply_notify()` drops the mutex and the last error
  is returned.
- `of_node_is_attached()` reads `OF_DETACHED` (it tests
  `kobj.state_in_sysfs`); `OF_OVERLAY` is set on unflattened overlay nodes (it
  is set in `add_changeset_node()` on the copies made for the live tree).
- In `of_irq_parse_raw()` an `interrupt-controller` ends the walk even when it
  has an `interrupt-map`. The map takes precedence, except for the compatibles
  in `of_irq_imap_abusers`.

Reader A alone: calling `of_node_put()` under `devtree_lock` is unsafe and the
iterators avoid it (they all do it); nodes flagged `OF_DYNAMIC` are freed
(`of_node_release()` also requires `OF_DETACHED`); of_node_alloc(), which does
not exist; `of_graph_get_port_by_id()` hands out with `no_free_ptr()` (it uses
`return_ptr()`); table order never decides a compatible match (on a tie the
earlier entry wins).

Reader C alone: a public of_device_is_fail() (the test is static
`__of_device_is_fail()`); `of_platform_notify()` test-and-setting
`OF_POPULATED` and clearing a firmware-node flag (it only checks); removed
properties never freed (`of_node_release()` frees `deadprops` with a dynamic
node).

## What the readers already knew

The file map and the entry points (no reader needed more than the KUnit files
added). Readers A and C: the two lists of functions that do and do not return
a reference, that step and find functions consume `prev` and `from`, that
leaving a plain iterator early needs a put and going round again must not have
one, the scoped forms with `return_ptr()` and `no_free_ptr()` and the mistake
of putting `__free(device_node)` on a borrowed pointer, the three-argument
`of_property_for_each_u32()`, that `of_property_read_bool()` warns on a
property with a value, that removed properties go to `deadprops`, the status
values and that CPU iteration skips only failed CPUs, the interrupt lookup
return values (all three), the four arguments of `of_overlay_fdt_apply()` and
what its caller does on error, and that `MAX_PHANDLE_ARGS` is 16. These are
dropped from the build set or kept only because reader B has them wrong.

## Where the hand-written guide is stale

- It says an extra `of_node_put()` in a loop is a double free leading to
  use-after-free. Without `CONFIG_OF_DYNAMIC` the call is an empty inline.
  With it, `of_node_release()` refuses to free a node that is not
  `OF_DETACHED` (it prints an error and a stack dump and returns) and never
  frees one that is not `OF_DYNAMIC`, so for the boot tree the result is a
  reference count underflow warning. Memory is really freed early only for
  detached dynamic nodes, such as an overlay's.
- Its list of iterators reads as complete and omits `for_each_node_by_name()`,
  `for_each_of_cpu_node()` and `for_each_endpoint_of_node()`, which behave the
  same way, and `for_each_of_allnodes()`, which takes no reference at all.
- It gives two scoped iterators. The tree also has
  `for_each_compatible_node_scoped()`, `for_each_of_graph_port()` and
  `for_each_of_graph_port_endpoint()`, and
  `for_each_child_of_node_with_prefix()` is scoped without saying so.
- It says a manual put is needed only on `break` or `return`. A `goto` out of
  the loop is the same.
- It says `of_map_id()` is called from `of_msi_xlate()`. The call is
  `of_map_msi_id()`, and `of_map_id()` itself has a different interface (see
  above). It describes `of_msi_xlate()` as checking both properties; a present
  `msi-map` ends the walk, and `msi-parent` is consulted only when the map is
  absent and the caller asked for the controller node.
- It says nothing about the reference left in `out_args->np` by the
  `of_parse_phandle_with_args()` family, or in `it.node` when an
  `of_for_each_phandle()` loop is left early.
- Correct and kept as questions: which iterators hold a reference and that
  `continue` needs no put, the scoped forms, the functions that consume
  `from`, `of_get_next_parent()` dropping its argument,
  `for_each_property_of_node()` taking no reference, and `of_msi_get_domain()`
  walking `msi-parent` with `#msi-cells`.

## Left out of the build set

The hand-written guide is 640 words, so the build set holds 11 of the 36
questions, weighted towards what the old guide was about: references held by
iterators and lookups, and MSI. Four of the eleven are reworded from the
measurement set. Two are narrowed to fit their smaller budgets: the iterator
question asks for groups by behaviour instead of a table with a row per macro,
and the phandle list question drops the variants and the cell limit, which
every reader knew. Two were changed after a first build. The file question
listed a dozen topics for a 25-word answer, and one builder answered with a
bare list of files "in question order", which means nothing to someone who
cannot see the question; it now asks only for the files whose names do not
give them away. The property read question asked about a property "with no
value", and one builder repeated the `-ENODATA` that every reader had given;
it now asks about an empty property and points at where its `value` pointer is
set. Left out although a reader got them wrong:

- The dynamic tree, changesets, the reconfiguration notifiers and both overlay
  questions. Every reader had details wrong, but the code is `dynamic.c` and
  `overlay.c` and a handful of callers, and a patch that touches them has the
  functions open. Reader B's belief that a failed overlay apply needs no
  cleanup is the one real loss.
- The locks, the node flags and the structure: readers A and C needed small
  corrections only, and the fact that matters most to a reviewer (every plain
  lookup takes `devtree_lock`, so none may be called under it) they all knew.
- Functions that return a reference, and keeping a node pointer: the
  consuming-argument, iterator and phandle questions carry the cases that go
  wrong in practice.
- Address translation and interrupt parsing: confined to two files, and the
  corrections were about internals a driver does not see. The interrupt return
  values were known to all three.
- Platform population, firmware-node handles and the supplier link table: the
  moved names are noted above; none changes how a driver is written.
- The boolean and presence tests, the value loops, the status values and
  compatible matching: only reader B was wrong.
- Configuration options, the flat tree, documentation and tests: what a change
  must keep building is kept as one question instead.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 76 corrections, 27% rewritten on average
reader B: 109 corrections, 72% rewritten on average
reader C: 68 corrections, 18% rewritten on average

question                        reader A      reader B      reader C
of.core-files                    5% ( 1)      10% ( 3)       0% ( 0)
of.entry-points                  1% ( 1)      12% ( 1)       2% ( 1)
of.docs-and-tests               25% ( 1)      72% ( 1)       0% ( 0)
of.config-options               44% ( 7)      59% ( 1)      35% ( 6)
of.node-structure                0% ( 0)      64% ( 4)      10% ( 4)
of.node-flags                   39% ( 3)      50% ( 4)      14% ( 4)
of.locks                        34% ( 3)      71% ( 3)       6% ( 2)
of.early-fdt                    15% ( 1)      83% ( 2)      12% ( 2)
of.refcount-basics              16% ( 3)      83% ( 7)      12% ( 2)
of.acquiring-functions           4% ( 1)      75% ( 3)      24% ( 2)
of.from-argument                15% ( 2)      85% ( 1)       2% ( 1)
of.iterator-macros              22% ( 3)      50% ( 3)      16% ( 2)
of.iterator-put-usage            8% ( 2)      86% ( 6)      20% ( 2)
of.scoped-cleanup               21% ( 1)      72% ( 2)       0% ( 0)
of.borrowed-pointers            28% ( 1)      63% ( 2)       7% ( 1)
of.phandle-args-ref             43% ( 2)      78% ( 3)       6% ( 0)
of.property-read-returns        50% ( 4)      73% ( 2)      39% ( 1)
of.bool-and-present              1% ( 0)      75% ( 1)       0% ( 0)
of.property-value-lifetime       0% ( 0)      76% ( 2)       0% ( 0)
of.property-iterators            0% ( 0)      63% ( 1)       0% ( 0)
of.status-values                18% ( 1)      88% ( 1)       2% ( 1)
of.compatible-matching          23% ( 1)      74% ( 1)       9% ( 1)
of.address-translation          42% ( 3)      91% ( 5)      30% ( 4)
of.irq-parse                    43% ( 2)      82% ( 3)      30% ( 2)
of.irq-get-returns               0% ( 0)      77% ( 1)       3% ( 1)
of.id-map                       67% ( 3)      75% ( 1)      56% ( 3)
of.msi-bindings                 49% ( 2)      79% ( 1)      65% ( 3)
of.live-tree-changes            71% ( 2)      89% ( 3)      21% ( 3)
of.changesets                   55% ( 3)      78% ( 5)      16% ( 2)
of.reconfig-notifiers           39% ( 3)      73% ( 2)      33% ( 2)
of.overlay-apply                48% ( 3)      76% ( 6)      57% ( 4)
of.overlay-remove               39% ( 4)      89% ( 4)      32% ( 2)
of.platform-populate            31% ( 3)      79% ( 8)      24% ( 3)
of.fwnode                       14% ( 1)      86% ( 4)       2% ( 1)
of.fw-devlink                   35% ( 3)      85% ( 4)      30% ( 1)
of.change-checklist             53% ( 6)      76% ( 8)      47% ( 5)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `of.config-options`, `of.changesets`, `of.overlay-apply`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `of.node-structure`, `of.node-flags`, `of.locks`, `of.acquiring-functions`, `of.borrowed-pointers`, `of.bool-and-present`, `of.property-value-lifetime`, `of.status-values`, `of.address-translation`, `of.irq-parse`, `of.irq-get-returns`, `of.overlay-remove`, `of.platform-populate`.

## Questions reorganised

Organised by subject, 29 questions before and 26 after: node references (iterators, lookups,
phandle lists and scoped cleanup together), reading properties, translating IDs, addresses and
interrupts, locks and live tree changes, devices from nodes.
Merged: `of.acquiring-functions` and `of.borrowed-pointers` into `of.counted-and-borrowed` (the
rule and what a reader misplaces, not two lists); `of.config-options` and `of.change-checklist`
into `of.build-variants`. Dropped: `of.node-structure`, an inventory the overview covers; what a
walk over every node must hold is asked by `of.iterator-macros`. Changesets, overlays and the
translation questions no longer ask for the steps inside.

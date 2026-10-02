# Questions: Open Firmware (Device Tree) Subsystem

- guide: of.md
- title: Open Firmware (Device Tree) Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/of-measurement.md` is the wider
set the readers were measured on and `catalogue/of-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## of.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## of.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file under `drivers/of/`: node lookup and phandle parsing; typed
property reads with the graph helpers and the firmware-node operations; interrupt and MSI
parsing; reference counting with changesets; phandle resolution for overlays; the sysfs
representation; the two kinds of test. Leave out any job whose file is named after it.

## of.build-variants: Compiled-out stubs and unit tests

- section: Finding your way
- relevance: 4 - several functions compile to nothing in most kernels

What does a caller get from the stub versions of the functions in `drivers/of/` when the part that
defines them is compiled out, and which Kconfig option selects each set of stubs, where that is
not `CONFIG_OF`? Which configurations build the tree from something other than a flat blob? How
does `drivers/of/unittest.c` declare the kernel messages it expects, and what does that require of
a patch that changes the text of a message printed by `drivers/of/`? Start from
`drivers/of/Kconfig`, `drivers/of/Makefile` and `drivers/of/unittest.c`.

# Node references

## of.iterator-macros: Iterator macros

- section: Node references
- relevance: 5 - the rules differ by macro and are not in the name

For the node and property iterator macros in `include/linux/of.h` and `include/linux/of_graph.h`,
who holds the reference on the loop variable during an iteration, and which macros declare the
loop variable themselves? Where a macro takes no reference, what must its caller hold instead?
Group the macros that follow the same rule, and name a stepping function only where the macro's
name does not give it away.

## of.refcount-basics: Node reference counts

- section: Node references
- relevance: 5 - what a leak or an extra put actually does

What do `of_node_get()` and `of_node_put()` do in a kernel with dynamic device tree support and
in one without, which nodes are ever freed, and what does the release function check and print
when the count reaches zero? So what does a missing put, and an extra one, actually cause for a
node of the boot tree and for a node of an overlay? Start from `drivers/of/dynamic.c` and
`of_node_release()`.

## of.counted-and-borrowed: Borrowed pointers and device of_node

- section: Node references
- relevance: 5 - each counted pointer needs a matching put and each stored borrowed one a get

Which functions that return a `struct device_node` pointer return it with a reference that the
caller must drop with `of_node_put()`, and which return it without one: give the rule, and the
functions whose names do not show which kind they are. What are the requirements for storing a
node pointer in a longer-lived structure, and for using a device's `of_node`, in order to assure
safe usage? Which core helpers take and drop that reference for the caller? Start from
`drivers/of/base.c`.

## of.from-argument: Lookups that consume an argument

- section: Node references
- relevance: 5 - a put on the argument afterwards is one too many

Which lookup and step functions drop the reference on the node passed in as their starting point
or previous position, and which take such an argument and leave its count alone? What are the
requirements for a caller that keeps using the node it passed in as that argument, in order to
assure safe usage? Start from `of_get_next_child()`, `of_get_next_parent()` and
`of_find_node_by_name()`.

## of.phandle-args-ref: Phandle lists and references

- section: Node references
- relevance: 4 - the reference hides in an output structure

When one entry of a property holding phandles with arguments is parsed, what comes back for an
empty entry, for a malformed one and for a phandle that resolves to no node, and who must drop
which reference, including when a loop over the iterator is left early? Start from
`__of_parse_phandle_with_args()` and `of_phandle_iterator_next()`.

## of.iterator-put-usage: Puts inside iterator loops

- section: Node references
- relevance: 5 - the commonest device tree bug in drivers

What are the requirements for calling `of_node_put()` on the loop variable of
`for_each_child_of_node()` and of the other node iterator macros, inside the loop and after it, in
order to assure safe usage? How do the requirements differ for `for_each_child_of_node_scoped()`
and the other iterator macros that declare the loop variable themselves? Name in-tree code that
shows it.

## of.scoped-cleanup: Automatic cleanup of nodes

- section: Node references
- relevance: 4 - new code is written this way and the pitfalls are new too

How is a node pointer declared so that its reference is dropped when it goes out of scope, and how
is a node handed out of such a scope without being dropped? What are the requirements for a
variable declared with `__free(device_node)` in order to assure safe usage? Start from
`DEFINE_FREE` in `include/linux/of.h` and `of_graph_get_port_by_id()`.

# Reading properties

## of.property-read-returns: Typed property reads

- section: Reading properties
- relevance: 4 - callers test for the wrong error

What do the integer, array and string property read functions return when the property is
missing, when it is present but empty (zero length, as a boolean property is), and when it is
shorter or longer than asked, and is the output argument written on failure? What do the
variable-length array forms return on success? Start from `of_find_property_value_of_size()` in
`drivers/of/property.c`, and from what `populate_properties()` in `drivers/of/fdt.c` stores for
an empty property.

## of.bool-and-present: Boolean and presence tests

- section: Reading properties
- relevance: 4 - the two look interchangeable and are not

What are the requirements for a property tested with `of_property_read_bool()` in order to assure
correct usage, and what does the function do for a property that does not meet them? Which
function tests for the presence of a property that carries a value? Start from
`of_property_read_bool()` in `drivers/of/property.c`.

## of.property-value-lifetime: Lifetime of property values

- section: Reading properties
- relevance: 4 - decides whether a returned pointer can be kept

How long does a pointer returned by `of_get_property()`, `of_find_property()` or
`of_property_read_string()` stay valid, what byte order is the data in, and what happens to a
property's memory when it is removed or replaced in the live tree? Start from
`__of_remove_property()`.

## of.status-values: Status property

- section: Reading properties
- relevance: 4 - "available" is not the only state the core knows

Which states does the core derive from a node's `status` property, and what does a missing
property mean? Which of the availability helpers, and which child and CPU iterators, skip nodes in
which state? Which functions let a caller tell the states other than okay from one another? Start
from `__of_device_is_status()` in `drivers/of/base.c`.

# Translating IDs, addresses and interrupts

## of.id-map: ID map translation

- section: Translating IDs, addresses and interrupts
- relevance: 5 - the interface may differ from what a reader remembers

Which functions translate a device ID through a map property such as the ones used for IOMMUs and
for MSI controllers, and in what form does the result come back? What do they return when the
property is absent, when no entry matches and when one does? Who owns the node that is handed
back? Start from `of_map_id()` in `drivers/of/base.c`.

## of.id-map-cells: Map entry output cells

- section: Translating IDs, addresses and interrupts
- relevance: 5 - the cell count decides how every entry of a map property is parsed

How does `of_map_id()` decide how many output cells an entry of the map property has, including
when the target node lacks the property that gives the count? What is the largest count it
accepts, and what does it return for a larger one? Start from `of_map_id()` in
`drivers/of/base.c`.

## of.msi-bindings: MSI controller lookup

- section: Translating IDs, addresses and interrupts
- relevance: 4 - a platform using the other form gets no MSIs

Which device tree properties can name the MSI controller a device uses and the ID it presents
there, and in what order does `of_msi_xlate()` consult them as it walks up from the device? What
ends the walk? Start from `of_msi_xlate()` and `of_msi_get_domain()` in `drivers/of/irq.c`.

## of.msi-controller-node: MSI controller node argument

- section: Translating IDs, addresses and interrupts
- relevance: 4 - a caller that passes a node in and one that gets a node back owe different puts

Who holds a reference on a controller node that `of_msi_xlate()` hands back through `msi_np`, and
when is `msi_np` an input and not an output? How is the controller's cell-count property read for
each property that can name the controller, including when it is absent? Start from
`of_msi_xlate()` in `drivers/of/irq.c`.

## of.address-translation: Address translation

- section: Translating IDs, addresses and interrupts
- relevance: 4 - failure is a value, not an errno

When `of_translate_address()` translates a `reg` address to a CPU physical address, what does a
missing `ranges` property mean and what an empty one? What is returned on failure, and how must a
caller test for it? Which property does `of_translate_dma_address()` read at each level, and which
node does it step to next? Start from `of_translate_address()` and `of_translate_one()` in
`drivers/of/address.c`.

## of.irq-parse: Interrupt parsing

- section: Translating IDs, addresses and interrupts
- relevance: 4 - two properties and a map, with a reference at the end

When a device's interrupt is resolved to a controller and a specifier, which of the two interrupt
properties wins when both are present, and when a node on the way up is both an interrupt
controller and has an `interrupt-map`, which takes precedence and for which nodes is the map
ignored? What reference does the caller hold on success, and who drops it? Start from
`of_irq_parse_one()` and `of_irq_parse_raw()`.

## of.irq-get-returns: Interrupt lookup results

- section: Translating IDs, addresses and interrupts
- relevance: 4 - zero, negative and deferral mean different things

What do `of_irq_get()`, `of_irq_get_byname()` and `irq_of_parse_and_map()` return on success,
when the interrupt cannot be mapped, when the controller has no domain yet and on a parse error,
and how should a probe function treat each?

# Locks and live tree changes

## of.locks: devtree_lock and of_mutex

- section: Locks and live tree changes
- relevance: 5 - which calls may sleep and which run with interrupts off

Which locks protect the live tree and what kind is each, so which calls may sleep and which run
with interrupts off? In what order are they taken? What are the requirements for calling a lookup
function, and for calling one of the forms with two leading underscores, with respect to those
locks, in order to assure safe usage? Start from `drivers/of/base.c` and
`drivers/of/of_private.h`.

## of.node-flags: Node flags

- section: Locks and live tree changes
- relevance: 4 - the flags decide whether memory is freed and devices made

A table of the flag bits kept in a node's `_flags`: what each makes the core do or refuse to do,
and who sets and clears it. Which may a bus or driver touch, and which belong to the core? Start
from `OF_DYNAMIC` in `include/linux/of.h`.

## of.changesets: Changesets

- section: Locks and live tree changes
- relevance: 4 - the supported way to change the tree, with its own lifetime rules

What state does `of_changeset_apply()` leave the tree in when one entry fails to apply, and
`of_changeset_revert()` when one entry fails to revert? What references does a changeset hold, and
what does `of_changeset_destroy()` do with them and with the tree when the changeset is still
applied? Start from `of_changeset_apply()` and `of_changeset_destroy()` in `drivers/of/dynamic.c`.

## of.changeset-notifiers: Changeset notifiers

- section: Locks and live tree changes
- relevance: 4 - decides what a notifier may do and what a caller learns from a failed one

When does `of_changeset_apply()` send notifiers relative to the changes it makes to the tree, and
which lock is held while they run? What becomes of an error that a notifier returns? Start from
`of_changeset_apply()` in `drivers/of/dynamic.c`.

## of.overlay-apply: Applying an overlay

- section: Locks and live tree changes
- relevance: 4 - the error path is not the usual one

When the function that applies an overlay blob returns an error, what must the caller do and how
does it know whether anything was applied? Under which locks do the notifiers around an apply
run? When does the core refuse every further overlay operation, and what sets that? Start from
`of_overlay_fdt_apply()` in `drivers/of/overlay.c`.

## of.overlay-remove: Removing an overlay

- section: Locks and live tree changes
- relevance: 4 - pointers into a removed overlay dangle

When does `of_overlay_remove()` refuse to remove an overlay? When is the overlay's memory freed,
and what does that require of code that holds a pointer to one of the overlay's nodes or property
values? What does the core check about node reference counts when the overlay's changeset is
destroyed, and what does it do on a mismatch? Start from `of_overlay_remove()` and
`Documentation/devicetree/overlay-notes.rst`.

# Devices from nodes

## of.platform-populate: Creating platform devices

- section: Devices from nodes
- relevance: 4 - which nodes become devices, and only once

When a subtree is populated, which nodes get a platform device and what decides whether the walk
goes on into a node's children? How do the populated flags stop a second device being made, and
which of the depopulate and destroy functions clears which flag? What does looking a device up by
its node hand back that the caller must release? Start from `of_platform_populate()` and
`of_platform_bus_create()` in `drivers/of/platform.c`.

# Model gaps

## of.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.

# pahole Technical Patterns

## The Central Model Is a Per-CU Graph

`struct cu` owns tags and assigns their IDs. Accessors such as `cu__type()`
are not generic global lookups: the tag ID and the CU must travel together.

```c
/* Correct: member's type ID belongs to this CU. */
struct tag *member_type = cu__type(cu, member->tag.type);
if (member_type == NULL)
	return -1;
```

Review code that stores an ID or `struct tag *` for later use: it must retain
the correct CU and respect the lifetime of the CU's tag table.

## Follow Type Wrappers Intentionally

An input type may be a typedef, pointer, array, modifier, forward declaration,
or concrete aggregate. Do not cast based only on an expected input shape.

```c
struct tag *type = cu__type(cu, id);
if (type == NULL)
	return -1;
if (tag__is_typedef(type))
	type = tag__follow_typedef(type, cu);
if (!tag__is_struct(type) && !tag__is_union(type))
	return 0;
```

Following a typedef is correct only when the operation needs its resolved type;
preserve the alias when it is meaningful to output or type identity.

## Offsets and Sizes Are Input Data

DWARF/BTF offsets, bit sizes, counts, and IDs can be malformed or exceed the
host type used to hold them. Validate before arithmetic, conversion, indexing,
or pointer addition. Pay special attention to bitfields, flexible arrays,
zero-sized/incomplete types, and architecture-specific ABI rules.

## Error Propagation Must Preserve Context

Loader and encoder helpers often run many times per CU. Do not turn a failure
into a quietly omitted type unless omission is an established, documented
policy. Propagate failures with enough context to identify the source CU/type
and clean up all partially initialized state.

```c
err = encode_type(encoder, tag, cu);
if (err) {
	fprintf(stderr, "failed to encode type in %s: %d\n", cu->name, err);
	goto out;
}
```

Use the project’s established error/reporting style in the nearby code; the
example illustrates the ownership and propagation rule, not a new API.

## Order Is Often Part of the Result

Traversal order can affect BTF IDs, deduplication, reproducibility, emitted
text, and split-BTF base compatibility. A switch from list order to hash order,
or a new early filter, needs a deterministic-output test and review of all
consumers of the sequence.

## Tests Should Build the Smallest Proof

Most regression tests are shell scripts that compile a small source fixture,
run the just-built tool, and inspect its result. Build a fixture that contains
only the problematic declaration or ABI case. This makes it clear whether the
test requires DWARF, BTF, a particular compiler, or a vmlinux input.

## `gobuffer`: Append-Only Serialized Data

Use `struct gobuffer` when constructing a variable-length, contiguous byte
stream whose entries are appended and retained until the whole buffer is
finished—for example CTF records, BTF section-variable information, or a list
of fixed-size ranges. It is not a general container: it grows only, does not
remove entries, and owns a reallocatable byte allocation.

- `gobuffer__add()` reserves space, copies bytes, and increments `nr_entries`.
- `gobuffer__allocate()` reserves uninitialized bytes and returns their byte
  offset for the caller to fill; it does not increment `nr_entries`.
- `gobuffer__size()` is the total used byte count, while `nr_entries` counts
  only successful `add()` calls.
- `gobuffer__copy()` requires a destination large enough for `size()` bytes;
  `__gobuffer__delete()` releases the owned allocation.

Always check the returned offset/error before writing. Treat offsets as the
stable handle, not pointers: a later append may `realloc()` and invalidate a
pointer returned by `gobuffer__entries()` or `gobuffer__ptr()`. Offset zero is
also a special case for `gobuffer__ptr()` (it returns `NULL`), so callers that
need the first byte should use the entries base or handle that sentinel
explicitly. Review length and offset arithmetic for `unsigned int` overflow
before asking the buffer to reserve input-derived sizes.

## `rbtree`: Ordered Indexes for Current Consumers

`rbtree.[ch]` is the local Linux-derived intrusive red-black-tree
implementation. It supplies balancing and ordered traversal, but each caller
owns the key comparison, search, insertion position, duplicate policy, and
object lifetime. Embed `struct rb_node` in the indexed object, walk to the
ordered leaf, call `rb_link_node()`, then call `rb_insert_color()` exactly once.
Erase a node before freeing or reusing its containing object.

Today it is used for three important indexes:

- Each `struct cu` indexes functions by address, supporting address-to-function
  lookup over function ranges.
- `struct strlist` uses a string-keyed tree for fast membership/duplicate
  detection while retaining a separate list for insertion-order traversal.
- `pahole` uses a tree of structures to deduplicate and order aggregate types
  for sorted output and re-sorting modes.

Comparator changes are semantic changes. They must establish a consistent
strict ordering and clearly define equality; otherwise lookup can miss an item,
duplicates can be admitted or discarded incorrectly, and ordered output can
change. When erasing while traversing, obtain `rb_next()` before `rb_erase()`.
For the global pahole structure tree, preserve the associated locking around
tree mutation and do not share one embedded `rb_node` between two live trees.

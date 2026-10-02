# Questions: BTF special fields in BPF maps (measurement set)

- guide: btf.md
- title: BTF Special Fields in BPF Maps

A wide set of questions about the special fields a map value or allocated
object can carry, used to measure what a model already knows. The hand-written
guide it will replace is 391 words. Format:
`../../../docs/subsystem-questions.md`.

# The fields

## btf.field-types: Field kinds

- section: What the fields are
- relevance: 4 - each kind owns a different resource
- words: 110

Which kinds of special field can a map value or allocated object contain, and
what kernel resource, if any, does each hold? A table, with each kind's
constant name written in full. Start from `enum btf_field_type` in
`include/linux/bpf.h`.

## btf.record: The field record

- section: What the fields are
- relevance: 4 - everything else walks this record
- words: 80

How are special fields found in a value's type, what structure records them and
where is it kept for a map and for an allocated object? Start from
`btf_parse_fields()` and `struct btf_record`.

## btf.map-type-support: Map type support

- section: What the fields are
- relevance: 4 - the allowlist keeps changing
- words: 110

Where is it decided which map types may hold which kinds of special field, and
what does that table look like in this tree, with each kind's and each map
type's constant name written in full? Start from `map_check_btf()` in
`kernel/bpf/syscall.c`.

## btf.verifier-access: Program access to special fields

- section: What the fields are
- relevance: 3 - direct loads and stores are refused
- words: 70

Can a program read or write the bytes of a special field directly, how does the
verifier know where they are, and how is each kind accessed instead?

## btf.core-files: Core files

- section: What the fields are
- relevance: 3 - the code is spread over four files
- words: 60

Which files hold parsing of the fields, copying and freeing them, the map types
that carry them and the verifier's handling of them?

# Copying and freeing

## btf.copy-helpers: Copying a value

- section: Copying, initialising and freeing
- relevance: 4 - a plain memcpy duplicates ownership
- words: 80

Which helpers copy a map value, what do they do about the special fields, and
how does the locked variant differ? Start from `copy_map_value()`,
`copy_map_value_long()` and `copy_map_value_locked()`.

## btf.check-and-init: Initialising fresh values

- section: Copying, initialising and freeing
- relevance: 4 - the other half of a copy
- words: 60

What does `check_and_init_map_value()` do, which lookup and update paths call
it and on what memory, and on what memory is calling it unsafe?

## btf.free-fields: Freeing fields

- section: Copying, initialising and freeing
- relevance: 5 - each field kind has its own destructor and its own context rules
- words: 100

What does `bpf_obj_free_fields()` do for each kind of field, and in which
execution contexts, NMI and interrupts off included, is each of those actions
safe? Start from `kernel/bpf/syscall.c`.

## btf.cancel-fields: Cancelling without freeing

- section: Copying, initialising and freeing
- relevance: 3 - a newer, narrower operation
- words: 60

What does `bpf_obj_cancel_fields()` do, how does it differ from freeing, and who
calls it? If this tree has no such function, say so and stop.

## btf.lookup-usage: Copying out to user space

- section: Copying, initialising and freeing
- relevance: 4 - kernel pointers reach user space otherwise
- words: 70

What handling of special fields is unsafe when a map value is copied out for a
system call lookup, and what does the correct sequence look like? Name a map
type's lookup that shows it.

## btf.update-ownership: Ownership across an update

- section: Copying, initialising and freeing
- relevance: 4 - the old value's resources have to go somewhere
- words: 90

When a map element is updated, what happens to the special fields of the value
being replaced, for a map that updates in place and for one that swaps in a new
element? Who frees them and when?

## btf.delete-and-reuse: Deleting and recycling elements

- section: Copying, initialising and freeing
- relevance: 4 - a recycled element may still own something
- words: 90

When a hash map element is deleted, when are its special fields freed relative
to the element's memory being reused, for preallocated and non-preallocated
maps? Start from `kernel/bpf/hashtab.c` and the allocator's destructor hook.

## btf.nmi-context: Destructors and NMI context

- section: Copying, initialising and freeing
- relevance: 4 - programs run in NMI, destructors may not
- words: 70

Which field destructors must not run in NMI or with interrupts off, and how is
freeing deferred when a program deletes an element from such a context?

# Particular kinds

## btf.timer-lifecycle: Timers and work items

- section: Particular kinds of field
- relevance: 3 - what an armed one keeps alive, and whether tearing it down waits
- words: 80

What does a timer, workqueue or task-work field reference once it is armed,
what cancels it and does that wait for a running callback, and what happens
when the map's last user reference goes? Start from
`bpf_timer_cancel_and_free()`.

## btf.kptr-semantics: Kernel pointers

- section: Particular kinds of field
- relevance: 4 - three kinds with different ownership
- words: 90

How do unreferenced, referenced and per-CPU kernel pointer fields differ in who
owns the object, how a program reads or replaces one, and which destructor runs
when the value is freed? Start from `bpf_kptr_xchg()`.

## btf.graph-ownership: Lists and trees

- section: Particular kinds of field
- relevance: 3 - the root owns the nodes
- words: 80

What does a list head or tree root field own, how do shared ownership and the
reference count field come into it, and what does freeing the root do to the
nodes?

## btf.spin-lock-field: Spin lock fields

- section: Particular kinds of field
- relevance: 3 - one per value, and copies must skip it
- words: 70

How many lock fields may a value have, what do the locking update flag and the
locked copy do with it, and how does the resilient lock differ?

## btf.uptr: User pointers

- section: Particular kinds of field
- relevance: 2 - one map type
- words: 60

What is a user pointer field, which map type allows it, and what is pinned and
unpinned on update and free?

# Changing the implementation

## btf.new-field-kind: Adding a kind of field

- section: What a change must preserve
- relevance: 3 - six places have to agree
- words: 80

What does adding a kind of special field involve: parsing, the size and
alignment tables, copy and init, free and cancel, the map allowlist, the
verifier?

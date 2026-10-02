# Questions: BTF Special Fields in BPF Maps

- guide: btf.md
- title: BTF Special Fields in BPF Maps

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/btf-measurement.md` is the wider
set the readers were measured on and `catalogue/btf-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## btf.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Field kinds and the record

## btf.field-types: Field kinds

- section: Field kinds and the record
- relevance: 4 - each kind owns a different resource

A table of the kinds of special field a map value or allocated object can contain and the kernel
resource, if any, that each holds and that freeing the value has to release, with each kind's
constant name written in full. Say which names that look like kinds are masks over several. Start
from `enum btf_field_type` in `include/linux/bpf.h`.

## btf.record: The field record

- section: Field kinds and the record
- relevance: 4 - everything else walks this record

Where is the record of a value's special fields kept for a map and for an allocated object, what
builds it and when, and how must code that touches a value find the fields in it? Start from
`btf_parse_fields()` and `struct btf_record`.

## btf.map-type-support: Map types per field kind

- section: Field kinds and the record
- relevance: 4 - the allowlist keeps changing

Which function decides which map types may hold which kinds of special field, and what does it
return for a kind or for a map type that it does not list? What must the update, delete and free
paths of a map type do with the special fields of a value before the map type can be allowed for a
kind? Start from `map_check_btf()` in `kernel/bpf/syscall.c`.

## btf.map-create-requirements: Map creation requirements

- section: Field kinds and the record
- relevance: 4 - a patch that adds a field kind or a map flag has to keep these checks

Apart from the map type, what does `map_check_btf()` require before it accepts a map whose value
has special fields, and what does it return when a requirement is not met? Start from
`map_check_btf()` in `kernel/bpf/syscall.c`.

## btf.kptr-semantics: Kptr fields

- section: Field kinds and the record
- relevance: 4 - three kinds with different ownership

For a `BPF_KPTR_UNREF`, a `BPF_KPTR_REF` and a `BPF_KPTR_PERCPU` field, who owns the object the
pointer refers to, and what does `bpf_obj_free_fields()` call on the object when the value is
freed? What does `bpf_kptr_xchg()` do with the pointer it replaces? Start from `bpf_kptr_xchg()`.

## btf.kptr-program-access: Kptr access from programs

- section: Field kinds and the record
- relevance: 4 - the three kinds differ in how a program may load and store the pointer

What does the verifier require of a program that loads the pointer from a `BPF_KPTR_UNREF`, a
`BPF_KPTR_REF` or a `BPF_KPTR_PERCPU` field, and of a program that stores a pointer into one?
Start from `check_map_kptr_access()` in `kernel/bpf/verifier.c`.

# Copying and initialising values

## btf.copy-helpers: Copying a value

- section: Copying and initialising values
- relevance: 4 - a plain memcpy duplicates ownership

Which of `copy_map_value()`, `copy_map_value_long()` and `copy_map_value_locked()` is used when,
and what does each do with the special fields in the source and in the destination? What are the
requirements for copying a map value that has special fields in order to assure safe usage?

## btf.check-and-init: Initialising fresh values

- section: Copying and initialising values
- relevance: 4 - the other half of a copy

What does `check_and_init_map_value()` do to a value, and what are the requirements for the memory
passed to it in order to assure safe usage? Name in-tree code that shows it.

## btf.lookup-usage: Copying out to user space

- section: Copying and initialising values
- relevance: 4 - kernel pointers reach user space otherwise

What are the requirements for the copy of a map value that a lookup system call returns to user
space, with respect to the special fields in the value, in order to assure safe usage? Name a map
type's lookup that shows it. Start from `bpf_map_copy_value()` in `kernel/bpf/syscall.c`.

# Freeing and cancelling fields

## btf.free-contexts: Freeing fields by context

- section: Freeing and cancelling fields
- relevance: 5 - each field kind has its own destructor and its own context rules

A table of what `bpf_obj_free_fields()` does for each kind of field, and the execution contexts,
NMI and interrupts off included, in which the tree allows that action. What does the tree do with
a field whose action is not allowed in the context of the program that deletes the element? Start
from `kernel/bpf/syscall.c`.

## btf.cancel-fields: Cancelling without freeing

- section: Freeing and cancelling fields
- relevance: 3 - a newer, narrower operation

What does `bpf_obj_cancel_fields()` do to each kind of field, and what does it leave in the value
that `bpf_obj_free_fields()` would have released? If this tree has no such function, say so and
stop.

## btf.timer-lifecycle: Timers and work items

- section: Freeing and cancelling fields
- relevance: 3 - what an armed one keeps alive, and whether tearing it down waits

What does a `BPF_TIMER`, a `BPF_WORKQUEUE` or a `BPF_TASK_WORK` field hold a reference on once it
is armed? Do `bpf_timer_cancel_and_free()`, `bpf_wq_cancel_and_free()` and
`bpf_task_work_cancel_and_free()` wait for a running callback? What does the tree do to these
fields when the last user reference to the map is dropped? Start from
`bpf_timer_cancel_and_free()`.

## btf.update-delete-ownership: Updated and deleted elements

- section: Freeing and cancelling fields
- relevance: 4 - a replaced or recycled element may still own something

When a map element is updated or deleted, which function frees the special fields of the old
value, for a map that updates in place and for a map that swaps in a new element? Are the fields
freed before or after the memory of the element can be reused, for a preallocated and for a
non-preallocated hash map? What does the tree guarantee about the special fields of an element
that it hands out for reuse? Start from `kernel/bpf/hashtab.c`, `kernel/bpf/arraymap.c` and the
allocator's destructor hook.

# Model gaps

## btf.model-gaps: Other mistakes models make

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

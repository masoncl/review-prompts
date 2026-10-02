# Questions: Libbpf

- guide: libbpf.md
- title: Libbpf

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/libbpf-measurement.md` is the
wider set the readers were measured on and `catalogue/libbpf-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## libbpf.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## libbpf.core-files: Core files

- section: Finding your way
- relevance: 3 - one very large file and many small ones

A table and nothing else, job to file: opening and loading objects and programs; the low-level
system call wrappers; BTF handling; CO-RE relocation, both the part that drives it and the part
shared with the kernel; the static linker; ring buffers; probing what the running kernel supports;
the public headers; the internal header; the symbol map. Start from `tools/lib/bpf/`.

# Error reporting

## libbpf.error-convention: Error convention

- section: Error reporting
- relevance: 5 - callers depend on it and nothing checks it

How does a public libbpf function report failure when it returns an integer and when it returns a
pointer, and what must be true of `errno` when it does? May a public function return an error
encoded in a pointer?

## libbpf.error-wrappers: The error helpers

- section: Error reporting
- relevance: 5 - the mechanism behind the convention

A table of the error helpers defined beside `libbpf_err()` in `tools/lib/bpf/libbpf_internal.h`,
to choose between: what each is given, whether it sets `errno` or reads it, and what it returns.
Start from `libbpf_err()` in `tools/lib/bpf/libbpf_internal.h`.

## libbpf.wrapper-usage: Using the error helpers

- section: Error reporting
- relevance: 5 - the mistake the old guide exists for

What are the requirements for using `libbpf_err()` and the helpers defined beside it in a public
function, in order to assure safe usage, and where on the error path must the helper be applied?
When is it correct for an internal or static function to end in one of them? Name in-tree code
that shows it.

## libbpf.syscall-wrappers: Low-level syscall wrappers

- section: Error reporting
- relevance: 3 - they translate the kernel's convention

How do the low-level wrappers around the bpf system call report a failure, given that the system
call itself returns -1 and sets `errno`? Start from `tools/lib/bpf/bpf.c` and
`libbpf_err_errno()`.

# Objects and descriptors

## libbpf.object-phases: The phases of an object

- section: Objects and descriptors
- relevance: 3 - setters are only valid in one phase

What phases does a BPF object go through from open to destroy, which kinds of setter are valid in
which phase, and how does a setter find out which phase the object is in? Start from
`bpf_object__prepare()` and `bpf_object__load()`.

## libbpf.fd-ownership: File descriptor ownership

- section: Objects and descriptors
- relevance: 3 - leaks and double closes

Who owns the file descriptors of the programs, maps and links that libbpf creates, and which call
closes each? What do `bpf_link__pin()` and `bpf_link__disconnect()` each change about what
`bpf_link__destroy()` does with the link and its descriptor?

# Public API and compatibility

## libbpf.public-functions: Adding a public function

- section: Public API and compatibility
- relevance: 4 - the rules in this guide apply only to these, and three places change together

What must a patch that adds a function marked `LIBBPF_API` change together with it, and what
decides which version section of `tools/lib/bpf/libbpf.map` the new name goes in? Start from
`LIBBPF_API`.

## libbpf.opts-structs: Options structures

- section: Public API and compatibility
- relevance: 4 - how the API grows without breaking callers

What does `OPTS_VALID()` accept and reject, and how does that let a function gain parameters
without breaking callers built against an older header? What are the requirements for reading or
writing a field of an options structure that a caller's copy may be too short to have, in order to
assure safe usage? Start from `OPTS_VALID()` and `LIBBPF_OPTS()`.

## libbpf.compat: Old kernels and feature probes

- section: Public API and compatibility
- relevance: 3 - the library runs on kernels older and newer than itself

How does libbpf find out what the running kernel supports? What are the requirements for a new
code path that uses a kernel feature not present in every kernel libbpf runs on, in order to
assure safe usage? Name in-tree code that shows it. Start from `kernel_supports()` and
`tools/lib/bpf/features.c`.

# Model gaps

## libbpf.model-gaps: Other mistakes models make

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

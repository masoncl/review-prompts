# Questions: libbpf (measurement set)

- guide: libbpf.md
- title: Libbpf

A wide set of questions about libbpf's public API conventions, used to measure
what a model already knows. The hand-written guide it will replace is 375
words. Format: `../../../docs/subsystem-questions.md`.

# The library

## libbpf.core-files: Core files

- section: Finding your way
- relevance: 3 - one very large file and many small ones
- words: 80

Which files hold the object and program loading code, the low-level system call
wrappers, BTF handling, CO-RE relocation, the linker, ring buffers, the public
headers and the symbol map? A table. Start from `tools/lib/bpf/`.

## libbpf.public-api: Public API marking

- section: Finding your way
- relevance: 4 - the rules below apply only to these
- words: 70

What marks a libbpf function as public API, which headers declare them, and
where is the list of exported symbols? Start from `LIBBPF_API` and
`tools/lib/bpf/libbpf.map`.

## libbpf.upstream: Upstream and mirror

- section: Finding your way
- relevance: 2 - patches go to one place only
- words: 40

Where is libbpf developed, and how does the copy outside the kernel tree relate
to it?

# Errors

## libbpf.error-convention: Error convention

- section: Error reporting
- relevance: 5 - callers depend on it and nothing checks it
- words: 80

How does a public libbpf function report failure when it returns an integer and
when it returns a pointer, and what must be true of `errno`? May a public
function return an error encoded in a pointer?

## libbpf.error-wrappers: The error helpers

- section: Error reporting
- relevance: 5 - the mechanism behind the convention
- words: 90

Which helpers set `errno` and produce the return value for a public function,
and what does each take and return? Start from `libbpf_err()` in
`tools/lib/bpf/libbpf_internal.h`.

## libbpf.wrapper-usage: Using the error helpers

- section: Error reporting
- relevance: 5 - the mistake the old guide exists for
- words: 80

What usage of the error helpers is incorrect in a public function and in an
internal one, and where on the error path must the helper be applied?

## libbpf.internal-errors: Errors inside the library

- section: Error reporting
- relevance: 3 - the two conventions meet at the API boundary
- words: 60

How do internal and static functions report errors, and how does a public
function turn an internal error pointer into its own return? Start from
`libbpf_ptr()`.

## libbpf.syscall-wrappers: Low-level wrappers

- section: Error reporting
- relevance: 3 - they translate the kernel's convention
- words: 60

How do the low-level wrappers around the bpf system call report a failure, given
that the system call itself returns -1 and sets `errno`? Start from
`tools/lib/bpf/bpf.c` and `libbpf_err_errno()`.

# API evolution

## libbpf.adding-api: Adding a public function

- section: Changing the API
- relevance: 4 - three places must be updated together
- words: 80

What does adding a public function involve: the declaration, the symbol map and
its version sections, documentation comments? What decides which version section
it goes in?

## libbpf.opts-structs: Options structures

- section: Changing the API
- relevance: 4 - how the API grows without breaking callers
- words: 90

How do options structures let a function gain parameters without breaking old
callers: the size field, the declaration macro, the validity check, and how a
field is read? Start from `OPTS_VALID()` and `DECLARE_LIBBPF_OPTS()`.

## libbpf.compat: Compatibility rules

- section: Changing the API
- relevance: 3 - the library runs on kernels older and newer than itself
- words: 70

What compatibility does libbpf promise to applications and across kernel
versions, and how does it find out what the running kernel supports? Start from
`kernel_supports()` and `tools/lib/bpf/features.c`.

## libbpf.object-phases: The phases of an object

- section: Changing the API
- relevance: 3 - setters are only valid in one phase
- words: 80

What phases does a BPF object go through from open to destroy, and which kinds
of setter are valid in which phase?

## libbpf.fd-ownership: File descriptor ownership

- section: Changing the API
- relevance: 3 - leaks and double closes
- words: 70

Who owns the file descriptors of programs, maps and links that libbpf creates,
when are they closed, and what does pinning or disconnecting a link change?

## libbpf.logging: Logging

- section: Changing the API
- relevance: 2 - a convention, easily followed by example
- words: 40

How does libbpf code report warnings and debug output, and how does an
application redirect it?

# Questions: Rust in the kernel

- guide: rust.md
- title: Rust Subsystem Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/rust-measurement.md` is the
wider set the readers were measured on and `catalogue/rust-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## rust.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## rust.layout: Crates and directories

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, crate to where it lives: the crates that `rust/Makefile` builds, the
directory or file under `rust/` that is the root of each, and which of them are vendored from
outside the kernel. Add one row each for where Rust drivers and Rust samples live. Start from
`rust/Makefile`.

# Building and toolchain

## rust.unstable-features: Unstable language features

- section: Building and toolchain
- relevance: 5 - decides whether a feature attribute in a patch can build

Which unstable Rust features may code outside `rust/` (a driver, a sample) use, which may the
`kernel` crate itself use, and what in the build, if anything, enforces the difference? Name each
feature in full. Start from `rust_allowed_features` in `scripts/Makefile.build`, the top of
`rust/kernel/lib.rs` and `RUSTC_BOOTSTRAP` in the top-level `Makefile`.

## rust.change-checklist: Minimum toolchain and build configurations

- section: Building and toolchain
- relevance: 4 - the crate is built with older tools and in more configurations than a developer tests

What are the oldest Rust compiler and bindgen a change has to build with, do they differ by
architecture, and where are they enforced? Which builds and tests compile code under
`rust/kernel/` that a developer's default build does not, and which command or option selects
each? Start from `scripts/min-tool-version.sh`.

## rust.lints: Lints and formatting checks

- section: Building and toolchain
- relevance: 4 - decides what CI catches and what a reviewer must

Which lints does an ordinary kernel build turn into errors for Rust code and which into warnings,
is arithmetic overflow checked, and what does an unfulfilled lint expectation do? Start from
`rust_common_flags` in the top-level `Makefile`.

## rust.separate-checks: Separately run checks

- section: Building and toolchain
- relevance: 4 - a reviewer has to know which checks an ordinary build did not run on a patch

Which checks of Rust code run only on a separate make invocation, and which invocation runs each?
What does `.clippy.toml` add to the checks? Start from the top-level `Makefile` and
`.clippy.toml`.

## rust.kconfig-cfg: Kconfig in Rust code

- section: Building and toolchain
- relevance: 4 - conditional compilation errors are what CI misses

How does Rust code test a Kconfig symbol, how does it tell built-in from modular, and how is a
condition that `cfg` cannot express, such as a compiler version, made available? Name an in-tree
example of the last. Start from `Documentation/rust/general-information.rst` and `init/Kconfig`.

## rust.builtin-subsystems: Abstractions for modular subsystems

- section: Building and toolchain
- relevance: 4 - a missing Kconfig dependency breaks the build in one configuration

When the C subsystem an abstraction wraps can be built as a module, under what condition is the
abstraction compiled into the `kernel` crate, and what Kconfig dependency do in-tree Rust drivers
for such a subsystem carry? Start from the `cfg` attributes on the `pub mod` lines of
`rust/kernel/lib.rs`.

## rust.testing: Kinds of test

- section: Building and toolchain
- relevance: 4 - decides where a new test goes and how it runs

Which kinds of test does `Documentation/rust/testing.rst` describe for kernel Rust, which is used
when, and how does each run? What happens to a documentation example that is marked as not to be
run or as failing to compile, or that sits on a private item? Where must the option for a new unit
test suite be added? Start from `Documentation/rust/testing.rst`.

# Reaching C from Rust

## rust.opaque-wrappers: Wrapping C structures

- section: Reaching C from Rust
- relevance: 5 - the shape of almost every abstraction

Which type holds a C structure inside an abstraction, which of its functions cast a pointer to
the wrapper to a pointer to the inner structure and back, and in which module are the trait and
smart pointer for C objects with their own reference count defined? Can they also be named
through `rust/kernel/types.rs`?

## rust.ffi-types: C integer types

- section: Reaching C from Rust
- relevance: 5 - the mapping differs from userspace Rust

Which Rust types do C char, long, unsigned long and size_t map to in kernel Rust, and how does
that differ from `core::ffi`? By which path should code name these types? Which methods of the C
string type, if any, does the Clippy configuration forbid, and what replaces them? Start from
`rust/ffi.rs`.

## rust.bindings-generation: Generating bindings

- section: Reaching C from Rust
- relevance: 4 - the first step of every new abstraction

What must a patch do so that a C function, type or constant becomes visible to Rust through the
`bindings` crate, where do the generated files land, and what is `rust/bindgen_parameters` for?
Start from `rust/bindings/bindings_helper.h`.

## rust.helpers: C helper functions

- section: Reaching C from Rust
- relevance: 5 - every new abstraction of an inline function adds one

What is a file under `rust/helpers/` for, how is a new one made part of the build, and how must
the functions in it be named, as against the name Rust calls them by? If the same C function is
later turned into a real exported function, which one does Rust end up calling?

## rust.helper-attribute: Helper function attribute

- section: Reaching C from Rust
- relevance: 4 - a missing attribute compiles and silently loses the inlining

Do the functions in `rust/helpers/` carry an attribute of their own, and if so what does it
expand to, in which build does it expand to something else, and which Kconfig option, if any, is
it there to serve? Does every helper in the tree carry it? Start from `rust/helpers/helpers.c`.

## rust.foreign-ownable: Handing Rust data to C

- section: Reaching C from Rust
- relevance: 4 - use after free and double free live here

Which trait lets Rust code store an owned Rust value in a C `void *` field and get it back, and
which types implement it? What does that trait require of code that uses the pointer after the
value is stored and before it is taken back? What does it guarantee about the pointer's alignment
and nullness?

## rust.vtable: Vtable traits

- section: Reaching C from Rust
- relevance: 4 - how optional C callbacks are expressed

How does a trait stand for a C structure of optional function pointers: what does `#[vtable]`
generate, what must the body of an optional method be, and how does an abstraction decide whether
to install a callback? Does `#[vtable]` do anything about the owning module? Start from
`rust/macros/lib.rs`.

## rust.layering: Direct use of bindings

- section: Reaching C from Rust
- relevance: 5 - the central design rule of Rust in the kernel

What does the documentation say about a driver calling `bindings::` functions directly, and where
must new `unsafe` wrapping of a C interface go instead? Does in-tree code outside `rust/` use the
generated bindings directly all the same? Name in-tree code that shows it. Start from
`Documentation/rust/general-information.rst` and `drivers/android/binder/`.

# Unsafe code

## rust.safety-comments: Safety comments and sections

- section: Unsafe code
- relevance: 5 - the first thing reviewed in any unsafe code

What is the difference between a `// SAFETY:` comment and a `# Safety` section, where is each
required and what must each say, and which lints enforce their presence and flag needless ones?

## rust.invariant-comments: Type invariants

- section: Unsafe code
- relevance: 4 - safety comments lean on invariants nobody checks

How does kernel Rust document an invariant of a type, and what comment marks the places where a
value of such a type is constructed or changed? Is that convention written down in
`Documentation/rust/`? Name in-tree code that shows it.

## rust.send-sync: Thread safety markers

- section: Unsafe code
- relevance: 4 - a wrong one is a data race no test shows

What are the requirements for an `unsafe impl Send` and for an `unsafe impl Sync` on a wrapper of
a C object in order to assure safe usage, and what must the `// SAFETY:` comment on each justify?
How does a type opt out of both? Name in-tree code that shows it.

## rust.soundness-usage: Soundness of safe functions

- section: Unsafe code
- relevance: 5 - what a review of an abstraction exists to find

What are the requirements for a safe function or a safe trait in an abstraction in order to assure
safe usage by every caller, where it builds a reference from a C pointer or registers a callback
with C? Name in-tree code that shows it.

# Assertions and panics

## rust.build-assert: Build-time assertions

- section: Assertions and panics
- relevance: 4 - the wrong one fails at link time with no message

A table of the build-time assertion macros the `kernel` crate offers to choose among: what the
condition of each may depend on, where each may be written, and how each fails. Which is
preferred when more than one would work, and when does a function that contains one need an
inline attribute, and which? Start from `rust/kernel/build_assert.rs`.

## rust.panics: Panics

- section: Assertions and panics
- relevance: 4 - a panic in kernel Rust stops the machine

What happens when kernel Rust code panics, and which ordinary operations can panic in a default
build (arithmetic, indexing, unwrapping)? What do the documentation and the `kernel` crate offer
instead? What is `unsafe_precondition_assert!` for, and when is it live?

# Core types

## rust.error-handling: Errors and results

- section: Core types
- relevance: 4 - every abstraction converts errno values

How does kernel Rust represent an errno, and which conversion is used for a C return value, for
an error pointer and for a Rust `Result`, in each direction? What may the integer inside the
error type never be? Start from `rust/kernel/error.rs`.

## rust.strings: Strings and formatting

- section: Core types
- relevance: 4 - the types were replaced and old spellings still compile

Which type is `CStr` in kernel Rust, how is a C string constant written, and what is `c_str!`
for? Which of `CStrExt`, `CString` and `BStr` is used when? How does a raw pointer print with
`{:p}` through `fmt!`? Start from `rust/kernel/str.rs` and `rust/kernel/fmt.rs`.

## rust.alloc: Memory allocation

- section: Core types
- relevance: 4 - differs from userspace Rust in every call

Which owned pointer and vector types does kernel Rust use in place of the standard library's, and
which allocator backs which? How is an allocation flag passed and failure reported? What do the
functions of the `Allocator` trait take besides the layout and the GFP flags? Start from
`rust/kernel/alloc.rs`.

## rust.transmute-bytes: Byte conversion traits

- section: Core types
- relevance: 3 - two sets of traits with the same names are in the tree

Which traits mark a type as safe to create from, or view as, raw bytes, which crates provide
them, and which does the prelude export? Can any of them be derived rather than implemented by
hand, and how?

## rust.atomics: Atomic operations

- section: Core types
- relevance: 4 - the language's own atomics follow a different memory model

Which atomic types should kernel Rust use, which memory model do they follow and how are
orderings spelled? What does the tree say about `core::sync::atomic`, and does in-tree code use
it? Start from `rust/kernel/sync/atomic.rs`.

# Pinned initialization

## rust.pin-init-syntax: Initializer macros

- section: Pinned initialization
- relevance: 5 - the syntax is not Rust and reviewers must read it

A table of the initializer macros to choose among and the crate each comes from, saying for each
whether it is pinned and whether it is fallible. What syntax do the macros accept inside the
braces that a struct expression does not? Start from `rust/pin-init/src/lib.rs` and
`rust/kernel/init.rs`.

## rust.pin-data: Pinned structs and in-place allocation

- section: Pinned initialization
- relevance: 4 - needed to read any type that embeds a lock or a work item

How is a struct declared so that it can be pin-initialized, with its structurally pinned fields
and its destructor? Which methods turn an initializer into a box, a reference-counted pointer or
a stack value? What must `unsafe` code inside an initializer guarantee on failure?

# The driver model

## rust.device-contexts: Device contexts

- section: The driver model
- relevance: 4 - the type states decide which methods a callback may call

A table of the type states a `Device` reference can carry: what each proves about the device and
which are reserved for bus abstractions. Which of them may be held in a reference-counted pointer,
and how do they convert into one another? Start from `DeviceContext` in `rust/kernel/device.rs`.

## rust.driver-data: Driver data and device resources

- section: The driver model
- relevance: 5 - the mechanism has been reworked and old driver code no longer matches

What does a bus driver's probe callback return, and what lifetime do the driver's private data
and the device resources in it (a mapped PCI BAR, I/O memory, an IRQ registration) carry? When is
a revocable or devres-managed wrapper needed to hold such a resource, and how is a resource
accessed through one? Start from `rust/kernel/driver.rs`, `rust/kernel/devres.rs` and
`samples/rust/rust_driver_pci.rs`.

# Conventions

## rust.conventions: Conventions for new code

- section: Conventions
- verbatim: ../verbatim/rust-conventions.md

# Model gaps

## rust.model-gaps: Other mistakes models make

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

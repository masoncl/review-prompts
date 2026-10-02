# Questions: Rust in the kernel (measurement set)

- guide: rust.md
- title: Rust Subsystem Details

A wide set of questions about Rust in the kernel: the crates under `rust/`,
how C interfaces reach Rust, the build integration, the conventions a reviewer
enforces, and the shared abstractions every Rust patch leans on. It is used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 417 words.
Individual subsystems' abstractions (DRM, block, network PHY and so on) belong
to those subsystems' guides and are not asked about here. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## rust.layout: Crates and directories

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

What does each directory and top-level file under `rust/` hold, which of them
are crates of their own, which are vendored from outside the kernel, and where
do Rust drivers and samples live? A table. Start from `rust/Makefile`.

## rust.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules live only in rustdoc comments
- words: 70

Which files under `Documentation/rust/` are the authority on style, on the
layering of abstractions and bindings, on testing and on architecture support,
and which conventions a reviewer enforces are written down only in rustdoc
comments inside `rust/`? Name the file for each of those.

## rust.maintainers: Maintainer entries

- section: Finding your way
- relevance: 2 - decides who must see a patch
- words: 60

Which `MAINTAINERS` entries cover Rust code, which parts of `rust/` have an
entry of their own, which mailing list do they share, and who maintains an
abstraction for a C subsystem that lives under `rust/kernel/`?

## rust.crate-graph: Crates visible to a driver

- section: Finding your way
- relevance: 3 - decides what a leaf module may name in a use statement
- words: 70

Which crates can a Rust driver or sample name directly, how does the build
make them visible, and how does such code reach the procedural macros, the
generated C bindings and the userspace API bindings? Start from
`rust_common_cmd` in `scripts/Makefile.build` and `rust/kernel/lib.rs`.

# Build integration

## rust.toolchain: Toolchain versions and architectures

- section: Building
- relevance: 3 - decides which language features and workarounds are needed
- words: 70

What are the minimum versions of the Rust compiler and of bindgen, where are
they defined, do they differ by architecture, and which architectures can
enable Rust at all and under which conditions? Start from
`scripts/min-tool-version.sh` and `HAVE_RUST`.

## rust.unstable-features: Unstable language features

- section: Building
- relevance: 5 - decides whether a feature attribute in a patch can build
- words: 70

Which unstable Rust features may code outside `rust/` (a driver, a sample) use,
which may the `kernel` crate itself use, and what in the build enforces the
difference? Start from `rust_allowed_features` in `scripts/Makefile.build`,
the top of `rust/kernel/lib.rs` and `RUSTC_BOOTSTRAP` in the top-level
`Makefile`.

## rust.lints: Lints and formatting checks

- section: Building
- relevance: 4 - decides what CI catches and what a reviewer must
- words: 90

Which compiler, Clippy and rustdoc lints does every kernel Rust build turn on,
which are errors and which warnings, which Clippy lints are switched off, what
does `.clippy.toml` add, and which make invocations run Clippy and check
formatting? Start from `rust_common_flags` in the top-level `Makefile`.

## rust.kconfig-cfg: Kconfig in Rust code

- section: Building
- relevance: 4 - conditional compilation errors are what CI misses
- words: 60

How does Rust code test a Kconfig symbol, how does it tell built-in from
modular, and how is a condition that `cfg` cannot express, such as a compiler
version, made available? Name an in-tree example of the last. Start from
`Documentation/rust/general-information.rst` and `init/Kconfig`.

## rust.builtin-subsystems: Abstractions for modular subsystems

- section: Building
- relevance: 4 - a missing Kconfig dependency breaks the build in one configuration
- words: 60

When the C subsystem an abstraction wraps can be built as a module, under what
condition is the abstraction compiled into the `kernel` crate, and what Kconfig
dependency do in-tree Rust drivers for such a subsystem carry? Start from the
`cfg` attributes on the `pub mod` lines of `rust/kernel/lib.rs`.

## rust.debug-options: Rust hacking options

- section: Building
- relevance: 3 - they change what a panic or an assertion does
- words: 70

Which Kconfig options under the Rust hacking menu change how Rust code is
compiled or checked, what is the default of each, and what does each do to
integer overflow, to debug assertions, to build-time assertions, to doctests
and to the C helpers? Start from `lib/Kconfig.debug`.

## rust.make-targets: Make targets

- section: Building
- relevance: 2 - how a developer reproduces a report
- words: 60

Which make targets exist for Rust: checking the toolchain, formatting, lints,
documentation, host tests, editor support, and single-file outputs such as
macro-expanded source or assembly? Say which need a configured tree.

## rust.symbol-export: Exported symbols

- section: Building
- relevance: 3 - decides what a module can link against
- words: 60

How do symbols defined in the `kernel` crate and the other crates under `rust/`
become available to loadable modules, under which license restriction, and what
is the `#[export]` attribute for, as opposed to that? Start from
`rust/exports.c`.

# Bindings and helpers

## rust.bindings-generation: Generating bindings

- section: Reaching C from Rust
- relevance: 4 - the first step of every new abstraction
- words: 70

What must a patch do so that a C function, type or constant becomes visible to
Rust through the `bindings` crate, which files are generated and where, and
what is `rust/bindgen_parameters` for? Start from
`rust/bindings/bindings_helper.h`.

## rust.helpers: C helper functions

- section: Reaching C from Rust
- relevance: 5 - every new abstraction of an inline function adds one
- words: 80

What is a file under `rust/helpers/` for, how is a new one made part of the
build, how must the functions in it be named and annotated, and under what name
does Rust call them? If the same C function is later turned into a real
exported function, which one does Rust end up calling?

## rust.helper-attribute: Helper function attribute

- section: Reaching C from Rust
- relevance: 4 - a missing attribute compiles and silently loses the inlining
- words: 60

Do the functions in `rust/helpers/` carry an attribute of their own, and if so
what does it expand to, in which build does it expand to something else, and
which Kconfig option, if any, is it there to serve? Does every helper in the
tree carry it? Start from `rust/helpers/helpers.c`.

## rust.const-helpers: Constants bindgen cannot evaluate

- section: Reaching C from Rust
- relevance: 3 - the usual answer to a constant missing from the bindings
- words: 60

How does the tree expose to Rust a C macro constant that bindgen cannot
evaluate, how are those definitions named, where do they live, and under what
name does Rust see them? Why are some of them also listed in
`rust/bindgen_parameters`?

## rust.ffi-types: C integer types

- section: Reaching C from Rust
- relevance: 5 - the mapping differs from userspace Rust
- words: 70

Which Rust types do C `char`, `long`, `unsigned long` and `size_t` map to in
kernel Rust, how does that differ from `core::ffi`, by which path should code
name these types, and which methods of the C string type does the Clippy
configuration forbid and what replaces them? Start from `rust/ffi.rs`.

## rust.uapi-crate: Userspace API bindings

- section: Reaching C from Rust
- relevance: 2 - a second bindings crate that is easy to overlook
- words: 40

What is the crate under `rust/uapi/` for, how does it differ from the one under
`rust/bindings/`, and who may use it directly?

## rust.layering: Abstractions and leaf modules

- section: Reaching C from Rust
- relevance: 5 - the central design rule of Rust in the kernel
- words: 80

What does the documentation say about a driver calling `bindings::` functions
directly, where must new `unsafe` wrapping of a C interface go instead, and
which in-tree code outside `rust/` nevertheless uses the generated bindings
directly? Start from `Documentation/rust/general-information.rst` and
`drivers/android/binder/`.

# Conventions

## rust.safety-comments: Safety comments and sections

- section: Comments and documentation
- relevance: 5 - the first thing reviewed in any unsafe code
- words: 80

What is the difference between a `// SAFETY:` comment and a `# Safety` section,
where is each required, what must each say, and which lints enforce their
presence and flag needless ones?

## rust.invariant-comments: Type invariants

- section: Comments and documentation
- relevance: 4 - safety comments lean on invariants nobody checks
- words: 70

How does kernel Rust document an invariant of a type, what comment marks the
places where a value of such a type is constructed or changed, is that
convention written down in `Documentation/rust/`, and which file shows it
well?

## rust.tagged-comments: Other tagged comments

- section: Comments and documentation
- relevance: 2 - a reader should recognise them
- words: 50

Besides safety comments, which other tagged comments and rustdoc section
headings are in use under `rust/kernel/`, and what does each justify or
promise?

## rust.doc-style: Documentation style

- section: Comments and documentation
- relevance: 3 - reviewers ask for it and rustfmt does not check it
- words: 70

What are the rules for doc comments and ordinary comments in kernel Rust: the
first paragraph, the sections for panics and examples, links to other items and
to C headers in the source tree, private items, punctuation and Markdown?

## rust.imports: Import formatting

- section: Style
- relevance: 3 - asked for on most patches that touch a use statement
- words: 60

How are `use` statements with several items laid out in kernel Rust, what keeps
rustfmt from undoing that layout, is the rule absolute, and which code under
`rust/` does not follow it?

## rust.expect-allow: Silencing lints

- section: Style
- relevance: 3 - the wrong one hides a warning or breaks a configuration
- words: 70

When should a lint be silenced with `#[expect]` and when with `#[allow]`? What
usage of `#[expect]` on an item that is only used under some `#[cfg(CONFIG_X)]`
is incorrect, and what that looks similar is correct?

## rust.naming: Naming wrapped C concepts

- section: Style
- relevance: 2 - reviewers ask for it
- words: 50

How should a Rust abstraction name a type, function, macro or constant that
wraps an existing C concept, and how are the C name's prefix and casing treated?

## rust.inline-annotations: Inline attributes

- section: Style
- relevance: 3 - reviewers ask for it and nothing checks it
- words: 70

Which functions under `rust/kernel/` carry `#[inline]`, which carry
`#[inline(always)]`, is a rule for either written down anywhere in the tree,
and does driver code follow the same practice?

# Facts that are easy to get wrong

## rust.build-assert: Build-time assertions

- section: Assertions and panics
- relevance: 4 - the wrong one fails at link time with no message
- words: 90

Which build-time assertion macros does the `kernel` crate provide, what may the
condition of each depend on, which is preferred when more than one would work,
how does each fail, and when does a function that contains one need an inline
attribute and which? Start from `rust/kernel/build_assert.rs`.

## rust.panics: Panics

- section: Assertions and panics
- relevance: 4 - a panic in kernel Rust stops the machine
- words: 80

What happens when kernel Rust code panics, which ordinary operations can panic
(arithmetic, indexing, unwrapping), what do the documentation and the `kernel`
crate offer instead, and what is `unsafe_precondition_assert!` for?

## rust.error-handling: Errors and results

- section: Core types
- relevance: 4 - every abstraction converts errno values
- words: 80

How does kernel Rust represent an errno, which functions convert a C return
value, an error pointer and a Rust `Result` to and from it, where are the
named error constants, and what may the integer inside the error type never
be? Start from `rust/kernel/error.rs`.

## rust.strings: Strings and formatting

- section: Core types
- relevance: 4 - the types were replaced and old spellings still compile
- words: 90

Which type is `CStr` in kernel Rust, how is a C string constant written, what
are `c_str!`, `CStrExt`, `CString`, `BStr` and `fmt!` for, and how does a raw
pointer print with `{:p}`? Start from `rust/kernel/str.rs` and
`rust/kernel/fmt.rs`.

## rust.alloc: Memory allocation

- section: Core types
- relevance: 4 - differs from userspace Rust in every call
- words: 80

Which owned pointer and vector types does kernel Rust use in place of the
standard library's, which allocators back them, how is an allocation flag
passed and failure reported, and what besides the GFP flags can be requested?
Start from `rust/kernel/alloc.rs`.

## rust.transmute-bytes: Byte conversion traits

- section: Core types
- relevance: 3 - two sets of traits with the same names are in the tree
- words: 60

Which traits mark a type as safe to create from, or view as, raw bytes, which
crates provide them, which does the prelude export, and how are they derived
rather than implemented by hand?

## rust.pin-init-syntax: Initializer macros

- section: Pinned initialization
- relevance: 5 - the syntax is not Rust and reviewers must read it
- words: 100

What are the initializer macros for pinned and unpinned, fallible and
infallible in-place initialization, which crate provides each, and what inside
the braces differs from a struct expression: in-place fields, running code
between fields, referring to earlier fields, a self pointer, zeroing the rest,
conditional fields, the error type? Start from `rust/pin-init/src/lib.rs` and
`rust/kernel/init.rs`.

## rust.pin-data: Pinned structures

- section: Pinned initialization
- relevance: 4 - needed to read any type that embeds a lock or a work item
- words: 80

How is a struct declared so that it can be pin-initialized, how are fields
marked as structurally pinned, how is a destructor written for it, and which
methods turn an initializer into a box, a reference-counted pointer or a stack
value? What must `unsafe` code inside an initializer guarantee on failure?

## rust.opaque-wrappers: Wrapping C structures

- section: Shared abstractions
- relevance: 5 - the shape of almost every abstraction
- words: 90

How does an abstraction wrap a C structure: which wrapper type holds it and
what does that type switch off, how is a C pointer turned into a Rust reference
and back, how is a pointer to the wrapper cast to a pointer to the inner
structure, and where are the trait and smart pointer for C objects with their
own reference count? Start from `rust/kernel/types.rs`.

## rust.foreign-ownable: Handing Rust data to C

- section: Shared abstractions
- relevance: 4 - use after free and double free live here
- words: 70

How does Rust code store an owned Rust value in a C `void *` field and get it
back, which types can be stored that way, what may be done with the pointer in
between, and what does the trait promise about its alignment and nullness?

## rust.vtable: Vtable traits

- section: Shared abstractions
- relevance: 4 - how optional C callbacks are expressed
- words: 80

How does a trait stand for a C structure of optional function pointers, what
does the attribute generate, what must the body of an optional method be, how
does an abstraction decide whether to install a callback, and what does the
attribute do about the owning module? Start from `rust/macros/lib.rs`.

## rust.module-macro: Module declaration

- section: Shared abstractions
- relevance: 3 - every driver starts with it
- words: 80

Which fields does the macro that declares a Rust kernel module accept, which
are required, how are module parameters declared and read, which traits can the
module type implement, and how do bus abstractions wrap the macro for a driver
with a single registration? Start from `rust/macros/module.rs`.

## rust.send-sync: Thread safety markers

- section: Shared abstractions
- relevance: 4 - a wrong one is a data race no test shows
- words: 70

What must a patch that writes `unsafe impl Send` or `unsafe impl Sync` for a
wrapper of a C object justify, how does a type opt out of both, and what usage
is unsafe, and what that looks similar is correct? Name in-tree code that shows
the correct form.

## rust.locks: Locks

- section: Shared abstractions
- relevance: 3 - the constructors are macros for a reason
- words: 80

Which lock types does `rust/kernel/sync/` provide, why are they created through
macros, why must they be pinned, how is a lock that disables interrupts
expressed, and how is data protected by a lock that lives elsewhere?

## rust.atomics: Atomic operations

- section: Shared abstractions
- relevance: 4 - the language's own atomics follow a different memory model
- words: 60

Which atomic types should kernel Rust use, which memory model do they follow,
how are orderings spelled, and what does the tree say about
`core::sync::atomic`? Start from `rust/kernel/sync/atomic.rs`.

## rust.device-contexts: Device contexts

- section: The driver model
- relevance: 4 - the type states decide which methods a callback may call
- words: 90

Which type states can a `Device` reference carry, what does each prove about
the device, which are reserved for bus abstractions, which is the only one that
may be reference counted, and how do they convert into one another? Start from
`DeviceContext` in `rust/kernel/device.rs`.

## rust.driver-data: Driver data and device resources

- section: The driver model
- relevance: 5 - the mechanism has been reworked and old driver code no longer matches
- words: 100

What does a bus driver's probe callback return, what lifetime do the driver's
private data and the device resources in it (a mapped PCI BAR, I/O memory, an
IRQ registration) carry, when is a revocable or devres-managed wrapper needed
to hold such a resource, and how is a resource accessed through one?
Start from `rust/kernel/driver.rs`, `rust/kernel/devres.rs` and
`samples/rust/rust_driver_pci.rs`.

## rust.soundness-usage: Soundness of safe functions

- section: The driver model
- relevance: 5 - what a review of an abstraction exists to find
- words: 90

What makes a safe function or a safe trait in an abstraction unsound: what
usage of raw pointers, of lifetimes on references built from C pointers, of
interior mutability, or of callbacks that C may run after the Rust value is
gone is unsafe, and what that looks similar is correct? Name in-tree code that
shows the correct form.

# Testing and changing the implementation

## rust.testing: Kinds of test

- section: Tests
- relevance: 4 - decides where a new test goes and how it runs
- words: 80

Which kinds of test exist for kernel Rust, how does each run, which Kconfig
options turn them on, where must the option for a new unit test suite be
added, and which crate's examples run on the build host instead?
Start from `Documentation/rust/testing.rst`.

## rust.doctest-style: Writing examples

- section: Tests
- relevance: 3 - examples are compiled and run, so reviewers read them as code
- words: 60

How should an example in a doc comment be written given that it becomes a test:
error handling, assertions, hidden lines, examples that must not run or must
not compile, and whether examples on private items are run?

## rust.vendored-crates: Vendored crates

- section: Changing `rust/`
- relevance: 2 - patches to them follow other rules
- words: 60

Which crates under `rust/` are copies of outside projects, how are lints
treated when they are built, do kernel style rules apply to them, and which of
them is developed upstream first with its own contribution rules?

## rust.change-checklist: Changing the kernel crate

- section: Changing `rust/`
- relevance: 4 - the crate is built in more configurations than a developer tests
- words: 80

What must a change under `rust/kernel/` keep working besides the default build:
the minimum compiler version, configurations where a module is compiled out,
32-bit and other architectures, Clippy, rustdoc, the doctests, the host tests
and the in-tree users outside `rust/`? Say which command or option checks each.

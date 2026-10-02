# What the rust measurement found

Three models were asked the 49 questions in `rust-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.16 to 7.0) and needed the fewest corrections, reader A
was close behind it (6.13 to 6.18), and reader B was older (6.12 to 6.13), had
every answer substantially rewritten, and made up several files and options.
The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted near the
end.

Readers A and C know this code well: how bindings and helpers are generated
and named, the constant helpers, the C integer types, the lint set, safety
comments and sections, the invariant convention and that it is unwritten, the
allocation and error types, `ForeignOwnable`, the pinned initialization syntax,
which abstractions are only built when their C subsystem is built in. What all
three get wrong is what moved most recently: the toolchain floor, the list of
unstable features a driver may use, a second set of byte-conversion traits in
the prelude, what `#[vtable]` does about the owning module, how `{:p}` prints,
and above all how a driver's private data and device resources are tied to the
bound scope. Reader B gets the basics wrong as well, so the build set keeps
several questions two readers answer when the hand-written guide cared about
the topic.

## What all three readers got wrong

- **Driver data carries a lifetime.** Every reader described probe returning
  `impl PinInit<Self, Error>` (reader B: `Result<Self::Data>`) with each device
  resource wrapped in `Devres`. In the tree a bus driver trait has
  `type Data<'bound>: Send + 'bound` and `probe()` returns
  `impl PinInit<Self::Data<'bound>, Error> + 'bound` (`rust/kernel/driver.rs`,
  `rust/kernel/pci.rs`). `pci::Bar<'a, SIZE>` and `IoMem<'a>` borrow the bound
  device and are stored directly; `samples/rust/rust_driver_pci.rs` holds
  `Bar0<'bound>` with no `Devres` and no `access()` call. `Devres` is opt-in,
  through `Bar::into_devres()` and `DevresLt`, for a resource that has to
  outlive the borrow. `irq::Registration` holds an `IrqRequest<'a>` and embeds
  no `Devres`; its `new()` is `unsafe` because the value must not be leaked
  with `mem::forget()`. `Devres::access()` returns `Result<&T>` and `EINVAL`
  for a different device. Reader C said plainly that it knew of no
  lifetime-parameterised driver data.
- **Device contexts.** No reader listed `BoundInternal`, none knew that `Core`
  and `CoreInternal` carry a branding lifetime (`Core<'a>`), and reader B
  invented bus-specific contexts. Private driver data is reached through
  `InternalBoundContext`, which covers `CoreInternal` and `BoundInternal`.
- **Toolchain floor.** All three said rustc 1.78.0 and bindgen 0.65.1 with no
  difference by architecture. `scripts/min-tool-version.sh` gives rustc 1.85.0
  (1.95.0 for powerpc, 1.96.0 for s390) and bindgen 0.71.1. All three left
  s390 and powerpc out of the architectures that select `HAVE_RUST`.
- **Unstable features.** Readers A and C recited a seven-entry list that is
  gone; reader B gave none. `rust_allowed_features` in `scripts/Makefile.build`
  is `arbitrary_self_types`, `asm_goto`, `generic_arg_infer` and
  `used_with_arg`, enabled for every leaf crate with `-Zcrate-attr`. The
  `kernel` crate's own list has no `coerce_unsized`, `dispatch_from_dyn` or
  `unsize`, which both named.
- **Two sets of byte traits.** Readers A and C knew only
  `kernel::transmute::FromBytes` and `AsBytes` and said there is no derive and
  no prelude export. The tree vendors `rust/zerocopy/` and
  `rust/zerocopy-derive/`, passes `--extern zerocopy --extern zerocopy_derive`
  to every leaf crate, and the prelude exports `zerocopy::{FromBytes,
  IntoBytes}` with their derives. The `kernel::transmute` traits are still
  there, hand-implemented, and are not in the prelude. Reader B knew of
  zerocopy but not of the kernel's own pair. No reader listed the zerocopy
  directories among the vendored crates.
- **`#[vtable]` and the owning module.** All three said the attribute does
  nothing about it. `rust/macros/vtable.rs` adds
  `type OwnerModule: ModuleMetadata` to the trait and
  `type OwnerModule = crate::LocalModule` to an impl that does not set one;
  `rust/kernel/miscdevice.rs` uses it for `.owner`. A `HAS_` constant is
  generated for every method, not only the defaulted ones.
- **`{:p}` is hashed.** All three said or guessed that it prints the real
  address. `fmt!` routes raw pointers through `Adapter` to `HashedPtr` in
  `rust/kernel/fmt.rs`, which formats with the C `%p`.
- **Build-time assertions.** Reader B did not know `static_assert!` or
  `const_assert!`; reader A was unsure `const_assert!` exists; A and C had the
  conditions each may use slightly wrong (`static_assert!` may not use
  variables either and is the only one usable outside a body; `const_assert!`
  is checked only for instantiated functions).
- **Kconfig in Rust.** Readers A and B said a modular symbol sets a
  `CONFIG_FOO_MODULE` cfg; it sets `CONFIG_FOO` and `CONFIG_FOO="m"`. The
  version-gate example A and C gave, RUSTC_HAS_COERCE_POINTEE, is not in the
  tree; `RUSTC_HAS_FILE_WITH_NUL` is one that is.
- **Doctests.** A `no_run` example is still built and run under KUnit
  (`scripts/rustdoc_test_builder.rs` saves every test and
  `scripts/rustdoc_test_gen.rs` calls each), which is why every in-tree one
  puts its code in a function that is never called; `compile_fail` is not
  checked; examples on private items are not run. The option for a new
  `#[kunit_tests]` suite goes in `rust/kernel/Kconfig.test`, and the macro
  gates the module on `CONFIG_KUNIT="y"`.
- **Atomics.** The type list also has `i8`, `i16`, `bool` and raw pointers;
  only `i32` and `i64` sit on `atomic_t` and `atomic64_t`. The tree says Rust's
  own atomics "should be avoided", and `drivers/gpu/nova-core/gsp/cmdq.rs`
  uses `core::sync::atomic::fence`.
- **Maintainers.** All three missed `RUST [BITFIELD]`, `RUST [INTEROP]`,
  `RUST [NUM]` and `RUST [SYNC]`, and that abstractions for a C subsystem often
  have their own `[RUST]` entry maintained by Rust developers.

## What only some readers got wrong

- **The helper attribute.** Readers A and B said `__rust_helper` expands to
  nothing in a normal build (reader B: to `__used` under LTO).
  `rust/helpers/helpers.c` defines it as `__always_inline`, and as nothing
  only under `__BINDGEN__`, because bindgen skips inline functions; it serves
  `CONFIG_RUST_INLINE_HELPERS`. Reader A said not every helper carries it;
  every definition under `rust/helpers/` does. Reader A did not know which of
  a helper and a real binding Rust calls: `rust/bindings/lib.rs` makes the
  direct binding win and the helper dead code.
- **Names that moved.** Reader A still had Opaque::raw_get(); the tree has
  `Opaque::cast_into()` and `Opaque::cast_from()`. Readers A and C said
  `rust/kernel/types.rs` re-exports `ARef` and `AlwaysRefCounted`; they are
  only in `rust/kernel/sync/aref.rs`.
- **Imports.** Reader A said the trailing `//` must follow the last item and
  that the style is only preferred; the guidelines say it works on any line,
  call the rule "not a hard rule", and ask that no new code use another style.
  Reader B described one-line merged imports produced by a rustfmt
  configuration that does not exist.
- **The zeroing trailer** of an initializer is `..Zeroable::init_zeroed()`;
  readers A and B wrote `..Zeroable::zeroed()`, which the parser rejects.
- Reader A did not recognise `unsafe_precondition_assert!`
  (`rust/kernel/safety.rs`, live only with `CONFIG_RUST_DEBUG_ASSERTIONS`).
  Reader C said there is no interrupt-disabling spinlock; `SpinLockIrq` and
  `new_spinlock_irq!` are in `rust/kernel/sync/lock/spinlock.rs`.

## What reader B got wrong as well

- Helpers are named after the C function they wrap (the name carries a
  `rust_helper_` prefix, except the find-bit helpers in
  `rust/helpers/bitops.c`, which omit it on purpose so that the declarations
  in `include/linux/find.h` match); constant helpers live under `rust/helpers/` (they
  are in `rust/bindings/bindings_helper.h`); there is a `c_size_t` in
  `rust/ffi.rs` (there is not); the Clippy configuration forbids `to_str()`
  (it forbids `as_ptr()` and `from_ptr()` on the C string type).
- An invariant is stated in an `// INVARIANT:` comment beside the type, and
  the convention is in the coding guidelines. It is a `# Invariants` doc
  section, `// INVARIANT:` marks construction and change, and nothing under
  `Documentation/rust/` mentions either.
- Every lint is a warning (`non_ascii_idents` and `unsafe_op_in_unsafe_fn` are
  errors); overflow checks default to off (`RUST_OVERFLOW_CHECKS` is
  `default y`); an unfulfilled `#[expect]` is a build error (a warning).
- `CStr` is the kernel's own type (it is `core::ffi::CStr`); all four
  initializer macros come from the `pin_init` crate (`try_pin_init!` and
  `try_init!` are in `rust/kernel/init.rs`); an abstraction for a modular
  subsystem is gated on a plain `#[cfg(CONFIG_X)]` (DRM, I2C, USB and
  GPU_BUDDY use `= "y"`); `#[export]` exports to modules (it does not).
- Names it made up: a `rust/alloc/` directory, rust/kernel/panic.rs,
  rust/helpers.c, rust/rustfmt.toml, Error::from_ptr(), a `make clippy`
  target, an `author` field in `module!`.

## What the readers already knew

How a header reaches bindgen and what is generated (A and C), helper naming,
`#[link_name]` and the constant helpers (A and C), the C integer mapping and
the forbidden `CStr` methods (A and C), the whole lint list (A and C), safety
comments against safety sections, `# Invariants` and `// INVARIANT:` and that
they are unwritten (A and C), `#[expect]` against `#[allow]`, the naming rule,
make targets, symbol export, `Error` and its conversions, the allocator types
and flags, `ForeignOwnable`, `Opaque` and the wrapper shape, `Send` and `Sync`
justification, the initializer syntax apart from the zeroing trailer, the
layering rule and that binder is the in-tree exception, and that an abstraction
for a tristate subsystem is only built when it is `y` (A and C).

## Where the hand-written guide is stale

`rust.md` is mostly right where it is specific, and incomplete rather than
wrong:

- "Assume Rust unstable features are available (the kernel uses
  `RUSTC_BOOTSTRAP=1`)" is too strong. Code outside `rust/` is built with
  `-Zallow-features=` and the four features listed above; anything else fails
  to build. Host programs get an empty list.
- It gives one build-time assertion. The tree has three, prefers
  `static_assert!` and `const_assert!` where they work, and the
  `#[inline(always)]` rule is written in `rust/kernel/build_assert.rs`.
- It states the `#[inline]` rule for abstractions as if it were written down.
  Nothing under `Documentation/rust/` or `rust/kernel/` states it; it is
  practice, applied unevenly (`Device::as_raw()` has none), and
  `#[inline(always)]` is also used with no `build_assert!` on the `Atomic<T>`
  operations.
- Its pin-init section is right but leaves out `&this in`,
  `..Zeroable::init_zeroed()`, `#[cfg]` on fields and the `? Type` error
  suffix.
- "Vendored crates (e.g. syn, pin-init) are exempt" from the import style: the
  `rustfmt` target skips syn, quote, proc-macro2, zerocopy and zerocopy-derive,
  but not pin-init, which is also built without `--cap-lints=allow`.
- The invariant comment convention it describes is real but is not in the
  coding guidelines it points to.
- It says nothing of the layering rule, the zerocopy traits, the driver
  lifetime model or where things live. It was never onboarded to the drift
  checker.

## What was left out of the build set and why

The hand-written guide is 417 words, so the built guide is sized to the 600-word
floor (480 to 720). With no answer budgeted under 40 words that is room for ten
questions and 565 words of budget. The first build set asked thirteen at 20 to
35 words each, 325 in all, and more than a quarter of the bullets it produced
were fragments that meant nothing without the question beside them, so this one
asks fewer and gives each more room. Six follow the hand-written guide's
emphasis (unstable features, helpers, C integer types, build-time assertions
with the inline rule that goes with them, initializer macros, invariant
comments), because reader B is wrong on all of them and every reader is wrong
on some detail. Four more are what every reader got wrong and a reviewer of any
Rust patch meets: names that moved, the two sets of byte traits, driver data
and device resources, and the checklist for a change to the `kernel` crate
(which carries the toolchain floor and the architectures). Left to the source:

- Where things live (`rust.layout`), the documentation pointer (`rust.docs`)
  and the `#[inline]` practice (`rust.inline-annotations`). All three were in
  the first build set and gave way to the larger budgets. Readers A and C place
  the crates correctly apart from the zerocopy directories, which the byte
  traits answer names; the files under `Documentation/rust/` are named for what
  they hold; and the one inline rule the tree writes down, `#[inline(always)]`
  where a `build_assert!` condition depends on an argument, is asked for by
  `rust.build-assert`. The rest of the inline practice is unwritten and uneven,
  and readers A and C describe it as such.
- The toolchain and architecture table, lints, make targets, debug options,
  symbol export, the crates a driver can name (one file each, and the old
  guide tells reviewers to assume the code builds).
- Bindings generation, constant helpers, the UAPI crate, the layering rule,
  safety comments, tagged comments, documentation style, imports, `#[expect]`,
  naming (readers A and C fair, and `Documentation/rust/` covers them; reader B
  is wrong on imports and the pointer is what it needs).
- Panics, errors, strings, allocation, pinned structures, `ForeignOwnable`,
  the module macro, `Send` and `Sync`, locks, soundness of safe functions
  (readers A and C fair; the errors listed above are each in one rustdoc
  comment a reviewer of such a patch will open).
- `#[vtable]` and the owning module, `{:p}` hashing, atomics, device contexts,
  `no_run` doctests and the vendored crates: all three readers were wrong, and
  they are recorded here, but each is confined to one kind of patch and there
  was no room.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader-A          107        33%     10     16   6.13 to 6.18
reader-B          124        78%      0     49   6.12 to 6.13
reader-C           83        25%     18     12   6.16 to 7.0

question                      reader-A      reader-B      reader-C   verdict
rust.layout                   11% ( 9)      87% ( 6)      33% ( 3)   weak: reader-B
rust.docs                     51% ( 2)      84% ( 3)      15% ( 1)   weak: reader-A, reader-B
rust.maintainers              54% ( 2)      88% ( 3)      18% ( 1)   weak: reader-A, reader-B
rust.crate-graph              28% ( 1)      90% ( 3)      27% ( 2)   weak: reader-B
rust.toolchain                51% ( 5)      80% ( 2)      38% ( 5)   weak: reader-A, reader-B
rust.unstable-features        20% ( 2)      60% ( 1)      14% ( 1)   weak: reader-B
rust.lints                    24% ( 2)      80% ( 4)      19% ( 1)   weak: reader-B
rust.kconfig-cfg              28% ( 2)      86% ( 2)      15% ( 1)   weak: reader-B
rust.builtin-subsystems        0% ( 0)      81% ( 1)      50% ( 1)   weak: reader-B, reader-C
rust.debug-options            27% ( 1)      74% ( 1)      10% ( 1)   weak: reader-B
rust.make-targets              0% ( 0)      70% ( 2)       0% ( 0)   weak: reader-B
rust.symbol-export            27% ( 1)      82% ( 1)      17% ( 1)   weak: reader-B
rust.bindings-generation      62% ( 3)      80% ( 3)      18% ( 2)   weak: reader-A, reader-B
rust.helpers                  27% ( 1)      66% ( 1)      28% ( 1)   weak: reader-B
rust.helper-attribute         80% ( 1)      76% ( 1)      36% ( 1)   weak: reader-A, reader-B
rust.const-helpers            39% ( 1)      84% ( 1)       1% ( 1)   weak: reader-B
rust.ffi-types                30% ( 1)      76% ( 1)       8% ( 1)   weak: reader-B
rust.uapi-crate                5% ( 1)      80% ( 1)       0% ( 0)   weak: reader-B
rust.layering                 37% ( 1)      86% ( 1)      42% ( 1)   weak: reader-B, reader-C
rust.safety-comments          10% ( 1)      57% ( 1)      14% ( 1)   weak: reader-B
rust.invariant-comments       10% ( 2)      83% ( 2)       3% ( 2)   weak: reader-B
rust.tagged-comments          37% ( 3)      93% ( 1)      30% ( 1)   weak: reader-B
rust.doc-style                50% ( 3)      82% ( 3)      40% ( 1)   all weak
rust.imports                  49% ( 3)      87% ( 4)      15% ( 2)   weak: reader-A, reader-B
rust.expect-allow             19% ( 2)      67% ( 1)      22% ( 1)   weak: reader-B
rust.naming                   36% ( 1)      88% ( 1)       0% ( 0)   weak: reader-B
rust.inline-annotations       38% ( 2)      88% ( 1)      51% ( 4)   weak: reader-B, reader-C
rust.build-assert             50% ( 3)      85% ( 4)      43% ( 3)   all weak
rust.panics                   43% ( 3)      74% ( 4)      42% ( 4)   all weak
rust.error-handling           15% ( 1)      73% ( 4)       6% ( 3)   weak: reader-B
rust.strings                  37% ( 3)      76% ( 5)      17% ( 1)   weak: reader-B
rust.alloc                     0% ( 0)      75% ( 3)       5% ( 1)   weak: reader-B
rust.transmute-bytes          76% ( 2)      88% ( 3)      66% ( 1)   all weak
rust.pin-init-syntax          19% ( 1)      81% ( 5)       6% ( 1)   weak: reader-B
rust.pin-data                 37% ( 3)      65% ( 4)      26% ( 2)   weak: reader-B
rust.opaque-wrappers          16% ( 4)      71% ( 4)       6% ( 1)   weak: reader-B
rust.foreign-ownable          20% ( 3)      59% ( 2)      22% ( 1)   weak: reader-B
rust.vtable                   56% ( 2)      80% ( 2)      49% ( 1)   all weak
rust.module-macro             11% ( 3)      75% ( 3)       9% ( 1)   weak: reader-B
rust.send-sync                 0% ( 0)      81% ( 1)      15% ( 1)   weak: reader-B
rust.locks                    32% ( 4)      83% ( 2)      38% ( 1)   weak: reader-B
rust.atomics                  49% ( 3)      85% ( 2)      46% ( 1)   all weak
rust.device-contexts          56% ( 1)      78% ( 3)      39% ( 2)   weak: reader-A, reader-B
rust.driver-data              71% ( 3)      90% ( 2)      70% ( 3)   all weak
rust.soundness-usage          17% ( 2)      76% ( 2)      37% ( 2)   weak: reader-B
rust.testing                  37% ( 2)      70% ( 4)      35% ( 2)   weak: reader-B
rust.doctest-style            42% ( 2)      80% ( 4)      60% ( 5)   all weak
rust.vendored-crates          59% ( 3)      85% ( 4)      43% ( 5)   all weak
rust.change-checklist         33% ( 6)      70% ( 5)      21% ( 4)   weak: reader-B
```

In the build set `rust.opaque-wrappers` is worded more narrowly than it was
measured, and `rust.helpers` also asks what the helpers' annotation expands to,
which was measured as `rust.helper-attribute`. Four questions carry a few words
the measured text did not, so that none presupposes its answer:
`rust.transmute-bytes` asks whether any of the traits can be derived,
`rust.unstable-features` asks what if anything enforces the difference and for
each feature's name in full, and `rust.helpers` and `rust.ffi-types` say "if
any" of the annotation and of the forbidden methods. The ids are unchanged.

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `rust.builtin-subsystems`, `rust.bindings-generation`, `rust.helper-attribute`, `rust.layering`, `rust.panics`, `rust.vtable`, `rust.atomics`, `rust.device-contexts`, `rust.testing`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `rust.layout`, `rust.lints`, `rust.kconfig-cfg`, `rust.safety-comments`, `rust.error-handling`, `rust.strings`, `rust.alloc`, `rust.pin-data`, `rust.foreign-ownable`, `rust.send-sync`, `rust.soundness-usage`.

## Questions reorganised

Subjects now, after the map of `rust/`: building and toolchain, reaching C from Rust, unsafe code,
assertions and panics, core types, pinned initialization, the driver model. The parts named for a
kind of statement are gone. Nothing merged or dropped: 32 before and after. `rust.helpers` no
longer asks about the helpers' attribute, which `rust.helper-attribute` asks beside it.
`rust.change-checklist` asks for the toolchain floor and the configurations a default build
misses, `rust.lints` for what an ordinary build catches and what needs a separate invocation,
`rust.testing` for which kind of test is used when; none of them asks for a list any more.

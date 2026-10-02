# What the libbpf measurement found

Two models were asked the questions in `libbpf-measurement.md` with no sources, and a checker
that had the sources then corrected each answer against a mainline tree (kernel
7.3.0-rc4). The readers are labelled A (the more current) and B (a few releases
older); which models they were does not matter here. The hand-written guide was
never checked against current sources, so differences between it and the built
guide are expected and are noted at the end.

## Reader A knew almost all of it

The error helpers and what adding an API function involves needed no
corrections. Its slips were small: which file drives CO-RE relocation, that the
static `bpf_object_load()` is an internal function that does use the public
error helper, that the low-level wrappers end in `libbpf_err_errno()`.

## What reader B got wrong

- `libbpf_err_errno()` "sets errno like `libbpf_err()`". It reads `errno` and
  returns its negation.
- libbpf is developed on GitHub and synced into the kernel. It is the other way
  round: the kernel tree is where changes go, the repository is a mirror.
- `OPTS_VALID()` accepts a zero size. `libbpf_validate_opts()` rejects anything
  smaller than a `size_t`, and checks the bytes after the last field libbpf
  knows, not after the structure.
- The symbol map uses 0.x stanzas; the newest are 1.x. The documentation
  comments are doxygen style, not kernel-doc.
- Destroying a disconnected link closes its file descriptor. It skips the
  detach callback, which is what would close it, so the descriptor stays open.
- It left out the prepared state of an object, after which map setters fail.

## Where the hand-written guide is stale

`libbpf.md` is accurate about the three helpers it names. It does not mention
`libbpf_err_errno()`, which the low-level wrappers in `bpf.c` use, and it was
never onboarded to the drift checker.

## What was left out of the build set and why

The build set has 11 of the 14 questions and 520 words of budget. The
hand-written guide is 375 words, under the 600-word floor for a built guide, so
the set is sized to 600 words (480 to 720) with no question budgeted under 40.
The first cut, 8 questions and 310 words held to the 375, left 25 to 50 words
an answer, and the answers came out as fragments that needed the question
beside them. Kept from the first cut: where the files and the API marking are,
the error convention, the four helpers and how they are used (what the guide is
loaded for, and where reader B was wrong about `libbpf_err_errno()`), the
low-level wrappers, adding a public function and the options structures. Added
with the larger size:

- `libbpf.object-phases`: reader B left out the prepared state, and a new
  setter has to test for the right one.
- `libbpf.fd-ownership`: reader B had a disconnected link's descriptor closed
  on destroy, and leaks and double closes turn on who closes what.
- `libbpf.compat`: the checker rewrote 39% and 87% of the two answers, and a
  patch that uses a kernel feature without probing for it breaks on the
  kernels that lack it.

Left out:

- `libbpf.internal-errors`, because `libbpf.error-wrappers` already says what
  `libbpf_ptr()` does with an internal error pointer and
  `libbpf.wrapper-usage` what an internal function returns.
- `libbpf.upstream`: reader B had the direction backwards, but a patch under
  review here is already in the kernel tree, which is where it belongs.
- `libbpf.logging`: relevance 2, a convention followed by example.

They stay in the measurement set.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 15 corrections, 19% rewritten on average
reader B: 19 corrections, 70% rewritten on average

question                 reader A        reader B
libbpf.core-files         14% ( 2)        12% ( 1)
libbpf.public-api         23% ( 3)        63% ( 1)
libbpf.upstream           12% ( 0)        77% ( 1)
libbpf.error-convention    7% ( 1)        48% ( 1)
libbpf.error-wrappers      0% ( 0)        84% ( 2)
libbpf.wrapper-usage      26% ( 2)        80% ( 2)
libbpf.internal-errors    15% ( 1)        39% ( 1)
libbpf.syscall-wrappers   27% ( 1)        90% ( 1)
libbpf.adding-api          0% ( 0)        72% ( 4)
libbpf.opts-structs       27% ( 1)        87% ( 1)
libbpf.compat             39% ( 1)        87% ( 1)
libbpf.object-phases      44% ( 1)        79% ( 1)
libbpf.fd-ownership        9% ( 1)        84% ( 1)
libbpf.logging            31% ( 1)        91% ( 1)
```

## Questions reorganised

Subjects: error reporting (the convention, the helpers, their usage, the low-level wrappers);
objects and descriptors; the public API (what marks it and adding to it, options structures,
compatibility). 13 questions became 12: `libbpf.public-api` and `libbpf.adding-api`, which both
asked about the declaration and the symbol map, are now `libbpf.public-functions`. Nothing was
dropped. `libbpf.error-wrappers` is a table of helpers to choose between, `libbpf.opts-structs` and
`libbpf.compat` each ask for the unsafe usage as well, and the pointer DECLARE_LIBBPF_OPTS(), a
legacy alias, became `LIBBPF_OPTS()`.

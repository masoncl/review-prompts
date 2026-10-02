# Questions: Objtool

- guide: objtool.md
- title: Objtool

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/objtool-measurement.md` is the
wider set the readers were measured on and `catalogue/objtool-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## objtool.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## objtool.core-files: Core files

- section: Finding your way
- relevance: 4 - the kernel-side macros are spread over several headers

A table and nothing else, job to file: the main checking pass; the per-architecture instruction
decoders; the reading of special sections; the ELF layer; ORC generation; the list of functions
that do not return; the livepatch subcommands; the kernel-side annotation macros; their type
numbers; the unwind-hint macros; the documentation. If the tree has no file for a job, say so in
the row. Start from `tools/objtool/` and `include/linux/objtool.h`.

## objtool.build-integration: Build integration

- section: Finding your way
- relevance: 4 - decides whether a per-file exception can work at all

On which objects does the build run objtool, which configuration options move the run from the
translation unit to link time, and which kbuild files compose its command line? Start from
`scripts/Makefile.lib` and `scripts/Makefile.vmlinux_o`.

# Annotations

## objtool.annotation-mechanism: Annotation sections

- section: Annotations
- relevance: 5 - the section names and the header have moved

Through which ELF sections do annotations in kernel code reach objtool, and which kernel headers
define the annotation macros and their type numbers? In what order does objtool read the
annotations and the unwind hints? Start from `read_annotate()` and
`include/linux/objtool_types.h`.

## objtool.annotation-types: Annotation types

- section: Annotations
- relevance: 5 - each one silences a different check

A table of the instruction annotation types this tree defines, the macro kernel code uses for
each, and what each makes objtool do or stop checking. Start from the `ANNOTYPE_` constants.

## objtool.reachability-annotations: Reachability annotations

- section: Annotations
- relevance: 4 - readers remember sections and macros that may be gone

Does `unreachable()` in `include/linux/compiler.h` emit anything for objtool? Which annotation
tells objtool that the code path carries on past a dead-end instruction, and on which instruction
does that annotation go?

## objtool.unread-sections: Sections that macros write

- section: Annotations
- relevance: 4 - an annotation in a section that objtool does not read changes nothing

Does objtool read every section that a macro in `include/linux/objtool.h` writes? Name each macro
whose section objtool does not read.

## objtool.func-vs-code: Callable and non-callable asm

- section: Annotations
- relevance: 4 - the wrong symbol type produces most asm warnings

What does objtool assume about the stack at entry to assembly marked with `SYM_FUNC_START` and to
assembly marked with `SYM_CODE_START`, what does each kind of code have to provide, and which
warnings come from marking code as the wrong kind?

## objtool.new-annotation-checklist: Adding an annotation type

- section: Annotations
- relevance: 3 - the number is shared between the kernel and the tool

What does objtool do when it reads an instruction annotation type or an unwind hint type that it
does not know? Which headers under `tools/` are copies of the kernel headers that define those
types, and what in the build compares each copy with its original?

## objtool.header-copy-check: Header copy comparison

- section: Annotations
- relevance: 3 - decides whether a copy that was not updated is noticed

Does the comparison of the header copies under `tools/` with the kernel headers run for every
architecture that objtool supports, and does a difference fail the build or print a warning? Start
from `tools/objtool/Makefile`.

## objtool.non-standard-usage: Skipping validation

- section: Annotations
- relevance: 5 - an exception that silently does nothing, or drops unwind data

What do `STACK_FRAME_NON_STANDARD`, `STACK_FRAME_NON_STANDARD_FP` and `OBJECT_FILES_NON_STANDARD`
each make objtool skip, and what happens to the ORC data of a skipped function? What are the
requirements for using each of the three in order for it to take effect and to assure safe usage?
Start from `add_ignores()` and `scripts/Makefile.build`.

# Trap instructions and dead ends

## objtool.bug-vs-trap: BUG and trap instruction types

- section: Trap instructions and dead ends
- relevance: 5 - swapping the two hides warnings or creates false ones

What does the generic code in `tools/objtool/check.c` do with an instruction that the decoder
typed `INSN_BUG`, and what with one typed `INSN_TRAP`, in the branch walk and in the checks that
run after it? What must be true of an instruction of each type for those checks to give the right
result?

## objtool.arch-bug-trap-map: Per-architecture BUG and trap encodings

- section: Trap instructions and dead ends
- relevance: 4 - the mapping is per architecture and has changed

Which machine instructions do the decoders under `tools/objtool/arch/` type `INSN_BUG`, and which
do they type `INSN_TRAP`? Does any decoder use neither type?

## objtool.runtime-trap-match: Kernel BUG and WARN macros

- section: Trap instructions and dead ends
- relevance: 4 - the decoder and the trap handler have to agree

On x86 and LoongArch, which instruction do `BUG()` and `WARN()` emit, which of those does
objtool's decoder treat as ending the code path, and how does the warning case keep the code after
it reachable for objtool? Start from `arch/x86/include/asm/bug.h` and
`arch/loongarch/include/asm/bug.h`.

## objtool.compiler-traps: Compiler-generated trap instructions

- section: Trap instructions and dead ends
- relevance: 4 - a classification change can turn compiler output into warnings

Which flags do the architecture Makefiles pass to stop the compiler from emitting trap or break
instructions that objtool's decoder classifies, and under which configuration option is each flag
passed? How does `ignore_unreachable_insn()` treat the trap instructions that remain?

## objtool.dead-end-detection: Functions that do not return

- section: Trap instructions and dead ends
- relevance: 5 - the most common objtool warning in C code comes from here

How does objtool decide that a call does not return, for a global function and for a local one?
What must someone who adds a `__noreturn` function to the kernel change for objtool, and which
warning appears if they do not? Start from `__dead_end_function()` and
`tools/objtool/noreturns.h`.

## objtool.rust-noreturn: Rust noreturn functions

- section: Trap instructions and dead ends
- relevance: 5 - a Rust function that does not return is not found the way a C function is

How does objtool decide that a Rust function does not return, and what must someone who adds such
a function change for objtool? Start from `is_rust_noreturn()`.

# Objtool diagnostics

## objtool.warnings-vs-errors: Warnings and errors

- section: Objtool diagnostics
- relevance: 4 - decides whether a finding breaks the build

What is the difference between what objtool reports as a warning and as an error, does this tree
have an option that upgrades warnings and which configuration symbol passes it, and what happens
to the object file when objtool fails? Start from `tools/objtool/include/objtool/warn.h` and the
end of `check()`.

## objtool.warning-meanings: Common warnings

- section: Objtool diagnostics
- relevance: 5 - the warning text is what a patch author sees

For each warning that `tools/objtool/Documentation/objtool.txt` explains, what condition in
`tools/objtool/check.c` produces it, and what fix does the documentation give? Where does the text
that `check.c` prints differ from the text in the documentation? Start from the `WARN_INSN()`
calls in `tools/objtool/check.c`.

# Noinstr and uaccess

## objtool.noinstr-validation: Noinstr validation

- section: Noinstr and uaccess
- relevance: 5 - entry code correctness rests on it

Which sections does objtool treat as non-instrumentable, which call targets are allowed from them
without a warning, and how are `instrumentation_begin()` and `instrumentation_end()` encoded and
counted? Start from `noinstr_call_dest()` and `include/linux/instrumentation.h`.

## objtool.noinstr-usage: Calls from noinstr code

- section: Noinstr and uaccess
- relevance: 4 - the annotation pair is easy to misplace

What are the requirements for a call from a `noinstr` function in order for objtool to accept it?
What are the requirements for placing `instrumentation_begin()` and `instrumentation_end()`, and
what does `instrumentation_end()` emit?

## objtool.uaccess-validation: Uaccess validation

- section: Noinstr and uaccess
- relevance: 5 - a call with user access enabled is a security bug

With user access enabled or the direction flag set, what does objtool check at a call, at a return
and at the instruction that disables access, and what is different inside a function on the safe
list? In which code does objtool track a save or a restore of the flags register? Start from
`validate_call()`, `validate_return()` and `uaccess_safe_builtin`.

## objtool.uaccess-usage: Calls with user access enabled

- section: Noinstr and uaccess
- relevance: 5 - which functions may run between the begin and end of a user access

What are the requirements for code between `user_access_begin()` and `user_access_end()` in order
for objtool to accept it? What does `tools/objtool/Documentation/objtool.txt` require of a
function before it is added to `uaccess_safe_builtin`?

# Stack validation and unwind hints

## objtool.unwind-hint-types: Unwind hint types

- section: Stack validation and unwind hints
- relevance: 4 - entry code review depends on knowing what each asserts

A table of the unwind hint types this tree defines to choose among: what each tells objtool about
the stack at that instruction, and which have no matching ORC type. Which section carries the
hints? Start from `include/linux/objtool_types.h` and `read_unwind_hints()`.

## objtool.stack-rules: Stack validation rules

- section: Stack validation and unwind hints
- relevance: 4 - the rules asm and inline asm must follow

What does stack validation require of a callable function, what must an inline asm statement that
contains a call declare, and which of the checks apply only when frame pointers are configured?
Start from `validate_insn()` and `validate_return()`.

## objtool.alternatives: Alternatives and the stack state

- section: Stack validation and unwind hints
- relevance: 4 - one unwind table has to fit every patched variant

What must hold about the stack state across all variants of an alternative, and which warning says
it does not? Under which conditions does objtool validate only one variant of an alternative?
Start from `handle_group_alt()` and `skip_alt_group()`.

# Model gaps

## objtool.model-gaps: Other mistakes models make

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

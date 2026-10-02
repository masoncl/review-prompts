# Questions: Objtool (measurement set)

- guide: objtool.md
- title: Objtool

A wide set of questions about `tools/objtool` and the annotations kernel code
uses to satisfy it, used to measure what a model already knows before deciding
what the built guide should spend its words on. The hand-written guide it will
replace is 312 words and covers only how two instruction types are classified.
Format: `../../../docs/subsystem-questions.md`.

# The tool

## objtool.core-files: Core files

- section: Finding your way
- relevance: 4 - the kernel-side macros are spread over several headers
- words: 110

Which files hold objtool's main checking pass, the per-architecture
instruction decoders, the reading of special sections, the ELF layer, ORC
generation, the list of functions that do not return, the livepatch
subcommands, the kernel-side annotation and unwind-hint macros, and the
documentation? A table. Say so for any of these this tree does not have.
Start from `tools/objtool/` and `include/linux/objtool.h`.

## objtool.build-integration: Build integration

- section: Finding your way
- relevance: 4 - decides whether a per-file exception can work at all
- words: 90

Which kbuild files compose objtool's command line, on which objects is it run
(each translation unit, `vmlinux.o`, linked modules), and which configuration
options move the run from the translation unit to link time? Start from
`scripts/Makefile.lib` and `scripts/Makefile.vmlinux_o`.

## objtool.actions-and-config: Actions and their config options

- section: Finding your way
- relevance: 3 - a warning only appears when its action is enabled
- words: 110

Give a table of objtool's action options (the ones in the actions group of
`check_options[]` in `tools/objtool/builtin-check.c`) and the kernel
configuration symbol that passes each one. Which actions may only be used on a
linked object?

## objtool.arch-support: Architecture support

- section: Finding your way
- relevance: 3 - a rule that holds on one architecture is not checked on another
- words: 80

Which architectures have a decoder under `tools/objtool/arch/`, and for each,
which objtool features does the kernel enable (stack validation, ORC
generation, noinstr and uaccess validation, mcount, static calls)? Start from
the `select HAVE_OBJTOOL` lines and `tools/objtool/Makefile`.

## objtool.decode-order: Decode step ordering

- section: How a run proceeds
- relevance: 3 - a new step put in the wrong place reads state that is not set yet
- words: 100

List in order the steps `decode_file()` in `tools/objtool/check.c` performs
between decoding instructions and the start of validation, and say which
ordering constraints between them the code states.

## objtool.validation-passes: Validation passes

- section: How a run proceeds
- relevance: 3 - says which options make the branch walk run at all
- words: 90

In `check()` in `tools/objtool/check.c`, which validation passes run, in which
order, and which options enable each? Which options cause the full walk of
every function's code paths, and what runs instead when only noinstr
validation is asked for?

## objtool.warnings-vs-errors: Warnings and errors

- section: How a run proceeds
- relevance: 4 - decides whether a finding breaks the build
- words: 80

What is the difference between what objtool reports as a warning and as an
error, does this tree have an option that upgrades warnings and which
configuration symbol passes it, and what happens to the object file when
objtool fails? Start from `tools/objtool/include/objtool/warn.h` and the end
of `check()`.

## objtool.debugging-aids: Investigating a warning

- section: How a run proceeds
- relevance: 3 - the documentation asks for this output with every report
- words: 70

Which options and environment variables help someone investigate an objtool
warning (more context, a backtrace of the branch walk, disassembly, a trace of
one function's validation, a copy of the failing object), and how are they
passed through a kernel build?

# Instruction classification

## objtool.insn-types: Instruction types

- section: Decoders
- relevance: 3 - the generic passes only see these types
- words: 100

List the values of `enum insn_type` in `tools/objtool/include/objtool/arch.h`
and say for each what the generic code in `tools/objtool/check.c` does with it
that it does not do for an ordinary instruction.

## objtool.bug-vs-trap: BUG and trap instruction types

- section: Decoders
- relevance: 5 - swapping the two hides warnings or creates false ones
- words: 100

How does the generic code treat an instruction the decoder typed as
`INSN_BUG` and one it typed as `INSN_TRAP`? Name every function in
`tools/objtool/check.c` that tests either type and say what the test decides.
What goes wrong if a decoder gives an instruction the wrong one of the two?

## objtool.arch-bug-trap-map: Per-architecture BUG and trap encodings

- section: Decoders
- relevance: 4 - the mapping is per architecture and has changed
- words: 70

For each architecture decoder under `tools/objtool/arch/`, which machine
instructions are typed `INSN_BUG` and which `INSN_TRAP`? A table. Say so if a
decoder uses neither.

## objtool.runtime-trap-match: Classification and runtime handling

- section: Decoders
- relevance: 4 - the decoder and the trap handler have to agree
- words: 90

On x86 and LoongArch, which instruction do `BUG()` and `WARN()` emit, which of
those does objtool's decoder treat as ending the code path, and how does the
warning case keep the code after it reachable for objtool? Start from
`arch/x86/include/asm/bug.h` and `arch/loongarch/include/asm/bug.h`.

## objtool.compiler-traps: Compiler-generated trap instructions

- section: Decoders
- relevance: 4 - a classification change can turn compiler output into warnings
- words: 90

Which compiler behaviours insert trap or break instructions that objtool's
decoder then classifies, which flags do the architecture Makefiles pass to
avoid them (name the flags, where they are set, and whether each depends on
objtool being enabled), and how does `ignore_unreachable_insn()` deal with the
ones that remain?

## objtool.dead-end-detection: Functions that do not return

- section: Decoders
- relevance: 5 - the most common objtool warning in C code comes from here
- words: 100

How does objtool decide that a call does not return, for a global function and
for a local one, and does it treat Rust functions separately? What must
someone adding a `__noreturn` function to the kernel do, and which warning
appears if they do not? Start from `__dead_end_function()` and
`tools/objtool/noreturns.h`.

## objtool.jump-tables: Switch jump tables

- section: Decoders
- relevance: 3 - differs per architecture and per compiler flag
- words: 90

How does objtool find the jump table behind an indirect jump in a switch
statement on each architecture it supports, how is a jump table written by
hand in C marked so that it is found, and which compiler flags do the
architecture Makefiles use to avoid or annotate jump tables? Start from
`find_jump_table()` and `__annotate_jump_table`.

# Annotations

## objtool.annotation-mechanism: Annotation sections

- section: Annotating code
- relevance: 5 - the section names and the header have moved
- words: 90

Through which ELF sections do annotations in kernel code reach objtool, what
is the layout of an entry in each, which kernel header defines the annotation
macros and which defines the type numbers, and which objtool function reads
them? Start from `read_annotate()` and `include/linux/objtool_types.h`.

## objtool.annotation-types: Annotation types

- section: Annotating code
- relevance: 5 - each one silences a different check
- words: 130

Give a table of the instruction annotation types this tree defines, the macro
kernel code uses for each, and what each makes objtool do or stop checking.
Start from the `ANNOTYPE_` constants.

## objtool.reachability-annotations: Reachability annotations

- section: Annotating code
- relevance: 4 - readers remember sections and macros that may be gone
- words: 80

Does `unreachable()` in `include/linux/compiler.h` emit anything for objtool
in this tree? How does code tell objtool that the instruction after a
dead-end instruction is reachable, which sections does objtool read for
reachability, and is any macro left in `include/linux/objtool.h` that writes a
section objtool does not read?

## objtool.func-vs-code: Callable and non-callable asm

- section: Annotating code
- relevance: 4 - the wrong symbol type produces most asm warnings
- words: 80

What does objtool assume about the stack at entry to assembly marked with
`SYM_FUNC_START` and to assembly marked with `SYM_CODE_START`, what does each
kind of code have to provide, and which warnings come from marking code as the
wrong kind?

## objtool.non-standard-usage: Skipping validation

- section: Annotating code
- relevance: 5 - an exception that silently does nothing, or drops unwind data
- words: 100

What do `STACK_FRAME_NON_STANDARD`, `STACK_FRAME_NON_STANDARD_FP` and
`OBJECT_FILES_NON_STANDARD` each make objtool skip, and what happens to the
ORC data of a skipped function? What usage of each is ineffective or unsafe,
and what that looks similar is correct? Start from `add_ignores()` and
`scripts/Makefile.build`.

## objtool.unwind-hint-types: Unwind hint types

- section: Unwind hints
- relevance: 4 - entry code review depends on knowing what each asserts
- words: 110

Give a table of the unwind hint types this tree defines, what each tells
objtool about the stack at that instruction, and which have no matching ORC
type. What are the fields of `struct unwind_hint` and which section holds
them? Start from `include/linux/objtool_types.h` and `read_unwind_hints()`.

## objtool.unwind-hint-macros: Architecture hint macros

- section: Unwind hints
- relevance: 3 - the same macro name expands differently per architecture
- words: 90

Which unwind hint macros do `arch/x86/include/asm/unwind_hints.h` and
`arch/loongarch/include/asm/unwind_hints.h` provide, for assembly and for C,
and where do the two architectures differ in what a macro of the same name
expands to? Which x86 hint macros also start return-thunk untraining
validation?

# Validation

## objtool.stack-rules: Stack validation rules

- section: Stack validation
- relevance: 4 - the rules asm and inline asm must follow
- words: 100

What rules does stack validation enforce on a callable function (frame
pointer setup before a call, the stack state at a return or sibling call,
entry and exit instructions), what must an inline asm statement that contains
a call declare, and which checks only apply when frame pointers are
configured? Start from `validate_insn()` and `validate_return()`.

## objtool.alternatives: Alternatives and the stack state

- section: Stack validation
- relevance: 4 - one unwind table has to fit every patched variant
- words: 90

How does the branch walk follow alternative instruction groups, jump labels
and exception table entries, what must hold about the stack state across all
variants of an alternative and which warning says it does not, and which
annotation or special case makes objtool follow only one variant? Start from
`handle_group_alt()` and `skip_alt_group()`.

## objtool.noinstr-validation: Noinstr validation

- section: Noinstr and uaccess
- relevance: 5 - entry code correctness rests on it
- words: 100

Which sections does objtool treat as non-instrumentable, which call targets
are allowed from them without a warning, how are `instrumentation_begin()` and
`instrumentation_end()` encoded and counted, and which warnings does the check
produce? Start from `noinstr_call_dest()` and
`include/linux/instrumentation.h`.

## objtool.noinstr-usage: Calls from noinstr code

- section: Noinstr and uaccess
- relevance: 4 - the annotation pair is easy to misplace
- words: 80

In a `noinstr` function, what usage of calls to ordinary functions, indirect
calls, paravirt calls and static calls is flagged, and what that looks similar
is accepted? Why is `instrumentation_end()` an instruction and not just a
label?

## objtool.uaccess-validation: Uaccess validation

- section: Noinstr and uaccess
- relevance: 5 - a call with user access enabled is a security bug
- words: 110

What state does objtool track for user access and the direction flag, which
instructions change it, how are saves and restores of the flags register
handled, what is checked at a call, at a return and at the disabling
instruction, and what is different inside a function on the safe list? Start
from `validate_call()`, `validate_return()` and `uaccess_safe_builtin`.

## objtool.uaccess-usage: Calls with user access enabled

- section: Noinstr and uaccess
- relevance: 5 - which functions may run between the begin and end of a user access
- words: 90

Between `user_access_begin()` and `user_access_end()`, what usage is flagged
by objtool, and what that looks similar is accepted? What does the
documentation require of a function before it is added to the safe list, and
which kinds of function are on it?

## objtool.mitigation-checks: Speculation mitigation checks

- section: Mitigations and generated sections
- relevance: 3 - each has its own annotation to vouch for an exception
- words: 110

What do the retpoline, return-thunk, straight-line-speculation and
return-untraining checks each require of the code, which warning does each
give, which code is exempt, and which annotation vouches for an exception to
each? Start from `validate_retpoline()`, `validate_sls()` and
`validate_unret()`.

## objtool.ibt-validation: Indirect branch tracking checks

- section: Mitigations and generated sections
- relevance: 3 - explains the relocation warnings and what silences them
- words: 90

What does objtool's indirect branch tracking validation check about
references to code, which warnings does it produce, which annotations say a
reference is never used for an indirect branch, and what does objtool emit so
that unused landing pads can be removed at boot? Start from `validate_ibt()`.

## objtool.generated-sections: Sections objtool writes

- section: Mitigations and generated sections
- relevance: 3 - the kernel consumes these at boot
- words: 100

Which sections and symbols does objtool add to an object file, under which
option each, and what in the kernel consumes them? A table. Start from the
`create_` functions called from `check()`.

# Warnings

## objtool.warning-meanings: Common warnings

- section: Reading a warning
- relevance: 5 - the warning text is what a patch author sees
- words: 150

Give a table of the warnings a kernel developer is most likely to see from
objtool (about ten), saying for each what it means and the usual fix. Include
any whose text differs from what `tools/objtool/Documentation/objtool.txt`
prints. Start from the `WARN_INSN()` calls in `tools/objtool/check.c`.

## objtool.documentation: Documentation coverage

- section: Reading a warning
- relevance: 2 - says where the written rules are and where they stop
- words: 60

Which documents in the tree describe objtool, its rules and its warnings, what
does `tools/objtool/Documentation/objtool.txt` cover, and which objtool
features in this tree does it not describe?

# Changing objtool

## objtool.decoder-change-checklist: Changing a decoder

- section: What a change must preserve
- relevance: 5 - what the hand-written guide exists for
- words: 100

What must a change to how an architecture decoder types an instruction be
checked against: the generic passes that act on the type, the compiler's own
use of that instruction, the architecture Makefile, and the kernel's runtime
handling of the instruction? Name where each is found.

## objtool.new-annotation-checklist: Adding an annotation type

- section: What a change must preserve
- relevance: 3 - the number is shared between the kernel and the tool
- words: 80

Which files have to change to add a new instruction annotation type or a new
unwind hint type, in the kernel and under `tools/`, and what breaks if only
some of them are changed?

## objtool.tools-header-sync: Headers shared with the kernel

- section: What a change must preserve
- relevance: 3 - a kernel header change can need a matching change under tools/
- words: 80

Which kernel headers and source files does objtool keep copies of under
`tools/`, what checks that the copies match and when does it run, and what
does it do when they differ? Start from `tools/objtool/sync-check.sh`.

## objtool.klp-subcommands: Livepatch subcommands

- section: What a change must preserve
- relevance: 2 - shares the ELF and decode code with the checker
- words: 80

What do the `objtool klp` subcommands do, which files implement them, what do
they need from the host to be built, which annotations in kernel headers exist
for them, and which script drives them? If this tree has no such subcommands,
say so and stop.

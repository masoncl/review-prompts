# Questions: Kernel build system

- guide: build.md
- title: Kernel Build System

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/build-measurement.md` is the
wider set the readers were measured on and `catalogue/build-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## build.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## build.core-files: Core files

- section: Finding your way
- relevance: 4 - several of the shared makefiles have been renamed or split

A table and nothing else, job to file: the rules that compile the objects of one directory; the
assembly of each object's flags; the machinery that reruns a command when it changes; the compiler
and linker option probes; host programs; userspace programs; the default and extra warning
options; the module stages that follow compilation; each step from the per-directory archives to
vmlinux; the installation of exported headers; the minimal tool versions the build enforces. Where
no single file in this tree does the job, say so in the row. Start from the top-level `Makefile`
and `scripts/`.

# Language and toolchain

## build.c-dialect: C dialect and global options

- section: Language and toolchain
- relevance: 5 - decides whether a construct is valid kernel C

In which C dialect does the build compile kernel code, which language extensions does it switch on
for every file, and which variable holds the dialect so that a makefile with a flag set of its own
can reuse it? Give every option by its full name. Start from `KBUILD_CFLAGS` in the top-level
`Makefile`.

## build.undefined-behaviour-options: Undefined behaviour options

- section: Language and toolchain
- relevance: 5 - decides whether a construct that the C standard leaves open is valid in kernel code

Which options in `KBUILD_CFLAGS` decide behaviour that the C standard leaves undefined or to the
implementation, and which of them does the build add only under a configuration option or a
compiler probe? Give every option and configuration symbol by its full name. Start from
`KBUILD_CFLAGS` in the top-level `Makefile`.

## build.tool-versions: Minimal tool versions

- section: Language and toolchain
- relevance: 4 - decides which compiler features and workarounds are still needed

How does the build refuse a tool that is older than the minimum in `scripts/min-tool-version.sh`,
and which file only documents the minimal versions? For which tools does the enforced minimum
depend on the architecture? Start from `scripts/min-tool-version.sh`.

## build.separate-flag-sets: Code built with its own flags

- section: Language and toolchain
- relevance: 4 - the global options do not reach this code

Which of the options in `KBUILD_CFLAGS` may code rely on when a makefile compiles it with a flag
set of its own, and how does a makefile replace the global flags for its objects? What are the
requirements for a source file that is compiled both with such a flag set and with the global
flags, in order to assure safe usage?

## build.tools-tree: The tools directory

- section: Language and toolchain
- relevance: 3 - kernel assumptions about the compiler do not hold there, and not uniformly

Which of the compiler options that `KBUILD_CFLAGS` sets for kernel code does the build also set
for code under `tools/`, and is the answer the same for every tool? Where does a makefile under
`tools/` set the flags of one tool, and where does that code get kernel headers from? Start from
`tools/scripts/Makefile.include` and `tools/build/`.

## build.script-languages: Interpreters for build scripts

- section: Language and toolchain
- relevance: 4 - a script that runs on the author's machine may not run elsewhere

Which interpreters, and which oldest Python, may a script that runs during the build rely on, and
which shell runs a recipe line? What are the requirements for the way a makefile rule invokes a
script, a script that needs bash included, in order to assure correct usage? Start from the script
invocation section of `Documentation/kbuild/makefiles.rst`.

# Exported headers

## build.uapi-export: Exported header processing

- section: Exported headers
- relevance: 4 - a new UAPI header can fail the install step

What does `scripts/headers_install.sh` rewrite or strip in a header exported to userspace, and
which contents make it fail? How does the tree exempt a header from those checks or keep it out of
the export? Start from `scripts/Makefile.headersinst` and `scripts/headers_install.sh`.

## build.uapi-header-test: Compile test of exported headers

- section: Exported headers
- relevance: 4 - limits the C a UAPI header may use

Does the build compile-test the headers it exports to userspace, and under which configuration
option? With which language standards and flags, given in full, does it compile them? How does
`usr/include/Makefile` excuse a header that cannot pass? Start from `usr/include/Makefile`.

## build.uapi-header-checks: Checks beyond a plain compile

- section: Exported headers
- relevance: 4 - a header that compiles can still fail the test

Apart from compiling a header as C, what does `cmd_hdrtest` in `usr/include/Makefile` check about
an exported header, and what does `usr/include/headers_check.pl` reject? Start from
`usr/include/Makefile`.

# Probing the toolchain

## build.option-probing: Option probes in makefiles

- section: Probing the toolchain
- relevance: 5 - copied from old makefiles, several no longer exist

A table of the probes that `scripts/Makefile.compiler` defines to test for a compiler, assembler,
linker or Rust compiler option or version: what each runs and which existing flags it includes in
the test. What does a probe do when it is handed an option that disables a warning? Start from
`scripts/Makefile.compiler`.

## build.probing-usage: Using option probes

- section: Probing the toolchain
- relevance: 4 - a probe in the wrong place is slow or gives the wrong answer

What are the requirements for a makefile that calls a probe from `scripts/Makefile.compiler`, in
order to assure correct usage? When does the tree put the test in a Kconfig symbol, and how do the
probes in `scripts/Kconfig.include` differ from the makefile probes in the flags they pass?

# Saying what to build

## build.goals: Goal variables

- section: Saying what to build
- relevance: 5 - every kbuild makefile is written in these

A table of the goal variables that `scripts/Makefile.build` reads: what Kbuild does with each and
when it is built. Which goal variables does `Documentation/kbuild/makefiles.rst` call deprecated,
and what does it say to write in their place? Start from the variables initialised at the top of
`scripts/Makefile.build`.

## build.duplicate-objects: Objects listed more than once

- section: Saying what to build
- relevance: 5 - decides what a reviewer says about a makefile that lists an object in two places

What does Kbuild do with an object that a makefile lists twice in one goal variable, and with a
source object that is listed in more than one module? Start from `modname-multi` in
`scripts/Makefile.lib`.

## build.host-programs: Host programs

- section: Saying what to build
- relevance: 4 - build-time tools are in many directories, and an unread variable builds nothing

What must a makefile write for a host program that is made of one source file, of several objects,
in C++ or in Rust, and what besides listing the program makes Kbuild build it? Which variables set
its compile and link flags for a directory and for one file? Start from `scripts/Makefile.host`.

## build.descending: Descending into subdirectories

- section: Saying what to build
- relevance: 5 - the wrong form builds nothing, or links nothing, without an error

Which forms tell Kbuild to descend into a subdirectory, and how do they differ in what is linked
into vmlinux and in whether modules found there are built? What does each form require of the goal
variables in the makefile of the subdirectory, and what does Kbuild do with an object that the
form does not collect? Start from `subdir-ym`, `need-builtin` and `need-modorder`.

# Flags and paths

## build.flag-variables: Per-directory and per-file flags

- section: Flags and paths
- relevance: 5 - the variables every driver makefile uses

For adding or removing a compiler, assembler, preprocessor, linker or Rust flag for one file, for
one directory, and for a directory and everything below it, which variable is used when? In what
order are they combined with the global flags, and which of them can put back a flag that another
removed? Start from `_c_flags` in `scripts/Makefile.lib`.

## build.include-paths: Source and object paths

- section: Flags and paths
- relevance: 5 - a wrong path works in-tree and fails elsewhere

What do `$(src)`, `$(obj)`, `$(srctree)`, `$(objtree)` and `$(srcroot)` hold when building
in-tree, with a separate output directory, and for an external module? What are the requirements
for an include path or a file reference in a kbuild makefile in order to work in all three builds?
Which include paths does Kbuild add by itself?

## build.instrumentation-opt-out: Instrumentation switches

- section: Flags and paths
- relevance: 4 - low-level code that is instrumented crashes or fails to link

Which objects does the build instrument or run objtool on when their makefile says nothing, and
how are the per-file and per-directory switches that turn one kind on or off named? What are the
requirements for the makefile of code that must not be instrumented, in order to assure safe
usage? Start from `is-kernel-object` in `scripts/Makefile.lib`.

# Custom rules

## build.if-changed: Command change detection

- section: Custom rules
- relevance: 5 - a rule written wrongly rebuilds every time, never, or runs nothing

Which macros can a custom rule choose among so that the rule reruns when its command line changes?
What are the requirements for the prerequisites, for `targets` and for the rule that calls
`if_changed`, in order to assure correct usage? Start from `if_changed` in
`scripts/Kbuild.include`.

## build.dependency-tracking: Header and configuration dependencies

- section: Custom rules
- relevance: 4 - what is rebuilt after a configuration change rests on this

Which objects does Kbuild rebuild when a `CONFIG_` option changes, and how does it know which
objects use the option? What are the requirements for a makefile whose object includes a header
that is generated in the same directory, in order to assure correct usage? Start from
`scripts/basic/fixdep.c`.

# Modules and modpost

## build.modpost-checks: Modpost diagnostics

- section: Modules and modpost
- relevance: 5 - decides whether a missing macro breaks the build

A table of the problems that modpost reports for a module or for vmlinux, saying of each whether
it is an error that stops the build or only a warning. Which option or variable, named in full,
turns which of the errors into warnings? Start from `read_symbols()` and `check_exports()` in
`scripts/mod/modpost.c`.

## build.symbol-namespaces: Namespaces in makefiles and modpost

- section: Modules and modpost
- relevance: 4 - the quoting changed and old forms no longer compile

How does a makefile put all of a directory's exports into one symbol namespace, and how must the
value be quoted? What does modpost do when a module uses a namespaced symbol without importing the
namespace? Which namespaces does the tree not let a module import explicitly?

## build.external-modules: External modules

- section: Modules and modpost
- relevance: 4 - shared makefiles must keep this working

Which command-line variables name the source of an external module and a separate directory for
its output, and what must already be built in the kernel tree? How does the build get the symbols
of another external module?

## build.external-module-steps: Build steps for external modules

- section: Modules and modpost
- relevance: 4 - a change to the top-level makefile has to keep the external module build working

Which steps of the build does the top-level `Makefile` leave out or change when `KBUILD_EXTMOD` is
set?

# Shared makefiles

## build.kbuild-change-checklist: Changing Kbuild itself

- section: Shared makefiles
- relevance: 4 - the shared makefiles run in many more setups than a developer tests

Which build setups other than an in-tree build must a rule in a shared makefile under `scripts/`
support, and what does the tree require of the rule for each? Name the code in the shared
makefiles that handles each setup.

# Model gaps

## build.model-gaps: Other mistakes models make

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

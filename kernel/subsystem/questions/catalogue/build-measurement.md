# Questions: Kernel build system (measurement set)

- guide: build.md
- title: Kernel Build System

A wide set of questions about Kbuild: the makefiles in each directory, the
shared makefiles under `scripts/`, compiler flags and option probes, modules
and modpost, exported headers, and the tools a build needs. It is used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 247 words and
covers only script languages, tool versions and a few compiler options. The
Kconfig language has its own set. Format: `../../../docs/subsystem-questions.md`.

# The build system

## build.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

Which files hold the rules that compile the objects of one directory, the
assembly of each object's flags, the machinery that reruns a command when it
changes, the compiler and linker option probes, host programs, userspace
programs, cleaning, the default and extra warning options, the module stages
that follow compilation, the steps from per-directory archives to vmlinux, and
the installation of exported headers? A table. Start from the top-level
`Makefile` and `scripts/`.

## build.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules are written down only there
- words: 60

Which files under `Documentation/` are the authority on kbuild makefile
syntax, on the variables a user can pass to make, on external modules, on
building with Clang, on reproducible builds, on minimal tool versions and on
the C dialect?

## build.vmlinux-stages: From archives to vmlinux

- section: Finding your way
- relevance: 3 - a change to the link has to go in the right stage
- words: 100

List in order the intermediate artifacts between the per-directory archives
and the final `vmlinux`, and name the makefile or script that produces each.
Where in that chain do modpost, objtool on the whole image, BTF generation and
table sorting run? Start from the `vmlinux` rule in the top-level `Makefile`.

## build.arch-makefile: Architecture makefiles

- section: Finding your way
- relevance: 3 - what belongs in which of an architecture's two files
- words: 100

What is an architecture's top `Makefile` expected to set or provide (flags,
image name and boot targets, directories to visit, prerequisite hooks), what
goes in the architecture's `Kbuild` file instead and why, and what is the
post-link hook? Start from the architecture section of
`Documentation/kbuild/makefiles.rst`.

## build.output-directory: Separate output directory

- section: Finding your way
- relevance: 3 - rules that work in-tree break here
- words: 70

How does building into a separate output directory work: which variables
select it, how does make re-invoke itself there, what is checked about the
source tree, and what must a makefile rule never do if it is to stay correct
in that mode?

# Kbuild makefiles

## build.goal-variables: Goal variables

- section: Saying what to build
- relevance: 5 - every kbuild makefile is written in these
- words: 120

Which variables may a kbuild makefile assign to say what gets built (objects
for vmlinux, modules, library objects, files built whenever the directory is
visited, host and userspace programs, other targets), and what does Kbuild do
with each? Is any of them deprecated or unused in this tree, and what is
written instead? A table. Start from the variables initialised at the top of
`scripts/Makefile.build`.

## build.composite-objects: Composite objects

- section: Saying what to build
- relevance: 4 - how most modules are declared
- words: 80

How is an object or module that is built from several source files declared,
which suffixes on the variable name does Kbuild recognise, and what does Kbuild
do when one source object is listed in more than one module? Start from
`multi-search` and `modname-multi`.

## build.builtin-and-module: Objects listed twice

- section: Saying what to build
- relevance: 3 - decides which of two entries wins
- words: 50

What happens to an object that ends up in both `obj-y` and `obj-m`, or in both
`obj-y` and `lib-y`, and what does `lib-m` do?

## build.descending: Descending into subdirectories

- section: Saying what to build
- relevance: 5 - the wrong form builds nothing, or links nothing, without an error
- words: 100

Which forms tell Kbuild to descend into a subdirectory, and how do they differ
in what is linked into vmlinux and in whether modules found there are built?
What usage is incorrect (a directory entered in a way that does not suit what
its makefile lists), what does Kbuild print in each such case if anything, and
what that looks similar is correct? Start from `subdir-ym`, `need-builtin` and
`need-modorder`.

## build.link-order: Order of entries

- section: Saying what to build
- relevance: 3 - reordering a makefile can change behaviour at boot
- words: 50

Does the order of entries in `obj-y`, and of directories, matter, and for
what? What happens to a duplicate entry?

## build.flag-variables: Per-directory and per-file flags

- section: Flags
- relevance: 5 - the variables every driver makefile uses
- words: 120

Which variables let a kbuild makefile add or remove compiler, assembler,
preprocessor, linker and Rust flags for one directory, for a directory and
everything below it, and for one file? In what order are they combined with
the global flags, and which of them can put back a flag that another removed?
Start from `_c_flags` in `scripts/Makefile.lib`.

## build.include-paths: Source and object paths

- section: Flags
- relevance: 5 - a wrong path works in-tree and fails elsewhere
- words: 100

What do `$(src)`, `$(obj)`, `$(srctree)`, `$(objtree)` and `$(srcroot)` hold
when building in-tree, with a separate output directory, and for an external
module? How should a kbuild makefile write an include path to its own
directory or to another directory of the source tree, and which include paths
does Kbuild add by itself?

## build.instrumentation-opt-out: Instrumentation switches

- section: Flags
- relevance: 4 - low-level code that is instrumented crashes or fails to link
- words: 120

Which per-file and per-directory variables turn sanitizer, coverage,
profiling, objtool and other instrumentation on or off, and which objects are
instrumented by default when none of them is set? A table. Start from
`is-kernel-object` in `scripts/Makefile.lib`.

## build.module-vs-builtin-flags: Built-in and module flags

- section: Flags
- relevance: 3 - code tests these macros
- words: 60

Which flags and macro definitions differ between an object compiled for
vmlinux and one compiled for a module, and which macros name the module or
file an object belongs to? Start from `modkern_cflags` and `modname_flags`.

# Language and toolchain

## build.c-dialect: C dialect and global options

- section: Language and toolchain
- relevance: 5 - decides whether a construct is valid kernel C
- words: 100

Which C standard and language-extension options is kernel code compiled with,
and which options set for all kernel code change what C code means (signedness
of char, aliasing, integer overflow, null pointer checks, wchar_t, automatic
variable initialisation, flexible arrays)? Which of them depend on the
configuration or on a compiler probe, and where is each set? Give every option
and configuration symbol by its full name. Start from `KBUILD_CFLAGS` in the
top-level `Makefile`.

## build.separate-flag-sets: Code built with its own flags

- section: Language and toolchain
- relevance: 4 - the global options do not reach this code
- words: 100

Which parts of the tree are compiled without the global kernel flags and build
their own flag set instead (boot and decompressor code, firmware stubs, vDSOs,
purgatory, host and userspace programs)? Do they get the kernel's C dialect,
and through what? Is any source file compiled both there and with the global
flags, and what is easy to get wrong in such a file?

## build.tools-tree: The tools directory

- section: Language and toolchain
- relevance: 3 - kernel assumptions about the compiler do not hold there
- words: 70

How is code under `tools/` built: does it use Kbuild, which shared makefiles
does it use, which compiler options differ from the kernel's (aliasing,
dialect, signedness of char), and how does it get kernel headers? Start from
`tools/scripts/Makefile.include` and `tools/build/`.

## build.tool-versions: Minimal tool versions

- section: Language and toolchain
- relevance: 4 - decides which compiler features and workarounds are still needed
- words: 80

What are the minimal versions of GCC, Clang, binutils, GNU Make, Python, Rust,
bindgen, pahole, flex, bison and bash that this tree requires, where are they
written down, and which of them does the build enforce and how?

## build.script-languages: Interpreters for build scripts

- section: Language and toolchain
- relevance: 4 - a script that runs on the author's machine may not run elsewhere
- words: 70

Which interpreters may scripts that run during the build rely on (shell, Perl,
Python, awk), which versions of Python does the tree support, and how must a
makefile rule invoke such a script? What invocation is incorrect, and what
that looks similar is correct? Start from the script invocation section of
`Documentation/kbuild/makefiles.rst`.

## build.option-probing: Option probes in makefiles

- section: Probing the toolchain
- relevance: 5 - copied from old makefiles, several no longer exist
- words: 120

Give a table of the helpers a makefile can use to test for a compiler,
assembler, linker or Rust compiler option or version: what each runs, which
existing flags it includes in the test, and what it returns. Which helpers
that a reader may remember from other trees does this tree not define? Start
from `scripts/Makefile.compiler`.

## build.probing-usage: Using option probes

- section: Probing the toolchain
- relevance: 4 - a probe in the wrong place is slow or gives the wrong answer
- words: 100

What usage of an option probe in a makefile is incorrect or wasteful (when it
is evaluated, which flags are already set at that point, cross-compiling with
Clang, options that disable a warning), and what that looks similar is
correct? When should the test be a Kconfig symbol instead, and how do the
probes in `scripts/Kconfig.include` differ in the flags they pass?

## build.warning-levels: Warning levels

- section: Probing the toolchain
- relevance: 3 - where a new warning option belongs
- words: 90

Where are the default warning options and the extra levels selected on the
make command line defined, which values does that switch take, and which flag
sets does turning warnings into errors affect (kernel C, assembler, linker,
Rust, host and userspace programs)? Does any level change what modpost or the
kernel-doc check report?

# Rules

## build.if-changed: Command change detection

- section: Custom rules
- relevance: 5 - a rule written wrongly rebuilds every time or never
- words: 110

How does a custom rule get rerun when its command line changes: which macros
are there and how do they differ, what must be true of the prerequisites and
of `targets`, and where is the previous command kept and under which variable
name? What usage is incorrect, and what that looks similar is correct? Start
from `if_changed` in `scripts/Kbuild.include`.

## build.filechk: Files that rarely change

- section: Custom rules
- relevance: 3 - avoids rebuilding everything that includes a generated header
- words: 50

Which helper writes a generated file only when its content has changed, how is
it used, and when is it the right choice rather than `if_changed`? Start from
`filechk`.

## build.dependency-tracking: Header and configuration dependencies

- section: Custom rules
- relevance: 4 - what is rebuilt after a configuration change rests on this
- words: 100

How does Kbuild know which headers and which `CONFIG_` options an object
depends on: what does `scripts/basic/fixdep.c` do with the compiler's
dependency output, where do the per-option files live, and what can it not
know before the first compile? What must a makefile add when an object
includes a header that is generated in the same directory?

## build.clean: Cleaning

- section: Custom rules
- relevance: 3 - generated files left behind break the next build
- words: 70

What does `make clean` remove by itself, which variables add to that or
protect from it, how is a directory that is not reached through `obj-` or
`subdir-` variables made to be cleaned, and how do `clean`, `mrproper` and
`distclean` differ? Start from `scripts/Makefile.clean`.

## build.host-programs: Host programs

- section: Programs
- relevance: 4 - build-time tools are in many directories
- words: 100

How are programs that run on the build machine declared (one source file,
several objects, C++, Rust), which variables set their compile and link flags
globally, per directory and per file, and when are they actually built? Start
from `scripts/Makefile.host`.

## build.user-programs: Userspace programs

- section: Programs
- relevance: 3 - samples and tests built by Kbuild use this
- words: 70

How are programs for the target's userspace declared, which flags are they
compiled with, how do they follow the kernel's target architecture, and what
must guard them in Kconfig? Start from `scripts/Makefile.userprogs`.

# Modules

## build.module-stages: Module build stages

- section: Modules and modpost
- relevance: 4 - where a module build failure comes from
- words: 100

List the stages that turn a module's sources into a `.ko`, the intermediate
files each stage writes, and the makefile that runs it. What is linked into
every module besides its own objects? Start from `scripts/Makefile.modpost`
and `scripts/Makefile.modfinal`.

## build.modpost-checks: Modpost diagnostics

- section: Modules and modpost
- relevance: 5 - decides whether a missing macro breaks the build
- words: 120

Which problems does modpost report for a module or for vmlinux, and which are
errors that stop the build and which only warnings: a missing licence, a
missing description, undefined symbols, a GPL-only symbol used by a module
with another licence, a missing namespace import, exported static or init
symbols, section mismatches? Which options or variables, named in full, turn
errors into warnings? Start from `read_symbols()` and `check_exports()` in
`scripts/mod/modpost.c`.

## build.section-mismatch: Section mismatch analysis

- section: Modules and modpost
- relevance: 3 - a common build message
- words: 80

What does modpost's section mismatch check compare, on which object does it
run for built-in code, which annotations or name patterns exempt a reference,
and is a mismatch fatal by default? Start from `check_sec_ref()`.

## build.symbol-versions: Symbol versioning

- section: Modules and modpost
- relevance: 3 - exports in assembly and generated code need extra steps
- words: 90

How are symbol CRCs computed when module versioning is on: which generators
exist, when in the build do they run, where are the CRCs kept, what does an
exported symbol defined in assembly need, and what does each line of
`Module.symvers` contain?

## build.symbol-namespaces: Namespaces in makefiles and modpost

- section: Modules and modpost
- relevance: 4 - the quoting changed and old forms no longer compile
- words: 80

How does a makefile put all of a directory's exports into one symbol
namespace, and how must the value be quoted? What does modpost do when a module
uses a namespaced symbol without importing the namespace, which make target
writes the missing imports, and which namespaces can a module not import
explicitly?

## build.external-modules: External modules

- section: Modules and modpost
- relevance: 4 - shared makefiles must keep this working
- words: 100

How is an out-of-tree module built against a kernel tree: which command-line
variables name the module's source and a separate directory for its output,
what must already be built in the kernel tree, how are symbols from another
external module supplied, and what does Kbuild itself do differently for such
a build?

# Headers

## build.uapi-export: Exported header processing

- section: Headers
- relevance: 4 - a new UAPI header can fail the install step
- words: 100

Which directories' headers are exported to userspace, what does the install
step rewrite or strip in each header, and which conditions make it fail? How
is a header kept out of the export? Start from `scripts/Makefile.headersinst`
and `scripts/headers_install.sh`.

## build.uapi-header-test: Compile test of exported headers

- section: Headers
- relevance: 4 - limits the C a UAPI header may use
- words: 90

Does the build compile-test the headers it exports to userspace? If it does:
under which configuration option, with which language standards and flags
(give them in full), what besides a plain compile is checked, and how is a
header that cannot pass listed? Start from `usr/include/Makefile`.

## build.asm-generic-wrappers: Architecture header lists

- section: Headers
- relevance: 3 - every new asm-generic header touches these
- words: 80

Every architecture has a file like `arch/x86/include/asm/Kbuild` and a uapi
counterpart. What do `generic-y`, `generated-y` and `mandatory-y` mean in
them, which file lists the mandatory headers, what does Kbuild warn about, and
which shared makefile generates the wrappers?

# Changing the implementation

## build.lto-and-objtool: LTO and delayed objtool

- section: What a change must preserve
- relevance: 3 - the object files are not always machine code
- words: 80

With Clang LTO, or another option that postpones objtool, what do the
per-directory `.o` files contain, where do objtool and the conversion to
machine code then run for vmlinux and for modules, and does the tree have a
distributed ThinLTO mode and how does it work? Start from `delay-objtool` and
`cmd_ld_single` in `scripts/Makefile.lib`.

## build.kbuild-change-checklist: Changing Kbuild itself

- section: What a change must preserve
- relevance: 4 - the shared makefiles run in many more setups than a developer tests
- words: 110

What must a change to the shared makefiles under `scripts/` keep working:
which make versions and shells, in-tree and separate output directories,
external modules, read-only source trees, very long object lists, both
compilers, parallel builds, interruption, `make clean`? Name the places in the
shared makefiles that exist for each.

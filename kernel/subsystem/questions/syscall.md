# Questions: System Calls

- guide: syscall.md
- title: System Calls

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/syscall-measurement.md` is the
wider set the readers were measured on and `catalogue/syscall-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## syscall.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## syscall.core-files: Core files

- section: Finding your way
- relevance: 4 - wiring a call up touches files in five directories

A table and nothing else, job to file: the documentation on adding a system call; the definition
macros for native and compat entry points; the prototypes; the table shared by several
architectures; where the tables that belong to one architecture live; the scripts that turn a
table into headers; the stubs for calls that are configured out; the helpers for copying a
structure whose size userspace supplies. Start from `Documentation/process/adding-syscalls.rst`
and `include/linux/syscalls.h`.

# Defining an entry point

## syscall.define-expansion: Definition macro expansion

- section: Defining an entry point
- relevance: 4 - the function a debugger or a tracer sees is not the one written

On an architecture with no wrapper of its own, what does `SYSCALL_DEFINE3(name, ...)` emit
besides the function the author wrote, what is each piece for, and which of them holds the
author's body? Start from `__SYSCALL_DEFINEx` in `include/linux/syscalls.h`.

## syscall.arch-wrappers: Architecture wrappers

- section: Defining an entry point
- relevance: 4 - the entry symbol and its argument differ per architecture

Where an architecture selects `ARCH_HAS_SYSCALL_WRAPPER`, how is the entry symbol of a system call
named foo formed from the architecture's prefix, and which arguments does it take? Does a plain
symbol for sys_foo exist there? Start from `arch/x86/include/asm/syscall_wrapper.h`.

## syscall.arg-type-limits: Argument count and types

- section: Defining an entry point
- relevance: 4 - a wrong argument type compiles on 64-bit and breaks elsewhere

How many arguments may a system call take, and what does the definition macro do to an argument
narrower than a register? Which argument types does `__SC_TEST` refuse at build time? Start from
`__SC_LONG` and `__SC_TEST` in `include/linux/syscalls.h`.

## syscall.in-kernel-calls: Calls from kernel code

- section: Defining an entry point
- relevance: 4 - a direct call builds on some architectures and not on others

What are the requirements for calling a function defined with `SYSCALL_DEFINEx` or
`COMPAT_SYSCALL_DEFINEx` from other kernel code in order to assure safe usage, and where does the
tree state them? What does the tree provide for kernel code that needs the work a system call
does? Start from `include/linux/syscalls.h` and `Documentation/process/adding-syscalls.rst`.

# Numbers and tables

## syscall.table-lines: Shared table and ABI tags

- section: Numbers and tables
- relevance: 5 - one line reaches every architecture that shares the table, and a missing one drops the call there

What do the values of the ABI column of `scripts/syscall.tbl` select, and where does an
architecture that builds from it say which of them it wants? Which directories hold the tables of
the architectures that do not build from it? Start from `scripts/Makefile.asm-headers`.

## syscall.number-allocation: Number allocation

- section: Numbers and tables
- relevance: 4 - a number chosen wrongly collides or wastes a slot

Does a new system call get the same number on every architecture, and what decides the next free
number? How does the number in each of the four tables named here relate to the number userspace
passes? Compare the last entries of `scripts/syscall.tbl`,
`arch/alpha/kernel/syscalls/syscall.tbl`, `arch/mips/kernel/syscalls/syscall_n64.tbl` and
`arch/x86/entry/syscalls/syscall_64.tbl`.

## syscall.closed-number-ranges: Closed number ranges

- section: Numbers and tables
- relevance: 4 - a number taken from a closed range collides with another ABI

Which ranges of numbers do the comments in `scripts/syscall.tbl` and in
`arch/x86/entry/syscalls/syscall_64.tbl` close to new system calls, and what reason does each
comment give?

## syscall.uapi-unistd: asm-generic unistd header

- section: Numbers and tables
- relevance: 4 - authors still ask whether this file needs a line

Is `include/uapi/asm-generic/unistd.h` still kept up to date in this tree, and does any
architecture's kernel build take its numbers or its table from it? What does the tree say about
who updates the copies of the tables and of this header under `tools/`?

## syscall.nr-syscalls: Count of system calls

- section: Numbers and tables
- relevance: 4 - a table sized by a stale count leaves the new call out

Where does the value of `__NR_syscalls` that an architecture's kernel builds with come from, and
does a patch that adds a system call have to change it by hand? Start from `scripts/syscallhdr.sh`
and `include/uapi/asm-generic/unistd.h`.

## syscall.ni-stubs: Stubs for absent calls

- section: Numbers and tables
- relevance: 5 - leaving the stub out breaks the build only with the option off

When does a system call need a `COND_SYSCALL()` or `COND_SYSCALL_COMPAT()` line in
`kernel/sys_ni.c`, what happens at build time and at run time without it, and what does the
line have to provide on an architecture with a wrapper of its own that it does not on the
others?

## syscall.doc-accuracy: The adding-syscalls document

- section: Numbers and tables
- relevance: 3 - the document is the first thing an author copies from

Does what `Documentation/process/adding-syscalls.rst` says about x86 table entries, about x32 and
about system calls that return elsewhere agree with `arch/x86/entry/syscalls/` and
`arch/x86/entry/`? Where they disagree, say what the tree has. Refer to a part of the document by
its subject, not by a kernel version.

## syscall.new-call-checklist: Adding a call

- section: Numbers and tables
- relevance: 5 - the list has changed and the document gives two versions of it

In this tree, what does a patch series that adds a system call have to contain, does it wire
the call into every table at once or into one architecture first, and when does it also need a
configuration option and a stub for when the call is configured out? Go by what the most
recently added calls did, not only by the document, and give macro and option names in full.

# Arguments and structures

## syscall.flags-validation: Unknown flag bits

- section: Arguments and structures
- relevance: 5 - a call that ignores unknown bits can never give them a meaning

What must a system call do with flag bits it does not know, and with a flags argument that has no
bits defined yet? Which error does `Documentation/process/adding-syscalls.rst` ask for? Name a
recently added call that shows it.

## syscall.extensible-struct: Extensible structure arguments

- section: Arguments and structures
- relevance: 5 - the size checks are split between the helper and its caller

How does `copy_struct_from_user()` treat a structure from userspace that is smaller than, equal to
and larger than the kernel's, and which errors does it return? Which size checks does it require
its caller to make? Start from `include/linux/uaccess.h` and the callers in `kernel/fork.c` and
`fs/open.c`.

## syscall.struct-layout: Structure layout rules

- section: Arguments and structures
- relevance: 4 - the right layout removes the need for a compat entry point

What are the requirements for the layout of a structure passed to a new system call so that one
entry point serves 32-bit and 64-bit callers? Start from `struct clone_args`, `struct open_how`,
`CLONE_ARGS_SIZE_VER0` and `OPEN_HOW_SIZE_VER0`.

## syscall.adding-arguments: Adding an argument

- section: Arguments and structures
- relevance: 5 - safe only under a precondition that is easy to leave out

Can an existing system call be given another argument without breaking programs built against
the old one? What has to be true of the old interface for that to be safe, and what must the
kernel do before it reads the new argument? Name a call in this tree that gained an argument
this way; start from `kernel/sched/membarrier.c`.

## syscall.flag-gated-args: Flag-gated arguments

- section: Arguments and structures
- relevance: 5 - a check moved out of the flag test reads a register userspace never set

When an argument of a system call only has a meaning if a flag or command selects it, what can the
kernel assume about the value of that argument when the flag is clear? What are the requirements
for reading such an argument in order to assure safe usage? Name the in-tree helpers that express
the gate; start from `vrm_implies_new_addr()` in `mm/mremap.c` and `futex_cmd_has_timeout()` in
`kernel/futex/syscalls.c`.

## syscall.user-memory-fetch: Reading arguments from user memory

- section: Arguments and structures
- relevance: 4 - validation of data userspace can still change is no validation

When a system call takes its arguments from a structure in user memory, what are the requirements
for reading that memory and for validating what was read in order to assure safe usage? Name an
in-tree call that shows it.

# Compat and 64-bit arguments

## syscall.compat-when: Arguments needing a compat entry

- section: Compat and 64-bit arguments
- relevance: 5 - the commonest question about a new call on a 64-bit kernel

What kinds of argument make a separate compat entry point necessary when a 32-bit program
calls a 64-bit kernel, and which that look similar do not? What becomes of a pointer argument,
and of a 64-bit value passed by value, when there is no compat entry point?

## syscall.compat-define: Compat definitions

- section: Compat and 64-bit arguments
- relevance: 4 - the compat macro treats arguments differently from the native one

How does `COMPAT_SYSCALL_DEFINEx` treat each argument compared with the native macro, what
that the native macro emits does it leave out, and how does shared code find out that it was
entered from a compat call, by default and where an architecture overrides the test? Start
from `__SC_DELOUSE`, `compat_ptr()` and `in_compat_syscall()`.

## syscall.compat-table-wiring: Compat entries in the tables

- section: Compat and 64-bit arguments
- relevance: 4 - the column is spelled differently from the symbol that is called

How is a compat entry point named in `scripts/syscall.tbl`, in
`arch/x86/entry/syscalls/syscall_32.tbl` and in `arch/arm64/tools/syscall_32.tbl`, and what turns
that name into the symbol that is called on x86? What does the tree say a new call should do about
the x32 entries of `arch/x86/entry/syscalls/syscall_64.tbl`?

## syscall.arg64-native: 64-bit arguments on 32-bit kernels

- section: Compat and 64-bit arguments
- relevance: 4 - argument position decides whether a register is wasted

How does a 64-bit argument such as `loff_t` reach a system call on a 32-bit architecture, and what
does an ABI that wants it in an aligned register pair require of the argument's position? What do
`SC_ARG64` and `SC_VAL64`, and `compat_arg_u64_dual()` and `compat_arg_u64_glue()` on the compat
side, require of the code that uses them? Start from `SC_ARG64`.

# Model gaps

## syscall.model-gaps: Other mistakes models make

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

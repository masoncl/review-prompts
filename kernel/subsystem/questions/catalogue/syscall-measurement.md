# Questions: System Calls (measurement set)

- guide: syscall.md
- title: System Calls

A wide set of questions about adding and changing system calls: the definition
macros, the tables that wire an entry point to a number, the stubs for calls
that are configured out, the conventions for flags and extensible structures,
64-bit arguments and the compat layer. It is used to measure what a model
already knows before deciding what the built guide should spend its words on.
The hand-written guide it will replace is 146 words and covers only two
points, added arguments and arguments that a flag gives meaning to. Format:
`../../../docs/subsystem-questions.md`.

# Where things are

## syscall.core-files: Core files

- section: Finding your way
- relevance: 4 - wiring a call up touches files in five directories
- words: 110

Which files hold the documentation on adding a system call, the definition
macros for native and compat entry points, the prototypes, the table shared by
several architectures and the tables that belong to one architecture, the
scripts that turn a table into headers, the stubs for calls that are
configured out, and the helpers for copying a structure whose size userspace
supplies? A table. Start from `Documentation/process/adding-syscalls.rst` and
`include/linux/syscalls.h`.

## syscall.doc-accuracy: Documentation against the code

- section: Finding your way
- relevance: 3 - the document is the first thing an author copies from
- words: 90

Where does `Documentation/process/adding-syscalls.rst` describe something the
code in this tree does differently or no longer has? Compare what it says
about x86 table entries, about system calls that return elsewhere, and about
the generic number header with `arch/x86/entry/syscalls/`, `arch/x86/entry/`
and `scripts/Makefile.asm-headers`. Refer to a part of the document by its
subject, not by a kernel version.

# Definitions

## syscall.define-expansion: Definition macro expansion

- section: Defining an entry point
- relevance: 4 - the function a debugger or a tracer sees is not the one written
- words: 90

On an architecture with no wrapper of its own, which functions does
`SYSCALL_DEFINE3(name, ...)` emit, what is each one for, and which of them
holds the body the author wrote? Start from `__SYSCALL_DEFINEx` in
`include/linux/syscalls.h`.

## syscall.arch-wrappers: Architecture wrappers

- section: Defining an entry point
- relevance: 4 - the entry symbol and its argument differ per architecture
- words: 100

Which architectures select `ARCH_HAS_SYSCALL_WRAPPER`, what does each of them
call the entry symbol of a system call named foo, and what single argument
does that symbol take? What does the wrapper buy over the generic definition?
Start from `arch/x86/include/asm/syscall_wrapper.h`.

## syscall.arg-type-limits: Argument count and types

- section: Defining an entry point
- relevance: 4 - a wrong argument type compiles on 64-bit and breaks elsewhere
- words: 80

How many arguments may a system call take, what does the definition macro do
to an argument narrower than a register, and which argument types does it
refuse at build time? Start from `__SC_LONG` and `__SC_TEST` in
`include/linux/syscalls.h`.

## syscall.metadata: Metadata and error injection

- section: Defining an entry point
- relevance: 2 - explains why open-coding an entry point loses features
- words: 60

Besides the entry point, what does the definition macro emit for tracing and
for error injection, under which configuration options, and which code
consumes it? Start from `SYSCALL_METADATA`.

## syscall.in-kernel-calls: Calls from kernel code

- section: Defining an entry point
- relevance: 4 - a direct call builds on some architectures and not on others
- words: 80

What usage of a `sys_` or `compat_sys_` function from other kernel code is
unsafe or does not build, and what that looks similar is correct? Say why,
name the helpers the tree provides instead, and say where the exception for
architecture code is written down.

# Tables

## syscall.generic-table: Shared table format

- section: Wiring a number
- relevance: 5 - one line here reaches every architecture that shares the table
- words: 110

What are the columns of `scripts/syscall.tbl`, which values of the ABI column
does the file use and what does each select, which architectures build their
tables from this file, and where does each say which ABIs it wants? Start from
`scripts/Makefile.asm-headers`.

## syscall.arch-tables: Per-architecture tables

- section: Wiring a number
- relevance: 5 - a call missing from one table is missing from that architecture
- words: 100

Which architectures keep a table of their own, in which file, and which keep
more than one? Does a patch that adds a system call in this tree add it to
every table at once or to one architecture first? Look at how the most recently
added calls appear across the tables.

## syscall.number-allocation: Number allocation

- section: Wiring a number
- relevance: 4 - a number chosen wrongly collides or wastes a slot
- words: 90

Does a new system call get the same number on every architecture? Name the
architectures or ABIs whose numbers are offset or in a separate range, and say
what decides the next free number. Compare the last entries of
`scripts/syscall.tbl`, `arch/alpha/kernel/syscalls/syscall.tbl`,
`arch/mips/kernel/syscalls/syscall_n64.tbl` and
`arch/x86/entry/syscalls/syscall_64.tbl`.

## syscall.uapi-unistd: Generic number header

- section: Wiring a number
- relevance: 4 - authors still ask whether this file needs a line
- words: 80

Is `include/uapi/asm-generic/unistd.h` still kept up to date in this tree,
does any architecture's kernel build take its numbers or its table from it,
and what is `__NR_syscalls` there for? Which copies of the tables and of this
header live under `tools/`, and who is expected to update them?

## syscall.table-generation: Table generation

- section: Wiring a number
- relevance: 3 - explains the build errors a bad table line produces
- words: 90

Which script writes the number header and which the table header, what does
the table script emit for a number that has no line, what ordering does it
insist on, and what may the columns after the native entry point contain?
Start from `scripts/syscalltbl.sh` and `scripts/syscallhdr.sh`.

## syscall.dispatch: Dispatch on x86

- section: Wiring a number
- relevance: 3 - code that patches or reads the pointer table may find it unused
- words: 70

How does the x86-64 entry code get from a system call number to the entry
function in this tree, what is `sys_call_table[]` used for, and how are
out-of-range numbers and speculation handled? Start from
`arch/x86/entry/syscall_64.c`.

## syscall.ni-stubs: Stubs for absent calls

- section: Wiring a number
- relevance: 5 - leaving the stub out breaks the build only with the option off
- words: 90

What do `COND_SYSCALL()` and `COND_SYSCALL_COMPAT()` in `kernel/sys_ni.c`
expand to on an architecture without its own wrapper, when does a system call
need a line there, and what happens at build time and at run time without it?
How does an architecture with a wrapper change the expansion?

## syscall.missing-check: Missing call warning

- section: Wiring a number
- relevance: 2 - a build warning people ask about
- words: 60

What does `scripts/checksyscalls.sh` compare, when is it run, and how does an
architecture say that it leaves a call out on purpose?

# Interface conventions

## syscall.flags-validation: Unknown flag bits

- section: Designing the interface
- relevance: 5 - a call that ignores unknown bits can never give them a meaning
- words: 80

What must a system call do with flag bits it does not know, and with a flags
argument that has no bits defined yet? Which error does the documentation ask
for? What usage is unsafe, and what that looks similar is correct? Name a
recently added call that shows the correct form.

## syscall.extensible-struct: Extensible structure arguments

- section: Designing the interface
- relevance: 5 - the size checks are split between the helper and its caller
- words: 110

How does `copy_struct_from_user()` treat a structure from userspace that is
smaller than, equal to and larger than the kernel's, and which errors does it
return? Which size checks does it leave to the caller, and what do in-tree
callers return for them? Start from `include/linux/uaccess.h` and the callers
in `kernel/fork.c` and `fs/open.c`.

## syscall.struct-to-user: Returning an extensible structure

- section: Designing the interface
- relevance: 3 - the helper for the outward direction is newer and less known
- words: 80

Does this tree have a helper for copying a structure out to a buffer whose size
userspace supplied? If so, what does it do when the buffer is smaller and when
it is larger than the kernel's structure, and what is its last argument for?
Name a system call that uses it.

## syscall.struct-layout: Structure layout rules

- section: Designing the interface
- relevance: 4 - the right layout removes the need for a compat entry point
- words: 90

How must a structure passed to a new system call be laid out so that one entry
point serves 32-bit and 64-bit callers: pointers, 64-bit fields, padding, the
first published size? Start from `struct clone_args`, `struct open_how` and
the `_SIZE_VER0` constants under `include/uapi/linux/`.

## syscall.flag-gated-args: Arguments a flag gives meaning to

- section: Designing the interface
- relevance: 5 - a check moved out of the flag test reads a register userspace never set
- words: 110

When an argument only means something if a flag or command selects it, what
may the register hold when that flag is clear, and does copying the arguments
into a kernel structure change that? What usage of such an argument is unsafe,
and what that looks similar is correct? Name the in-tree helpers that express
the gate; start from `vrm_implies_new_addr()` in `mm/mremap.c` and
`futex_cmd_has_timeout()` in `kernel/futex/syscalls.c`.

## syscall.adding-arguments: Adding an argument

- section: Designing the interface
- relevance: 5 - safe only under a precondition that is easy to leave out
- words: 90

Can an existing system call be given another argument without breaking
programs built against the old one? What has to be true of the old interface
for that to be safe, and what must the kernel do before it reads the new
argument? Name a call in this tree that gained an argument this way; start
from `kernel/sched/membarrier.c`.

## syscall.fd-and-path-conventions: Descriptor and path conventions

- section: Designing the interface
- relevance: 2 - design advice that rarely decides a review
- words: 70

What does the documentation ask of a new call that returns a file descriptor,
of one that takes a path name, and of one that takes a file offset? Which flag
value is an author told not to reuse, and why?

# 64-bit arguments and compat

## syscall.arg64-native: 64-bit arguments on 32-bit kernels

- section: Word size
- relevance: 4 - argument position decides whether a register is wasted
- words: 100

How does a 64-bit argument such as `loff_t` reach a system call on a 32-bit
architecture, and which architectures need it in an aligned register pair?
Does this tree have macros that declare the two halves and put them back
together in the right byte order, and if so which calls use them? Start from
`SC_ARG64`.

## syscall.compat-when: Need for a compat entry point

- section: Word size
- relevance: 5 - the commonest question about a new call on a 64-bit kernel
- words: 90

Which argument types make a separate compat entry point necessary when a
32-bit program calls a 64-bit kernel, and which that look similar do not? What
becomes of a pointer argument, and of a 64-bit value passed by value, when
there is no compat entry point?

## syscall.compat-define: Compat definitions

- section: Word size
- relevance: 4 - the compat macro treats arguments differently from the native one
- words: 100

What does `COMPAT_SYSCALL_DEFINEn` emit, how does it treat each argument
compared with the native macro, where do the prototype and any 32-bit mirror
structure go, and how does shared code find out that it was entered from a
compat call? Start from `__SC_DELOUSE`, `compat_ptr()` and
`in_compat_syscall()`.

## syscall.compat-arg64: 64-bit arguments in compat calls

- section: Word size
- relevance: 3 - each architecture opts in to the generic compat versions
- words: 90

How do the generic compat entry points for calls such as `pread64`,
`fallocate` and `sync_file_range` receive their 64-bit arguments, which macros
describe the halves, and how does an architecture say that it wants them?
Start from `include/asm-generic/compat.h` and the `__ARCH_WANT_COMPAT_`
symbols.

## syscall.compat-table-wiring: Compat entries in the tables

- section: Word size
- relevance: 4 - the column is spelled differently from the symbol that is called
- words: 100

How is a compat entry point named in `scripts/syscall.tbl`, in
`arch/x86/entry/syscalls/syscall_32.tbl` and in
`arch/arm64/tools/syscall_32.tbl`, and what turns that name into the symbol
that is actually called on x86? How are the x32 entries of
`arch/x86/entry/syscalls/syscall_64.tbl` arranged, and what is a new call
expected to do about x32?

## syscall.time-types: Time arguments

- section: Word size
- relevance: 3 - a new call with the wrong time type needs a second entry point
- words: 70

Which type does a new system call use for a time value passed by pointer, what
do the `_time32` entry points and the `time32` ABI keyword exist for, and which
configuration option builds them? Start from `struct __kernel_timespec` and
`struct old_timespec32`.

# Changing things

## syscall.new-call-checklist: Adding a call

- section: What a change must preserve
- relevance: 5 - the list has changed and the document gives two versions of it
- words: 110

In this tree, what does a patch series that adds a system call have to
contain: the definition, the prototype, the table lines, the test, the manual
page, the mailing lists to copy? When does it also need a configuration option
and a stub for when the call is configured out? Go by what the most recently
added calls did, not only by the document, and give macro and option names in
full.

## syscall.other-consumers: Other tables of system calls

- section: What a change must preserve
- relevance: 3 - a call like open or execve has to be classified in more places
- words: 80

Besides the tables, which kernel code keeps its own lists or classes of system
calls that a new call may have to join: audit, seccomp, tracing, the argument
accessors? Start from `audit_classify_syscall()`, `lib/audit.c` and
`syscall_get_arguments()`.

## syscall.return-values: Return values

- section: What a change must preserve
- relevance: 3 - a large valid result can look like an error
- words: 70

What is the return type of every entry point, which range of values does
userspace take for an error, and what does a call that can validly return a
value in that range do about it? Start from
`force_successful_syscall_return()`.

## syscall.user-memory-fetch: Reading arguments from user memory

- section: What a change must preserve
- relevance: 4 - validation of data userspace can still change is no validation
- words: 80

When a system call takes its arguments from a structure in user memory, what
usage of that memory is unsafe once a field has been checked, and what that
looks similar is correct? Name an in-tree call that copies first and then
validates the kernel copy.

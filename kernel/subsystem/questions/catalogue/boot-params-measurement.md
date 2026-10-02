# Questions: Boot parameters (measurement set)

- guide: boot-params.md
- title: Boot Parameters

A wide set of questions about kernel command-line parameters: the macros that
define one (`__setup()`, `early_param()`, `core_param()`, `module_param()` and
their relatives), the order in which the boot code runs their handlers, what a
handler is given and what it must return, how a name is matched, what happens
to a word nobody claims, how long the value string lives, the sysfs side, the
value-parsing helpers, bootconfig and sysctl settings on the command line, and
the documentation in `Documentation/admin-guide/kernel-parameters.txt` with the
rule about adding to it. It is used to measure what a model already knows
before deciding what the built guide should spend its words on. The
hand-written guide it will replace is 231 words, so most of what is asked here
cannot be in the built guide; the point is to find which few things must be.
The x86 `struct boot_params` (the zero page) is a different subject and is not
covered. The trimmed set a guide is built from is `../boot-params.md`. Format:
`../../../docs/subsystem-questions.md`.

# Where to look

## bootparams.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 90

Which files hold the macros that define a command-line parameter, the boot
code that walks the command line and calls the handlers, the generic parameter
parser with its sysfs side, the helpers that parse values, the in-kernel tests
for those helpers, and the list of parameters kept for administrators? A
table. Start from `include/linux/init.h` and `kernel/params.c`.

## bootparams.defining-macros: Defining macros

- section: Finding your way
- relevance: 4 - a patch picks one of these and each behaves differently
- words: 110

Give a table of the macros a built-in file can use to define a command-line
parameter. For each: does the name get a prefix, is it usable in code that may
be built as a module, is there a sysfs file, and does the author write a
handler or name a type? Start from `include/linux/init.h` and
`include/linux/moduleparam.h`.

# How the command line is parsed

## bootparams.parse-order: Order of parsing

- section: Parsing at boot
- relevance: 5 - which handler has run by a given point decides whether a parameter works
- words: 100

In what order during boot are the different kinds of parameter handler run,
and which function runs each kind? Give the sequence from architecture setup
to the last initcall level. Start from `start_kernel()` and
`do_initcall_level()`.

## bootparams.early-environment: Environment of early handlers

- section: Parsing at boot
- relevance: 4 - an early handler that allocates or flips a static key may run too soon
- words: 80

Who decides when the handlers registered with `early_param()` run, and which
kernel services (memory allocators, static keys, interrupts) can such a
handler rely on and which can it not? Start from `parse_early_param()` and its
callers under `arch/`.

## bootparams.handler-arguments: Handler arguments

- section: Parsing at boot
- relevance: 5 - handlers that test the wrong string are a recurring bug
- words: 80

What string does each kind of handler receive: the whole word, the text after
the registered string, or only the value? What does each receive when the word
was given with no `=value`? Start from `do_early_param()`,
`obsolete_checksetup()` and `parse_one()`.

## bootparams.return-values: Handler return values

- section: Parsing at boot
- relevance: 5 - the conventions differ between the macros and the wrong one is silent
- words: 100

What must a handler registered with each macro return on success and on a bad
value, and what does the boot code do with each possible return: log, pass the
word on to init, stop? Start from the comments in `include/linux/init.h`,
`obsolete_checksetup()` and `parse_args()`.

## bootparams.name-matching: Name matching

- section: Parsing at boot
- relevance: 4 - one parameter can swallow another
- words: 90

How is a word on the command line compared with the string given to
`__setup()`, with the string given to `early_param()`, and with the name of a
`module_param()`? What follows when one registered string is the beginning of
another, and are `-` and `_` told apart? Start from `parameq()` and
`parameqn()`.

## bootparams.duplicate-names: Repeated and shared names

- section: Parsing at boot
- relevance: 3 - decides whether a handler runs once, twice or never
- words: 70

If the same name is registered with more than one macro, or a parameter
appears more than once on the command line, which handlers run and how many
times? Does a match stop the search? Start from `do_early_param()`,
`obsolete_checksetup()` and `parse_one()`.

## bootparams.unknown-words: Unclaimed words

- section: Parsing at boot
- relevance: 4 - explains where a mistyped or unhandled parameter ends up
- words: 90

What happens to a word on the command line that no handler claims: when does
it become an argument to init, when an environment variable, when is it
dropped without a message, and what is logged? Start from
`unknown_bootoption()` and `print_unknown_bootoptions()`.

## bootparams.string-lifetime: Lifetime of the value string

- section: Parsing at boot
- relevance: 5 - a saved pointer into freed init memory shows in no diff
- words: 100

Which buffer does the string handed to each kind of handler point into, and is
that buffer still there after boot? What usage that keeps the pointer is
unsafe, and what that looks similar is correct? Start from
`parse_early_param()`, `setup_command_line()`, `do_initcalls()` and
`param_set_charp()`.

## bootparams.levelled-params: Parameters tied to initcall levels

- section: Parsing at boot
- relevance: 3 - few users, but the timing surprises people
- words: 70

What does the `level` field of `struct kernel_param` control, which macros set
it to something other than the default, and when are such parameters applied
relative to the initcalls? Start from `__level_param_cb()` and
`do_initcall_level()`.

## bootparams.sections-and-modules: Sections and modular builds

- section: Parsing at boot
- relevance: 3 - the compiler or the linker catches some of this, not all
- words: 80

In which sections do the records made by `__setup()`, `early_param()` and
`module_param()` live, what does that require of the handler function and its
data, and what does each macro turn into when the file is built as a module?
Start from `__setup_param()` and `__module_param_call()`.

# Module parameters on the command line

## bootparams.builtin-module-params: Module parameters at boot

- section: Module parameters
- relevance: 4 - the command-line name is not in the source
- words: 90

What name does a `module_param()` take on the kernel command line when the
code is built in, where does the prefix come from and how do files override
it? When the same code is a loadable module, how does a value on the kernel
command line reach it? Start from `MODULE_PARAM_PREFIX`.

## bootparams.sysfs-side: Sysfs exposure

- section: Module parameters
- relevance: 3 - a writable parameter races with its readers
- words: 90

Where does a built-in parameter appear under `/sys/module`, what does a
permission of 0 do, which permission values does the build reject, and what
serialises a write through sysfs against code that reads the variable? Start
from `param_sysfs_builtin()`, `VERIFY_OCTAL_PERMISSIONS()` and
`kernel_param_lock()`.

## bootparams.unsafe-and-hw: Unsafe and hardware parameters

- section: Module parameters
- relevance: 2 - narrow, but changes what setting a parameter does
- words: 60

Which flags can a `struct kernel_param` carry, what does setting a parameter
that has each of them do, and which macros set them? Start from
`param_check_unsafe()`.

## bootparams.module-unknown: Unknown parameters to a module

- section: Module parameters
- relevance: 2 - differs from what the boot parser does
- words: 60

When a module is loaded with a parameter it does not define, what happens, and
which names are handled specially for every module? Start from
`unknown_module_param_cb()`.

# Values

## bootparams.value-helpers: Value parsing helpers

- section: Parsing values
- relevance: 3 - each helper reports errors differently
- words: 100

Which helpers does a handler use to parse an integer, a size with a suffix, a
boolean, a comma-separated list of integers and a list of CPUs, and how does
each report a malformed value? Start from `lib/cmdline.c`, `kstrtobool()` and
the `param_set_` functions in `kernel/params.c`.

## bootparams.quoting: Quoting and separators

- section: Parsing values
- relevance: 2 - rarely matters, surprising when it does
- words: 60

How does the parser split the command line into words and into name and value:
what do double quotes do, can a quote be escaped, and what ends parsing? Start
from `next_arg()` and `parse_args()`.

# Other sources of parameters

## bootparams.bootconfig: Bootconfig and the command line

- section: Other sources
- relevance: 3 - decides which handlers can see a bootconfig key
- words: 100

How do keys from a bootconfig file reach parameter handlers, where are they
placed relative to what the boot loader passed, and which handlers cannot see
them? Does this tree have a way to make an embedded bootconfig visible
earlier, and on which architectures? Start from `setup_boot_config()` and
`Documentation/admin-guide/bootconfig.rst`.

## bootparams.sysctl-on-cmdline: Sysctl settings at boot

- section: Other sources
- relevance: 2 - an alternative to adding a parameter at all
- words: 70

How can a sysctl be set from the kernel command line, when during boot is it
applied, and what is the table of aliases for and what does its comment say
about adding to it? Start from `do_sysctl_args()` and `sysctl_is_alias()`.

## bootparams.builtin-cmdline: Built-in command line and its size

- section: Other sources
- relevance: 2 - per-architecture, but it is where parameters silently vanish
- words: 70

Where is the limit on the length of the command line defined and what range
does it cover across architectures? Which code combines a command line built
into the kernel with the one from the boot loader, and is that generic or
per-architecture? Start from `COMMAND_LINE_SIZE`.

## bootparams.before-early: Options read before early parsing

- section: Other sources
- relevance: 2 - such options never reach a handler
- words: 60

Which code reads options from the command line before `parse_early_param()`
has run, such as a decompressor or very early architecture setup, and what
does it use to find them? Start from `arch/x86/lib/cmdline.c`.

# Documentation

## bootparams.doc-file: The parameter list

- section: Documenting a parameter
- relevance: 5 - the file every new parameter is checked against
- words: 90

Which file lists the kernel's command-line parameters for administrators, how
is it ordered, where are the bracketed restriction tags defined, and how do
the `.rst` and `.txt` files of that name relate? Start from
`Documentation/admin-guide/kernel-parameters.rst`.

## bootparams.doc-entry: Entry format

- section: Documenting a parameter
- relevance: 4 - what a reviewer compares a new entry with
- words: 90

What does an entry in the parameter list look like: how the name is written
with and without a value, what goes in the square brackets, how the accepted
values and the default are given, and how a parameter of a built-in module is
named? What does the tag for early parameters promise? Take two or three
existing entries as the model.

## bootparams.doc-rule: Documentation rule

- section: Documenting a parameter
- relevance: 5 - the one thing the guide exists to enforce
- words: 110

What do the process documents and `scripts/checkpatch.pl` ask of a patch that
adds a boot parameter, and what do they ask for a module parameter? Which
macros does the checkpatch test look at and at what severity? By in-tree
practice, which additions come with an entry in the parameter list and which
that look similar do not? Start from
`Documentation/process/submit-checklist.rst`.

# Changing the implementation

## bootparams.parser-users: Other users of the parser

- section: What a change must preserve
- relevance: 3 - the parser is shared by more than boot
- words: 80

Besides the boot code, which callers hand a string to `parse_args()`, and what
does each rely on: the unknown-parameter callback, the level range, stopping
at `--`, the returned pointer? Which tests cover the parser and the value
helpers?

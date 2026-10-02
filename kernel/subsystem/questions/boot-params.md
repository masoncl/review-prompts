# Questions: Boot Parameters

- guide: boot-params.md
- title: Boot Parameters

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/boot-params-measurement.md` is
the wider set the readers were measured on and `catalogue/boot-params-measurement-results.md` says
what they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## bootparams.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Defining a parameter

## bootparams.defining-macros: Defining macros

- section: Defining a parameter
- relevance: 4 - a patch picks one of these and each behaves differently

One table of the macros a patch chooses among, `__setup()`, `early_param()`, `core_param()`
and `module_param()`, one row each and nothing else: whether the name on the command line gets
a prefix, where the parameter appears in sysfs if at all, and what happens when the file is
built as a module. Start from `include/linux/init.h` and `include/linux/moduleparam.h`.

## bootparams.builtin-module-params: Module parameters at boot

- section: Defining a parameter
- relevance: 4 - the command-line name is not in the source

What name does a `module_param()` take on the kernel command line when the code is built in, and
what sets the prefix? When the same code is a loadable module, what does the kernel do with a
value for it that was given on the kernel command line? Start from `MODULE_PARAM_PREFIX`.

# Parsing at boot

## bootparams.parse-order: Order of parsing

- section: Parsing at boot
- relevance: 5 - which handler has run by a given point decides whether a parameter works

In what order during boot are the different kinds of parameter handler run, and which function
runs each kind? Give the sequence from architecture setup to the last initcall level. Start
from `start_kernel()` and `do_initcall_level()`.

## bootparams.matching-and-arguments: Matching and handler arguments

- section: Parsing at boot
- relevance: 5 - handlers that test the wrong string, and one parameter swallowing another, are recurring bugs

How does the boot code match a word on the command line against a string registered with
`__setup()`, against one registered with `early_param()` and against the name of a
`module_param()`? What string does each kind of handler receive, when the word has a value and
when it has none? Start from `do_early_param()`, `obsolete_checksetup()`, `parse_one()` and
`parameqn()`.

## bootparams.several-matches: Words matching several registrations

- section: Parsing at boot
- relevance: 5 - a new parameter can take words meant for an existing one, or lose its words to it

Which handlers run for a word on the command line that matches more than one string registered
with `__setup()` or `early_param()`, and in what order? Start from `obsolete_checksetup()` and
`do_early_param()`.

## bootparams.return-values: Handler return values

- section: Parsing at boot
- relevance: 5 - the conventions differ between the macros and the wrong one is silent

What must a handler registered with `__setup()` and one registered with `early_param()` return on
success and on a bad value, and what must the set function of a `struct kernel_param_ops` return?
What does the boot code do with each return value? Start from the comments in
`include/linux/init.h`, `obsolete_checksetup()` and `parse_args()`.

## bootparams.init-args-after-error: Init arguments after an error

- section: Parsing at boot
- relevance: 5 - a handler that reports an error at boot changes what init receives

What does `start_kernel()` do with the words that follow `--` on the command line after
`parse_args()` has reported an error for an earlier word? Start from `parse_args()`.

## bootparams.unknown-words: Unclaimed words

- section: Parsing at boot
- relevance: 4 - explains where a mistyped or unhandled parameter ends up

What does the boot code do with a word on the command line that no handler claims, and what does
it log about that word? Start from `unknown_bootoption()` and `print_unknown_bootoptions()`.

## bootparams.value-helpers: Value parsing helpers

- section: Parsing at boot
- relevance: 3 - each helper reports errors differently

What do the parsing helpers in `lib/cmdline.c` return for a malformed value, and how does a caller
of each tell a malformed value from a valid one? What do `kstrtobool()`, `cpulist_parse()` and the
`param_set_` functions in `kernel/params.c` return for a malformed value? Start from
`lib/cmdline.c`, `kstrtobool()` and the `param_set_` functions in `kernel/params.c`.

## bootparams.accepted-input: Input the helpers accept

- section: Parsing at boot
- relevance: 3 - a handler that relies on a helper to refuse a value may accept that value

Which strings does `kstrtobool()` accept as true and as false, and what does `memparse()` do with
the text that follows the number? Start from `kstrtobool()` and `lib/cmdline.c`.

## bootparams.early-environment: Environment of early handlers

- section: Parsing at boot
- relevance: 4 - an early handler that allocates or flips a static key may run too soon

Which code decides when the handlers registered with `early_param()` run? What does the tree
guarantee about memory allocation and about static keys at the time those handlers run, whatever
the architecture? Start from `parse_early_param()` and its callers under `arch/`.

## bootparams.string-lifetime: Lifetime of the value string

- section: Parsing at boot
- relevance: 5 - a saved pointer into freed init memory shows in no diff

Which buffer does the string handed to a `__setup()` handler, to an `early_param()` handler and to
the set function of a `module_param()` point into, and how long does each buffer stay valid? What
are the requirements for a handler that keeps a pointer into that string in order to assure safe
usage? Start from `parse_early_param()`, `setup_command_line()`, `do_initcalls()` and
`param_set_charp()`.

# Documenting a parameter

## bootparams.doc-rule: Submit checklist and checkpatch

- section: Documenting a parameter
- relevance: 5 - the one thing the guide exists to enforce

What do the process documents require of a patch that adds a boot parameter, and of a patch that
adds a module parameter? What does `scripts/checkpatch.pl` check about either? Start from
`Documentation/process/submit-checklist.rst`.

## bootparams.doc-list: Parameter list and entries

- section: Documenting a parameter
- relevance: 5 - the file every new parameter is checked against, and what a reviewer compares a new entry with

In which file do entries for the kernel's command-line parameters go, and what order does that
file require of them? What form does that file require of an entry? Start from
`Documentation/admin-guide/kernel-parameters.rst`.

## bootparams.doc-tags: Restriction tags

- section: Documenting a parameter
- relevance: 5 - a reviewer compares the tags of a new entry with the ones the documentation defines

Where are the bracketed restriction tags of an entry in the list of command-line parameters
defined? Which tag, if any, marks a parameter that is handled early, and what does that tag state
about the parameter? Start from `Documentation/admin-guide/kernel-parameters.rst`.

# Model gaps

## bootparams.model-gaps: Other mistakes models make

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

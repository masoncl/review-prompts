# Questions: Kconfig

- guide: kconfig.md
- title: Kconfig

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/kconfig-measurement.md` is the
wider set the readers were measured on and `catalogue/kconfig-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## kconfig.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# References to undefined symbols

## kconfig.check-tools: Checking symbol references

- section: References to undefined symbols
- relevance: 5 - a reviewer can run these instead of searching by hand

Which tools in the tree, if any, find references to Kconfig symbols that no entry defines, in
Kconfig files and in source code, and how is each run? Give each make target, option and
environment variable name in full. Do the Kconfig tools themselves ever report such a reference
while they configure? Start from the help text of the top-level `Makefile`,
`scripts/checkkconfigsymbols.py` and the scripts in `scripts/kconfig/`.

## kconfig.undefined-symbols: Value of an undefined symbol

- section: References to undefined symbols
- relevance: 5 - a misspelt name is accepted without a word

What do the Kconfig tools do when `depends on`, `select`, `default` or a comparison names a symbol
that no `config` entry defines: is anything printed, what value does the name take in each
position, and what is the effect on the entry that used it? Start from `sym_lookup()`,
`sym_calc_value()` and `sym_check_prop()`.

# Value of a symbol

## kconfig.value-precedence: Precedence of value sources

- section: Value of a symbol
- relevance: 5 - which source wins, and why a value in a configuration file is ignored

For a bool or tristate symbol outside a choice, when the user value, a default, a weak reverse
dependency and a reverse dependency disagree, which wins, and which of them can raise the result
above what the direct dependencies allow? When does `sym_calc_value()` not use a value read from a
configuration file, and what does it print then? Start from `sym_calc_value()` and
`sym_calc_visibility()`.

## kconfig.defaults: Default properties

- section: Value of a symbol
- relevance: 4 - the first match wins and its condition caps the value

When a symbol has several `default` lines, possibly in several entries, which one is used, and how
do the condition on the line and the entry's dependencies limit the value it gives a tristate?
When does a default apply to a symbol that has a prompt? Start from `sym_get_default_prop()`.

## kconfig.default-policy: Default value policy

- section: Value of a symbol
- relevance: 4 - new options defaulting to y are routinely rejected

What default should a new option have, and which cases, if any, do the documents list as
deserving `default y` or `default m`? Name the document.

# Select and compile testing

## kconfig.select-semantics: Select semantics

- section: Select and compile testing
- relevance: 5 - the most misused attribute in the language

What exactly does `select` do to the selected symbol: which bound does it set and from which
value, and how does `if` change it? What becomes of the selected symbol's own `depends on`, and
are the symbols that the selected symbol depends on or selects enabled in turn? Start from the
handling of `P_SELECT` in `_menu_finalize()`.

## kconfig.unmet-dependencies: Unmet dependency warning

- section: Select and compile testing
- relevance: 5 - the warning a wrong select produces

Under exactly which condition does Kconfig report unmet direct dependencies, and what does the
report contain? Does the build stop, and what, if anything, makes it stop? Name any environment
variable or make option in full. Start from `sym_calc_value()`.

## kconfig.compile-test: COMPILE_TEST

- section: Select and compile testing
- relevance: 4 - most new driver entries carry it

How do the documents say `COMPILE_TEST` is to be combined with an architecture or platform
dependency, and what do they ask of code that is only compile-tested? Name the documents.

## kconfig.select-usage: Selecting symbols with dependencies

- section: Select and compile testing
- relevance: 5 - the central judgement call in reviewing an entry

What are the requirements for a `select` of a symbol that is visible or has dependencies in order
to assure safe usage? What does `Documentation/kbuild/kconfig-language.rst` advise about which
symbols to select, and how do in-tree entries that select such a symbol keep its dependencies met?
Name such entries.

## kconfig.compile-test-selects: Selects in compile-tested drivers

- section: Select and compile testing
- relevance: 5 - the warning appears only on the architectures nobody built

What are the requirements for a `select` of a symbol that has architecture or platform
dependencies, in an entry that can be enabled through `|| COMPILE_TEST`, in order to assure safe
usage? Which forms do in-tree entries use to meet them? Give each form with a real entry; in a
schematic example use only the placeholder names the language document uses.

# Modules and built-in code

## kconfig.generated-files: Generated configuration files

- section: Modules and built-in code
- relevance: 4 - what C, make and Rust each see for y, m and n

What do C code, makefiles and Rust code each see for a symbol that is y, m or n, and how are int,
hex and string symbols written for each, quoting included? What does C code see for a numeric
symbol whose dependencies are not met? Start from `conf_write_autoconf()`.

## kconfig.bool-under-tristate: Bool symbols below tristate symbols

- section: Modules and built-in code
- relevance: 4 - m is raised to y for a bool, so built-in code can end up calling a module

What value can a bool symbol take when the symbol it depends on is m, and what does a `select`
inside that bool symbol then force on a tristate target? What are the requirements for a `select`
of a tristate symbol from a bool symbol in order to assure safe usage? Name in-tree entries that
meet them.

## kconfig.optional-dependencies: Optional dependencies

- section: Modules and built-in code
- relevance: 5 - built-in code calling into a module fails at link time

How should an entry say that its code can use another subsystem when present, but must not be
built in while that subsystem is a module, and which spellings does the language document of this
tree give? Does the parser support a conditional form of `depends on`, and into which expression
does it turn one? What must the other subsystem's header provide? Start from `menu_add_dep()`.

## kconfig.reachable-usage: IS_ENABLED and IS_REACHABLE

- section: Modules and built-in code
- relevance: 4 - reviewers push back on one of them

Which of `IS_ENABLED()` and `IS_REACHABLE()` do `Documentation/process/coding-style.rst` and
`Documentation/kbuild/kconfig-language.rst` recommend, and which, if any, do they discourage and
why? What are the requirements for code that tests a symbol with `IS_ENABLED()` or
`IS_REACHABLE()` in order to assure safe usage?

# Entries and syntax

## kconfig.keywords: Keywords the parser accepts

- section: Entries and syntax
- relevance: 4 - entries copied from old trees use keywords that are gone

Do the lexer and the parser of this tree accept each of these forms: an option line, an optional
choice, a type or a name on a choice, the dashed spelling of help, and relative or optional
variants of source? Start from `scripts/kconfig/lexer.l` and `scripts/kconfig/parser.y`.

## kconfig.choice: Choice blocks

- section: Entries and syntax
- relevance: 4 - the rules for choices were tightened

What does the parser of this tree refuse in a choice or in one of its members, and is each refusal
an error that stops the configuration or only a warning? Can a choice be left with no member set,
and how is the winner picked when a configuration file sets several members? Start from
`choice_check_sanity()` and `sym_calc_choice()`.

## kconfig.renaming-symbols: Renaming or removing a symbol

- section: Entries and syntax
- relevance: 4 - a rename silently resets every user's setting

When an entry is renamed or removed, what happens to the old name in a user's existing
configuration on the next update? Does this tree have a mechanism for carrying the old value over
to a new symbol, and if so, how is such an entry written and what may it contain? If it has none,
say so.

# Model gaps

## kconfig.model-gaps: Other mistakes models make

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

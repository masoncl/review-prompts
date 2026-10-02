# Questions: Kconfig (measurement set)

- guide: kconfig.md
- title: Kconfig

A wide set of questions about writing and reviewing Kconfig entries: the
language, how a symbol's value is computed from prompts, defaults, selects and
dependencies, tristate and module semantics, the C macros that test a symbol,
the idioms the tree recommends, and the parts of `scripts/kconfig/` that
explain the behaviour. It is used to measure what a model already knows before
deciding what the built guide should spend its words on. The hand-written guide
it will replace is 580 words. Kbuild makefiles have their own guide. Format:
`../../../docs/subsystem-questions.md`.

# Where to look

## kconfig.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 100

Which files hold the Kconfig lexer and parser, the code that computes a
symbol's value, the code that builds the menu tree and propagates
dependencies, the expression evaluator, the macro preprocessor, the reader and
writer of configuration files, the front ends, the helper macros every Kconfig
file can use, the root Kconfig file, and the C header that defines the macros
for testing a symbol? A table. Start from `scripts/kconfig/`.

## kconfig.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - the conventions live in documents, not in code
- words: 70

Which files under `Documentation/` are the authority on the Kconfig language,
on its macro language, on the configuration targets and their environment
variables, on the layout and style of an entry, and on what a submitter must
check about a new option?

## kconfig.check-tools: Checking symbol references

- section: Finding your way
- relevance: 4 - a reviewer can run these instead of searching by hand
- words: 80

Which tools in the tree find references to Kconfig symbols that no entry
defines, in Kconfig files and in source code, and how is each run? Start from
the help text of the top-level `Makefile`, `scripts/checkkconfigsymbols.py` and
the scripts in `scripts/kconfig/`.

## kconfig.unit-tests: Kconfig unit tests

- section: Finding your way
- relevance: 3 - a change to the tools has tests to run and extend
- words: 60

Where are the tests for the Kconfig tools, which make target runs them, what
does one test directory contain, and which behaviours of the language do the
existing tests pin? Start from `scripts/kconfig/tests/conftest.py`.

# The language

## kconfig.keywords: Keywords the parser accepts

- section: Syntax
- relevance: 4 - entries copied from old trees use keywords that are gone
- words: 90

List the keywords the lexer of this tree accepts for entries and for
attributes of an entry. Then say whether it accepts each of these forms, which
readers bring from older trees or from other projects' Kconfig dialects: an
option line, an optional choice, a type or a name on a choice, the dashed
spelling of help, and relative or optional variants of source. Say only what
this lexer does, not what any earlier one did. Start from
`scripts/kconfig/lexer.l` and `scripts/kconfig/parser.y`.

## kconfig.symbol-types: Symbol types and expression values

- section: Syntax
- relevance: 3 - the basis for every dependency expression
- words: 70

Which types can a symbol have, what value does a bare symbol of each type
contribute to a dependency expression, and what happens when one symbol is
given two different types in two entries? Start from `menu_set_type()` and
`expr_calc_value()`.

## kconfig.comparisons: Comparisons and constants

- section: Syntax
- relevance: 3 - a mistyped constant is silently a symbol
- words: 80

How are `=`, `!=`, `<` and the other comparisons evaluated when the operands
are tristates, numbers or strings, and what does the parser make of an
unquoted word such as an upper-case Y or N used as a value? Start from
`expr_calc_value()` and the symbol rules in `scripts/kconfig/parser.y`.

## kconfig.multiple-definitions: Symbols defined more than once

- section: Syntax
- relevance: 3 - architectures override defaults this way
- words: 70

When a symbol has several `config` entries, how are their dependencies,
prompts, defaults and selects combined, and what is refused or warned about?
Start from `_menu_finalize()` and `menu_add_prompt()`.

## kconfig.menu-structure: Menus and if blocks

- section: Syntax
- relevance: 3 - decides which dependencies an entry silently inherits
- words: 80

How do `menu`, `if` and `menuconfig` pass their dependencies to the entries
inside them, which properties of an entry receive those dependencies, what does
`visible if` change that `depends on` does not, and when does an entry become
a child of the entry before it without any block? Start from `_menu_finalize()`.

## kconfig.choice: Choice blocks

- section: Syntax
- relevance: 4 - the rules for choices were tightened
- words: 90

In this tree, which types may a choice and its members have, what must a
choice and each member carry, which forms of default are accepted on the
choice and on a member, and can a choice be left with no member set? How is
the winner picked when a configuration file sets several members? Start from
`choice_check_sanity()` and `sym_calc_choice()`.

## kconfig.ranges: Numeric symbols and ranges

- section: Syntax
- relevance: 2 - narrow, but the clamping surprises people
- words: 60

What may the default of an int or hex symbol be, what does a `range` do to a
user value or a default that lies outside it, and what value does a numeric or
string symbol have when no default applies? Start from `sym_validate_range()`
and `sym_check_prop()`.

## kconfig.help-text: Help text and entry layout

- section: Syntax
- relevance: 3 - what reviewers and checkpatch ask of every new entry
- words: 70

How is an entry indented, how does the parser find the end of a help text,
what does it do with an empty one, how long must the help of a new visible
option be to satisfy `scripts/checkpatch.pl`, and what does the style document
ask of the prompt of a dangerous option?

# How a value is computed

## kconfig.visibility: Visibility and promptless symbols

- section: Value of a symbol
- relevance: 5 - explains why a value in a configuration file is ignored
- words: 90

How is a symbol's visibility computed, what can set the value of a symbol with
no prompt, what happens to a value read from a configuration file when the
symbol is not visible, and how is a visibility of m treated for a bool symbol?
Start from `sym_calc_visibility()`.

## kconfig.value-order: Order of value calculation

- section: Value of a symbol
- relevance: 5 - select, imply, default and the user value interact in a fixed order
- words: 100

For a bool or tristate symbol outside a choice, in what order does
`sym_calc_value()` consult the user value, the defaults, the weak reverse
dependencies, the direct dependencies and the reverse dependencies, and which
of them can raise the result above what the dependencies allow?

## kconfig.defaults: Default properties

- section: Value of a symbol
- relevance: 4 - the first match wins and its condition caps the value
- words: 90

When a symbol has several `default` lines, possibly in several entries, which
one is used, how do the condition on the line and the entry's dependencies
limit the value it gives a tristate, when does a default apply to a symbol
that has a prompt, and is an explicit `default n` ever needed? Start from
`sym_get_default_prop()`.

## kconfig.select-semantics: Select semantics

- section: Value of a symbol
- relevance: 5 - the most misused attribute in the language
- words: 100

What exactly does `select` do to the selected symbol: which bound it sets, from
which value, how `if` changes it, what becomes of the selected symbol's own
`depends on`, and whether the symbols that the selected symbol depends on or
selects are enabled in turn? Start from the handling of `P_SELECT` in
`_menu_finalize()`.

## kconfig.unmet-dependencies: Unmet dependency warning

- section: Value of a symbol
- relevance: 5 - the warning a wrong select produces
- words: 80

Under exactly which condition does Kconfig report unmet direct dependencies,
which function prints the report and what does it contain, does the build stop,
and what makes it stop? Start from `sym_calc_value()`.

## kconfig.imply: Imply semantics

- section: Value of a symbol
- relevance: 3 - its meaning has changed and the old one is still repeated
- words: 80

What does `imply` do to the implied symbol in this tree: can the user still
set it to n or to m when the implying symbol is y, how do the implied symbol's
dependencies limit it, and where in the calculation is it applied? Start from
`sym_calc_value()`.

## kconfig.undefined-symbols: References to undefined symbols

- section: Value of a symbol
- relevance: 5 - a misspelt name is accepted without a word
- words: 90

What do the Kconfig tools do when `depends on`, `select`, `default` or a
comparison names a symbol that no `config` entry defines: is anything printed,
what value does the name take in each position, and what is the effect on the
entry that used it? Start from `sym_lookup()`, `sym_calc_value()` and
`sym_check_prop()`.

## kconfig.bool-under-tristate: Bool symbols below tristate symbols

- section: Value of a symbol
- relevance: 4 - m is raised to y for a bool, so built-in code can end up calling a module
- words: 90

What value can a bool symbol take when the symbol it depends on is m, and what
does a `select` inside that bool symbol then force on a tristate target? What
usage is unsafe here, and what that looks similar is correct? Name in-tree
entries that handle it.

## kconfig.recursive-dependencies: Recursive dependency errors

- section: Value of a symbol
- relevance: 3 - the usual cost of mixing select and depends on
- words: 70

What makes the tools report a recursive dependency, which relations between
symbols count as edges of the cycle, is the report fatal, and which remedies
does the language documentation recommend? Start from `sym_check_deps()`.

# Modules and C code

## kconfig.generated-files: Generated configuration files

- section: From symbols to code
- relevance: 4 - what C, make and Rust each see for y, m and n
- words: 100

Which files does the syncconfig step write for C, for make and for the Rust
compiler, how does each represent a symbol that is y, m or n, and how are int,
hex and string symbols written? What does C code see for a numeric symbol whose
dependencies are not met? Start from `conf_write_autoconf()`.

## kconfig.enabled-macros: Macros that test a symbol

- section: From symbols to code
- relevance: 5 - the wrong one compiles and silently drops code
- words: 100

What does each of `IS_ENABLED()`, `IS_BUILTIN()`, `IS_MODULE()` and
`IS_REACHABLE()` evaluate to when the symbol is y, m or n, in built-in code and
in module code, which symbol types do they work on, and what does a plain
#ifdef on the symbol see when the symbol is m? A table. Start from
`include/linux/kconfig.h`.

## kconfig.reachable-usage: Choosing between the macros

- section: From symbols to code
- relevance: 4 - reviewers push back on one of them
- words: 80

Which of the symbol-testing macros do the coding style and the Kconfig
language document recommend, which if any do they discourage and why, and when
is an `#ifdef` still needed? What usage is unsafe, and what that looks similar is
correct?

## kconfig.optional-dependencies: Optional dependencies

- section: From symbols to code
- relevance: 5 - built-in code calling into a module fails at link time
- words: 100

How should an entry say that its code can use another subsystem when present,
but must not be built in while that subsystem is a module? Which spellings does
the language document of this tree give, does the parser support a conditional
form of `depends on` and how does it turn one into an expression, and what
must the other subsystem's header provide? Start from `menu_add_dep()`.

## kconfig.module-constraints: Constraining to module or built-in

- section: From symbols to code
- relevance: 3 - idioms whose meaning is not obvious from the text
- words: 70

How does an entry restrict itself to being a module only, how is a bare `m`
in an expression treated when module support is off, and what do dependencies
written as FOO=y, FOO=m and FOO!=n allow? Start from `rewrite_m()`.

# Idioms and conventions

## kconfig.select-usage: Select versus depends on

- section: Writing an entry
- relevance: 5 - the central judgement call in reviewing an entry
- words: 110

What use of `select` is unsafe, and what that looks similar is correct? Say
what the language document advises about which symbols to select, how
in-tree entries that select a symbol with dependencies keep those dependencies
met, how a conditional select is written, and name in-tree entries that select
a visible symbol or one with dependencies correctly.

## kconfig.compile-test: COMPILE_TEST

- section: Writing an entry
- relevance: 4 - most new driver entries carry it
- words: 80

Where is `COMPILE_TEST` defined and what does it itself depend on, how is it
meant to be combined with an architecture or platform dependency, what do the
documents ask of code that is only compile-tested, and which configuration
targets turn it on?

## kconfig.compile-test-selects: Selects in compile-tested drivers

- section: Writing an entry
- relevance: 4 - the warning appears only on the architectures nobody built
- words: 90

When an entry can be enabled through `|| COMPILE_TEST`, what use of `select`
on a symbol that has architecture or platform dependencies is unsafe, and what
that looks similar is correct? Give the forms used in the tree to avoid the
problem, each with a real entry; in a schematic example use only the
placeholder names the language document uses.

## kconfig.capability-symbols: HAVE and ARCH_HAS symbols

- section: Writing an entry
- relevance: 3 - the pattern that makes select safe
- words: 70

What is the recommended pattern for a feature that only some architectures
support: which symbol is promptless, who selects it, where do the feature's
real dependencies go, and why is it built that way? Start from the hints
section of `Documentation/kbuild/kconfig-language.rst`.

## kconfig.toolchain-tests: Compiler and toolchain tests

- section: Writing an entry
- relevance: 3 - evaluated when the configuration is parsed, not when it is used
- words: 80

Which macros are available for testing what the compiler, assembler, linker
and Rust compiler support, where are they defined, what prefix is recommended
for a symbol that records such a capability, and what can such a test not take
as an argument? Start from `scripts/Kconfig.include`.

## kconfig.macro-language: Macro language

- section: Writing an entry
- relevance: 2 - rarely touched, easy to get subtly wrong
- words: 80

Which built-in functions does the Kconfig preprocessor provide, which kinds of
variable assignment, how is an environment variable referenced, and what are
the pitfalls with whitespace, commas and expanding to keywords? Start from
`scripts/kconfig/preprocess.c`.

## kconfig.default-policy: Default value policy

- section: Writing an entry
- relevance: 4 - new options defaulting to y are routinely rejected
- words: 70

What default should a new option have, and which cases do the documents list
as deserving `default y` or `default m`?

## kconfig.new-entry-review: Reviewing a new entry

- section: Writing an entry
- relevance: 4 - the list a reviewer walks through
- words: 100

What should be checked about a patch that adds a new `config` entry or a
family of related entries: the symbols it names, its type, prompt and help, its
default, its dependencies and selects, the combinations to build, and the
makefile and source lines that use it?

# Configuration files and tools

## kconfig.config-file-format: Reading a configuration file

- section: Configuration files
- relevance: 3 - the format is an interface users and distributions depend on
- words: 80

How does the reader treat a line setting a symbol to n, a comment saying a
symbol is not set, a symbol it does not know, a symbol assigned twice and a
value the symbol's type does not allow? Which of these are reported, and only
when? Start from `conf_read_simple()`.

## kconfig.renaming-symbols: Renaming or removing a symbol

- section: Configuration files
- relevance: 4 - a rename silently resets every user's setting
- words: 100

When an entry is renamed or removed, what happens to the old name in a user's
existing configuration on the next update? Does this tree have a mechanism for
carrying the old value over to a new symbol; if so how is it written, what may
such an entry contain, and is the old name written back out? If it has none,
say so.

## kconfig.environment: Environment variables

- section: Configuration files
- relevance: 3 - how warnings are turned on and made fatal
- words: 90

Which environment variables do the configuration tools read in this tree, which
of them turn on extra warnings and which make warnings fatal, and which
letters of the build's extra-warning option set them? Start from
`scripts/kconfig/Makefile` and `Documentation/kbuild/kconfig.rst`.

## kconfig.config-targets: Configuration targets

- section: Configuration files
- relevance: 3 - which target to use to test an entry
- words: 90

What does each of the non-interactive configuration targets do with new
symbols and with the existing configuration: the update targets, the
all-something targets, the ones that list new symbols, the ones that convert
between y and m, and the ones that apply a fragment? Start from
`scripts/kconfig/Makefile` and `enum input_mode` in `scripts/kconfig/conf.c`.

## kconfig.defconfig-files: Defconfigs and fragments

- section: Configuration files
- relevance: 3 - a defconfig line can be dead without anyone noticing
- words: 90

What does the target that writes a minimal configuration leave out, what
happens to a line in a defconfig or a fragment that names a removed symbol or
one whose dependencies are not met, where do fragments live and how are they
merged? Start from `conf_write_defconfig()` and
`scripts/kconfig/merge_config.sh`.

# Changing the implementation

## kconfig.tool-changes: Changing the Kconfig tools

- section: What a change must preserve
- relevance: 3 - one library serves five front ends and other projects
- words: 90

What must a change to the lexer, parser or evaluator under `scripts/kconfig/`
keep working: which programs share the code, which other places have to be
updated when a keyword or property type is added, which file formats are
interfaces, and which tests and documents go with it? Generated files are not
in the tree, so name them in plain text.

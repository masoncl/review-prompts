# What the kconfig measurement found

Three models were asked the 40 questions in `kconfig-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader A said it assumed kernels 6.12 to
6.18 and reader C 6.12 to 7.0; both describe the value calculation, select,
imply and the symbol-testing macros correctly, and reader C needed the fewest
corrections. Reader B said 6.10 to 6.12 and was wrong about fundamentals: what
a bool symbol under a module does, which macro is defined for m, how a choice
is resolved, and which keywords still exist. The hand-written guide was never
checked against current sources, so differences between it and the built guide
are expected and are noted near the end.

The Kconfig language is old and its outline is well known. What the readers
got wrong is what the last few releases added or removed (conditional
`depends on`, `transitional`, the dangling-symbol checker, the strict choice
rules), what the language document now recommends, and the corners of the
evaluator nobody reads: what an undefined name evaluates to, how comparisons
are done, what is an error and what only a warning.

## What all three readers got wrong

- **The dangling-symbol checker.** None knew `make kconfig-sym-check`, which
  runs `scripts/kconfig/kconfig-sym-check.pl` over every Kconfig file, takes
  `KCONFIG_SYM_CHECK_EXCLUDES`, and also flags an upper-case Y, N or M used as
  a value. Readers A and C said there is no such script under
  `scripts/kconfig/`; reader B offered a make target for
  `scripts/checkkconfigsymbols.py` that does not exist. Readers A and B also
  said the Kconfig tools themselves warn about undefined names in some cases.
  They never do: `sym_check_prop()` skips a `select` or `imply` target whose
  type is unknown.
- **Conditional `depends on`.** The parser accepts `depends on X if Y`, and
  `menu_add_dep()` turns it into X || (Y = n). Reader B said the form does not
  exist, readers A and C were unsure, and reader A gave the expression as
  X || !Y, which differs when Y is m. None knew that the language document now
  recommends `depends on BAR if BAR` for an optional dependency and calls
  BAR || !BAR the "counterintuitive" alternative, or that it describes
  `IS_REACHABLE()` as generally discouraged: all three offered that macro
  somewhere as an ordinary choice.
- **`transitional`.** Reader B said the tree has no way to carry a value over
  a rename. Readers A and C knew the keyword and not its rules: the entry may
  have a type and help and nothing else (any other property, a dependency or a
  visibility is a parse error), it counts as visible so its value is read from
  the old configuration, the new symbol whose default names it is marked as
  user-set so it is not asked, and it is never written back.
- **Errors they called warnings.** Blank help text, a `default` on a choice
  member, a member prompt in another entry, a member that is not bool and a
  member with no prompt all count in `yynerrs` and make `conf_parse()` exit.
  Every reader said blank help is warned about or accepted, and readers B and C
  said the same of the choice rules.
- **Strings in the file make includes are not quoted.** All three showed
  them quoted. `print_symbol_for_autoconf()` asks for no escaping; the
  configuration file, the C header and the Rust file do quote them.
- **The unit tests.** None listed `conditional_dep`, `transitional`,
  `err_transitional` or `warn_changed_input`; reader A named a directory that
  does not exist and reader B said each test is a loose Python script (it is
  an `__init__.py` beside a `Kconfig` and expected files).
- **`KCONFIG_WARN_CHANGED_INPUT`**, which reports user values that the
  dependencies or a range changed, was in nobody's list of environment
  variables. No letter of the extra-warning option sets it.
- **Several definitions of one symbol.** Each reader was partly wrong: every
  entry's dependency is ORed into `dir_dep`, a second type only warns and the
  first is kept, and "prompt redefined" is about two prompts in one entry.
- **The toolchain macros.** Readers A and B listed macros that are make
  helpers, not Kconfig ones; readers A and C offered a linker capability prefix
  no symbol uses. The document recommends only `CC_HAS_`.
- **The capability-symbol example in the language document is hypothetical.**
  HAVE_GENERIC_IOMAP is defined nowhere in this tree and never was: the passage
  says "we would in lib/Kconfig see" and was written as an illustration, not as
  a description of a real symbol. Reader C repeated it as if it were real and
  reader B made names up. The real symbol is `GENERIC_IOMAP`, a plain bool that
  architectures select.

## What only some readers got wrong

- **Reader B on fundamentals.** A bool symbol whose dependency is m is
  truncated to n (it is raised to y, while a select inside it still carries
  the m); `depends on FOO=m` makes an entry module-only (a comparison yields
  y, the form is `depends on m`); `rewrite_m()` replaces m with n (it appends the modules
  symbol); m defines `CONFIG_FOO` as well as `CONFIG_FOO_MODULE` (only the
  latter); choices and their members may be tristate or optional and the first
  member set to y wins (bool only, no such keyword, the last assignment wins
  because `conf_read_simple()` moves it to the front); `option`, `optional`,
  the dashed help keyword, the relative and optional source keywords are still
  accepted (none is in the lexer, and the source variants belong to other
  projects' Kconfig dialects, not to any kernel); the unmet-dependency report comes from
  `sym_check_deps()` and covers `imply` (it is `sym_warn_unmet_dep()`, on
  `dir_dep.tri < rev_dep.tri`, fed by select only); a lower default overrides
  an imply; `COMPILE_TEST` is in lib/Kconfig.debug and excludes UML (it is in
  `init/Kconfig` and depends on `HAS_IOMEM`); the unknown-symbol warning is
  turned on by the first extra-warning level (it is the letter c, and e makes
  warnings fatal); the symbol-testing macros are defined in the generated
  header.
- **Comparisons** (readers A and B). Both said tristates are compared as
  strings. `expr_calc_value()` compares numerically, n < m < y, unless both
  sides are string symbols. An undefined name's string value is the name
  itself, not the empty string, so UNDEF != n is y.
- **Undefined names** (readers A and B). Not quite silent: an int or hex
  default that names one gets "number is invalid" and a range that names one
  gets "range is invalid". An entry whose
  `depends on` names one can still be switched on by a select.
- **What the documents say** (readers A and B). Both invented cases for
  `default y`; the language document lists four. Reader A said the document
  recommends `depends on` for everything that is not a hidden symbol, and that
  compile-tested code need not run; the document asks that it not crash.
- **`syncconfig` asks about new symbols** (readers A and B said it takes
  defaults silently).
- **Imply and the user value** (reader A). `sym_tristate_within_range()` does
  not look at `implied`, so m is still allowed when the implying symbol is y.
- **Choice fallback** (readers A and C). With no member set to y,
  `sym_calc_choice()` skips the choice default if the user set it to n and
  skips members that carry any user value.
- **Examples that are not in the tree** (reader C). A conditional select and a
  dependency quoted for two real drivers were not what those entries contain.

## What the readers already knew

Readers A and C: where the files are, the order in which `sym_calc_value()`
combines user value, default, imply, direct and reverse dependencies, that the
first default whose condition holds wins and its condition caps the value,
what select does and does not propagate, the table of `IS_ENABLED()`,
`IS_BUILTIN()`, `IS_MODULE()` and `IS_REACHABLE()`, the configuration targets,
how a bare m is rewritten, and what to do about a select in a driver that can
be compile-tested. All three knew where the macros for compiler tests live and
how `COMPILE_TEST` is meant to be combined with a platform dependency.

## Where the hand-written guide is stale or thin

- It says a reference to an undefined symbol causes "silent build failures".
  Nothing fails: a `depends on` it reads as n, a `select` of it does nothing,
  and no tool in the configuration step says a word. It names no checker; the
  tree has two.
- It says an entry that selects a symbol "must have" that symbol's
  dependencies. In-tree entries also meet them another way: `DRM_I915` selects
  each dependency of `ACPI_VIDEO` under the same condition, and `PHY_BRCM_USB`
  selects `SOC_BRCMSTB` only `if ARCH_BRCMSTB`.
- Its quoted warning and its `QCS_DISPCC_615` example still match the tree, and
  `COMPILE_TEST` is where it says; it does not say that symbol depends on
  `HAS_IOMEM`, or that the warning becomes fatal under `KCONFIG_WERROR`.
- It has nothing on tristate against bool, the symbol-testing macros, optional
  dependencies, defaults, choices, renames or the keywords that are gone, all
  of which the measurement shows at least one reader gets wrong.
- It was never onboarded to the drift checker.

## What was left out of the build set and why

The hand-written guide is 580 words, so the built guide is sized to the 600-word
floor (480 to 720). With no answer budgeted under 40 words that is room for ten
questions and 505 words of budget. The first build set asked fifteen at 20 to
45 words each, 465 in all, and many of the bullets it produced were fragments
that meant nothing without the question beside them ("Select still wins.",
"Correct: optional dependency."), so this one asks fewer and gives each more
room. Three of the ten are the hand-written guide's own subjects: names that no
entry defines, the unmet-dependency warning, and selects in drivers that can be
compile-tested. Five are what every reader got wrong and a reviewer of any
Kconfig patch meets: the two checkers, optional dependencies, which
symbol-testing macro the documents want, select against `depends on`, and
renames. Reader B's errors decided as much as the other two readers' did: the
questions on the unmet-dependency condition and on bool under tristate stay
although readers A and C answer them. The default policy stays because readers
A and B invented its cases.

- In the first build set, and gave way to the larger budgets:
  `kconfig.core-files` (every reader places the files, and every kept answer
  names the file it rests on), `kconfig.keywords` (a keyword that is gone is a
  parse error the moment it is used, and the two this tree has gained, the
  conditional `depends on` and `transitional`, are carried by
  `kconfig.optional-dependencies` and `kconfig.renaming-symbols`),
  `kconfig.enabled-macros` (readers A and C give the whole table without a
  correction, a table costs sixty words or more, and
  `kconfig.reachable-usage` still says which macro to use and which the
  document discourages), `kconfig.new-entry-review` (a checklist whose built
  answer pointed back at the items above it) and `kconfig.tool-changes`
  (relevance 3: the guide is loaded for changes to entries, and patches to
  `scripts/kconfig/` are few). With them went the "what this tree calls things"
  and "changing the implementation" parts. Bring the macro table back first if
  the size limit is raised: reader B thinks m defines the plain `CONFIG_` name
  as well.
- Dropped because readers A and C answer them and the kept questions carry the
  part reader B lacks: `kconfig.value-order`, `kconfig.defaults`,
  `kconfig.select-semantics`, `kconfig.imply`, `kconfig.visibility`,
  `kconfig.module-constraints`, `kconfig.compile-test`,
  `kconfig.config-targets`, `kconfig.symbol-types`.
- Dropped because a mistake is reported by the tools the moment it is made:
  `kconfig.choice`, `kconfig.help-text`, `kconfig.recursive-dependencies`,
  `kconfig.ranges`, `kconfig.macro-language`.
- Dropped for room, although every reader was weak: `kconfig.comparisons`,
  `kconfig.multiple-definitions`, `kconfig.generated-files`,
  `kconfig.environment`, `kconfig.defconfig-files`,
  `kconfig.config-file-format`, `kconfig.toolchain-tests`,
  `kconfig.capability-symbols`, `kconfig.menu-structure`. They come back after
  the macro table.
- `kconfig.docs` and `kconfig.unit-tests` had been folded into
  `kconfig.core-files` and `kconfig.tool-changes`, and went with them.

Three build questions carry a few words the measured text did not, so that none
presupposes its answer and each name comes back in full:
`kconfig.check-tools` says "if any" of the tools and asks for each make target,
option and environment variable by name, `kconfig.unmet-dependencies` says "if
anything" of what stops the build and asks for the variable or option by name,
and `kconfig.default-policy` says "if any" of the listed cases and asks which
document lists them. `kconfig.renaming-symbols` moved from the syntax section
to "Writing an entry". The ids are unchanged.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A:  79 corrections, 33% rewritten on average
reader B: 126 corrections, 73% rewritten on average
reader C:  71 corrections, 19% rewritten on average

question                         reader A      reader B      reader C
kconfig.core-files               6% ( 1)       3% ( 7)       0% ( 3)
kconfig.docs                     0% ( 0)       42% ( 1)      11% ( 1)
kconfig.check-tools              81% ( 5)      82% ( 1)      42% ( 2)
kconfig.unit-tests               60% ( 2)      93% ( 1)      50% ( 1)
kconfig.keywords                 38% ( 2)      70% ( 6)      23% ( 3)
kconfig.symbol-types             27% ( 1)      69% ( 1)      13% ( 1)
kconfig.comparisons              72% ( 2)      99% ( 1)      10% ( 1)
kconfig.multiple-definitions     48% ( 1)      77% ( 1)      46% ( 1)
kconfig.menu-structure           39% ( 3)      78% ( 6)      18% ( 3)
kconfig.choice                   28% ( 3)      74% ( 4)      60% ( 5)
kconfig.ranges                   43% ( 2)      75% ( 3)      0% ( 0)
kconfig.help-text                32% ( 2)      82% ( 5)      18% ( 3)
kconfig.visibility               12% ( 1)      83% ( 6)      23% ( 2)
kconfig.value-order              13% ( 1)      78% ( 1)      3% ( 1)
kconfig.defaults                 4% ( 1)       71% ( 1)      0% ( 0)
kconfig.select-semantics         7% ( 1)       73% ( 1)      7% ( 1)
kconfig.unmet-dependencies       25% ( 1)      86% ( 1)      11% ( 1)
kconfig.imply                    31% ( 2)      85% ( 4)      4% ( 2)
kconfig.undefined-symbols        43% ( 4)      84% ( 4)      1% ( 1)
kconfig.bool-under-tristate      40% ( 3)      84% ( 4)      6% ( 1)
kconfig.recursive-dependencies   40% ( 2)      71% ( 5)      11% ( 1)
kconfig.generated-files          25% ( 2)      70% ( 7)      15% ( 3)
kconfig.enabled-macros           0% ( 0)       42% ( 1)      0% ( 0)
kconfig.reachable-usage          19% ( 2)      77% ( 4)      18% ( 1)
kconfig.optional-dependencies    55% ( 4)      73% ( 2)      17% ( 1)
kconfig.module-constraints       19% ( 1)      75% ( 3)      5% ( 1)
kconfig.select-usage             34% ( 4)      72% ( 4)      36% ( 4)
kconfig.compile-test             21% ( 2)      63% ( 3)      9% ( 1)
kconfig.compile-test-selects     6% ( 1)       64% ( 1)      12% ( 2)
kconfig.capability-symbols       49% ( 1)      79% ( 2)      36% ( 2)
kconfig.toolchain-tests          53% ( 5)      84% ( 7)      35% ( 4)
kconfig.macro-language           30% ( 2)      84% ( 3)      11% ( 1)
kconfig.default-policy           62% ( 2)      85% ( 1)      5% ( 1)
kconfig.new-entry-review         45% ( 3)      77% ( 2)      26% ( 2)
kconfig.config-file-format       48% ( 2)      54% ( 3)      30% ( 2)
kconfig.renaming-symbols         55% ( 1)      83% ( 1)      48% ( 2)
kconfig.environment              43% ( 1)      66% ( 3)      27% ( 1)
kconfig.config-targets           3% ( 1)       67% ( 3)      12% ( 1)
kconfig.defconfig-files          45% ( 1)      81% ( 4)      33% ( 2)
kconfig.tool-changes             32% ( 4)      80% ( 8)      29% ( 6)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `kconfig.choice`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `kconfig.keywords`, `kconfig.visibility`, `kconfig.value-order`, `kconfig.defaults`, `kconfig.select-semantics`, `kconfig.generated-files`, `kconfig.compile-test`, `kconfig.new-entry-review`.

## Questions reorganised

Subjects now: references to undefined symbols, value of a symbol, select and compile testing,
modules and built-in code, entries and syntax. `# Where to look` went: its one question,
`kconfig.check-tools`, sits with `kconfig.undefined-symbols`. Merged: `kconfig.value-order` and
`kconfig.visibility` into `kconfig.value-precedence`. Dropped: `kconfig.new-entry-review`, a
checklist of eight items whose built answer pointed back at the other questions.
`kconfig.keywords` no longer asks for the list of keywords, only which remembered forms the lexer
refuses and what it has gained; `kconfig.choice` asks what is refused and how loudly. 21 became 19.

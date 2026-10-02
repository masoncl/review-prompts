# What the boot-params measurement found

Three models were asked the 26 questions in `boot-params-measurement.md` with
no sources, and a checker that had the sources then corrected each answer
against a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and
C; which models they were does not matter here. Reader A said it was
describing kernel 6.12, reader B 6.10 to 6.12, reader C 6.12 to 6.15. The
hand-written guide was never checked against current sources, so differences
between it and the built guide are expected and are noted below.

## What all three readers got wrong

- **`early_param()` in code built as a module.** Readers A and B said it
  expands to nothing, reader C said "built-in only" and was unsure. Under
  `MODULE`, `include/linux/init.h` defines only `__setup()` and
  `__setup_param()` as empty; `early_param()` is not defined at all, so a
  modular build fails. `core_param()` is the same, behind `#ifndef MODULE` in
  `include/linux/moduleparam.h`.
- **An embedded bootconfig can now reach early handlers.** Every reader said
  there was no way. `CONFIG_CMDLINE_FROM_BOOTCONFIG` renders the `kernel`
  keys at build time and x86 `setup_arch()` puts them in front of
  `boot_command_line` with `xbc_prepend_embedded_cmdline()` before
  `parse_early_param()`. Only x86 selects
  `ARCH_SUPPORTS_CMDLINE_FROM_BOOTCONFIG`. An initrd bootconfig is still too
  late for `early_param()`.
- **Where the restriction tags are defined.** Readers A and C said the `.rst`
  defines them; reader B thought the `.rst` holds the list. The tags (with
  `EARLY`, `KNL`, `BOOT`, `BUGS=`) are a legend at the top of
  `Documentation/admin-guide/kernel-parameters.txt`; the `.rst` has the
  introduction and pulls the `.txt` in with an `include` directive.
- **An error does not stop the parser, but it loses the init arguments.**
  `parse_args()` logs, carries on, and at `--` returns `err ?: args`. After
  any failed parameter `start_kernel()` gets an `ERR_PTR()` and skips the
  "Setting init args" pass. Reader A left this out, reader B said a negative
  return aborts parsing, reader C said parsing stops at the first error.
- **Words dropped without a message.** Nobody listed the boot loader words
  `BOOT_IMAGE=` and `kexec` in `unknown_bootoption()`, and only reader C had
  the rest: any name with a `.` in it, a sysctl alias, and a word that
  exactly matches an `early_param()` string.
- **Other callers of `parse_args()`.** All three named module loading and at
  most dynamic debug. `do_sysctl_args()`, `bootconfig_cmdline_requested()`
  (which turns the returned pointer into an offset) and
  `lkdtm_check_bool_cmdline()` call it too. The tests are
  `lib/tests/cmdline_kunit.c`, not lib/cmdline_kunit.c, and
  `lib/test-kstrtox.c`.
- **`kstrtobool()` looks at one character** (two for on/off), and takes e/E
  and d/D as well; "yellow" is true. `memparse()` reports nothing: a bad
  value shows only through `retptr`.
- **Options read before early parsing.** Each reader named callers of
  `arch/x86/lib/cmdline.c` that do not call it (memory encryption, page table
  isolation). The decompressor has its own copy in `arch/x86/boot/cmdline.c`.

## What readers A and B got wrong

- **`core_param()` has a sysfs file.** Both said it has none.
  `param_sysfs_builtin()` files a name with no `.` under the module name
  "kernel", so it appears in `/sys/module/kernel/parameters/` when its
  permission is not 0.
- **The checkpatch test.** `UNDOCUMENTED_SETUP` looks only at `__setup("`, is
  reported through `CHK()` (so only with `--strict`, or under `net/`,
  `drivers/net/` and `drivers/staging/`), and is satisfied only by lines the
  same patch adds to `kernel-parameters.txt`; it never reads the file. Reader
  A called it a warning that greps the file. Reader B described a test for
  `MODULE_PARM_DESC()` that does not exist. Reader C had it nearly right.
- **Static keys in early handlers.** Reader A said enabling one warns, reader
  B said early handlers always run before `jump_label_init()`. x86, arm64,
  riscv, s390, powerpc, loongarch and m68k call `jump_label_init()` just
  before `parse_early_param()`; openrisc and um also call it from architecture
  code; arm, mips and sparc do not. alpha and parisc never call it from
  architecture code, so there the call in `start_kernel()` does the work.

## What readers A and C got wrong

- Both said the word `console` also runs the earlycon handler inside
  `do_early_param()`. That special case is not in this tree;
  `drivers/tty/serial/earlycon.c` registers its own `early_param("console")`.
  Reader B did not mention it.

## What reader B got wrong alone

Reader B had most of the mechanism wrong, not just the names:

- `__setup()` strings are matched exactly, so one cannot swallow another.
  `obsolete_checksetup()` compares only the length of the registered string, a
  prefix match.
- A `__setup()` handler gets the value, or NULL when there is none. It gets
  the text after the registered string and never NULL; only `early_param()`
  and `module_param()` handlers can see NULL.
- `do_initcall_level()` parses nothing, and `core_param()` sets a level. It
  calls `parse_args()` for its level before the initcalls, `core_param()` is
  level -1, and the macros that set a level are `core_param_cb()` to
  `late_param_cb()`.
- The kernel keeps `module.param=value` words for a module loaded later.
  `unknown_bootoption()` drops them; modprobe reads `/proc/cmdline`.
- `param_set_charp()` uses kstrdup(). It keeps the pointer it was given until
  the slab allocator is up.
- The unsafe and hardware flags the wrong way round:
  `KERNEL_PARAM_FL_HWPARAM` is refused under lockdown,
  `KERNEL_PARAM_FL_UNSAFE` only taints.
- Bootconfig `kernel` keys go after the boot loader's words. They go in
  front, so the boot loader wins for a last-value-wins handler.
- List entries written `name=value`; they are written `name=`.

## What the readers already knew

Readers A and C answered these with little to correct: the order of parsing
(early handlers, then level -1 parameters and `__setup()` handlers interleaved
in command-line order, then levelled parameters before each initcall level),
what each kind of handler is given, the return conventions of `__setup()`
(1 when handled) and `early_param()` (0 when fine), prefix matching and `-`
against `_`, which buffer each kind of handler's string lives in and that the
early one is freed with init memory, the levelled macros, the two parameter
flags, and what a list entry looks like. Reader C also had the sysfs side and
the sysctl prefix right. All three knew that the process documents ask for a
list entry for a boot parameter and only `MODULE_PARM_DESC()` for a module
parameter.

## Where the hand-written guide is stale

- It says every `module_param()` and `module_param_named()` must be documented
  in `kernel-parameters.txt`. `Documentation/process/submit-checklist.rst` asks
  that of boot parameters and asks only for `MODULE_PARM_DESC()` for module
  parameters. The tree has about seven thousand module parameters and the list
  has a few hundred dotted entries, nearly all for code that is normally
  built in (`usbcore.autosuspend=`, `rcutree.blimit=`).
- Its exceptions do not match the tree. `CONFIG_EXPERIMENTAL` does not exist.
  Nothing in the process documents excuses parameters under
  `CONFIG_DEBUG_KERNEL`; in practice some `__setup()` parameters are
  documented elsewhere (`fail_futex=` is in
  `Documentation/fault-injection/fault-injection.rst` and not in the list).
- The example format `tlbi=off` or `tlbi=[off]` is not how entries are
  written: the name carries a trailing `=` when it takes a value, the values
  go on a `Format:` line, and the square brackets hold restriction tags from
  the legend at the top of the `.txt`.
- It says nothing about the `EARLY` tag, about where the tags are defined, or
  that checkpatch only tests `__setup()`.
- It is all report-this instructions and says nothing about how the macros
  behave. The built guide adds the order of parsing, what an early handler
  can rely on, what a handler receives and returns, how long the string
  lives, and how the value helpers report a bad value, since that is where a
  new parameter goes wrong in ways a diff does not show.

## What was left out of the build set, and why

The build set is sized to 600 words, the floor for a guide whose hand-written
form is shorter: nine questions, 510 words asked for, none under 50 and the
macro table at 70. The first build set had seven questions of 30 to 45 words
for a 300-word guide, and the answers came out as fragments that meant nothing
without the question, so the extra room went to the answers first and to new
questions second. Kept: the macros side by side (prefix, sysfs, modular builds;
every reader wrong somewhere), the order of parsing, matching together with
what a handler is given, return values, lifetime of the string, the
documentation rule and the entry format (which also carries where the list and
its tags are). Name matching was folded into the handler-arguments question.
Added back from the measurement set, as worded there: the environment of early
handlers (readers A and B had static keys wrong, and whether an architecture
calls `jump_label_init()` before it parses shows in no diff), and the value
helpers (every reader had `kstrtobool()` and `memparse()` wrong, and nearly
every new handler calls one of them). Left out: the file table (readers A and
C know it, and the other answers name the files), repeated names, unclaimed
words (the next to add if there were room; the return-values answer already
says when a word goes on to init and when it is dropped), levelled parameters,
the sysfs side, the two flags, unknown module parameters, quoting, bootconfig,
sysctl settings, the built-in command line, options read before early parsing,
and the other users of the parser. Several of those are where every reader was
wrong, but they are narrow, and a reviewer who needs them is already reading
`kernel/params.c` or `init/main.c`.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader-A           56        32%      5      9   6.12 to 6.12
reader-B           74        80%      0     26   6.10 to 6.12
reader-C           44        19%     12      3   6.12 to 6.15

question                              reader-A      reader-B      reader-C   verdict
bootparams.core-files                  3% ( 2)      48% ( 5)       8% ( 1)   weak: reader-B
bootparams.defining-macros            27% ( 4)      67% ( 3)      25% ( 4)   weak: reader-B
bootparams.parse-order                19% ( 1)      88% ( 4)      12% ( 3)   weak: reader-B
bootparams.early-environment          45% ( 3)      89% ( 1)      32% ( 1)   weak: reader-A, reader-B
bootparams.handler-arguments          50% ( 2)      88% ( 1)       6% ( 1)   weak: reader-A, reader-B
bootparams.return-values              31% ( 3)      71% ( 2)      11% ( 1)   weak: reader-B
bootparams.name-matching              14% ( 3)      93% ( 1)      47% ( 1)   weak: reader-B, reader-C
bootparams.duplicate-names            17% ( 1)      65% ( 3)      31% ( 2)   weak: reader-B
bootparams.unknown-words              37% ( 1)      83% ( 2)       6% ( 1)   weak: reader-B
bootparams.string-lifetime            20% ( 1)      85% ( 2)      29% ( 2)   weak: reader-B
bootparams.levelled-params            11% ( 1)      88% ( 2)       0% ( 0)   weak: reader-B
bootparams.sections-and-modules       21% ( 1)      80% ( 1)      22% ( 1)   weak: reader-B
bootparams.builtin-module-params      30% ( 1)      74% ( 3)       7% ( 2)   weak: reader-B
bootparams.sysfs-side                 32% ( 3)      85% ( 3)       2% ( 1)   weak: reader-B
bootparams.unsafe-and-hw               8% ( 1)      77% ( 2)       4% ( 1)   weak: reader-B
bootparams.module-unknown             45% ( 2)      92% ( 3)      26% ( 2)   weak: reader-A, reader-B
bootparams.value-helpers              16% ( 5)      64% ( 5)      16% ( 2)   weak: reader-B
bootparams.quoting                    56% ( 2)      81% ( 3)      36% ( 3)   weak: reader-A, reader-B
bootparams.bootconfig                 57% ( 2)      88% ( 4)      27% ( 2)   weak: reader-A, reader-B
bootparams.sysctl-on-cmdline          45% ( 1)      80% ( 2)       5% ( 1)   weak: reader-A, reader-B
bootparams.builtin-cmdline            68% ( 2)      97% ( 2)      19% ( 1)   weak: reader-A, reader-B
bootparams.before-early               42% ( 2)      86% ( 3)      47% ( 3)   all weak
bootparams.doc-file                   36% ( 2)      78% ( 3)      17% ( 1)   weak: reader-B
bootparams.doc-entry                  14% ( 1)      72% ( 4)       2% ( 1)   weak: reader-B
bootparams.doc-rule                   39% ( 3)      75% ( 3)      13% ( 2)   weak: reader-B
bootparams.parser-users               56% ( 6)      92% ( 7)      57% ( 4)   all weak
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `bootparams.name-matching`, `bootparams.unknown-words`, `bootparams.builtin-module-params`, `bootparams.doc-file`.

## Questions reorganised

Grouped by subject: defining a parameter, parsing at boot, documenting a parameter. 15 questions
became 13.
Merged: `bootparams.handler-arguments` and `bootparams.name-matching` into
`bootparams.matching-and-arguments` (both asked about prefix matching); `bootparams.doc-entry` and
`bootparams.doc-file` into `bootparams.doc-list` (both asked where the list and its tags are).
`bootparams.value-helpers` asks how each helper reports a bad value, not which helpers exist, and
`bootparams.return-values` also asks what becomes of the arguments for init after an error, which
every reader had wrong. Nothing was dropped.

- `if_changed`, `if_changed_dep`, `if_changed_rule`: read only `$?`, `$^` and
  `$@` themselves; `$<` and `real-prereqs` matter only where `cmd_<name>`
  uses them.
- `if_changed_rule`: the comparison is against `cmd_<name>` with the same
  `<name>` as `rule_<name>`, so where `cmd_<name>` is defined `rule_<name>`
  must save that command, through `cmd_and_fixdep` or `cmd_and_savecmd`; see
  `rule_cc_o_c` in `scripts/Makefile.lib`.
- `echo-cmd`: not defined for Kbuild; it is defined only in
  `tools/build/Build.include`. `cmd` in `scripts/Kbuild.include` prints the
  log line.
- `if_changed_dep`: the command must write `$(depfile)`; `read_file()` in
  `scripts/basic/fixdep.c` exits with status 2 when the depfile, or a file
  listed in it, cannot be opened, and the recipe fails.
- `check-FORCE`: the warning is part of the recipe, so it prints only on a
  build where make already runs the recipe; a rule without `FORCE` whose
  prerequisites are older than the target prints nothing.
- Phony prerequisites: must be in the `PHONY` variable (`PHONY += name`), not
  only under `.PHONY:`; `newer-prereqs` filters `$?` by `$(PHONY)`, and a
  name left in it reruns the command on every build.
- `targets`: selects which `.cmd` files are read (and what
  `scripts/Makefile.clean` removes); it does not cause the target to be
  built. See the `$(obj)/:` rule in `scripts/Makefile.build`.
- Automatic `targets` entries beyond the `obj-y` family: for example
  `userprogs`, the `dtb-y` primitives, `MAKECMDGOALS`, and files derived by
  `intermediate_targets` such as `.asn1.c`, `.lex.c`, `.tab.c`.
- Makefiles not run through `scripts/Makefile.build`: must read the `.cmd`
  files themselves; search for `existing-targets` to see the block most of
  them repeat, for example in `scripts/Makefile.modpost`.
- **Potentially unsafe usage**: a `targets` entry that carries `$(obj)/`.
  - Unsafe: in a kbuild file read by `scripts/Makefile.build` with `$(obj)`
    other than `.`; `targets := $(addprefix $(obj)/, $(targets))` prefixes it
    again, no file matches, the `.cmd` file is never read and the target is
    rebuilt on every build.
  - Safe: stripping the prefix first, as
    `targets += $(patsubst $(obj)/%,%,$(vmlinux-objs-y))` does in
    `arch/x86/boot/compressed/Makefile`.
  - Safe: in a fragment included after that line, such as
    `scripts/Makefile.host`, where `targets += $(host-csingle)` appends names
    that already carry the prefix.
  - Safe: in a standalone makefile such as `scripts/Makefile.asm-headers`,
    where `targets := $(syscall-y)` holds prefixed names; it does no
    prefixing and uses the names as written.
- Several targets in one rule: a static pattern rule over a list, such as
  `$(host-cobjs): $(obj)/%.o: $(obj)/%.c FORCE` in `scripts/Makefile.host`,
  runs once per target with its own `$@` and `.cmd` file; each member must be
  in `targets`.
- Two `if_changed` calls in one recipe: both write `savedcmd_$@` to the same
  file, so on the next run the call that did not write last sees a changed
  command and reruns without the other.

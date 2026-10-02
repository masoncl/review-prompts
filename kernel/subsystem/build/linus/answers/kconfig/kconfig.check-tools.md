- Two scripts do this job; there is no "checkkconfigsymbols" make target.

| | `scripts/kconfig/kconfig-sym-check.pl` | `scripts/checkkconfigsymbols.py` |
|---|---|---|
| Run as | `make kconfig-sym-check` | by hand, from the top of a git checkout |
| Scans | Kconfig files only | Kconfig files, plus `CONFIG_` names in the other tracked files outside `tools/` |
| Kconfig lines read | `default`, `def_bool`, `def_tristate`, `select`, `imply`, `depends on`, `visible if`, `range`, `if`, and the condition after a type or `prompt` | lines that start with `if`, `select`, `imply`, `depends on` or `default` |
| git | not needed; falls back to `find` | needed, for `git ls-files` |
| Output | bare names on stdout, no file names | name, referencing files, similar symbols |
| Exit status | 1 if any name is reported, so the make target fails | 0 even when names are reported |

- `KCONFIG_SYM_CHECK_EXCLUDES`: optional make variable for
  `kconfig-sym-check`, naming a file of symbol names to accept, one per line,
  `#` for comments.
- No exclude file ships in the tree.
- `scripts/kconfig/kconfig-sym-check.pl` adds a hint when the name is `N`, `Y`
  or `M`: the tristate literals are lowercase.
- `scripts/checkkconfigsymbols.py` has no "--yes" or "--missing" option.
- `--find` lists the commits that touch each reported symbol. It needs
  `--diff`, and `--commit` turns it off.
- `--commit` and `--diff` run `git reset --hard` on the working tree.
- Both scripts count a name as defined if any Kconfig file they read has a
  `config` or `menuconfig` entry for it. Neither knows which files an
  architecture sources.
- `KCONFIG_WARN_UNKNOWN_SYMBOLS` checks the input `.config`, not references. It
  is exported when the make variable `W` (`KBUILD_EXTRA_WARN`) contains `c`;
  see `scripts/kconfig/Makefile`.
- `KCONFIG_WARN_UNKNOWN_SYMBOLS` stays silent for a `.config` name that some
  Kconfig expression references but no entry defines. `sym_find()` in
  `conf_read_simple()` returns the `S_UNKNOWN` symbol the reference created,
  and the line is dropped.
- The configurators have no check of their own for undefined references. The
  few warnings that can appear are listed under "Value of an undefined symbol".

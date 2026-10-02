- The validator is `tools/docs/get_abi.py`, with subcommands `rest`,
  `validate`, `search` and `undefined`; there is no get_abi script under
  `scripts/`.
- The parser is `AbiParser` in `tools/lib/python/abi/abi_parser.py`;
  `Documentation/sphinx/kernel_abi.py` runs the same parser and
  `check_issues()` during the docs build.
- `Documentation/Makefile` runs `get_abi.py validate` only when
  `CONFIG_WARN_ABI_ERRORS` is set; that option is inside `if COMPILE_TEST` in
  `Documentation/Kconfig`.
- `AbiParser` warns on, for example: a `Where:` tag, an unknown tag directly
  after a field other than `Description:`, an entry with no `Description:`,
  and one `What:` defined in more than one file.
- An unknown field name after `Description:` is taken as description text,
  with no warning.
- Nothing in the parser compares entries with kernel code; only `undefined`
  does a comparison, against a mounted sysfs.
- `scripts/checkpatch.pl` has no check for a missing ABI entry.
- `stable/` in `Documentation/ABI/README`: backward compatibility for at least
  2 years, not forever.
- `testing/` in `Documentation/ABI/README`: features may be added, but the
  current interface must not break except for grave errors or security
  problems.

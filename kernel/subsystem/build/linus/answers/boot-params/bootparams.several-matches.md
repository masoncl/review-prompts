- `__setup()` strings that overlap as prefixes: each matching entry is called
  in table order; the first to return non-zero ends the walk, so a shorter
  string linked earlier can claim a word meant for a longer one.
- Early entry in `obsolete_checksetup()`: not called; if its string equals the
  word's name (next character `\0` or `=`) it sets `had_early_param`.
- `had_early_param`: is the return value when no `__setup()` handler claimed
  the word, so the word counts as handled and is not passed to init.

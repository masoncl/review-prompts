- Every rejected form below: a syntax error, counted in `yynerrs`;
  `conf_parse()` in `scripts/kconfig/parser.y` exits 1 right after
  `yyparse()`.

| Form | Accepted | In this tree |
|---|---|---|
| option line | no | no token in `scripts/kconfig/lexer.l`; the word lexes as `T_WORD` |
| optional in a choice | no | no token; `choice_option` has only `prompt` and `default` |
| name after `choice` | no | the rule is `choice: T_CHOICE T_EOL` |
| type line in a choice, with or without prompt text | no | `choice_option_list` has no `type` rule |
| dashed spelling of `help` | no | lexer class `n` contains `-`, so the whole word is one `T_WORD`, not `T_HELP` |
| `source "path"` | yes | the only form of `source` |
| relative or optional `source` variants | no | only `"source"` returns `T_SOURCE` |

- Choice type: the `choice` rule sets `S_BOOLEAN` itself.
- Choice prompt: written only as `prompt "text"`; the header also takes
  `default`, `depends on` and `help`.
- `source` path: `zconf_fopen()` tries it as given, then under `srctree`
  if it is not absolute; never relative to the including file.

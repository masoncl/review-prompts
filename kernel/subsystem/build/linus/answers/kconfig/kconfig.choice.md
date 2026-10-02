| Refused | Checked in | Result |
|---|---|---|
| choice with no `prompt` | `choice_entry` rule | error |
| member with no prompt | `config_stmt` rule | error |
| member whose type is not `S_BOOLEAN`, including no type line | `config_stmt` rule | error, "choice member must be bool" |
| member with `default` or `def_bool` | `choice_check_sanity()` | error |
| member with a prompt in another entry | `choice_check_sanity()` | error, "choice value must not have a prompt in another entry" |
| anything but `config`, `comment`, `if` inside the choice, `source` included | `stmt_list_in_choice` | error, "invalid statement" |
| choice `default` naming a non-member | `sym_check_prop()` in `scripts/kconfig/menu.c` | warning only, via `prop_warn()` |

- `choice_check_sanity()`: defined in `scripts/kconfig/parser.y`; it checks
  only the two rows that name it.
- Error counter: `yynerrs`, which `conf_parse()` increments when
  `choice_check_sanity()` returns -1.
- `conf_parse()` exits twice: after `yyparse()` for the grammar-rule rows,
  then after `menu_finalize()` for `choice_check_sanity()`. Grammar errors
  hide the later messages.
- `select` in a member: no choice-specific check.
- Tristate choices: none; `sym_calc_choice()` in `scripts/kconfig/symbol.c`
  sets each visible member to `yes` or `no`, never `mod`.
- No member set: only when no member is visible, as long as every choice
  `default` names a member. `sym_calc_choice()` tests member visibility, not
  the choice's own.
- Winner, in `sym_calc_choice()`, first match wins:
  1. first visible member in `choice_members` order with user value `y`;
  2. `sym_choice_default()`, unless the user set that member to `n`;
  3. first visible member in menu order with no user value;
  4. last visible member in `choice_members` order.
- Losing members set `y` in the file: no message by default; with
  `KCONFIG_WARN_CHANGED_INPUT` set to a non-empty value, `conf_write()` in
  `scripts/kconfig/confdata.c` lists them.

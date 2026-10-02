- Front-end programs: `conf`, `mconf`, `nconf`, `qconf`, `gconf`; `menuconfig`,
  `xconfig` and `gconfig` are make targets, mapped in
  `scripts/kconfig/Makefile`.
- `conf_write_autoconf()` in `scripts/kconfig/confdata.c`: also writes
  `include/generated/rustc_cfg`.
- Choice: a `struct symbol` whose `name` is NULL, tested by `sym_is_choice()`;
  there is no SYMBOL_CHOICE flag.
- Choice symbol: `sym_lookup(NULL, 0)` allocates a new one for each `choice`
  block, so it has exactly one `struct menu`.
- Choice state: the member list `choice_members` lives on the choice's
  `struct menu`, not on its symbol; `sym_calc_choice()`,
  `sym_choice_default()` and `choice_set_value()` take the menu node and
  return or accept the member symbol.
- Choice to members: two routes. `menu_for_each_sub_entry()` gives Kconfig
  order; the `choice_members` list (linked through `choice_link` in each
  member) gives priority order, which, for example, `choice_set_value()` and
  `conf_read_simple()` reorder with `list_move()`.
- Member to choice: `sym_get_choice_menu()` walks `parent` from the member's
  node that has a prompt; `sym_is_choice_value()` tests `choice_link` instead.
- Unquoted literal such as a number in `range` or `default`: an ordinary
  `struct symbol` of type `S_UNKNOWN` without `SYMBOL_CONST`;
  `sym_calc_value()` gives it its own name as string value.
- Quoted word: a separate `struct symbol` with `SYMBOL_CONST`, in the same
  hash table as a non-constant symbol of the same name.
- `enum prop_type`: has no help and no choice kind; help text is `help` on
  `struct menu`, one per definition site.
- `struct property` of a node without a symbol (`menu`, `comment`,
  `rootmenu`): on no symbol's list; reachable only through `menu->prompt`.
- `struct property` fields: `expr` is the payload (default value, selected
  symbol, range pair) and `visible.expr` is the `if` condition; the comment
  on `expr` in `scripts/kconfig/expr.h` says otherwise, see
  `menu_add_prop()` in `scripts/kconfig/menu.c`.
- `visible if` of enclosing menus: ANDed at parse time by `menu_add_prompt()`
  into a prompt added as `P_PROMPT`, and into no other property kind; a
  `menuconfig` prompt is added as `P_PROMPT` and retyped `P_MENU` afterwards,
  so it has them too.
- `dep` of the node and its ancestors: ANDed into every property condition of
  that node later, by `_menu_finalize()`.
- `dir_dep` is not built for a choice that has entries, or for a direct child
  of a choice node.
- Menu tree after `menu_finalize()`: children of a promptless node are moved
  up to follow it as siblings, so an `if` node (`M_IF`) ends up with no
  children.
- `struct expr`: interned; `expr_lookup()` in `scripts/kconfig/expr.c` is the
  only allocator and returns the existing node for an equal (type, left,
  right), so pointer equality means structural equality.
- `struct expr` nodes are never freed, and their `type`, `left` and `right`
  never change; the transform helpers, for example `expr_transform()` and
  `expr_eliminate_dups()`, return a node and leave the node they were given
  as it was.
- `struct expr` value: each node caches its tristate result until
  `expr_invalidate_all()`, which `sym_clear_all_valid()` calls.
- `struct file`: private to `scripts/kconfig/util.c`; `file_lookup()` uses it
  to intern file names and to exit on a repeated inclusion.
- Include stack: `struct buffer` in `scripts/kconfig/lexer.l`; `struct menu`
  and `struct property` hold only a `filename` string and a `lineno`.
- There is no struct kconf_id in this tree.

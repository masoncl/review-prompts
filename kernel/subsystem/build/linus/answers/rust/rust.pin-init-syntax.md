| Macro | Defined in | Pinned | Error type |
|---|---|---|---|
| `pin_init!` | `pin_init` crate | yes | `Infallible`, or `? Type` |
| `init!` | `pin_init` crate | no | `Infallible`, or `? Type` |
| `try_pin_init!` | `kernel`, `rust/kernel/init.rs` | yes | `Error`, or `? Type` |
| `try_init!` | `kernel`, `rust/kernel/init.rs` | no | `Error`, or `? Type` |

- All four macros: accept the same syntax, `? Type` included; a `try_` macro
  differs from its plain form only in the default error type.
- `pin_init!` and `init!` with `? Type`: fallible; `pin_init!(Foo { .. }? Error)`
  is valid.
- `pin_init` crate: defines no `try_pin_init!` and no `try_init!`.
- `kernel` crate: defines no `pin_init!` and no `init!`; the names in
  `rust/kernel/prelude.rs` are the `pin_init` crate's, with default
  `Infallible`.
- `try_pin_init!` and `try_init!`: exported from `kernel` and from the prelude;
  each forwards to the macro without `try_`.
- Zeroing trailer: only `..Zeroable::init_zeroed()` is accepted, see
  `get_init_kind()` in `rust/pin-init/internal/src/init.rs`.
- `..Zeroable::zeroed()` inside a macro: rejected; that spelling belongs to
  plain struct expressions, as in `rust/kernel/iommu/pgtable.rs`.
- `&this in` before the path: works in all four macros; binds a `NonNull` to
  the struct being initialized.
- Field names: must be identifiers, so a field of a tuple struct cannot be
  named.
- Field bindings: after each field, a `let` of the field's name is in scope for
  the rest of the initializer.
- Binding type in `pin_init!` and `try_pin_init!`: `Pin<&mut T>` for a `#[pin]`
  field, `&mut T` otherwise.
- Binding type in `init!` and `try_init!`: `&mut T` for every field.
- Binding shadows an outer variable of the same name: after `request,` a later
  `request.irq` reads the field, as in `Registration::new()` in
  `rust/kernel/irq/request.rs`.

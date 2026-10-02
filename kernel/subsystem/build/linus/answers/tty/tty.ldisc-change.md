- Fallback order in `tty_ldisc_restore()`: the old ldisc number, then `N_TTY`,
  then `N_NULL`, then `panic()`.
- Restored old ldisc: a new `struct tty_ldisc` from `tty_ldisc_get()`, opened
  again after its `close` already ran, with `tty->disc_data` NULL and
  `tty->receive_room` 0; the previous ldisc state is gone.
- `tty_set_ldisc()` return value after a successful restore: still the error
  from the new ldisc's `open`.
- Console test in `__tty_hangup()`: an open file whose `write_iter` is
  `redirected_tty_write()`.

| open files at hangup | `tty_ldisc_hangup()` does | `tty->ldisc` after |
|---|---|---|
| console among them | `tty_ldisc_reinit()`: `tty->termios.c_line`, then `N_TTY`, then `N_NULL` | new instance |
| no console | `tty_ldisc_kill()` | NULL |

- Hangup callbacks: `flush_buffer`, `write_wakeup` and `hangup` run first,
  under `tty_ldisc_ref()`, before the write side is taken.
- Hangup while the trylock fails: all three callbacks are skipped; the kill or
  reinit still happens.
- `tty_ldisc_setup()`: never sets `tty->ldisc` to NULL, also when `open`
  fails.
- `tty_ldisc_reinit()`: sets `tty->ldisc` to NULL only when the new `open`
  fails; it stays NULL until a later `tty_ldisc_reinit()` succeeds.
- Changes of `tty->ldisc` in `tty_ldisc_reinit()`: made on the write side of
  `tty->ldisc_sem`, so a reference holder never sees one.
- `tty_reopen()` after a hangup without console: tries only
  `tty->termios.c_line`, with no `N_TTY` fallback; on failure the open fails
  and `tty->ldisc` stays NULL.

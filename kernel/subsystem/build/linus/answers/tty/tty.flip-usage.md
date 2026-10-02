- **Potentially unsafe usage**: inserting into, or pushing, one
  `struct tty_port` from more than one context.
  - Unsafe: when two of the contexts can run at the same time and share no
    lock; `__tty_buffer_request_room()` and `__tty_insert_flip_string_flags()`
    update `port->buf.tail` and `tail->used` with plain stores and take no
    lock.
  - Safe: one lock held across the insert and the commit, as
    `tty_insert_flip_string_and_push_buffer()` does with `port->lock`.
  - Safe: a single context that cannot run concurrently with itself and holds
    no lock, as `max310x_handle_rx()` in `drivers/tty/serial/max310x.c`,
    reached only from the threaded handler `max310x_ist()`.
- `uart_insert_char()` in `drivers/tty/serial/serial_core.c`: neither takes nor
  asserts the `struct uart_port` lock; the caller supplies the serialisation.
- `tty_insert_flip_string_and_push_buffer()`: `port->lock` covers the insert
  and the commit only; the work is queued after the unlock, also when nothing
  was inserted.
- `tty_insert_flip_string_and_push_buffer()` is declared in
  `drivers/tty/tty.h` and not exported, so modules cannot call it.
- `tty_buffer_request_room()` and `tty_insert_flip_string_and_push_buffer()`
  return `int`, never negative; the other insert functions return `size_t`.
- `__tty_buffer_request_room()` when allocation fails: returns the room left
  in the current tail, but 0 if the caller needs flag bytes and the tail has
  none.
- When allocation fails and the tail has no flag bytes, a character with a
  flag other than `TTY_NORMAL` is dropped while `TTY_NORMAL` bytes still fit
  in the room the tail has left, except through
  `tty_insert_flip_string_flags()`, which always needs flag bytes.
- `tty_prepare_flip_string()`: adds the returned length to `tail->used` before
  the driver has written the bytes; the next commit publishes all of them,
  written or not.
- `buf_overrun` is a field of `struct uart_icount` in `struct uart_port`;
  `struct tty_port` has no counter and the tty core counts nothing for a short
  insert.

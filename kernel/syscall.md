- Adding arguments to an existing syscall breaks the ABI.
- If you need more data, add a new syscall number or use an extensible struct
  argument with a size/flags field; never change existing arguments in place.

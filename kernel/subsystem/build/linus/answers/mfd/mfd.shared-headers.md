- Private headers: the files matched by `drivers/mfd/*.h`. None of them has a
  name that starts with "tps".
- `include/linux/mfd/tps6594.h` and `include/linux/mfd/tps65010.h`: shared
  headers, not private ones.
- No source file or Makefile outside `drivers/mfd/` reaches a header in
  `drivers/mfd/`: there is no `../mfd/` include and no include path that names
  the directory. A child driver in another directory can only use what is
  under `include/`.

- `kstrtobool()`: also accepts `e` and `E` as true, `d` and `D` as false, on
  the first character alone.
- `memparse()` suffix with no number before it (for example `K`): the suffix
  is not consumed; the result is 0 and `*retptr == ptr`.

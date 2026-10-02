- Tests in use: `if (_T)`, `if (!IS_ERR_OR_NULL(_T))`, `if (!IS_ERR(_T))`, and
  no test.
- `_T >= 0`: no `DEFINE_FREE()` uses it; it is the test in
  `DEFINE_CLASS(get_unused_fd, ...)` in `include/linux/file.h`.
- `if (!IS_ERR(_T))` wrappers: `mntput` and `mnt_ns_release` in
  `fs/namespace.c`, `x509_free_certificate` in
  `crypto/asymmetric_keys/x509_parser.h`; each release function tests NULL
  itself.
- `fwnode_handle` in `include/linux/property.h`: no test in the wrapper;
  `fwnode_handle_put()` skips both NULL and error pointers through
  `fwnode_has_op()` in `include/linux/fwnode.h`.
- Wrapper with no test: what the release function accepts decides, for NULL and
  for error pointers alike; `release_firmware()` in
  `drivers/base/firmware_loader/main.c`, behind the `firmware` wrapper in
  `include/linux/firmware.h`, and `free_percpu()` test NULL only.
- `dput()`: has no `DEFINE_FREE()` wrapper in this tree.
- Finding a definition: search for `DEFINE_FREE(name,`; if nothing matches,
  search for `__free_name`, since some cleanup functions are written by hand.
- Hand-written cleanup functions: `__free_path_put` (see "Types other than
  pointers"), `__free_klistmount_free()` in `fs/namespace.c`,
  `__free_klistns_free()` in `kernel/nstree.c`; each gets the address of the
  variable and has no `_T`.

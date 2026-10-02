- Tree check: only `checked-configs` is tested; the error text says to run `make
  oldconfig && make prepare`, not `modules_prepare`.
- `prepare`: replaced by a rule that only prints warnings when
  `CC_VERSION_TEXT` or `PAHOLE_VERSION` differ from the kernel's; its recipe
  never fails.
- `outputmakefile`: still a prerequisite of `prepare`; with a separate output
  directory it fails if `$(srcroot)/modules.order` exists, and writes `Makefile`,
  a `source` symlink and `.gitignore` there.
- `KBUILD_MODULES`: set to `y`, not 1; `KBUILD_BUILTIN` is empty.
- modpost `-i` dumps: only `$(objtree)/Module.symvers` plus
  `KBUILD_EXTRA_SYMBOLS`; `vmlinux.symvers` is not read.
- modpost `-e`: `add_header()` leaves out `MODULE_INFO(intree, "Y")`.
- BTF: `%.ko` in `scripts/Makefile.modfinal` has no `$(objtree)/vmlinux`
  prerequisite because `KBUILD_BUILTIN` is empty; `cmd_btf_ko` prints a skip
  message when `vmlinux` is absent.
- `modules_install`: installs under `$(MODLIB)/$(INSTALL_MOD_DIR)`, default
  `updates`; the `depmod` target still runs.
- `modules_install` leaves out: removing `$(MODLIB)/kernel`, the `build` symlink,
  and installing `modules.order` and `modules.builtin`.
- Signing in `modules_install`: under `KBUILD_EXTMOD` `cmd_sign` ends in
  `|| true`, so a signing failure does not stop the install.
- `CONFIG_MODULES` unset: `modules` and `modules_install` fail through
  `__external_modules_error`.
- Targets: everything inside the `ifeq ($(KBUILD_EXTMOD),)` block of the
  top-level `Makefile` is absent; targets after it still work, for example
  `nsdeps`, `compile_commands.json` and single targets, though `help` lists only
  `modules`, `modules_install`, `clean` and `rust-analyzer`.

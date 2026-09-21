# nfs.conf and the conffile parser

Applies to `support/nfs/conffile.c`, `support/include/conffile.h`,
`tools/nfsconf/`, and every caller of `conf_get_*`.

`conffile.c` is an OpenBSD-derived INI parser. It backs `/etc/nfs.conf`, and
also `/etc/nfsmount.conf` via `mount_config.h` (see `mount.md`). Almost every
daemon calls `conf_init_file(NFS_CONFFILE)` at startup, so a change here
affects the whole package.

## Format

```ini
[section]
[section "arg"]
tag = value          # or ';' comment
long = value \
       continued
include /path/to/more.conf
include -optional /path/that/may/not/exist
```

Parsed by `conf_parse_line()`. It works by `strchr()` plus in-place NUL
insertion, and it checks for `NULL` after **every** `strchr()` for `]`, `"`,
`'` and `=`. Off-by-one and unbalanced-quote bugs are easy to introduce here;
a change to the tokeniser needs the malformed-input cases walked explicitly,
not assumed.

## API

```c
char *conf_get_str(const char *section, const char *tag);
char *conf_get_str_with_def(const char *section, const char *tag, char *def);
char *conf_get_section(const char *section, const char *arg, const char *tag);
char *conf_get_entry(const char *section, const char *arg, const char *tag);
int   conf_get_num(const char *section, const char *tag, int def);
_Bool conf_get_bool(const char *section, const char *tag, _Bool def);
struct conf_list *conf_get_list(const char *section, const char *tag);
struct conf_list *conf_get_tag_list(const char *section, const char *tag);
void  conf_free_list(struct conf_list *);
struct sockaddr *conf_get_address(const char *section, const char *tag);
```

- **`conf_get_str()` and friends return a pointer into the parser's own
  storage.** Do not free it, and do not hold it across `conf_cleanup()` or a
  reload. Code that needs to keep a value must `strdup()` it.
- **`conf_get_list()` must be paired with `conf_free_list()`.** This is a
  common leak on an early-return path.
- `conf_get_entry()` is the raw accessor — it does **not** do the `$`
  expansion described below. Choosing between it and `conf_get_section()`
  changes behaviour; a patch that swaps one for the other is a semantic change,
  not a cleanup.

## Gotcha 1: `$` values are a silent indirection

`conf_get_section()` treats any value whose first character is `$` as a lookup
rather than a literal:

```c
if (cb->value[0] == '$') {
	/* expand $name from [environment] section, or from environment */
	char *env = getenv(cb->value + 1);
	if (env && *env)
		return env;
	section = "environment";
	tag = cb->value + 1;
	goto retry;
}
```

The process environment wins over the `[environment]` section. Consequences to
check:

- A value that legitimately starts with `$` cannot be expressed.
- A daemon's configuration can be influenced by its environment. For anything
  privileged, that is worth thinking about — check what the systemd unit
  passes in.
- The `goto retry` re-runs the lookup; a chain of `$` values can loop. There is
  no depth limit.

## Gotcha 2: case handling

Section names are lower-cased on insert (`upper2lower()` in `conf_set()`) and
all four comparisons in `conf_get_section()` use `strcasecmp()` — including
the sub-section **`arg`**:

```c
if (arg && (cb->arg == NULL || strcasecmp(arg, cb->arg) != 0))
	continue;
```

That means a per-export or per-client sub-section name is matched
case-insensitively even though the underlying object (a filesystem path, a
hostname in some contexts) may be case-sensitive. When reviewing a new
sub-sectioned option, decide whether case-insensitive matching is actually
correct for that key, and say so.

## Gotcha 3: load order defines override precedence

`conf_init_file()`:

```c
/* If the config file is in /etc (normal) then check
 * /usr/etc first.  Also check config.conf.d for files
 * names *.conf.
 *
 * Content or later files always over-rides earlier
 * files.
 */
```

Effective order: `/usr/etc/nfs.conf`, `/usr/etc/nfs.conf.d/*.conf`,
`/etc/nfs.conf`, `/etc/nfs.conf.d/*.conf`. Later wins. Drop-in directories are
scanned by `conf_init_dir()`, which accepts only names ending in `.conf`,
sorts with `versionsort()`, and caps the constructed path at `PATH_MAX`.

**This ordering is a documented guarantee.** A patch that reorders the loads,
or that adds a new source in the middle, changes which file wins for every
existing deployment. It needs to be deliberate and called out.

`conf_set_now()` warns about a duplicate tag only when `override` is false, so
the legitimate override case is silent by design — do not "fix" the missing
warning.

## Gotcha 4: file locking

- `conf_readfile()` takes `flock(fd, LOCK_SH)` before sizing and reading, so it
  never observes a half-rewritten file.
- `conf_write()` takes `flock(fd, LOCK_EX)` before rewriting.

Any new reader or writer of `nfs.conf` that bypasses these helpers bypasses
the locking discipline and can race `nfsconf --set`. Reuse the helpers.

Note `conf_readfile()` sizes the file with `lseek(fd, 0, SEEK_END)` into an
`off_t`. `AC_SYS_LARGEFILE` makes that 64-bit; do not narrow it to `int` or
`long`.

## Adding a new option

A new `nfs.conf` option is a user-visible interface. Check that the patch:

- [ ] Documents it in `systemd/nfs.conf.man`.
- [ ] Supplies a default that preserves existing behaviour, via the `_with_def`
      / `def` argument rather than a separate `if (!value)` branch.
- [ ] Puts it in the right section, and does not collide with an existing tag
      in that section.
- [ ] Uses `conf_get_bool()`/`conf_get_num()` rather than parsing the string
      itself, so the accepted spellings stay consistent.
- [ ] Frees a `conf_get_list()` result on every path.
- [ ] Does not retain a `conf_get_str()` pointer past a reload.
- [ ] Is honoured on the reload path too, if the daemon supports `SIGHUP`
      reload — otherwise the option only works at startup, which should be
      documented.
- [ ] Is covered by `tests/nfsconf/` if it changes parser behaviour. Note that
      `tests/t0002-nfsconf.sh` exists but is **not** wired into `TESTS` in
      `tests/Makefile.am` and references a `nfsconftool` binary that nothing
      builds — do not assume it runs.

## Netlink interaction

`nfs.conf` carries `no-netlink` options for the `mountd` and `exportd` stanzas
that force the `/proc` fallback instead of the kernel netlink interface. A
change to either export path must keep both working; see `export.md` and
`netlink.md`.

# Subsystem Guide Index

A subsystem guide lists where this kernel tree differs from what you are
likely to believe:

- names that are gone, and what does the job now
- what a function requires, returns and locks
- `**Unsafe usage**:` and `**Potentially unsafe usage**:` rules, each with the
  safe usage beside it

A guide does not explain its subsystem. Where a guide says nothing, what you
already know is probably right.

## Subsystem Guides

### Find the build directory

The built guides are in build directories, in `build/` beside this file. There
can be several. One of them is always there:

```
review-prompts/kernel/subsystem/build/linus/
```

Each build directory holds the guides built from one kernel tree,
`subsystem-guide-index.txt`, and `kernel-version.yaml`. The line `kernel:` in
that file is the release of the tree, and the line `sha:` is its commit.

| Directory | Which tree its guides are from |
|---|---|
| `build/linus/` | the most recent tree of Linus Torvalds's that was scanned. `linus` is not a release, and the directory is rebuilt as that tree moves on |
| any other, such as `build/v6.18.y/` | a tree of the series that its name gives. `v6.18.y` is the stable series of `v6.18`: `v6.18` itself, `v6.18.1`, `v6.18.2` and so on |

If the prompt that started this review names a build, use that directory.
Otherwise choose one:

1. Find the release of the tree under review. The first lines of its
   `Makefile` give it:

   ```
   VERSION = 7
   PATCHLEVEL = 3
   SUBLEVEL = 0
   EXTRAVERSION = -rc5
   ```

   That tree is at `v7.3-rc5`.

   | `SUBLEVEL` | `EXTRAVERSION` | The release |
   |---|---|---|
   | 0 | `-rc5` | `v7.3-rc5` |
   | 0 | empty | `v7.3` |
   | 2 | empty | `v7.3.2` |

2. List the directories in `build/`, and read `kernel-version.yaml` in each.
3. Choose the directory whose kernel best suits the tree under review. For
   example, `build/v6.18.y/` suits a tree at `v6.18.7`.
4. Say which one you chose, by the name of the directory:

   ```
   Build directory: linus, built from v7.3-rc5; tree under review: v7.3-rc5
   ```

A guide describes the tree it was built from. If that release is not the
release of the tree under review, look up each name in the tree before you
rely on what a guide says about it.

> **Path resolution:** `subsystem-guide-index.txt` and every guide named below
> are in **the build directory you chose**. For example, with `build/linus/`,
> `subsystem-guide-index.txt` resolves to
> `review-prompts/kernel/subsystem/build/linus/subsystem-guide-index.txt`.
> The guides under "Guides written by hand" and `subjective-review.md` are
> beside this file, and `callstack.md` is in `review-prompts/kernel/`.

### Search the index for what the patch touches

A guide is a list of answers, and each answer has a title.
`subsystem-guide-index.txt` has one line for each answer of every guide:

```
## <section> ### <title>, <guide>:<line>, <source file>, <symbols>
```

| Part of the line | What it holds |
|---|---|
| `<section>` and `<title>` | the section and the title that the answer is under in its guide |
| `<guide>:<line>` | the guide, and the line where the answer starts |
| `<source file>` | the kernel file that the answer is mostly about |
| `<symbols>` | every function, macro, structure, field and option that the answer names |

A few lines have no source file or no symbols, and a title can contain a
comma.

The index is long. Search it, and read only the lines that match.

1. List the symbols that the patch touches:
   - each function that it changes
   - each function, macro, structure and field on a line that it adds or
     removes
2. Search the index for every symbol on your list. For example:

   ```
   grep -n -w -F -e 'walk_pmd_range' -e 'walk_pud_range' -e 'ACTION_AGAIN' subsystem-guide-index.txt
   ```

   `-w` matches whole names only, so that `list_for_each_entry` does not also
   find `list_for_each_entry_rcu`.

   If the search finds no answer about the code that the patch changes, search
   for each file that the patch changes:

   ```
   grep -n -w -F -e 'mm/pagewalk.c' subsystem-guide-index.txt
   ```

3. Read the section and the title of each line that matches. Keep the lines
   whose answer is about code that the patch changes or calls.
4. Read each answer that you kept. Open the guide at `<line>` and read to the
   next title, which is the next line that starts with `**` or with `#`.

A search for `walk_pmd_range` finds lines like these. They are shown here
without their line numbers, source file and symbols:

```
## The callback walker ### Walker callbacks, mm-pagetable.md:<line>, ...
## The callback walker ### PMD callbacks and huge entries, mm-pagetable.md:<line>, ...
## The callback walker ### Retrying from a callback, mm-pagetable.md:<line>, ...
```

| The search finds | Do this |
|---|---|
| no line | Go on with the review. The guides say nothing about that code, so what you know is probably right |
| a few lines | Read each answer |
| many lines for one symbol | The symbol is a common helper. Choose by section and title, or search for a second symbol from the patch |

### Guides to load whole

A search of the index can miss what these guides say, since each applies to a
kind of file or a kind of bug. Load the whole guide when its row matches. A
change can match more than one row: load every guide that matches.

| Subsystem | Triggers | File |
|-----------|----------|------|
| Race tracing | any suspected race or use-after-free against asynchronous work; loaded on demand by `callstack.md` | races.md |
| Selftests | tools/testing/selftests/, TEST_PROGS, TEST_FILES, TEST_GEN_FILES | selftests.md |
| Kconfig | a Kconfig file, and in one: `config `, `select `, `depends on `, `tristate `, `bool ` | kconfig.md |
| Build System | Kbuild, Makefile, scripts/, tools/, `gnu11`, `-funsigned-char`, `-fno-strict-aliasing`, and code built with its own flags: arch/*/boot/, drivers/firmware/efi/libstub/, realmode, purgatory, vdso | build.md |
| Rust | any Rust code | rust.md |

### Guides written by hand

These guides have no questions yet, so no build makes them and no index covers
them. They are beside this file, not in a build directory. Load the whole
guide when its row matches.

| Subsystem | Triggers | File |
|-----------|----------|------|
| FUSE | fs/fuse/, fuse_uring_, fuse_chan_, fuse_dev_, FUSE_IO_URING, FUSE_OVER_IO_URING | fuse.md |
| hwmon | drivers/hwmon/, hwmon_*, asus-ec-sensors, ec_board_info | hwmon.md |
| LEDs | drivers/leds/, include/linux/leds.h, led_classdev_register, devm_led_classdev_register | leds.md |
| Media/V4L2 | drivers/media/, include/media/, v4l2_subdev_, V4L2_SUBDEV_, MEDIA_BUS_FMT_ | media.md |
| Multi-Function Devices (MFD) | drivers/mfd/, include/linux/mfd/, mfd_add_devices, devm_mfd_add_devices, mfd_cell, mfd_remove_devices | mfd.md |

## Optional Patterns

Load only when explicitly requested in the prompt:

- **Subjective Review** (subjective-review.md): Subjective general assessment

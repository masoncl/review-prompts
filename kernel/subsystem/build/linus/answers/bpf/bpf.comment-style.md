- Style to use in new BPF code: the general kernel form, with `/*` alone on the
  first line, ` * ` on each following line and ` */` alone on the last.
- Written rule: `Documentation/process/coding-style.rst`, which shows that
  one form. The English file has no exception for `net/` or `drivers/net/`.
- Translations: `Documentation/translations/sp_SP/process/coding-style.rst` and
  `Documentation/translations/zh_TW/process/coding-style.rst` describe a
  separate `net/` form with text on the opening line; they do not match the
  English file.
- BPF documentation: no file under `Documentation/bpf/` states a comment style
  for kernel code. `Documentation/bpf/bpf_devel_QA.rst` and
  `Documentation/process/maintainer-netdev.rst` do not mention it.
- `Documentation/bpf/libbpf/libbpf_naming_convention.rst`: its `/**` rule is
  for libbpf API documentation comments only.
- `scripts/checkpatch.pl`: has no networking-specific comment-style check, and
  no comment check that tests the path for `kernel/bpf/`. Its
  `BLOCK_COMMENT_STYLE` warnings cover the leading `*`, its alignment and the
  trailing `*/`; they accept either opening line.
- Existing code is mixed: files such as `kernel/bpf/liveness.c` and
  `kernel/bpf/rqspinlock.c` mostly use the bare `/*` opening; files such as
  `kernel/bpf/core.c` and `kernel/bpf/verifier.c` mostly put text on the
  opening line. Text on the opening line in surrounding code is not a model
  for new comments.

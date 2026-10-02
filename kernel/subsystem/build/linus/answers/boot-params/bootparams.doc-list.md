- Order: `Documentation/admin-guide/kernel-parameters.rst` defines it as
  "English Dictionary order": ignore all punctuation, digits before letters,
  case insensitive; "alphabetical" alone is not the whole rule.
- Order is not checked by any script, and the list in
  `Documentation/admin-guide/kernel-parameters.txt` is not fully sorted; for
  example `autoconf=` sits between `apicpmtimer` and `apm=`. Place a new
  entry by the rule, not by its neighbours.
- Form stated by the `.rst`: only three things, namely the bracketed text at
  the start of the description, the trailing `=`, and that names are case
  sensitive. Tabs, `Format:` lines and column layout are convention.
- Trailing `=`: the `.rst` words it as "will be entered as an environment
  variable", and its absence as a kernel argument readable via
  `/proc/cmdline`; it does not say "takes a value".
- Description lines: the prevailing indent in the `.txt` is three tabs, with
  the name at one tab.
- Bracketed tags: may be on the name line or on the next line, and some
  entries have none, for example `apicpmtimer`.

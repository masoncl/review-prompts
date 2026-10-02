- `Documentation/kbuild/kconfig-language.rst` has the policy, in the paragraph
  and note that follow the `default` attribute.
- `Documentation/process/submit-checklist.rst`, "Review Kconfig changes": says
  new or modified options "default to off" unless they meet the exception
  criteria, and points to `Documentation/kbuild/kconfig-language.rst`.
- `Documentation/process/coding-style.rst`, section
  "10) Kconfig configuration files": covers indentation and marking dangerous
  features in the prompt, has no default-value policy, and points to
  `Documentation/kbuild/kconfig-language.rst`.
- Cases the note lists as meriting "default y/m":

  | Case | Value the note names |
  |---|---|
  | a) new option for something that used to always be built | `default y` |
  | b) new gatekeeping option that hides or shows other options and generates no code | `default y` |
  | c) sub-driver behavior or similar options for a driver that is `default n` | none named |
  | d) hardware or infrastructure everybody expects, such as `CONFIG_NET` or `CONFIG_BLOCK`; "rare exceptions" | none named |

- `default m`: appears only in the heading "default y/m"; no case names it.
- Drivers needed for a platform to boot: not among the listed cases; the only
  hardware case is d), hardware "that everybody expects".

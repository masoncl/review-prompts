- What to return: "information identifying the created object such as the
  allocated object's ID".
- Strength of the guidance: "Try to find useful data to return" and "better
  to err on the side of replying"; an ACK-only command is not forbidden.
- `Documentation/userspace-api/netlink/specs.rst`: lets a SET `do` omit the
  reply section when the kernel answers with the error code alone.
- Scope of the specific rule: NEW and ADD commands; a command that changes an
  object is covered only by the general sentence.
- Echo in "Answer requests": the only text is the parenthesis "(without
  having to resort to using `NLM_F_ECHO`)"; the document gives no reason.
- Separate "NLM_F_ECHO" section: pass the request info to `genl_notify()` so
  the flag takes effect; described as useful for precise feedback, for
  example logging.
- `genl_notify()` in `net/netlink/genetlink.c`: the helper that honours
  `NLM_F_ECHO`, through `nlmsg_report()` on `info->nlhdr`.
- `genlmsg_multicast()` in `include/net/genetlink.h`: takes no
  `struct genl_info`, so a notification sent with it is never echoed.
- `Documentation/userspace-api/netlink/intro.rst`, "Notification echo":
  states the feature "is not universally implemented".

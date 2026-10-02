- Notifications: get command IDs separate from requests and replies; only the
  request and its reply share an ID.
- Reason given for the shared ID: easier to match request and reply, and
  "we have plenty of ID space".
- Reason given for separate notification IDs: easier to sort notifications
  from replies and present them through a different API.
- Model names: `unified` and `directional`; there is no "classic" model.
- New family: `unified`; `Documentation/netlink/genetlink.yaml` and
  `Documentation/netlink/genetlink-c.yaml` accept no other `enum-model`.
- `unified`: one enumeration for all messages; notification IDs come from the
  same space as request IDs.
- Value 0 in a new family: no `unspec` entry is defined at all; the first
  attribute and the first command are 1, as in `include/uapi/linux/netdev.h`.
- Reason given for dropping `unspec`: the values "are not used in practice"
  (`Documentation/core-api/netlink.rst`);
  `Documentation/userspace-api/netlink/specs.rst` adds that entry 0 "is
  almost always reserved as undefined".
- Sending 0 by mistake: not a reason either document gives.

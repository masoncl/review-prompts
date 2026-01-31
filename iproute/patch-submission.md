# Submitting Patches

## Patch Format

Patches follow the Linux kernel patch submission guidelines:
https://www.kernel.org/doc/html/latest/process/submitting-patches.html

## Subject Line

Use the appropriate prefix based on the target tree:

```
Subject: [PATCH iproute2] component: brief description
Subject: [PATCH iproute2-next] component: brief description
```

Examples:
```
Subject: [PATCH iproute2-next] ip: fix syntax for rules
Subject: [PATCH iproute2] tc: fix memory leak in filter parsing
```

## Commit Message

- First line: brief summary (50 chars or less)
- Blank line
- Detailed description wrapped at 72 characters
- Signed-off-by line

```
ip: add support for new feature

Detailed explanation of what this patch does and why.
Reference any relevant kernel commits if this adds support
for new kernel features.

Signed-off-by: Your Name <your.email@example.org>
```

## Signed-off-by and Developer Certificate of Origin

The `Signed-off-by:` line certifies that you wrote the code or have the right
to submit it, following the Developer's Certificate of Origin (DCO):
https://developercertificate.org/

By adding your Signed-off-by, you certify:
- The contribution was created by you, or
- It is based on previous work with a compatible license, or
- It was provided to you by someone who certified the above

Use `git commit -s` to automatically add your Signed-off-by line.

## Sending Patches

Send patches to the netdev mailing list:

```
git send-email --to=netdev@vger.kernel.org your-patch.patch
```

## Testing

- Test both JSON and non-JSON output modes
- Test with various kernel versions (features may not be available on older kernels)
- Verify error handling with invalid inputs
- Check for memory leaks with valgrind

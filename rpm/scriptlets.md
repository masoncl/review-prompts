# RPM Scriptlet Safety Guide

## When to Load

Load this file when the spec file contains %pre, %post, %preun, %postun,
%pretrans, %posttrans, or %trigger* sections.

## Scriptlet Execution Order

### Install ($1 == 1)
1. `%pretrans` of new package
2. `%pre` of new package
3. Files installed
4. `%post` of new package
5. `%posttrans` of new package

### Upgrade ($1 == 2 for new, $1 == 1 for old)
1. `%pretrans` of new package
2. `%pre` of new package
3. Files of new package installed
4. `%post` of new package
5. `%preun` of old package ($1 == 1)
6. Files of old package removed
7. `%postun` of old package ($1 == 1)
8. `%posttrans` of new package

### Uninstall ($1 == 0)
1. `%preun` of old package ($1 == 0)
2. Files removed
3. `%postun` of old package ($1 == 0)

## The $1 Argument

| Scriptlet | Install | Upgrade | Uninstall |
|-----------|---------|---------|-----------|
| %pre | 1 | 2 | - |
| %post | 1 | 2 | - |
| %preun | - | 1 | 0 |
| %postun | - | 1 | 0 |
| %pretrans | 0 | 0 | - |
| %posttrans | 0 | 0 | - |

## systemd Service Macros

### Proper Usage
```
%post
%systemd_post myservice.service

%preun
%systemd_preun myservice.service

%postun
%systemd_postun_with_restart myservice.service
```

### Variants
- `%systemd_post` - enable service on install
- `%systemd_preun` - stop and disable on uninstall
- `%systemd_postun` - just reload daemon on upgrade (no restart)
- `%systemd_postun_with_restart` - restart service on upgrade

### tmpfiles and sysusers
```
%post
%tmpfiles_create_package %{name} %{_tmpfilesdir}/myapp.conf
%sysusers_create_package %{name} %{_sysusersdir}/myapp.conf
```

## File Trigger Scriptlets

Modern replacement for many scriptlets. Executed when files matching a
path pattern are installed/removed by any package.

```
%transfiletriggerin -- %{_libdir}
/sbin/ldconfig

%transfiletriggerpostun -- %{_libdir}
/sbin/ldconfig
```

Most common use: ldconfig is now handled by file triggers in base packages,
so `%ldconfig_scriptlets` or explicit ldconfig calls are often unnecessary
on modern systems.

## User/Group Creation

### Modern: sysusers.d (preferred)
```
# Install a sysusers.d file
Source1: myapp.sysusers
...
install -D -m 644 %{SOURCE1} %{buildroot}%{_sysusersdir}/myapp.conf

%post
%sysusers_create_package %{name} %{_sysusersdir}/myapp.conf
```

### Legacy: useradd in %pre
```
%pre
getent group myapp >/dev/null || groupadd -r myapp
getent passwd myapp >/dev/null || \
    useradd -r -g myapp -d /var/lib/myapp -s /sbin/nologin \
    -c "My Application" myapp
exit 0
```

## Common Scriptlet Bugs

### 1. Not Checking $1
```
# WRONG - runs on uninstall too
%post
systemctl enable myservice.service

# CORRECT - use macros that handle $1
%post
%systemd_post myservice.service
```

### 2. Failing on Uninstall
```
# WRONG - if config was already removed, this fails
%preun
rm /etc/myapp/generated.conf

# CORRECT - guard against missing files
%preun
rm -f /etc/myapp/generated.conf
```

### 3. Interactive Prompts
```
# WRONG - no terminal during package transactions
%post
read -p "Enter configuration value: " value

# CORRECT - use default values or config file
```

### 4. Assuming Network Availability
```
# WRONG - network may not be available
%post
curl -O https://example.com/data.json

# CORRECT - include needed files in the package
```

### 5. Referencing %{buildroot} Paths
```
# WRONG - buildroot does not exist at install time
%post
cat %{buildroot}%{_sysconfdir}/myapp.conf

# CORRECT
%post
cat %{_sysconfdir}/myapp.conf
```

### 6. Calling a Tool From a Package That Is Not Required
Minimal roots (containers, mock `--postinst`) often lack tools such as
`udevadm` (systemd-udev). An unguarded call exits 127 and fails the
transaction. Scriptlets MUST exit 0 (Packaging Guidelines, Scriptlets:
"All scriptlets MUST exit with the zero exit status"; `|| :` is the
generic trick, but "other error checking/prevention measures may be more
appropriate"). Decide by whether the action is critical:

- **Not critical** (cache refresh, udev retrigger, ...): guard the call
  with `command -v`, add `|| :`, and at most declare
  `OrderWithRequires(post): <pkg>` so the tool is installed first when it
  is in the same transaction. Do not add `Requires`. This is the same idea
  as the guidelines' `%{?systemd_ordering}`, a weaker form of
  `%{?systemd_requires}` that "only declares an ordering during an RPM
  transaction" (Scriptlets, "Dependencies on the systemd package").
- **Critical**: `Requires(post): <pkg>`, and still `|| :`.

```
# WRONG - udevadm is not installed in minimal roots
%post hid2hci
/sbin/udevadm trigger --subsystem-match=usb

# CORRECT - not critical: order, guard, never fail
OrderWithRequires(post): systemd-udev
...
%post hid2hci
# udevadm is not installed in minimal roots (containers, mock)
if command -v udevadm >/dev/null; then
    # retrigger is best-effort, e.g. /sys may be read-only in containers
    udevadm trigger --subsystem-match=usb || :
fi
```

`OrderWithRequires` needs RPM >= 4.9.0, which every live EL/EPEL branch
has; see "Spec Feature Availability by RPM Version" in `spec-file.md`.

### 7. Commands That Can Fail Without `|| :`
rpm treats a failed `%post` as non-critical (the package stays installed),
but dnf5 reports the whole transaction as failed. A non-zero exit status is
what matters; output on stderr alone does not fail anything.
```
# WRONG
%post
some-cache-tool --refresh

# CORRECT - best-effort step must not fail the transaction
%post
some-cache-tool --refresh || :
```

### 8. systemd Macro Scope Mismatch
The `%systemd_*` macros are for system units in `%{_unitdir}`; the
`%systemd_user_*` macros are for user units in `%{_userunitdir}`
(Packaging Guidelines, Scriptlets, "User units"). Using the
wrong family fails with `Failed to preset unit: Unit X.service does not
exist` in the scriptlet output. This often comes from copying the
scriptlets of an adjacent subpackage that ships the other kind of unit.

Check: compare where `%files` installs the unit with the macro family used.
When switching to `%systemd_post`/`%systemd_preun`, also add `%postun`
(`%systemd_postun_with_restart` or `%systemd_postun`).
```
# WRONG - bluetooth-mesh.service is installed to %{_unitdir}
%post mesh
%systemd_user_post bluetooth-mesh.service

# CORRECT
%post mesh
%systemd_post bluetooth-mesh.service

%preun mesh
%systemd_preun bluetooth-mesh.service

%postun mesh
%systemd_postun_with_restart bluetooth-mesh.service
```

# SPDX-License-Identifier: GPL-3.0-or-later
# grub-btrfs is Copyright (C) Antynea, licensed under GPL-3.0-or-later.
# Based on the spec by zzahkaboom24 (https://github.com/zzahkaboom24/grub-btrfs-rpm),
# changed to package snapshots of upstream master instead of tagged releases.

# The CI workflow passes the upstream commit via --define; the defaults allow a
# local build of a known-good commit.
%{!?commit:     %global commit     38cd2fa419e4c1c0f1e345a374b37c040c170047}
%{!?commitdate: %global commitdate 20260824}
%global shortcommit %(c=%{commit}; echo ${c:0:7})
# Last upstream release. The snapshot version sorts above it and below the next
# release, so a future tag supersedes these builds without an epoch.
%global baseversion 4.14

Name:           grub-btrfs
Version:        %{baseversion}^%{commitdate}git%{shortcommit}
Release:        2%{?dist}
Summary:        Include btrfs snapshots in GRUB boot options

License:        GPL-3.0-or-later
URL:            https://github.com/Antynea/grub-btrfs
Source0:        %{url}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz

BuildArch:      noarch
BuildRequires:  make
BuildRequires:  systemd-rpm-macros

Requires:       bash >= 4.0
Requires:       btrfs-progs
Requires:       gawk
Requires:       grub2-tools
# grub-btrfsd watches the snapshot directory with inotifywait and exits without it.
Requires:       inotify-tools

%description
grub-btrfs adds Btrfs snapshots to the GRUB boot menu, allowing you to
boot into a snapshot directly from GRUB. Supports manual snapshots,
snapper, and timeshift.

This package tracks upstream master, which carries fixes that are not
part of a release yet (e.g. multi-device Btrfs, upstream PR #440).

%prep
%autosetup -n %{name}-%{commit}

# Fail loudly if upstream renames the options we set, instead of silently
# shipping a config that does not work on Fedora.
for option in \
    '^#GRUB_BTRFS_GRUB_DIRNAME=' \
    '^#GRUB_BTRFS_SCRIPT_CHECK='; do
    if ! grep -q "$option" config; then
        echo "ERROR: expected config option not found: $option" >&2
        exit 1
    fi
done

sed -i \
  -e '/^#GRUB_BTRFS_GRUB_DIRNAME=/a GRUB_BTRFS_GRUB_DIRNAME="/boot/grub2"' \
  -e '/^#GRUB_BTRFS_SCRIPT_CHECK=/a GRUB_BTRFS_SCRIPT_CHECK=grub2-script-check' \
  config

if ! grep -q 'id -u' Makefile; then
    echo "ERROR: expected root-check pattern not found in Makefile" >&2
    exit 1
fi
# rpmbuild runs unprivileged and installs into DESTDIR, so the root check only gets in the way.
sed -i '/test "$(shell id -u)" != 0/,/^[[:space:]]*fi$/d' Makefile

%build
# Nothing to compile, grub-btrfs is shell scripts.

%install
make install DESTDIR=%{buildroot} PREFIX=%{_prefix} \
    SYSTEMD=true OPENRC=false INITCPIO=false GRUB_UPDATE_EXCLUDE=true

# Fedora's default preset disables unknown units, and %systemd_post applies it
# on first install. Without this, installing over a make-install setup removes
# the existing enablement and the daemon silently stops after the next reboot.
install -Dm644 /dev/stdin %{buildroot}%{_presetdir}/80-grub-btrfs.preset <<'PRESET'
enable grub-btrfsd.service
PRESET

%check
# Regression guard for multi-device Btrfs (upstream PR #440): grub2-probe
# prints one line per device, and without head -n1 the UUID lookup comes back
# empty. If upstream ever drops this, the build fails instead of shipping it.
grep -q -- '--target=device / | head -n1' %{buildroot}%{_sysconfdir}/grub.d/41_snapshots-btrfs
grep -q -- '--target=device "${boot_directory}" | head -n1' %{buildroot}%{_sysconfdir}/grub.d/41_snapshots-btrfs
grep -q '^GRUB_BTRFS_GRUB_DIRNAME="/boot/grub2"' %{buildroot}%{_sysconfdir}/default/grub-btrfs/config
grep -q '^GRUB_BTRFS_SCRIPT_CHECK=grub2-script-check' %{buildroot}%{_sysconfdir}/default/grub-btrfs/config
bash -n %{buildroot}%{_sysconfdir}/grub.d/41_snapshots-btrfs
bash -n %{buildroot}%{_bindir}/grub-btrfsd

%post
%systemd_post grub-btrfsd.service

%preun
%systemd_preun grub-btrfsd.service

%postun
%systemd_postun_with_restart grub-btrfsd.service

%files
%license %{_datadir}/licenses/grub-btrfs/LICENSE
%doc %{_datadir}/doc/grub-btrfs/README.md
%doc %{_datadir}/doc/grub-btrfs/initramfs-overlayfs.md
%dir %{_sysconfdir}/default/grub-btrfs
%config(noreplace) %{_sysconfdir}/default/grub-btrfs/config
%{_sysconfdir}/grub.d/41_snapshots-btrfs
%{_bindir}/grub-btrfsd
%{_unitdir}/grub-btrfsd.service
%{_presetdir}/80-grub-btrfs.preset
%{_mandir}/man8/grub-btrfs.8*
%{_mandir}/man8/grub-btrfsd.8*

%changelog
* Thu Sep 17 2026 Michael Köster <github.com@koester-familie.de> - 4.14^20260824git38cd2fa-2
- Ship a preset that enables grub-btrfsd.service; the default preset disabled it on install

# Versions are generated per upstream commit; see the git history of
# https://github.com/mkocustos/grub-btrfs-rpm for packaging changes.
* Thu Sep 17 2026 Michael Köster <github.com@koester-familie.de> - 4.14^20260824git38cd2fa-1
- Package snapshots of upstream master (includes multi-device Btrfs fix, PR #440)

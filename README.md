# grub-btrfs-rpm

Fedora packaging of [grub-btrfs](https://github.com/Antynea/grub-btrfs), built from
**upstream master** into the COPR project
[`mkocustos/grub-btrfs`](https://copr.fedorainfracloud.org/coprs/mkocustos/grub-btrfs/).

> [!WARNING]
> **Pitfalls, most severe first**
>
> 1. **This is a snapshot of `master`, not a release.** Every upstream commit lands here
>    within a day, untested beyond the build checks below. It exists because the latest
>    release (v4.14, 2025-09) lacks fixes that some systems need, above all
>    [#440](https://github.com/Antynea/grub-btrfs/pull/440): on a multi-device Btrfs
>    `41_snapshots-btrfs` aborts with `Cannot determine UUID` and no snapshot
>    submenu is generated.
> 2. **Switching from `make install`:** the package takes over the unowned files.
>    `/etc/default/grub-btrfs/config` is a `%config(noreplace)` file, so a differing
>    existing config is kept aside as `config.rpmorig` or `config.rpmnew` — back it up
>    first and reconcile afterwards.
> 3. **The COPR API token expires** (see `expiration` in `~/.config/copr`). Once it does,
>    the daily workflow fails at the COPR step; renew it at
>    <https://copr.fedorainfracloud.org/api/> and update the `COPR_CONFIG` secret.

## Install

```bash
sudo dnf copr enable mkocustos/grub-btrfs
sudo dnf install grub-btrfs
sudo systemctl enable --now grub-btrfsd.service
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
```

Chroots: Fedora 43 and 44 (the package is `noarch`).

## What the package changes

- Sets the Fedora paths in `/etc/default/grub-btrfs/config`:
  `GRUB_BTRFS_GRUB_DIRNAME="/boot/grub2"` and `GRUB_BTRFS_SCRIPT_CHECK=grub2-script-check`.
  Nothing else — in particular no snapshot kernel parameters, so boot behaviour is upstream's.
- Removes the root check from the Makefile install target (the build runs unprivileged).
- `%check` fails the build if the multi-device fix (`| head -n1` for root and boot device)
  disappears from `41_snapshots-btrfs`, or if either script has a syntax error.

## Versioning

`4.14^<commitdate>git<shortcommit>`, e.g. `4.14^20260824git38cd2fa`. The `^` marks a
post-release snapshot: it sorts above 4.14 and below 4.15, so the next upstream release
supersedes these builds without an epoch.

## Build pipeline

[`.github/workflows/copr.yaml`](.github/workflows/copr.yaml) runs daily at 03:00 UTC:

1. **setup** resolves the tip of upstream master and skips the run if the latest succeeded
   COPR build already carries that commit.
2. **build** creates the SRPM in a Fedora container and submits it to COPR.
3. **verify** installs the fresh build in `fedora:43` and `fedora:44`, checks the version
   matches the commit, runs `rpm -V` and checks the fix is present.

Manual runs (`workflow_dispatch`) accept a specific upstream `commit` and `force`.

Repository configuration: secret `COPR_CONFIG` (contents of `~/.config/copr`), variable
`COPR_REPO_NAME` (`mkocustos/grub-btrfs`).

## License

GPL-3.0-or-later, same as grub-btrfs. The spec is based on
[zzahkaboom24/grub-btrfs-rpm](https://github.com/zzahkaboom24/grub-btrfs-rpm).

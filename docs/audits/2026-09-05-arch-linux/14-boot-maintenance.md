# Applied Boot Maintenance

Applied on 2026-09-05 after explicit user approval of the recommendation to
keep stock Arch as the default kernel and enable the packaged systemd-boot
update service. This authorization was limited to those boot changes.

## Changes and Results

| Item | Before | After |
| --- | --- | --- |
| Default entry in `/boot/loader/loader.conf` | `arch-zen`, matching neither entry ID | `arch.conf`, verified as default by `bootctl list` |
| Primary EFI loader | systemd-boot 259.1-1-arch | 261.2-1-arch |
| EFI fallback at `/boot/EFI/BOOT/BOOTX64.EFI` | systemd-boot 259.1-1-arch | 261.2-1-arch |
| `systemd-boot-update.service` | Disabled | Enabled; `active (exited)`, result `success`, exit status 0 |

Only the default-entry line was edited; existing comments, the three-second
menu timeout, and `editor 0` were preserved. Zen remains available as
`arch-zen.conf`. Both kernel images, both initramfs files, and their entry
files were checked for presence before the change. No EFI default or one-shot
entry override was present.

The service was enabled and started with
`sudo systemctl enable --now systemd-boot-update.service`. Its packaged command
is `bootctl --variables=no --graceful update`. It will run at subsequent boots;
it is not a hook that runs immediately after each package transaction.

Both updated EFI files were compared byte for byte with
`/usr/lib/systemd/boot/efi/systemd-bootx64.efi` and matched. The ESP was flushed
with `sync -f /boot` after the changes.

The additional `/boot/EFI/systemd/systemd-boot-fallbackx64.efi` contains 259.1.
Preserving the previous primary binary at that path is part of the upstream
[systemd 261.2 update implementation](https://github.com/systemd/systemd/blob/v261.2/src/bootctl/bootctl-install.c).
It is distinct from the updated `EFI/BOOT/BOOTX64.EFI`. No automatic firmware
selection of this older copy is claimed: the service disables EFI-variable
writes.

An independent repository review found no bootloader configuration management
or service policy that would overwrite these settings. No Ansible source
change or playbook execution was needed. No package update, firmware flash,
initramfs rebuild, reboot, commit, or push was performed.

## Backup and Rollback

Before mutation, the three affected files were copied with their directory
structure into this root-owned directory outside the repository:

`/root/systemd-boot-backup-20260905T110121Z-6sHb4S`

The directory has mode `0700`. Each backup was compared with its original;
checksums and the previous service state were also saved there. It contains
only the selected loader configuration, EFI executables, and verification
metadata.

If a full rollback is needed from the running installed system, use:

```bash
set -euo pipefail
boot_backup_dir=/root/systemd-boot-backup-20260905T110121Z-6sHb4S
sudo systemctl disable --now systemd-boot-update.service
for boot_file in \
    /boot/loader/loader.conf \
    /boot/EFI/systemd/systemd-bootx64.efi \
    /boot/EFI/BOOT/BOOTX64.EFI; do
    sudo cp -- "$boot_backup_dir$boot_file" "$boot_file"
done
sudo sync -f /boot
```

This restores the original configuration, including its incorrect default
identifier. For recovery from installation media, unlock and mount the actual
root and ESP first; the paths above refer to the installed system. Rollback
has not been executed or boot-tested.

## Remaining Verification

Reboot when convenient, then inspect:

```bash
bootctl status
uname -r
systemctl status systemd-boot-update.service --no-pager
```

Expected: current bootloader 261.2-1-arch, entry `arch.conf`, a stock Arch kernel,
and a successful update service. At application time the running kernel was
`7.2.2-arch1-1`. Until reboot, the current-bootloader field still reports 259.1
because that version started the existing session. Actual boot of the updated
EFI binary remains unverified.

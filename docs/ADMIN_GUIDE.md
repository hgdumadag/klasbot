# Klasbot Admin Guide

## First-Time Setup

1. Install the app on the Raspberry Pi with `sudo deploy/setup-pi.sh`.
2. Create the first admin PIN:

   ```bash
   sudo -u klasbot KLASBOT_DB_PATH=/var/lib/klasbot/klasbot.db /opt/klasbot/.venv/bin/python /opt/klasbot/scripts/seed_admin.py --name Admin --pin 1111
   ```

3. Open `http://127.0.0.1:8000` on the Pi and log in with the admin PIN.
4. Use Teacher Admin to add each teacher and assign a unique PIN.

## Daily Operation

- Teachers log in with their PIN, generate a draft, edit it, save it to My Library, and print.
- Saved outputs are scoped to the logged-in teacher.
- Admin users can add teachers and reset PINs from the right-side admin panel.

## Updating Over Tethered Internet

Connect the Pi to a phone hotspot, then run:

```bash
sudo /opt/klasbot/deploy/update.sh
```

The update pulls the latest git changes, reinstalls the local package, and restarts the service.

## Useful Commands

```bash
systemctl status klasbot.service
journalctl -u klasbot.service -f
curl http://127.0.0.1:8000/healthz
lpstat -p
```

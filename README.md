# Klasbot

Offline-first AI teaching assistant for shared Raspberry Pi kiosks in GIDA schools.

## Local Development

```powershell
python -m pip install -e .
python scripts\seed_admin.py --name Admin --pin 1111
python -m uvicorn klasbot.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and log in with the seeded PIN.

For wireless testing from a phone or another laptop on the same trusted Wi-Fi:

```powershell
.\scripts\run_lan_windows.ps1
```

The script prints the LAN URLs to open from the teacher device. If the device cannot connect, allow Python through Windows Defender Firewall for Private networks.

## Raspberry Pi Deployment

On Raspberry Pi OS Bookworm:

```bash
sudo deploy/setup-pi.sh
```

The setup script installs Python, Chromium, CUPS, Ollama, the `klasbot.service` systemd unit, and the kiosk launch script.

After setup, seed the first admin:

```bash
sudo -u klasbot KLASBOT_DB_PATH=/var/lib/klasbot/klasbot.db /opt/klasbot/.venv/bin/python /opt/klasbot/scripts/seed_admin.py --name Admin --pin 1111
```

## Verification

```powershell
python -m compileall klasbot scripts
pytest
```

For a running app:

```powershell
python scripts\smoke_api.py --pin 1111
```

The smoke test also calls `/api/ollama/status`, which reports whether Ollama is reachable and whether the configured model is installed.

See `docs/ADMIN_GUIDE.md` and `docs/PILOT_QA.md` for pilot operation. The student records roadmap is documented in `docs/STUDENT_MANAGEMENT_PLAN.md`.

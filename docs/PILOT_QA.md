# Klasbot Pilot QA Checklist

Run this on the actual Raspberry Pi kiosk before the pilot.

## Cold Boot

- Power on the Pi.
- Confirm Chromium opens `http://127.0.0.1:8000` within 60 seconds.
- Confirm the login screen is visible and the PIN keypad works.

## Auth

- Log in as admin.
- Add a second teacher.
- Log out.
- Log in as the second teacher.

## Generation

- Click `Check` in the Ollama Status panel and confirm it says `Connected`.
- Generate a DLP lesson plan for Grade 4 Math, topic `fractions`, resources `paper, stones, bottle caps`.
- Confirm first streamed output appears within 5 seconds after Ollama is warm.
- Confirm the full draft completes within 120 seconds.
- Repeat one SDLP, one DLL, one quiz, and one exam.

## Library

- Save the generated draft.
- Reopen it from My Library.
- Edit a typo and save.
- Regenerate from the saved item.
- Delete a throwaway saved item.

## Printing

- Print a saved output.
- Confirm margins, header, footer, and page breaks are acceptable.
- If backend printing fails, confirm browser print fallback opens.

## Offline

- Disable Wi-Fi or unplug Ethernet.
- Repeat login, generate with local Ollama, save, reopen, and print.

## Update

- Tether the Pi to a phone hotspot.
- Run `sudo /opt/klasbot/deploy/update.sh`.
- Confirm `systemctl status klasbot.service` is active.

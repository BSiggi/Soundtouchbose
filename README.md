# SoundTouchBose

SoundTouchBose ist eine lokale Windows-Desktop-Anwendung zur Verwaltung von Bose SoundTouch-Geräten nach dem Bose-Cloud-Shutdown. Die App findet Geräte im LAN, verwaltet Internetradio-Sender, beschreibt Preset-Tasten 1–6 lokal auf dem Gerät und bietet zusätzlich Zeitpläne, Zonen, Tray-Betrieb, Mini-Web-UI und eine optionale Home-Assistant-Bridge.

SoundTouchBose is a local Windows desktop app for managing Bose SoundTouch devices after the Bose cloud shutdown. It discovers devices on the LAN, manages internet radio stations, writes presets 1–6 locally to the speaker, and also includes schedules, zones, tray support, a mini web UI, and an optional Home Assistant bridge.

## Screenshots / Platzhalter

- Desktop-Hauptfenster: Platzhalter – nach dem ersten Start Geräte-Scan, Preset-Editor und Dashboard sichtbar.
- Web-UI mobil: Platzhalter – Preset-Buttons, Lautstärke und Zonen für Handy-Zugriff.

## Features

- Zeroconf/mDNS-Discovery für `_soundtouch._tcp.local.`
- Manuelles Hinzufügen von Geräten per IP mit `/info`-Validierung
- 40+ DACH-Radiosender als Startbibliothek, plus Import/Export und eigene Sender
- Preset-Editor für 6 Tasten pro Gerät, inkl. Drag & Drop und Bulk-Übertragung
- Preset-Klick-Editor: nicht belegte Presets lassen sich direkt per Klick belegen/bearbeiten/löschen
- Lokale Preset-Programmierung via `/select` und `/key PRESET_X`
- Multi-Room-Zonen mit speicherbaren Gruppen
- APScheduler-Zeitpläne für Senderstart, Lautstärke und Ausschalten
- Live-Dashboard mit WebSocket-Triggern, Lautstärke und Transporttasten
- Tray-Icon, Windows-Autostart-Skript, Backup/Restore
- In-App-Update (ZIP-Paket) mit automatischem Pre-Update-Backup und Update-Log
- Diagnose-Export als ZIP (`report.json` + Log-Auszüge) für Supportfälle
- Wartungs-/Cleanup-Hilfe für Autostart, Backups und optionale Dienst-Stopps
- Mini-Web-UI auf Port 8765 und Home-Assistant-Bridge auf Port 8766 (localhost, Token wird automatisch erzeugt)
- Logging nach `%APPDATA%/SoundTouchBose/logs/app.log`

## Installation

### Empfohlen: Windows `.exe` aus GitHub Actions

1. Repository öffnen → **Actions** → Workflow **Build Windows**.
2. Nach erfolgreichem Lauf das Artifact `SoundTouchBose.exe` herunterladen.
3. Die `.exe` auf dem 24/7-Windows-PC ausführen.

### Aus den Quellen

```bash
pip install -r requirements.txt
python -m soundtouchbose
```

## Erste Schritte

1. Tab **Geräte** öffnen und **Neu scannen** oder Geräte manuell per IP hinzufügen.
2. Tab **Sender** öffnen und aus der DACH-Bibliothek wählen oder eigene TuneIn-IDs/Stream-URLs eintragen.
3. Gewünschten Sender per Drag & Drop auf einen Preset-Button im Tab **Presets** ziehen.
4. Optional Zonen, Zeitpläne, Web-UI oder Home-Assistant-Bridge aktivieren.

## Update und Diagnose

- **Einstellungen → Update anwenden …**: ZIP-Update auswählen, Backup wird automatisch erstellt, Änderungen in `logs/update.log` protokolliert.
- **Einstellungen → Diagnose exportieren**: erzeugt ein ZIP mit Versions-/OS-Infos, Gerätestatus, Netz-Checks und relevanten Logs.
- **Einstellungen → Cleanup ausführen**: entfernt Autostart, bereinigt alte Backups und versucht bekannte Windows-Dienste sauber zu stoppen.

## Bose-Cloud-Shutdown

Die Anwendung nutzt ausschließlich lokale, weiterhin verfügbare Schnittstellen:

- HTTP/XML auf Port `8090`
- WebSocket auf Port `8080` mit `gabbo`
- mDNS/Zeroconf über `_soundtouch._tcp.local.`

Nicht benötigt werden Bose-Konten, Cloud-Logins oder Spotify-Authentifizierung über Bose-Server.

## FAQ / Troubleshooting

### Gerät wird nicht gefunden

- Firewall-Regeln für Port `8090` und `8080` prüfen
- Multicast/mDNS im Heimnetz aktivieren
- Testweise Gerät manuell per IP hinzufügen

### Preset wird nicht geschrieben

- Sicherstellen, dass der Sender kurz gestartet werden kann
- Prüfen, ob das Gerät im LAN erreichbar ist
- Bei Bedarf den Sender testweise im Tab **Sender** abspielen

### Web-UI ist nicht erreichbar

- Standard-Port ist `8765`
- Im Settings-Tab prüfen, ob die Web-UI aktiviert ist
- Nur für das vertrauenswürdige LAN gedacht, ohne Authentifizierung

## Entwicklung und Tests

```bash
pytest -q
```

## Project Layout

```text
soundtouchbose/
  api/               HTTP, XML, Discovery und WebSocket
  core/              Konfiguration, Presets, Geräte, Zonen, Scheduler
  gui/               PySide6-Oberfläche mit Tabs und Widgets
  web/               Flask-Web-UI
  integrations/      Home-Assistant-Bridge
  data/              Standard-Radiosender
```

## License

MIT – die vorhandene `LICENSE` bleibt unverändert.

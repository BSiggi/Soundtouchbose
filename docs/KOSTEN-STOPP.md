# SoundTouchBose: Kosten-Stopp und vollständige Abschaltung

## Bereits im Repository abgeschaltet

- GitHub Actions **CI** und **Build Windows** sind auf `workflow_dispatch` umgestellt.
  - Ergebnis: Keine automatischen Runs mehr bei `push`, `pull_request` oder Tags.
  - Kosten durch unbeabsichtigte Build-/Testläufe aus diesem Repo sind damit gestoppt.

## Prüfergebnis: Automatisierte Prozesse im Repo

- GitHub Workflows: vorhanden, aber jetzt nur noch manuell startbar.
- Geplante Jobs (`schedule`/`cron`): keine gefunden.
- Webhooks-Konfiguration: nicht im Repository verwaltet (nur in GitHub-Repository-Einstellungen sichtbar).
- API-Keys/Secrets im Code: keine externen Bezahl-API-Keys im Repository gefunden.
- Externe Cloud-Integrationen im Code:
  - optional Home-Assistant-Bridge (lokal, Token lokal erzeugt)
  - Mini-Web-UI (lokal)
  - SoundTouch-Kommunikation direkt im lokalen Netzwerk (HTTP/XML/WebSocket zum Gerät)

## Sofort-Checkliste: Alles stoppen, was Kosten verursachen könnte

### 1) GitHub (Repository-Einstellungen)

1. **Actions komplett deaktivieren (optional, härter als workflow_dispatch):**  
   `Settings → Actions → General → Actions permissions` auf deaktiviert setzen.
2. **Webhooks prüfen/deaktivieren:**  
   `Settings → Webhooks` → alle nicht benötigten Webhooks deaktivieren/löschen.
3. **Secrets/Variablen prüfen:**  
   `Settings → Secrets and variables` → ungenutzte Tokens entfernen/rotieren.

### 2) Laufende lokale SoundTouchBose-Prozesse stoppen

1. App schließen (inkl. Tray-Icon).
2. In der App: `Einstellungen → Cleanup ausführen` (entfernt Autostart, stoppt bekannte Dienste).
3. Optional manuell prüfen (Windows):
   - Task-Manager: `SoundTouchBose` beenden
   - Dienste: `SoundTouchBoseService` / `soundtouchbose` stoppen, falls vorhanden

### 3) Lokale Integrationen deaktivieren

In SoundTouchBose unter `Einstellungen`:

- `Mini-Web-UI aktiv` **aus**
- `Home Assistant Bridge aktiv` **aus**
- `Mit Windows starten` **aus**

Dann **Speichern** und App neu starten/schließen.

### 4) Externe Kostenquellen außerhalb des Repositories

Dieses Repo kann keine Drittanbieter-Abos automatisch kündigen. Bitte manuell prüfen:

- Hosting/VPS/Cloud-Instanzen
- Domain/DNS/Reverse-Proxy
- WordPress-/Plugin-Lizenzen (falls parallel im Einsatz)
- Monitoring/SaaS-Tools

## Status

- ✅ Automatische GitHub-Workflow-Läufe aus dem Repo gestoppt.
- ✅ Keine offensichtlichen kostenpflichtigen Cloud-API-Keys im Code gefunden.
- ⚠️ Webhooks, Secrets, Abos und externe Konten müssen in den jeweiligen Provider-Backends manuell deaktiviert werden.

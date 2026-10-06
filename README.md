
Readme · MD
# Quiz- und Lernkarten-Generator
 
Ein kleines Lernprojekt: Man fügt einen Vorlesungstext ein, und ein Sprachmodell (Google Gemini) erstellt daraus Quizfragen und Lernkarten. Die App ist als Streamlit-Anwendung gebaut und online ausprobierbar.
 
**Live-Demo:** (Link hier einfügen, sobald veröffentlicht)
 
Das Projekt ist bewusst nicht perfekt. Es ist mein erstes Projekt mit einer LLM-API, und ich habe darin vor allem gelernt, wie man ein Sprachmodell zuverlässig in ein eigenes Programm einbaut. Was funktioniert und was nicht, steht weiter unten.
 
## Funktionen
 
- Text einfügen (max. 5.000 Zeichen), Anzahl der Fragen wählen (3 bis 10)
- Quiz mit 4 Antwortmöglichkeiten, Auswertung mit Punktzahl und Erklärung
- Lernkarten-Modus zum Umdrehen
- Hinweis zum Datenschutz direkt in der App
## So funktioniert es
 
Text -> Prompt -> Gemini API (JSON-Ausgabe) -> Prüfung der Struktur -> Quiz und Lernkarten
 
1. Der Prompt weist das Modell an, nur auf Basis des Textes zu fragen und nichts dazuzuerfinden.
2. Die Antwort kommt als JSON und wird in Python eingelesen.
3. Jede Frage wird geprüft (4 Antworten, gültiger Index der richtigen Antwort, Erklärung vorhanden). Ungültige Fragen werden verworfen.
## Verbesserungen im Laufe der Entwicklung
 
Beim Testen sind mir Probleme aufgefallen, die ich Schritt für Schritt gelöst habe:
 
- **Von lokal zu online:** Die erste Version lief mit Ollama auf meinem Rechner. Dafür musste jeder Nutzer Ollama und ein 5-GB-Modell installieren. Jetzt nutzt die App die Gemini API, und man braucht nur einen Link.
- **Veraltetes Modell:** Das zuerst genutzte Modell wurde von Google für neue Nutzer abgeschaltet (Fehler 404). Der Modellname steht jetzt als Konstante `MODEL` oben im Code und lässt sich leicht ändern.
- **Überlastete Server (Fehler 503):** Bei hoher Nachfrage antwortet die API manchmal nicht. Die App wartet in diesem Fall kurz (2, dann 4 Sekunden), versucht es bis zu 3-mal erneut und zeigt danach eine verständliche Meldung statt eines Absturzes.
- **Kaputtes JSON:** Das Modell liefert gelegentlich ungültige Ausgaben. Auch hier gibt es bis zu 3 Versuche.
- **Zeitlimit:** Anfragen brechen nach 60 Sekunden ab, damit die App nicht endlos lädt.
- **Missbrauchsschutz:** Der API-Key ist öffentlich nutzbar, deshalb gibt es maximal 5.000 Zeichen Text und 10 Anfragen pro Sitzung.
## Bekannte Schwächen
 
- Das Modell kann Fragen oder Antworten falsch formulieren, auch wenn der Prompt "nichts erfinden" verlangt. Man sollte die Fragen nicht blind übernehmen.
- Der Schutz vor Missbrauch ist einfach: Wer die Seite neu lädt, bekommt wieder 10 Anfragen. Zusätzlich sollte beim Anbieter ein Ausgabenlimit gesetzt sein.
- Bei hoher Auslastung der API kann die Erstellung lange dauern oder fehlschlagen.
- Nur Text als Eingabe, kein PDF-Upload.
- Die Fragen erscheinen alle auf einmal, nicht nacheinander.
- Keine automatisierten Tests.
## Auswertung (mit eigenen Tests ausfüllen)
 
| Text | Fragen | Inhaltlich korrekt | Auffälligkeiten |
|------|--------|--------------------|-----------------|
|      |        |                    |                 |
 
## Datenschutz
 
Der eingegebene Text wird an die Google Gemini API gesendet. Bitte keine vertraulichen oder personenbezogenen Daten eingeben. Bei der Nutzung des kostenlosen Tarifs können Eingaben laut Google zur Produktverbesserung verwendet werden, die aktuellen Bedingungen stehen bei Google.
 
## Lokal ausführen
 
1. Python installieren und einen API-Key in Google AI Studio erstellen.
2. Pakete installieren:
```
   pip install -r requirements.txt
```
3. Key setzen (Windows PowerShell):
```
   $env:GEMINI_API_KEY="dein-key"
```
   Auf Mac und Linux: `export GEMINI_API_KEY="dein-key"`
4. Starten:
```
   streamlit run app.py
```
 
## Veröffentlichen (Streamlit Community Cloud)
 
1. Repo auf GitHub hochladen. Der API-Key gehört nie in den Code.
2. Auf share.streamlit.io mit GitHub anmelden, das Repo und `app.py` auswählen.
3. Unter "Advanced settings" bei "Secrets" eintragen: `GEMINI_API_KEY = "dein-key"`.
## Ideen für später
 
- PDF-Upload mit `pypdf`, damit man ganze Skripte einlesen kann
- Fragen einzeln nacheinander anzeigen
- Verschiedene Prompts vergleichen und die Qualität messen
- Fortschritt speichern und schwierige Karten häufiger wiederholen
## Technik
 
Python, Streamlit, Google Gemini API (`google-genai`)
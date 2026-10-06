FaceAttend Final UI Upgrade

FILES TO REPLACE IN YOUR PROJECT
1. public/index.html
2. server.js

KEEP YOUR EXISTING .env / DATABASE_URL / JWT_SECRET.
Do not commit .env or API keys.

OPTIONAL AI ON RENDER (recommended: OpenAI)
Add these Render Environment variables:
OPENAI_API_KEY=<your key>
OPENAI_MODEL=gpt-6-luna

The key stays server-side. Never place it in public/index.html.

OLLAMA ALTERNATIVE
OLLAMA_BASE_URL=https://your-reachable-ollama-server.example
OLLAMA_MODEL=llama3.2
A local Ollama running only on your PC cannot be reached by a Render cloud service unless you expose it securely.

WHAT IS INCLUDED
- Unified light/dark glass OS-style UI
- Animated login background + show/hide password
- Large live clock/date with seconds
- SVG icons
- Floating FaceAttend AI assistant
- Teacher timetable dates
- Existing Data Science data stays unchanged
- Classroom scanner remains manually/unlocked accessible as requested
- Admin remove controls for classes, teachers, students and timetable rows
- Admin clear-all-attendance-history control
- Teacher remove attendance-session control
- Existing face enrollment / wall face recognition retained

DEPLOY
Copy both files into your faceattend project, then:
  git add public/index.html server.js
  git commit -m "Finalize FaceAttend UI AI and data controls"
  git push origin main

On Render, add OPENAI_API_KEY and OPENAI_MODEL if you want AI enabled, then redeploy.

FINAL KIOSK + AI UPDATE
- Classroom Scanner is now a separate common wall/kiosk terminal, not a teacher menu item.
- From the login screen choose Classroom Scanner and enter the KIOSK_PIN.
- Set KIOSK_PIN in Render Environment (recommended: a private 6+ digit PIN). Development fallback is 2468; do not rely on that for a real deployment.
- FaceAttend AI now receives live, role-scoped application context (teacher timetable/classes/recent sessions, student attendance, or admin counts) without sending biometric descriptors or password data.
- Teachers still enrol faces and correct attendance; the wall kiosk performs recognition and PRESENT marking.

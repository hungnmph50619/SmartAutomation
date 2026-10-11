# One-click Windows startup

Double-click **Start-SmartAutomation.bat** in the SmartAutomation-UI directory.

The launcher checks local UFO and dependency paths, starts the API on 127.0.0.1:8765 and Vite on 127.0.0.1:5173 only when needed, waits for both health checks, then opens the browser. Two terminal windows stay open while the app is running. A second click avoids starting duplicate services.

The launcher detects UFO from the existing Downloads installation. If that directory moved, set SMARTAUTOMATION_UFO_ROOT and SMARTAUTOMATION_UFO_PYTHON in the environment before launching. First-time installs still require Python 3.11, npm, frontend/node_modules, UFO dependencies and credentials to be set up.

Security: the backend execution feature is enabled locally, but each desktop-control request still requires explicit opt-in in the UI. The launcher does not submit tasks or bypass UFO security. Both services listen only on 127.0.0.1.

To stop the app press Ctrl+C in the two spawned terminal windows (or close them). If a port is occupied by an unrelated service, the launcher stops and explains the conflict; it never terminates arbitrary processes.
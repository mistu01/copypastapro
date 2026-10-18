# Privacy Policy for Mistus Copy Pasta

**Last Updated:** October 2026

**Mistus Copy Pasta** ("the Application") is built with privacy and offline reliability as its core principles. This Privacy Policy describes how your information is handled by the Application.

---

### 1. No Data Collection or Telemetry
- **Zero Cloud Transmission**: The Application does **not** collect, transmit, upload, or sell your personal information, clipboard content, images, 2FA credentials, or usage statistics to external servers or third parties.
- **Offline by Design**: The Application runs 100% locally on your computer and does not require an internet connection or account registration to function.

---

### 2. Local Storage and Data Protection
- **Local SQLite Database**: All clipboard clippings, saved history, and user preferences are stored strictly on your local device in `%APPDATA%\CopyPasta\copypasta.db`.
- **Cached Media**: Local image screenshots and copied images are temporarily cached on your local device in `%APPDATA%\CopyPasta\media` and can be purged at any time from within the app.
- **DPAPI Encryption for 2FA**: Two-Factor Authentication (TOTP) secret keys are protected using Microsoft Windows Data Protection API (DPAPI), meaning they can only be decrypted by your authenticated Windows user account.

---

### 3. System Permissions and Hardware Access
- **Clipboard Monitoring**: The Application accesses the Windows clipboard to record clippings into your local history and simulate paste (`Ctrl+V`) into your selected input fields.
- **Screen Capture**: When you activate the Snipping tool (`PrtScn` or button), the Application captures a temporary screenshot on your screen solely for you to edit, copy, or save locally.
- **Hotkeys**: The Application intercepts `Win + V` while running to surface the CopyPasta clipboard manager flyout. When exiting or uninstalling the app, your native Windows Clipboard History is cleanly restored.

---

### 4. Data Retention and Deletion
- You can clear your clipboard history or delete individual snippets at any time directly through the app interface.
- Choosing **Clear Unpinned History** permanently erases non-pinned clippings from your local database.
- Completely uninstalling the Application deletes all application files and restores Windows registry settings.

---

### 5. Contact Information
For questions, issue reports, or open-source feature requests:
- **Project Repository**: [https://github.com/mistu01/copypastapro](https://github.com/mistu01/copypastapro)
- **Publisher**: Mistus Project

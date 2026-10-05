# Code Signing Policy

Free code signing provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org).

---

## 1. Project Information
- **Project Name**: Mistus Copy Pasta
- **Repository**: [https://github.com/mistu01/copypastapro](https://github.com/mistu01/copypastapro)
- **License**: [MIT License](LICENSE.txt) (OSI-Approved Open-Source License)
- **Project Description**: Next-Gen Windows 11 Fluent dark clipboard manager and 2FA TOTP authenticator with desktop floating island widget and instant selection quick copy.

---

## 2. Purpose of Code Signing
Code signing ensures the integrity and authenticity of official Mistus Copy Pasta releases for Windows users. It guarantees that:
1. The binaries and installers originate directly from the verified source code in this repository.
2. The software has not been altered, tampered with, or injected with third-party code in transit.
3. Users do not encounter Microsoft Defender SmartScreen *"Unknown Publisher"* warnings upon installation.

---

## 3. Scope of Signing
The following release artifacts are signed by this policy:
- **Windows Setup Wizard Installers**: `Mistus_Copy_Pasta_Setup_v*.exe`
- **Standalone Windows Executables**: `MistusCopyPasta.exe`

Only production release artifacts built from official version tags (`v*`) on the `main` branch are eligible for signing under the Release Signing Policy.

---

## 4. Trusted Build Pipeline
All signed artifacts are built in a secure, isolated, and automated Continuous Integration (CI) environment:
- **Build System**: GitHub Actions running on clean, ephemeral `windows-latest` runners.
- **Workflow File**: [`.github/workflows/build-and-release.yml`](.github/workflows/build-and-release.yml)
- **Source Code Verification**: The build workflow checks out code exclusively from official commits on `main`.
- **No Secret Exposure**: Private signing keys are stored exclusively in SignPath's certified Hardware Security Modules (HSM) and are never accessible to maintainers, contributors, or CI runners.

---

## 5. Roles & Responsibilities
- **Project Maintainer**: Mistus Marsh ([@mistu01](https://github.com/mistu01))
- **Responsibilities**:
  - Reviewing and auditing all code changes before merging into `main`.
  - Authorizing release tags and inspecting release notes.
  - Ensuring the GitHub repository and associated accounts maintain Multi-Factor Authentication (MFA/2FA) enabled at all times.
  - Revoking signing permissions immediately in the unlikely event of any security compromise.

---

## 6. Transparency & Auditing
- Every signed artifact is publicly traceable to a specific Git commit hash, release tag, and GitHub Actions build run.
- Build logs and artifacts are publicly visible in the GitHub Actions tab of this repository.

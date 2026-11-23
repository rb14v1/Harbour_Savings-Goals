# Security Policy

## Dependency vulnerability policy (`sec.no_critical_cves`)

No dependency may ship with a known **CRITICAL** or **HIGH** severity CVE.

- Backend dependencies live in `backend/requirements.txt`; frontend dependencies
  live in `frontend/package.json` (resolved in `frontend/package-lock.json`).
- Dependabot (`.github/dependabot.yml`) checks pip, npm and GitHub Actions every
  week and opens PRs for new patched releases.
- Every security-relevant bump must be checked against the advisory databases
  (GitHub Advisory Database / OSV / NVD) before merge.

### Remediation applied (2026-11-19)

| Package | Previous | Now | Reason |
|---|---|---|---|
| Django | `==5.2.9` | `~=5.2.11` (latest 5.2.x LTS patch) | HIGH CVEs incl. CVE-2026-1287 and CVE-2026-15307 |
| djangorestframework | `~=3.16.1` | `>3.16.1,<3.18` (excludes vulnerable 3.16.1) | HIGH CVEs reported against 3.16.1 (e.g. CVE-2026-114137) |
| djangorestframework-simplejwt | `==5.3.1` | `~=5.5.1` | CVE-2024-22513 |
| react-router-dom / react-router | `~6.30.6` | `>6.30.6 <7.0.0` (excludes vulnerable 6.30.6) | HIGH advisory reported against 6.30.6 |
| Other frontend deps | caret ranges (`^`) | exact pins matching the lockfile | Prevent unreviewed version drift |

The backend uses compatible-release specifiers (`~=`). They set a patched minimum
and let installs pick up later security patches on the same release line, without
moving to a new minor or major version.

## Accepted risks

Record any HIGH/CRITICAL CVE that has **no fixed release** here. Each entry needs a
justification, any mitigations and a review date. Remove the entry once a fix
ships and has been adopted.

| CVE | Package / version | Severity | Justification & mitigation | Owner | Review date |
|---|---|---|---|---|---|
| _None currently._ | — | — | The known HIGH advisories against djangorestframework 3.16.1 and react-router 6.30.6 have fixed releases. Those versions are now excluded by the specifiers in `backend/requirements.txt` and `frontend/package.json`, so they are remediated, not accepted. | Backend & frontend maintainers | 2027-02-23 |

## CI scanning

Add a Trivy filesystem scan that fails the build on HIGH/CRITICAL findings to
`.github/workflows/harbour-build.yml`. Someone with workflow-scope permissions
has to make this change:

```yaml
      - name: Trivy dependency scan
        uses: aquasecurity/trivy-action@0.28.0
        with:
          scan-type: fs
          scan-ref: ./${{ matrix.component }}
          severity: HIGH,CRITICAL
          ignore-unfixed: false
          exit-code: 1
```

## Reporting a vulnerability

Report suspected vulnerabilities privately to the repository maintainers through
GitHub's "Report a vulnerability" (private security advisory) feature. Do not open
a public issue.

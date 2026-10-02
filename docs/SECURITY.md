# Security design and boundaries

## Implemented

- Names, symptoms, predictions, assessments and notes are encrypted in the application before database writes using Fernet authenticated encryption.
- Passwords use Werkzeug's salted password hashing. Public registration always creates a patient. Clinicians are provisioned via the local administration CLI.
- Patient queries and PDF downloads are scoped to the authenticated patient's ID. Role guards protect both workspaces.
- Every state-changing form has CSRF protection. Logout requires POST. Login rotates the session contents. Cookies are HttpOnly/SameSite=Lax with a 30-minute sliding lifetime; production additionally requires Secure cookies.
- Login and registration are rate limited. Default storage is per-process memory; deployments need a shared backend and a reviewed reverse proxy setup.
- Security headers restrict scripts/styles to same origin and prevent framing. Responses use no-store. Jinja escapes user text.
- Review and summary creation are committed together. A unique constraint prevents duplicate summaries even with concurrent reviews.
- PDF generation happens in memory. Audit entries record actors, action names, record IDs and time, without copying clinical text.

## Explicit limits

This is field encryption, not full-disk/database encryption. Email addresses, IDs, relationship metadata, timestamps, and audit metadata remain plaintext. Database administrators can alter audit records. All clinician accounts share the demo queue. There is no tenant boundary, MFA, password recovery, session revocation service, retention automation, key rotation workflow, encrypted backup configuration, or compliance certification.

Local keys live beside the database for developer convenience and do not protect against full workstation compromise. Production must provide independent keys from a secret manager and isolate encryption keys from database backups. Losing the key makes encrypted fields unreadable. Existing plaintext databases cannot be upgraded by `create_all`; use a fresh demo database. Production deployment requires a separately designed migration and backup process.

Never publish real patient data, a CV, `.env`, `instance/`, downloaded summaries, or credentials. Use fictional information in screenshots and demo accounts. Public repository excludes the original third-party CSVs until licensing is verified.

## Reporting

For a public repository, use GitHub private vulnerability reporting if enabled. Do not post credentials or health information in issues.

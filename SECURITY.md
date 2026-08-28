# Security Policy

This is a research-analysis package with no network services, authentication,
or user-input execution paths beyond reading local files and fetching a
fixed, documented set of public astronomical-data URLs (see
`docs/DATA_SOURCES.md`): the NASA Exoplanet Archive TAP endpoint and the
CDS/VizieR ASU endpoint, both fixed HTTPS hosts in `src/hwoevidence/data.py`.

## Reporting a vulnerability

Open a GitHub Issue labeled `security` or use GitHub's private
vulnerability reporting for this repository.

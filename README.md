[![tests](https://github.com/boutetnico/ansible-role-sentry/workflows/Test%20ansible%20role/badge.svg)](https://github.com/boutetnico/ansible-role-sentry/actions?query=workflow%3A%22Test+ansible+role%22)
[![Ansible Galaxy](https://img.shields.io/badge/galaxy-boutetnico.sentry-blue.svg)](https://galaxy.ansible.com/boutetnico/sentry)

ansible-role-sentry
===================

This role installs and configures [Self-Hosted Sentry](https://develop.sentry.dev/self-hosted/).

The `install.sh` script is only run when the Sentry version or a configuration
file changes. A marker file (`.ansible-installed-version`) in the install
directory records the last successfully installed version; delete it to force
a reinstall.

Requirements
------------

Ansible 2.19 or newer.

Supported Platforms
-------------------

- [Debian - 12 (Bookworm)](https://wiki.debian.org/DebianBookworm)
- [Debian - 13 (Trixie)](https://wiki.debian.org/DebianTrixie)
- [Ubuntu - 22.04 (Jammy Jellyfish)](http://releases.ubuntu.com/22.04/)
- [Ubuntu - 24.04 (Noble Numbat)](http://releases.ubuntu.com/24.04/)

Role Variables
--------------

| Variable                         | Required | Default                | Choices   | Comments                                          |
|----------------------------------|----------|------------------------|-----------|---------------------------------------------------|
| sentry_version                   | true     | `26.8.0`               | string    | Git tag or branch to clone.                       |
| sentry_install_dir               | true     | `/opt/sentry`          | string    |                                                   |
| sentry_install_options           | true     |                        | string    | See `defaults/main.yml`.                          |
| sentry_mail_host                 | true     | `smtp`                 | string    |                                                   |
| sentry_mail_port                 | true     | `25`                   | int       |                                                   |
| sentry_mail_username             | true     | `25`                   | string    |                                                   |
| sentry_mail_password             | true     | `25`                   | string    |                                                   |
| sentry_mail_use_tls              | true     | `false`                | boolean   |                                                   |
| sentry_mail_use_ssl              | true     | `false`                | boolean   |                                                   |
| sentry_mail_from                 | true     | `root@localhost`       | string    |                                                   |
| sentry_mail_enable_replies       | true     | `false`                | boolean   |                                                   |
| sentry_mail_reply_hostname       | true     | `''`                   | string    |                                                   |
| sentry_mail_mailgun_api_key      | true     | `''`                   | string    |                                                   |
| sentry_system_secret_key         | true     | `!!changeme!!`         | string    | This *should* be set.                             |
| sentry_slack_client_id           | true     | `''`                   | string    |                                                   |
| sentry_slack_client_secret       | true     | `''`                   | string    |                                                   |
| sentry_slack_signing_secret      | true     | `''`                   | string    |                                                   |
| sentry_github_app_id             | true     | `''`                   | string    |                                                   |
| sentry_github_app_name           | true     | `''`                   | string    |                                                   |
| sentry_github_app_webhook_secret | true     | `''`                   | string    |                                                   |
| sentry_github_app_client_id      | true     | `''`                   | string    |                                                   |
| sentry_github_app_client_secret  | true     | `''`                   | string    |                                                   |
| sentry_github_app_private_key    | true     | `''`                   | string    |                                                   |
| sentry_system_url_prefix         | true     | `''`                   | string    | Sets `system.url-prefix`.                         |
| sentry_csrf_trusted_origins      | true     | `[]`                   | list      | Sets `CSRF_TRUSTED_ORIGINS` for multi-domain.     |
| sentry_reverse_ssl_proxy         | true     | `false`                | boolean   |                                                   |
| sentry_geoip_account_id          | true     | `''`                   | string    |                                                   |
| sentry_geoip_license_key         | true     | `''`                   | string    |                                                   |
| sentry_geoip_edition_ids         | true     | `GeoLite2-City`        | string    |                                                   |
| sentry_backup_enabled            | true     | `false`                | boolean   |                                                   |
| sentry_backup_command            | true     |                        | boolean   | See `defaults/main.yml`.                          |
| sentry_backup_frequency          | true     | `daily`                | string    |                                                   |
| sentry_custom_env                | true     | `[]`                   | list      |                                                   |
| sentry_alerts_api_url            | true     |                        | string    | See `defaults/main.yml`.                          |
| sentry_alerts_organization       | true     | `sentry`               | string    | Organization slug.                                |
| sentry_alerts_slack_integration  | true     | `''`                   | string    | Slack integration id used by alerts.              |
| sentry_alerts_token              | true     | `''`                   | string    | Alerts are only managed when set.                 |
| sentry_alerts_user               | true     | `alerts@localhost`     | string    | Service user owning the token.                    |
| sentry_issue_alerts              | true     | `[]`                   | list      | See below.                                        |
| sentry_metric_alerts             | true     | `[]`                   | list      | See below.                                        |

Alerts
------

When `sentry_alerts_token` is set, the role creates a service user with
`sentry createuser`, gives it that token, and manages alerts through the
monitors and alerts API. Monitors are matched by name, so renaming one creates
a new monitor. Alerts removed from the lists are not deleted.

    sentry_metric_alerts:
      - name: Backend is slow
        project: backend
        query: "is_transaction:1"
        aggregate: p95(span.duration)
        time_window: 600       # seconds
        critical: 2000
        warning: 1000
        direction: above       # or below, e.g. for apdex
        owner: team:1          # optional
        slack_channel: { name: monitoring, id: C0123456789 }  # id is optional

    sentry_issue_alerts:
      - name: New issues on backend
        project: backend
        frequency: 30          # minutes
        filters: []            # optional extra conditions
        slack_channel: { name: errors }

Metric alerts on spans only support the aggregates Sentry allows there, e.g.
`count`, `p95`, `avg`, `apdex` or `failure_rate`; `count_if` is rejected.

Dependencies
------------

- Docker
- Git

Example Playbook
----------------

    - hosts: all
      roles:
        - role: ansible-role-sentry

Testing
-------

## Debian

    molecule --base-config molecule/shared/base.yml test --scenario-name debian-12
    molecule --base-config molecule/shared/base.yml test --scenario-name debian-13

## Ubuntu

    molecule --base-config molecule/shared/base.yml test --scenario-name ubuntu-2204
    molecule --base-config molecule/shared/base.yml test --scenario-name ubuntu-2404

License
-------

MIT

Author Information
------------------

[@boutetnico](https://github.com/boutetnico)

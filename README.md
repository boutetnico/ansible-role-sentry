[![tests](https://github.com/boutetnico/ansible-role-sentry/workflows/Test%20ansible%20role/badge.svg)](https://github.com/boutetnico/ansible-role-sentry/actions?query=workflow%3A%22Test+ansible+role%22)
[![Ansible Galaxy](https://img.shields.io/badge/galaxy-boutetnico.sentry-blue.svg)](https://galaxy.ansible.com/boutetnico/sentry)

ansible-role-sentry
===================

This role installs and configures [Self-Hosted Sentry](https://develop.sentry.dev/self-hosted/).

Requirements
------------

Ansible 2.15 or newer.

Supported Platforms
-------------------

- [Debian - 11 (Bullseye)](https://wiki.debian.org/DebianBullseye)
- [Debian - 12 (Bookworm)](https://wiki.debian.org/DebianBookworm)
- [Ubuntu - 22.04 (Jammy Jellyfish)](http://releases.ubuntu.com/22.04/)
- [Ubuntu - 24.04 (Noble Numbat)](http://releases.ubuntu.com/24.04/)

Role Variables
--------------

| Variable                         | Required | Default                | Choices   | Comments                                          |
|----------------------------------|----------|------------------------|-----------|---------------------------------------------------|
| sentry_version                   | true     | `25.11.1`              | string    | Git tag or branch to clone.                       |
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
| sentry_reverse_ssl_proxy         | true     | `false`                | boolean   |                                                   |
| sentry_geoip_account_id          | true     | `''`                   | string    |                                                   |
| sentry_geoip_license_key         | true     | `''`                   | string    |                                                   |
| sentry_geoip_edition_ids         | true     | `GeoLite2-City`        | string    |                                                   |
| sentry_backup_enabled            | true     | `false`                | boolean   |                                                   |
| sentry_backup_command            | true     |                        | boolean   | See `defaults/main.yml`.                          |
| sentry_backup_frequency          | true     | `daily`                | string    |                                                   |
| sentry_custom_env                | true     | `[]`                   | list      |                                                   |

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

    molecule --base-config molecule/shared/base.yml test --scenario-name debian-11
    molecule --base-config molecule/shared/base.yml test --scenario-name debian-12

## Ubuntu

    molecule --base-config molecule/shared/base.yml test --scenario-name ubuntu-2204
    molecule --base-config molecule/shared/base.yml test --scenario-name ubuntu-2404

License
-------

MIT

Author Information
------------------

[@boutetnico](https://github.com/boutetnico)

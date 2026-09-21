# Qu’est-ce qu’OpenCloud ?

[OpenCloud](https://opencloud.eu/) est une plateforme open source de stockage, de
synchronisation et de partage de fichiers. Ce scanner vérifie ses canaux de publication,
sa configuration et ses points d’accès publics. Cette page présente l’architecture qui se
trouve derrière ces contrôles.

<!-- TOC -->
* [What OpenCloud is](#what-opencloud-is)
  * [Where OpenCloud comes from](#where-opencloud-comes-from)
  * [How OpenCloud is structured](#how-opencloud-is-structured)
  * [Why this matters for a security scan](#why-this-matters-for-a-security-scan)
<!-- TOC -->

## Where OpenCloud comes from

OpenCloud is developed as an independent open-source project with its own
releases and support lifecycle. Its Go server uses the CS3 APIs and Reva
components for storage and collaboration. See the
[OpenCloud documentation](https://docs.opencloud.eu/) for deployment and
configuration instructions.

Some public interfaces preserve compatibility with existing clients. For
example, `/status.php` still has a PHP-style name even though OpenCloud is a Go
application. Its response includes both compatibility values and the actual
OpenCloud release. The [status endpoint guide](status-php.md) explains which
fields are useful to a scanner.

## How OpenCloud is structured

OpenCloud combines services for authentication, file access, sharing and its
web interface. The main deployment choices affect what an external scan can see:

| Component | Operational consideration |
|:--|:--|
| Web interface and proxy | Public URL, TLS termination, security headers and forwarded headers |
| Identity provider | Sign-in policy, client registration, account provisioning and second factors |
| Storage | Data and metadata layout, permissions, backups and tested recovery |
| Office and calendar integrations | Separate service configuration, credentials and network boundaries |
| Release track | Update recommendations and the period in which fixes are available |

The absence of a relational database in OpenCloud’s core storage does not mean
the whole deployment has no persistent state. Identity providers and other
integrations can have their own databases and backup requirements.

## Why this matters for a security scan

A familiar endpoint is not enough to identify the software behind it. The
scanner checks the reported product before applying OpenCloud release data,
advisories and configuration rules. A different product is refused instead of
being assigned an OpenCloud grade; see [Troubleshooting](troubleshooting.md).

The result describes what the scanner could observe at the submitted address.
It cannot verify private files, account permissions, backup recovery or all of
an identity provider’s policies. The [secure deployment guide](secure-deployment.md)
covers those separate operational tasks.

## Trademarks and affiliation

This is an independent community project, not affiliated with or supported by
OpenCloud GmbH. OpenCloud and related marks belong to their respective owners
and are used here to identify the software being checked.

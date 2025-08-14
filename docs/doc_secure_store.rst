Security Considerations
=======================

The application stores encrypted configuration values (of type ``str``) within a ``keystore_file``.  
This encryption process uses two components:


- **Master Key** – used to derive the actual encryption key for protecting secrets
- **Salt** – adds randomness and uniqueness to encryption

Both elements are essential to the confidentiality and integrity of stored data.

----

Key Storage Options
-------------------

There are three supported methods for storing the **salt** and **master key** securely:

1. System Keyring (Recommended for Desktop Systems)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Uses the operating system's secure credential store (e.g., **Windows Credential Manager**).
- Provides encrypted, user-specific storage managed by the OS.
- Key creation and updates can be handled automatically by the application.
- **Not supported in most Docker containers** due to lack of desktop session or GUI access.

2. Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~

- Suitable for **Docker containers**, **CI/CD pipelines**, or local development/test setups.
- Secrets must be set on the **Docker host**, passed via ``-e`` flags, or injected via ``.env`` files.
- Key updates **cannot be performed automatically** by the application when running in Docker.
- The application reads environment variables **once at startup**.
- ⚠️ **Caution**: Environment variables may be exposed via process lists (``ps``), logs, or crash dumps. Avoid on shared or multi-tenant systems.

3. Text File (Mounted Secret)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Suitable for **Docker containers** or local development/test setups.
- Keys are stored in a **plain text file** on the host and **mounted read-only** into the container.
- 🔁 Key updates **cannot be handled automatically** by the application when running within a docker container.
- Security depends on proper file handling:

  - Apply restrictive file permissions (e.g., ``chmod 600``)
  - Limit host access to authorized users only
  - Ensure files are excluded from version control and backup systems

- Example: ``-v /host/keys/master_key:/app/secrets/master_key:ro``

----

Key Lifecycle Management
------------------------
The application can generate both the **master key** and the **salt**.  
However, **automatic storage is only supported when using the System Keyring**.  
In Docker-based environments, generated keys must be **manually copied** to the configured storage location  
(e.g., mounted file or environment variable).

Master Key
~~~~~~~~~~

- Generated **during application installation** and regenerated when triggered.
- Should be changed regularily (e.g. once a year). This needs to be done by the app using mgconf.

Salt
~~~~

- The salt is a random value added to data before hashing (like passwords). Its main purpose is to prevent precomputed attacks (rainbow tables) and make hashes unique, even for identical inputs.
- Generated **once during application installation**.
- Must remain **unchanged across application updates** to ensure encrypted values remain decryptable


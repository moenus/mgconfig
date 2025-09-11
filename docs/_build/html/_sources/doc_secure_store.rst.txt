Security Considerations
=======================

The application stores configuration values of type ``secret`` inside a ``keystore_file`` in **encrypted format**.  
Encryption relies on two components:

- **Master Key** – used to derive the actual encryption key for protecting secrets  
- **Salt** – adds randomness and uniqueness to encryption  

Both are critical to ensuring the **confidentiality** and **integrity** of stored data.

Salt
----

- A **random value** added to data before hashing (e.g., passwords).  
- Prevents precomputed attacks (rainbow tables) and ensures uniqueness, even for identical inputs.  
- Generated **once during keystore_file creation**.  
- Stored in the **keystore file header** to allow decryption of encrypted values.  
- Can be made public without creating a security risk

----

Key Storage Options
-------------------

The **master key** can be stored in one of three ways:

1. System Keyring (Recommended for Desktop Systems)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Uses the operating system’s secure credential store (e.g., **Windows Credential Manager**).  
- Provides encrypted, user-specific storage managed by the OS.  
- Key creation and updates can be handled automatically by the application.  
- ⚠️ **Not supported in most Docker containers** (no desktop session or GUI).  

2. Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Suitable for **Docker containers**, **CI/CD pipelines**, or local development/test setups.  
- Secrets must be provided via Docker host configuration (``-e`` flags, ``.env`` files, or injected securely).  
- Key updates **cannot be automated** when running in Docker.  
- Application reads environment variables **only once at startup**.  
- ⚠️ **Caution**: Environment variables can be exposed in process lists (``ps``), logs, or crash dumps. Avoid on shared or multi-tenant systems.  

3. Text File (Mounted Secret)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Suitable for **Docker containers** or local development/test setups.  
- Keys are stored in a **plain text file** on the host and mounted **read-only** into the container.  
- 🔁 Key updates **must be handled manually** (application cannot rotate keys in containers).  
- Security relies on proper file handling:
  
  - Use restrictive file permissions (e.g., ``chmod 600``).  
  - Restrict host access to authorized users only.  
  - Exclude key files from version control and backups.  

- Example:  

  ``-v /host/keys/master_key:/app/secrets/master_key:ro``  

----

Key Lifecycle Management
------------------------
The application can generate a new **master key**, but **automated storage of this key is only supported with the System Keyring**.  

In Docker-based environments, generated keys must be **manually transferred** to the configured storage location (e.g., mounted file or environment variable).  

Master Key
^^^^^^^^^^
- Generated **during installation** or when explicitly triggered.  
- Should be rotated **regularly** (e.g., annually).  
- Rotation is performed via the application using ``mgconf``.  

----

Known Limitations
-----------------
- The implementation is **not resistant to memory forensics**.  

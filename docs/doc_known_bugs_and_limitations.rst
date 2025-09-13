
Known Bugs and Limitations
==========================

- ``None`` type is used for missing values. 

  Therefore setting a value to ``None`` will delete this value from the ``configuration file`` respectively from the ``securestore file``. A default cannot be overwritten with ``None`` from a higher priority source. 
  A value can only be None, if there is no default and the value was not set in the environment variables or one of the above mentiioned files. 

- The package is not thread-safe.

  As configuration values should be determined only once at application startup and changing configuration values is assumed to happen not very often, this might be acceptable for most use cases. 
  If you need thread-safety it needs to be applied as a wrapper around the used mgconfig objects. 

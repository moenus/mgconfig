Usage Tips and Hints
====================

- The order of the configuration definitions within the configuration definion files and the order of the files (when working with multiple configuration definion files) is important. 
  The default reference resolution requires that the referenced configuration item was evaluated before.

- A section prefix can be used for multiple sections. The config_id ([section_prefix]_[config_name]) must be unique. 

- The **configuration definition files** should be considered part of the source code. They will be read only once at application startup.

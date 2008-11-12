A parser for [OpenEXR](http://www.openexr.com/) files, implemented purely in Python.

This is not designed to be fast, or complete. It is written to learn about the OpenEXR file format.

----

Status: *Work in progress*

Currently can parse:

- The "magic number" (file check)
- The version number
- Headers

It also deals correctly with the following data-types:

- string
- float
- compression
- box2i
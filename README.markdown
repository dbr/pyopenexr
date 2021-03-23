A parser for [OpenEXR](http://www.openexr.com/) image files, implemented purely in Python.

This is not designed to be fast, or complete. It is written to learn about the OpenEXR file format.

You probably want to use Python bindings to the OpenEXR library, such this:

https://github.com/jamesbowman/openexrpython

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
- lineOrder

It cannot currently parse:

- Image data

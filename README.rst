======
calval
======

|Build Status|_

Python Library for access and manipulation of satellite measurement sets containing
parameters such as surface and TOA reflection coefficients of specific calibration sites.

Input data comes as zipped products in provider specific format.
The attached `make_sm.py` script contains sample code.

.. |Build Status| image:: https://travis-ci.org/satellogic/calval.svg?branch=master
	          :alt: Build Status
.. _Build Status: https://travis-ci.org/satellogic/calval

Installation:
-------------------

``pip install calval``



Usage:
-------------------
define spectral response of a camera:

.. image:: https://user-images.githubusercontent.com/17533233/43821388-b28e5444-9af1-11e8-91e3-918945562d29.png

simulate TOA/SR of specific camera, from site measurements:

.. image:: https://user-images.githubusercontent.com/17533233/43821224-2e2a18e6-9af1-11e8-9c54-f01faec1a168.png

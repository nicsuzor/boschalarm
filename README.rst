========================
Bosch Solution Alarm API
========================


.. image:: https://img.shields.io/pypi/v/boschalarm.svg
        :target: https://pypi.python.org/pypi/boschalarm

.. image:: https://img.shields.io/travis/nicsuzor/boschalarm.svg
        :target: https://travis-ci.com/nicsuzor/boschalarm

.. image:: https://readthedocs.org/projects/boschalarm/badge/?version=latest
        :target: https://boschalarm.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/nicsuzor/boschalarm/shield.svg
     :target: https://pyup.io/repos/github/nicsuzor/boschalarm/
     :alt: Updates



A python API to connect to Bosch Solution 2000/3000 alarm systems over local tcp/ip sockets


* Free software: GNU General Public License v3


Features
--------

* TODO


Bugs
----
The **connection to the alarm is insecure**. The Bosch certificate expired in 2022 and needs a firmware update. The alarm also does not speak modern TLS; this package relies on you running an older version of python with an older version of openssl that still has support for SSLv2. BEWARE.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

# The Bobolith

![Bobolith](chezbob/bobolith/static/snack_odyssey_2001.png)

This repository contains the Chez Bob 2020 codebase. It is organized as a set of Python packages under the `chezbob` [namespace package](https://packaging.python.org/guides/packaging-namespace-packages/). 


The contents of the `chezbob` namespace are as follows:

### `bobolith`

The Django+channels server proper. The `manage.py` in the root of this repository manages and runs this site. This site depends on other packages in the `chezbob` namespace.

### `accounts`

A reusable Django+channels app that extends/replaces the default `django.contrib.auth` app with Chez Bob specific functionality.

### `appliances`

A reusable Django+channels app for managing appliances, including:

- Registering appliance consumers by UUID.
- Dispatching websocket connect attempts to the correct consumers.
- Linking appliances.
- ...
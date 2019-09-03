GSKY Provisioning
=================

Overview
--------

This repo contains scripts to automatically build, configure and provision GSKY to one 
or more raijin HPC nodes. All the GSKY dependencies are built from source to take 
advantage of the native CPU instruction set on raijin nodes. MAS indexing data and GSKY 
config files are constructed as closely as possible from the production environment. 

Prerequisites
-------------

* [Anaconda3](https://www.anaconda.com/distribution/#download-section) on Linux is 
required to run the scripts.

* The runtime environment is the raijin HPC nodes.

Building GSKY
----------------

Run `build_gsky.py` to build all the required dependencies as well as GSKY itself. By
default, all the binaries will be installed into the `gsky` directory under the current
working directory. It is safe to run this script multiple times. The dependecies that 
have been built will be skipped from re-building. GSKY, however, re-builds from the
Github master branch every time `build_gsky.py` is run.

`build_gsky.py` is also successfully tested on tenjin with some minor modifications.

Main entry scripts
------------------

 The main entry scripts are `provision_single_node.py` and
`provision_multi_node.py`. These two scripts illustrate the essential workflow of
orchestrating GSKY components (see below) to lanuch an instance of GSKY. The Aster 
dataset is used as an example to demostrate a WMS GetMap operation.

GSKY components
---------------

* There are three components for managing GSKY server processes - `ows.py`, `mas.py` and
`worker.py`. These scripts abstract environment and process management of the underlying 
GSKY processes. 

* `mas.py` also manages the Postgres indexer database as well as ingesting crawl files
into the indexer database. `mas.py` delegates to `pg_sql.py` for Postgres management.

* `env_configs.py` provides a central place for managing the envrionment settings of GSKY
such as PATH, LD_LIBRARY_PATH, server ports, and so on.

GSKY config files
------------------

`gsky_config.py` generates `config.json` (aka. GSKY config file) from the yaml files under
the `assets` directory. yaml files are easier to tweak than json files especially when
the config file gets complex. This is how config management is actually done in the
production environment.

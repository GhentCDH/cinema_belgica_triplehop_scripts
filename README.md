TripleHop scripts for the Cinema Belgica project
==============================================

Preprocess data
---------------

Prerequisites:

* Make sure the original csv files exist within the `data/original` folder.
* Make sure the censorship fixtures exist within the `data/fixtures` folder.

The data can be preprocessed using the `preprocess_data.py` script as follows:

```sh
python cinema_belgica_triplehop_scripts/preprocess_data.py
```

The sources can be processed using the `preprocess_sources.py` script as follows:

```sh
python cinema_belgica_triplehop_scripts/preprocess_sources.py
```

Import data
-----------

Prerequisites:

* Add the basic db structure, add user data, add db structure for revisions, generate group config, generate relation config and process the config files using the `triplehop_import_tools` package.
* Make sure the data has been preprocessed.

The data can be imported using the `import_data.py` script as follows:

```sh
python cinema_belgica_triplehop_scripts/import_data.py
```

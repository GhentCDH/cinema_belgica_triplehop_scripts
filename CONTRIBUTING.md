# Contributing Guide

We're really excited that you are interested in contributing to Ciname Belgica. Please take a moment to read through our [Code of Conduct](CODE_OF_CONDUCT.md) first. All contributions (participation in discussions, issues, pull requests, ...) are welcome. Unfortunately, we cannot make commitments that issues will be resolved or pull requests will be merged swiftly, especially for new features.

Documentation is currently severely lacking. Please contact <https://github.ugent.be/pdpotter> to get started.

## Development set-up (based on a Debian Virtual Machine)

### Install Poetry

    ```sh
    sudo apt-get install python3-distutils
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="/home/vagrant/.local/bin:$PATH"
    ```

### Download code

    ```sh
    git clone git@github.com:GhentCDH/cinema_belgica_triplehop_scripts.git
    ```

### Install Python dependencies (in code folder)

    ```sh
    poetry install
    ```

### Preprocess data

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

### Import data

Prerequisites:

* Add the basic db structure, add user data, add db structure for revisions, generate group config, generate relation config and process the config files using the [triplehop_import_tools](https://github.com/GhentCDH/triplehop_import_tools/blob/main/CONTRIBUTING.md) package.
* Make sure the data has been preprocessed.

The data can be imported using the `import_data.py` script as follows:

    ```sh
    python cinema_belgica_triplehop_scripts/import_data.py
    ```
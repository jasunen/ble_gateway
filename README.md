# BLE Gateway for Raspberry Pi

## Uses
- python 3.7
- [aioblescan](https://github.com/frawau/aioblescan) by frawau

## Setup for running
```sh
# Install dependencies
pipenv install
```

## Setup for development
```sh
# Install dependencies
pipenv install --dev

# Setup pre-commit and pre-push hooks
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

## Credits
Template for this package was created with Cookiecutter and the [sourceryai/python-best-practices-cookiecutter](https://github.com/sourceryai/python-best-practices-cookiecutter) project template.

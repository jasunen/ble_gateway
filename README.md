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

# Helpful infos
- https://github.com/influxdata/influxdb-python/blob/master/examples/tutorial_server_data.py
- https://github.com/frawau/aioblescan/blob/master/aioblescan/__main__.py
- https://github.com/Scrin/RuuviCollector
- https://github.com/ttu/ruuvitag-sensor/blob/master/examples/http_server_asyncio.py
- https://docs.python.org/2/library/multiprocessing.html

# To-Do list
- implement run_ble process for reading ble messages
- verify ruuvitag message encoding (do we need decoder from ruuvitag-sensor?)
- implement data_writers (to influxDB, ThingSpeak, etc)
- use multiprocessing module for run_ble and data_writers
- inter process communication using multiprocessing queue

## Credits
Template for this package was created with Cookiecutter and the [sourceryai/python-best-practices-cookiecutter](https://github.com/sourceryai/python-best-practices-cookiecutter) project template.
Based on great aioblescan by @frauwau

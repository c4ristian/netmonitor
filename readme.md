# netmonitor

## What is it?
This Python library provides tools network monitoring.

## Main Features
The library offers [common](netmonitor/commons.py) functions, [notebooks](notebooks) and scripts.

## Where to get it
The source code is currently hosted on GitHub at:
https://github.com/c4ristian/netmonitor

## Setup
```sh
conda env create -f environment.yml

conda activate netmonitor
```

## Run Tests
```sh
pytest
```

## Code Coverage
```sh
pytest --cov
```

## Code Quality
```sh
pylint FILENAME.py
```

## Run script
```sh
python FILENAME.py
```

## Jupyter
### Install Kernel 
```sh
python -m ipykernel install --user --name=netmonitor
```

### Run Notebooks
```sh
jupyter notebook --notebook-dir="./notebooks"
```

## License
[Apache 2.0](LICENSE.txt)


## Contact us
[christian.koch@th-nuernberg.de](mailto:christian.koch@th-nuernberg.de)

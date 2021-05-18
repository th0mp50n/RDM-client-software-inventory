# iRODS performance test script

Author: Christine Staiger (Wageningen University & Research)

## Synopsis

This little script is made to quickly run performance tests on different iRODS clients. Currently, the script runs the icommands, the python iRODS API and cadaver (on the webdav endpoint Davrods).

## Prerequisites

To run the script you need a Linux environment with:

- Cadaver
- icommands
- Python iRODS API

Further python dependecies:

- Python 3.6
- pickle
- matplotlib
- numpy
- pandas

## Usage

```
python3 irodsPerf.py
```

Results will be stored in a pickle file `irodsPerformances.out.pickle`.


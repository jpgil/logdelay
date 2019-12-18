# logdelay
Code for Master Thesis in Mathematical Modelling
jgil@2019-12-17

To enable the notebooks you need to activate the venv


Dataset
-------
You need the file logdelay-original-dataset.tar.bz2 in logdelay/
From here, you need to uncompress it to create the data tree structure:
```bash
tar -jxf logdelay-original-dataset.tar.bz2

data
|-- external
|-- interim
|-- processed
`-- raw
    |-- ALMA
    `-- PARANAL
```

ENV Setup
---------
```bash
source venv/bin/activate

pip install jupyterlab
jupyter serverextension enable --py jupyterlab --sys-prefix
```

Notebooks
------------
Open Jupyter lab and browse into notebook folders:
```bash
jupyter lab
```

And browse into the notebooks.

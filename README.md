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
If you haven't set your environment yet, go to logdelay and execute:
```bash
python -venv venv
```

in Mac, you need to instally pygraphviz and networkx
```
# option 1:
brew install graphviz
pip install pygraphviz
pip install networkx

# option 2, seems to not work anymore
pip install --install-option="--include-path=/usr/local/include/" --install-option="--library-path=/usr/local/lib/" pygraphviz
```

Then, go to logdelay/ and execute
```bash
source venv/bin/activate
pip install -r requirements.txt
```
Some common tricks:
```bash
# Freeze new dependencies
pip freeze > requirements.txt
```

Notebooks
------------
Open Jupyter lab and browse into notebook folders:
```bash
jupyter lab
```

And browse into the notebooks.

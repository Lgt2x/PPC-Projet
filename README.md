# PPC-Projet
by Antoine Merle & Louis Gombert, January 2021

## Installation guide
1) Install the requirements (use virtualenv)

```bash
pip install -r requirements.txt
```

2) Then, launch the server :
```bash
cd market_simulation
python server.py config.json
```

3) Run the client
```bash
python client.py
```

You can edit some simulation parameters by changing the server config json file.

Check the pylint compliance with `pylint market_simulation`

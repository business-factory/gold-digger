# Gold-digger (Exchange rates service)


## Used technologies
 - [Python](https://www.python.org/)
 - [PostgreSQL](http://www.postgresql.org/)


## Development setup
```sh
python -m venv .env
. ./.env/bin/activate  # or for BFU .env\Scripts\activate.bat
pip install -U pip wheel
pip install --use-wheel -r requirements-dev.txt
```

Create PostgreSQL database and user named *gold-digger*.

Create local configuration file called `gold_digger/config/params_local.py` with configuration for local machine.
For development purposes there is no configuration required so file may look like the below one:

```python
# -*- coding: utf-8 -*-

LOCAL_CONFIG_PARAMS = {

}
```

## Usage
Create local database and update connection parameters.

* `python -m gold_digger initialize-db` to create tables
* `python -m gold_digger update [--date="yyyy-mm-dd"]` to update rates of specified date (default today)
* `python -m gold_digger update-all [--origin-date="yyyy-mm-dd"]` to update rates since specified origin date
* `python -m gold_digger serve` starts API server

## API endpoints

* /rate?from=X&to=Y&date=YYYY-MM-DD
	* from currency - required
	* to currency - required 
	* date of exchange - optional; returns last exchange rates if omitted 

	* example: http://localhost:25800/rate?from=EUR&to=USD&date=2005-12-22

* /range?from=X&to=Y&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
	* from currency - required
	* to currency - required
	* start date + end date of exchange - required
	
    * example: hhttp://localhost:25800/range?from=EUR&to=AED&start_date=2016-02-15&end_date=2016-02-15
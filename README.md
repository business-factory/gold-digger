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

## Usage
Create local database and update connection parameters.

* `python exchange_rates.py recreate-db` to create table
* `python exchange_rates.py update` to update rates from today
* `python exchange_rates.py update-all` to update rates from specified origin date
* `python exchange_rates.py serve` start API server

## API endpoints

* /rate?from=X&to=Y&date=YYYY-MM-DD
	* from currency - required
	* to currency - optional; returns all available currencies if omitted 
	* date of exchange - optional; returns last exchange rates if omitted 

	* example: http://localhost:25800/rate?from=EUR&to=USD&date=2005-12-22

* /range?from=X&to=Y&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
	* from currency - required
	* to currency - optional; returns all available currencies if omitted
	* start date + end date of exchange - required
	
    * example: hhttp://localhost:25800/range?from=EUR&to=AED&start_date=2016-02-15&end_date=2016-02-15
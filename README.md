# Gold-digger (Exchange rates service)


## Used technologies
 - [Python 3.5](https://www.python.org/)
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
Available commands:

* `python -m gold_digger initialize-db` creates all tables in new database
* `python -m gold_digger update [--date="yyyy-mm-dd"]` updates exchange rates for specified date (default today)
* `python -m gold_digger update-all [--origin-date="yyyy-mm-dd"]` updates exchange rates since specified origin date
* `python -m gold_digger serve` starts API server

For running the tests simply use:
* `py.test` or `ptw` which starts watchdog which run the tests after every save of Python file
* `py.test --database-tests --db-connection postgres://postgres:postgres@localhost:5432/golddigger-test` (with custom db connection) which runs also tests marked as `@database_test`.
 These tests are executed against real test database.


## API endpoints

* `/rate?from=X&to=Y&date=YYYY-MM-DD`
	* from currency - required
	* to currency - required 
	* date of exchange - optional; returns last exchange rates if omitted 

	* example: [http://localhost:8000/rate?from=EUR&to=USD&date=2005-12-22](http://localhost:8000/rate?from=EUR&to=USD&date=2005-12-22)

* `/range?from=X&to=Y&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
	* from currency - required
	* to currency - required
	* start date & end date of exchange - required
	
    * example: [http://localhost:8000/range?from=EUR&to=AED&start_date=2016-02-15&end_date=2016-02-15](http://localhost:8000/range?from=EUR&to=AED&start_date=2016-02-15&end_date=2016-02-15)
    
## Docker
Ensure you have created local params file according to *Development setup* section. Then build docker image.

`docker build -t gold-digger-ubuntu .`

If you are connecting to local database on the host (outside the container) run the container with --net=host option.

`docker run --name gold-digger --net=host -t -i -p 8000:8000 gold-digger-ubuntu`

Run production container as daemon (production).

`docker run --name gold-digger -d -p 8000:8000 gold-digger-ubuntu`

Docker container starts the Gunicorn server. Web server is kept alive by supervisor. Cron performs daily updates at 00:05.

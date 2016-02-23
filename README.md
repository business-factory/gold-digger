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

Now you can run test by command `py.test` or start watchdog that run the tests
after every save of Python file by command `ptw`.

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

* `/rate?from=X&to=Y&date=YYYY-MM-DD`
	* from currency - required
	* to currency - required 
	* date of exchange - optional; returns last exchange rates if omitted 

	* example: [http://localhost:25800/rate?from=EUR&to=USD&date=2005-12-22](http://localhost:25800/rate?from=EUR&to=USD&date=2005-12-22)

* `/range?from=X&to=Y&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
	* from currency - required
	* to currency - required
	* start date + end date of exchange - required
	
    * example: [http://localhost:25800/range?from=EUR&to=AED&start_date=2016-02-15&end_date=2016-02-15](http://localhost:25800/range?from=EUR&to=AED&start_date=2016-02-15&end_date=2016-02-15)
    
## Docker
Ensure you have created local params file according to *Development setup* section. Then build docker image.

`docker build -t gold-digger-ubuntu .`

If you are connecting to local database on the host (outside the container) run the container with --net=host option.

`docker run --name gold-digger --net=host -t -i -p 8000:8000 gold-digger-ubuntu`

Run production container as daemon (production).

`docker run --name gold-digger -d -p 8000:8000 gold-digger-ubuntu`

Docker container starts the Gunicorn server. Web server is kept alive by supervisor. Cron performs daily updates at 00:05.

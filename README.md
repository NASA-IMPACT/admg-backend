# Contents of this readme

1. `admg_webapp` backend documentation
2. `admin_ui` frontend setup

# `admg_webapp` backend documentation

## ER Diagrams

Entity Relationship Diagrams can be found at this [link](https://drive.google.com/drive/folders/1_Zr_ZP97Tz8hBk5wxEpLmZ8Es2umJvjh)

## How to use the interactive Query

```
pip install notebook<br>
pip install django-extensions
```

Add django_extensions to installed apps unless using cookiecutter<br>

```
python manage.py shell_plus --notebook
```

in the notebook, import your models file

## How to get the token

- go to /authenticate/applications/register/
- create a user and verify the email address by clicking on the link that shows up in the terminal where you've done `python manage.py runserver`
- register the app
- Use Client Type: confidential, Authorization Grant Type: Resource owner password-based
- get the `client_id` and `client_secret`
- `curl -X POST -d "grant_type=password&username=<user_name>&password=<password>" -u"<client_id>:<client_secret>" http://domain/authenticate/token/`
- You will get something like:

  ```javascript
  {
      "access_token": "access_token",
      "expires_in": 36000,
      "token_type": "Bearer",
      "scope": "read write",
      "refresh_token": "refresh_token"
  }
  ```

- Use this `access_token` to hit on APIs
  - `curl -H "Authorization: Bearer <your_access_token>" http://localhost:8000/your_end_point_here`
- To refresh your token
  - `curl -X POST -d "grant_type=refresh_token&refresh_token=<your_refresh_token>&client_id=<your_client_id>&client_secret=<your_client_secret>" http://localhost:8000/authenticate/token`

Example JavaScript code

```
const url = 'http[s]://www.domain.com/authenticate/token/';
const cId = '<application client id>'
const cSecret = '<application sectret key>'
const data = new FormData();
data.append('username', '<username>');
data.append('password', '<password>');
data.append('grant_type', 'password');
const config = {
   method: 'post',
   url,
   data,
   auth: {
      username: cId,
      password: cSecret,
   }
};
axios(config)
.then(function (response) {
   // response.access_token will have the token
})
```

## Automatic deployment

- Update the webserver IP in the hosts/<environment> file. If no hosts file exists, create one [see hosts/<environment>.sample file]
- Run the command `ansible-playbook --private-key private_key_file.pem -i hosts/<environment> playbook.yml -v [-e 'branch=<your_branch_here>']`
  - `private_key_file.pem` is the private key for the webserver
  - `environment` a choice of staging or production
  - `[-e 'branch=<your_branch_here>']` part is optional and can be used in case some another branch is desired

## Local Setup

- Install docker and docker-compose
- Copy `.env.sample_local` to `.env`
- Run docker-compose with docker-compose.local.yml instead of docker-compose.yml
  - `docker-compose -f docker-compose.local.yml up`

## Running Tests

`docker-compose -f docker-compose.local.yml run web python manage.py test`

### Reporting test coverage

Run your tests with coverage:

`docker-compose -f docker-compose.local.yml run web coverage run -m pytest`

Generate coverage report:

`docker-compose -f docker-compose.local.yml run web coverage report -m --skip-covered`

If you want to view coverage in your editor using, for example, VSCode's Coverage Gutters plugin, export the coverage report to a supported format:

`docker-compose -f docker-compose.local.yml run web coverage lcov -o coverage.lcov`

## Sass

To build Sass files for the project:

```sh
python manage.py sass admin_ui/static/scss admin_ui/static/css --watch
```

# `admin_ui` setup

## Installation

1.  Install prerequisite technologies (for example, using `brew` on a mac): postgres, postgis

2.  Create a virtual environment

    Set up the env (only need to do once)

    ```
    python3 -m venv .venv
    ```

3.  Activate the virtual environment (do this every time you start the project)

    ```
    source .venv/bin/activate
    ```

4.  Install requirements

    1. general requirements

       ```
       pip install -r requirements/base.txt
       ```

    2. local requirements

       ```
       pip install -r local.txt
       ```

5.  Start postgres

    To get a path that you can use to start Postgres:

    ```
    brew info posgresql
    ```

    (It will probably look something like `pg_ctl -D /usr/local/var postgres start`)

6.  Check that postgres is working
    If `psql -l` gives you a list of tables then all is well.

7.  Create a database

    ```
    createdb admg_prod
    ```

8.  Load a dump of the database

    Download the latest zip file of example data (get this from one of the database maintainers) & load into the database. For example:

    ```
    cat ./production_dump-2020.01.28.sql | psql admg_prod
    ```

9.  Run migrations

    ```
    python manage.py migrate
    ```

10. Create yourself a user

    ```
    python manage.py creatersuperuser
    ```

## Running the application

1. With the virual environment activated, run the server

   ```
   python manage.py runserver_plus
   ```

2. Open the website
   http://localhost:8000/

### Understanding `python manage.py`

`python manage.py <command>`

- `manage.py` is your entry point into the django app. It has several commands, including:
  - `test`
  - `migrate`
  - `makemigrations`
  - `runserver_plus`
  - `shell_plus`
  - django extensions — third party modules

### Optional additional tools

interactive way to interact with the database and the database models.

`python manage.py shell_plus`

### Running the infrastructure for DOI fetching

DOI fetching uses rabbitmq and celery.

#### Installation

Install `rabbitmq` (probably using `brew` if you’re on a Mac)

#### Starting the service

1. start rabbitmq:

   ```
   rabbitmq-server
   ```

2. start the celery worker:

   ```
   celery -A config.celery_app worker --beat --scheduler django -l DEBUG
   ```

   _Note: If running locally (ie not in Docker), you may need to overwrite the `CELERY_BROKER_URL` setting:_

   ```
   CELERY_BROKER_URL=amqp://guest:guest@localhost:5672 celery -A config celery_app worker --beat --scheduler django -l DEBUG`
   ```

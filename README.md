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
- You will get something like
  - ```javascript
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
- Run docker-compose with docker-compose.local.yml instead of docker-compose.yml
  - `docker-compose -f docker-compose.local.yml up`

## Sass

To build Sass files for the project:

```sh
python manage.py sass admin_ui/static/scss admin_ui/static/css --watch
```

# `admin_ui` frontend setup

## Installation
1. Install prerequisite technologies (for example, with `brew` on a mac): postgres, postgis

2. Create a virtual environment

Set up the env (only need to do once)
> `python3 -m venv .venv`

To activate the env (do this every time you start the project)
> `source .venv/bin/activate`

3. Install requirements

Part 1 - general requirements
> `pip install -r requirements/base.txt`

Part 2 - local requirements
> `pip install -r local.txt`

4. Start postgres

`brew info posgresql` should give a path that you can use to start it (It will probably look something like `pg_ctl -D /usr/local/var/postgres start`)

5. Check that postgres is working
If `psql -l` gives you a list of tables then all is well.

6. Create a database
> `createdb admg_prod`

7. Load a dump of the database
- download the latest zip file of example data (get this from one of the database maintainers)
For example:
> `cat ./production_dump-2020.01.28.sql | psql admg_prod` 

(change the filename to match your local db data)

## Start service

1. Activate your environment
> `source .venv/bin/activate`

### Understanding `python manage.py`
`python manage.py <command>`

- `manage.py` is your entry point into the django app. It has several commands, including:
    - `test` `migrate` `makemigrations` `runserver_plus` `shell_plus`
    - django extensions — third party modules

### Set up your database
1. Create the migrations
> `python manage.py migrate`

2. (varies depending on how the data model develops)
You first have to delete all the problematic tables `psql admg_prod -c "delete from data_models_doi";`) also `data_models_instrument_dois`; `data_models_platform_dois`; `data_models_collectionperiod_dois`;

3. Create yourself a user

> `python manage.py creatersuperuser`

4. Run the server

`python manage.py runserver_plus`

5. Open the webiste 
http://localhost:8000/

### Optional additional tool
interactive way to interact with the database and the database models.

> `python manage.py shell_plus`

### Running the infrastructure for DOI fetching
DOI fetching uses rabbitmq and celery.

Installation
install `rabbitmq` (probs using `brew` if you’re on a Mac)

Starting the service
1. start rabbitmq with `rabbitmq-server` 
2. start the celery worker: 
    ```
    celery -A config.celery_app worker --beat --scheduler django -l DEBUG
    ```

_Note: If running locally (ie not in Docker), you may need to overwrite the `CELERY_BROKER_URL` setting:

```
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672 celery -A config.celery_app worker --beat --scheduler django -l DEBUG
```
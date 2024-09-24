# ADMG Project Repo
Welcome to the ADMG project repository. This repository contains the code for the ADMG web application, which is a Django web application that provides a user interface for the ADMG database. The application is built using the Django web framework and is designed to be deployed using Docker.


## README Contents
- Project Structure
- Local Development
- Additional Dev Tools
- Automated Deployment
- Configuring system to deploy CASEI


## Project Structure
- frontend: `/app/admin_ui`
- backend: `/app/admg_webapp`

## Local Development

### Project Setup

1. Install docker
2. Copy `.env.sample_local` to `.env`
3. Run docker compose <br />
  `docker compose up`

#### If this is your first time setting up & running the application, you will also need to:
**Run migrations** to create the database schema:
```sh
docker compose run --rm web sh -c "python manage.py migrate"
```
**Create a superuser** to access the admin interface:
``` sh
docker compose run --rm web sh -c "python manage.py createsuperuser"
```
**Load a dump** of the database to view the application with some data:
Download the latest zip file of example data (or get this from one of the database maintainers) & load into the database. The following command will load the data into the database:
```sh
cat ./production_dump-2020.01.28.sql | psql admg_webapp
```

> ^ These commands should be run in a new terminal window, while the application is running.

## Additional Dev Tools


### Understanding `python manage.py`

`python manage.py <command>`

`manage.py` is your entry point into the django app. It has several commands, including:
  - `test`
  - `migrate`
  - `makemigrations`
  - `runserver_plus`
  - `shell_plus`
  - django extensions — third party modules

To run python manage.py commands using docker compose, use the following command structure:
  ```
  docker compose run --rm -it web python manage.py <command>
  ```

### Shell Access

Utilize Django's shell for experimentation with queries & other Django functionality:

```sh
docker compose run --rm -it web python manage.py shell_plus
```
### Project URLs

List all of the URL patterns for the project:
```sh
docker compose run --rm it web python manage.py show_urls
```
### Running Tests

Run your tests:
```sh
docker compose run --rm -it web pytest
```

### Reporting test coverage

Run your tests with coverage:
```sh
docker compose run --rm -it web python -m coverage run -m pytest
```

Generate coverage report:
```sh
docker compose run --rm -it web python -m  coverage report -m --skip-covered
```

If you want to view coverage in your editor using, for example, VSCode's Coverage Gutters plugin, export the coverage report to a supported format:

```sh
docker compose run --rm -it web python -m coverage lcov -o coverage.lcov
```

### Sass

To build Sass files for the project:

```sh
python manage.py sass admin_ui/static/scss admin_ui/static/css --watch
```


## Automated deployment

Several automated workflows are already configured. These can be found within the .github/workflows directory. 


## Configuring system to deploy CASEI

The Maintenance Interface is able to initiate a deployment of [CASEI](https://github.com/NASA-IMPACT/admg-inventory/). This works by triggering a [workflow dispatch event](https://docs.github.com/en/rest/reference/actions#create-a-workflow-dispatch-event) on CASEI's [`deploy-to-production` workflow](https://github.com/NASA-IMPACT/admg-inventory/actions/workflows/deploy-to-production.yml). To allow the Maintenance Interface to trigger CASEI, a [Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) with `actions:write` permissions should be provided via the `CASEI_GH_TOKEN` environment secret. The following environment variables may optionally be provided to override default configuration:

- `CASEI_GH_REPO`, the repo to deploy. Defaults to `NASA-IMPACT/admg-inventory`
- `CASEI_GH_WORKFLOW_ID`, the workflow to run. Defaults to `deploy-to-production.yml`
- `CASEI_GH_BRANCH`, the branch to deploy. Defaults to `production`

NOTE: We are considering OIDC for deployment if this backend needs to be maintained more long term

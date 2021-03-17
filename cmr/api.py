import json
import os
import sys

import environ
import requests

ROOT_DIR = environ.Path(__file__)-2
env = environ.Env()
env.read_env(str(ROOT_DIR.path('.env')))

DEFAULT_APPROVAL_NOTE = 'this action was perfomed using the API'


class Api:
    def __init__(self):
        """Initializes the api by setting up the credentials and
        getting the token from one of the various servers
        """

        self.base_url = f"{env('INGEST_API_SERVER')}/api/"
        self._make_connection()


    def _make_connection(self):
        """Connects to the database and sets the headers for future api requests.

        Raises:
            ValueError: Will raise error if connection fails.
        """
        data = {
            'grant_type': env('INGEST_API_GRANT_TYPE'),
            'username': env('INGEST_API_USERNAME'),
            'password': env('INGEST_API_PASSWORD')
        }

        token_url = f"{env('INGEST_API_SERVER')}/authenticate/token/"
        response = requests.post(
            token_url,
            data=data,
            auth=(env('INGEST_API_CLIENT_ID'), env('INGEST_API_CLIENT_SECRET')),
        )

        response_dict = self._generate_response_dict(response)
        access_token = response_dict['access_token']

        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }


    @staticmethod
    def _generate_response_dict(response):
        """Takes a response and raises any HTTPErrors. If no errors are found, it will
        convert the response text to a dict.

        Args:
            response (response): response

        Returns:
            response_dict [dict]: dictionary of the response.text
        """

        response.raise_for_status()
        response_dict =  response.json()

        return response_dict


    def _approve_change_object(self, response_dict, notes=DEFAULT_APPROVAL_NOTE):
        """Change objects must pass through an approval process in order to be added
        to the database. This function streamlines every step of the approval process
        and results in the draft change object being published to the database.

        Args:
            response (response): Response object from a python request. This should
                come from the update, delete, or create methods.
            notes (str): Notes to be left in the ApprovalLog. Defaults to this action
                was perfomed using the API

        Returns:
            response : Response object from the approval process.
        """

        uuid = response_dict['data']['uuid']
        notes_dict = {'notes': notes}

        for approval_step in ['submit', 'claim', 'review', 'claim', 'publish']:
            response_dict = self.post(f'change_request/{uuid}/{approval_step}', notes_dict)

            if not response_dict['success']:
                raise Exception(response_dict)

        return response_dict


    def post(self, endpoint, data):
        """Generic POST function. Not really intended to be used directly in any routine ingest pipelines,
        as self.create and self.update fulfil that role. However this is useful for testing out
        new views during development, and is used during the approval process.

        Args:
            endpoint (str): API endpoing such as 'partner_org'
            data ([dict]): dictionary of data matching endpoint requirements

        Returns:
            dict: API response dictionary
        """

        post_url = f'{self.base_url}{endpoint}'
        response = requests.post(post_url, data=json.dumps(data), headers=self.headers)
        response_dict = self._generate_response_dict(response)

        return response_dict


    def get(self, endpoint):
        """Takes an ADMG endpoint as a string and runs a get request

        Args:
            endpoint (str): API endpoint such as 'campaign'

        Returns:
            dict: API response dictionary
        """

        get_url = f'{self.base_url}{endpoint}'
        response = requests.get(get_url, headers=self.headers)
        response_dict = self._generate_response_dict(response)

        return response_dict


    def delete(self, endpoint):
        """Takes an endpoint and deletes the object in the db

        Args:
            endpoint (str): full endpoint including a UUID, 'season/37b0daa7-caa4-4649-b95c-929e8abe1dc8'
        """

        delete_url = f'{self.base_url}{endpoint}'
        response = requests.delete(delete_url, headers=self.headers)
        response_dict = self._generate_response_dict(response)

        self._approve_change_object(response_dict)


    def update(self, endpoint, data, draft=False):
        """Takes and endpoint and some data and updates the object in the db

        Args:
            endpoint (str): full endpoint including a UUID, 'season/37b0daa7-caa4-4649-b95c-929e8abe1dc8'
            data ([dict]): dictionary of data matching endpoint requirements
        """

        post_url = f'{self.base_url}{endpoint}'
        response = requests.patch(post_url, data=json.dumps(data), headers=self.headers)
        response_dict = self._generate_response_dict(response)

        if draft:
            return response_dict
        else:
            return self._approve_change_object(response_dict)


    def create(self, endpoint, data, draft=False):
        """Takes and endpoint and some post data and creates an entry in the
        database

        Args:
            endpoint (str): endpoint such as 'campaign' or 'season'
            data (dict): dictionary of data matching endpoint requirements

        Returns:
            dict: response dictionary from API
        """

        post_url = f'{self.base_url}{endpoint}'
        response = requests.post(post_url, data=json.dumps(data), headers=self.headers)
        response_dict = self._generate_response_dict(response)

        if not(response_dict['success']) and 'this short name already exists' in response_dict['message']:
            return f'the following entry already existed {endpoint=} {data=}'

        if draft:
            return response_dict
        else:
            return self._approve_change_object(response_dict)

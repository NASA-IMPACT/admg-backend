import json
import os
import sys

import requests

parent_directory = os.path.split(os.getcwd())[0]

import_path = parent_directory + '/data_models'

if import_path not in sys.path:
    sys.path.insert(0, import_path)

from utils.config.server import credentials as CREDENTIALS


class Api:
    def __init__(self, deployment):
        """Initializes the api by setting up the credentials and 
        getting the token from one of the various servers

        Args:
            deployment (str): 'test', 'production', or 'local'
        """

        self.deployment = deployment
        self.credentials = CREDENTIALS[self.deployment]
        self.base_url = f"{self.credentials['server']}/api/"
        self._make_connection()

    def _make_connection(self):
        token_url = f"{self.credentials['server']}/authenticate/token/"
        response = requests.post(
            token_url,
            data=self.credentials['data'],
            auth=(self.credentials['client_id'], self.credentials['client_secret']),
        )
        access_token = json.loads(response.text)['access_token']

        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

    def get(self, endpoint):
        """Takes an ADMG endpoint as a string and runs a get request

        Args:
            endpoint (str): API endpoint such as 'campaign'

        Returns:
            dict: API response dictionary
        """

        get_url = f'{self.base_url}{endpoint}'
        response = requests.get(get_url, headers=self.headers)

        return json.loads(response.text)

    def delete(self, endpoint, uuid):
        delete_url = f'{self.base_url}{endpoint}'
        response = requests.delete(delete_url, headers=self.headers)

        print(response)
        print(response.text)

        # get the change_request_uuid
        uuid = response.text.split(':')[4].strip().split(' ')[0]

        requests.post(f'{self.base_url}change_request/{uuid}/push', headers=self.headers).text
        approved = json.loads(requests.post(f'{self.base_url}change_request/{uuid}/approve', headers=self.headers).text)
        
        return approved

    def update(self, endpoint, data):
        post_url = f'{self.base_url}{endpoint}'
        response = requests.patch(post_url, data=json.dumps(data), headers=self.headers)

        # get the change_request_uuid
        uuid = response.text.split(':')[4].strip().split(' ')[0]

        requests.post(f'{self.base_url}change_request/{uuid}/push', headers=self.headers).text
        approved = json.loads(requests.post(f'{self.base_url}change_request/{uuid}/approve', headers=self.headers).text)
        
        return approved

    def create(self, endpoint, data):
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

        if '"success": false' in response.text and 'this short name already exists' in response.text:
            return f'the following entry already existed {endpoint=} {data=}'

        # get the change_request_uuid
        uuid = response.text.split(':')[4].strip().split(' ')[0]

        requests.post(f'{self.base_url}change_request/{uuid}/push', headers=self.headers).text
        approved = json.loads(requests.post(f'{self.base_url}change_request/{uuid}/approve', headers=self.headers).text)
        
        return approved

    def gmcd_shorts(self, endpoint, uuid):
        """Most items in the database have a potential GCMD translation.
        This function takes an endpoint and the uuid of a specific obj at
        that endpoint and returns the GCMD translation short_names for the UUID.

        Args:
            endpoint (str): API endpoint such as 'platform' or 'campaign'
            uuid (str): uuid of a specific item such as an instrument uuid

        Returns:
            list: Because an item can have multiple GCMD translations, function
            returns a list of GCMD short_names
        """

        gcmd_uuids = self.get(f'{endpoint}/{uuid}')['data'][f'gcmd_{endpoint}s']
        gcmd_short_names = [
            self.get(f'gcmd_{endpoint}/{gcmd_uuid}')['data']['short_name']
            for gcmd_uuid in gcmd_uuids
        ]

        return gcmd_short_names

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
        self.deployment = deployment
        self.credentials = CREDENTIALS[self.deployment]
        self.base_url = f"{self.credentials['server']}/api/"
        self._make_connection()

    def _make_connection(self):
        url = f"{self.credentials['server']}/authenticate/token/"
        response = requests.post(
            url,
            data=self.credentials['data'],
            auth=(self.credentials['client_id'], self.credentials['client_secret']),
        )
        access_token = json.loads(response.text)['access_token']

        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

    def get(self, end_point):
        """Takes an ADMG endpoint as a string and runs a get request

        Args:
            end_point (str): API end_point such as 'campaign'

        Returns:
            dict: API response dictionary
        """

        url = f'{self.base_url}{end_point}'
        response = requests.get(url, headers=self.headers)

        return json.loads(response.text)

    def gmcd_shorts(self, end_point, uuid):
        """Most items in the database have a potential GCMD translation.
        This function takes an end_point and the uuid of a specific obj at
        that enpoint and returns the GCMD translation short_names for the UUID.

        Args:
            end_point (str): API endpoint such as 'platform' or 'campaign'
            uuid (str): uuid of a specific item such as an instrument uuid

        Returns:
            list: Because an item can have multiple GCMD translations, function
            returns a list of GCMD short_names
        """

        gcmd_uuids = self.get(f'{end_point}/{uuid}')['data'][f'gcmd_{end_point}s']
        shorts = [
            self.get(f'gcmd_{end_point}/{gcmd_uuid}')['data']['short_name']
            for gcmd_uuid in gcmd_uuids
        ]

        return shorts

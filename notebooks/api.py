import json
import os
import sys

import requests

parent_directory = os.path.split(os.getcwd())[0]

import_path = os.path.join(parent_directory, 'data_models')

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

    def _approve_change_object(self, response):
        # get the change_request_uuid
        uuid = json.loads(response.text)['data']['uuid']

        push_response = json.loads(requests.post(
            f'{self.base_url}change_request/{uuid}/push', headers=self.headers
        ).text)

        if push_response.get('success'):
            approve_response = json.loads(
                requests.post(
                    f'{self.base_url}change_request/{uuid}/approve', headers=self.headers
                ).text
            )
            final_response = approve_response
        else:
            final_response = push_response

        return final_response

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

    def delete(self, endpoint):
        """Takes and endpoint and deletes the object in the db

        Args:
            endpoint (str): full endpoint including a UUID, 'season/37b0daa7-caa4-4649-b95c-929e8abe1dc8'
        """

        delete_url = f'{self.base_url}{endpoint}'
        response = requests.delete(delete_url, headers=self.headers)

        self._approve_change_object(response)

    def update(self, endpoint, data):
        """Takes and endpoint and some data and updates the object in the db

        Args:
            endpoint (str): full endpoint including a UUID, 'season/37b0daa7-caa4-4649-b95c-929e8abe1dc8'
            data ([dict]): dictionary of data matching endpoint requirements
        """

        post_url = f'{self.base_url}{endpoint}'
        response = requests.patch(post_url, data=json.dumps(data), headers=self.headers)

        change_response = self._approve_change_object(response)

        return change_response


    def upload_image(self, metadata, image):
        """Upload an image with metadata to the database.

        Args:
            metadata (dict): dictionary with fields and values
            image (binary): binary image

        Returns:
            dict: response from API
        """

        post_url = f'{self.base_url}image'
        headers = {'Authorization': self.headers['Authorization']}
        files = [
            ('image', image)
        ]  

        response = requests.post(post_url, data=metadata, files=files, headers=headers)
        return response

    def upload_excel(self, excel, data=None):
        """Upload an excel with optional data parameters to the validation endpoint.

        Args:
            data (dict): dictionary with fields and values
            excel (binary): binary excel

        Returns:
            dict: response from API
        """

        post_url = f'{self.base_url}validate_excel'
        headers = {'Authorization': self.headers['Authorization']}
        files = [
            ('excel', excel)
        ]  

        response = requests.post(post_url, data=data, files=files, headers=headers)
        return response


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
        
        response_dict = json.loads(response.text)
        if not(response_dict['success']) and 'this short name already exists' in response_dict['message']:
            return f'the following entry already existed {endpoint=} {data=}'

        return self._approve_change_object(response)


    def gcmd_shorts(self, table_name, uuid):
        """Most items in the database have a potential GCMD translation.
        This function takes a table_name and the uuid of a specific obj at
        that table_name and returns the GCMD translation short_names for the UUID.

        Args:
            table_name (str): API table_name such as 'platform' or 'campaign'
            uuid (str): uuid of a specific item such as an instrument uuid

        Returns:
            list: Because an item can have multiple GCMD translations, function
            returns a list of GCMD short_names
        """

        gcmd_uuids = self.get(f'{table_name}/{uuid}')['data'][f'gcmd_{table_name}s']
        gcmd_short_names = [
            self.get(f'gcmd_{table_name}/{gcmd_uuid}')['data']['short_name']
            for gcmd_uuid in gcmd_uuids
        ]

        return gcmd_short_names

    def add_link_doi(self, linked_table, linked_uuid, doi_data):
        self.create('doi', doi_data)
        doi_uuid = self.get(f"doi?short_name={doi_data['short_name']}")['data'][0]['uuid']
        dois = self.get(f"{linked_table}/{linked_uuid}")['data']['dois']
        dois.append(doi_uuid)
        dois = list(set(dois))
        self.update(f"{linked_table}/{linked_uuid}", {'dois': dois})

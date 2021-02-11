import json
import requests

from cmr.server import credentials as CREDENTIALS


class Api:
    def __init__(self):
        """Initializes the api by setting up the credentials and 
        getting the token from one of the various servers

        Args:
            deployment (str): 'test', 'production', or 'local'
        """

        self.credentials = CREDENTIALS
        self.base_url = f"{self.credentials['server']}/api/"
        self._make_connection()

    def _make_connection(self):
        token_url = f"{self.credentials['server']}/authenticate/token/"
        response = requests.post(
            token_url,
            data=self.credentials['data'],
            auth=(self.credentials['client_id'], self.credentials['client_secret']),
        )
        
        response = json.loads(response.text)
        if response.get('error') == 'invalid_client':
            raise ValueError("Invalid Client. Check token details in config file.")
        
        access_token = response['access_token']


        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

    def _approve_change_object(self, response):
        # get the change_request_uuid
        response = json.loads(response.text)
        uuid = response['data']['uuid']

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

    def update(self, endpoint, data, draft=False):
        """Takes and endpoint and some data and updates the object in the db

        Args:
            endpoint (str): full endpoint including a UUID, 'season/37b0daa7-caa4-4649-b95c-929e8abe1dc8'
            data ([dict]): dictionary of data matching endpoint requirements
        """

        post_url = f'{self.base_url}{endpoint}'
        response = requests.patch(post_url, data=json.dumps(data), headers=self.headers)

        if draft:
            return json.loads(response.text)
        else:
            return self._approve_change_object(response)


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
        
        response_dict = json.loads(response.text)
        if not(response_dict['success']) and 'this short name already exists' in response_dict['message']:
            return f'the following entry already existed {endpoint=} {data=}'

        if draft:
            return response_dict
        else:
            return self._approve_change_object(response)

# rename this file to server.py
# these credentials will allow scripts to use the API

credentials = {
    'production': {
        'server': 'https://admg.nasa-impact.net',
        'client_id': '',
        'client_secret': '',
        'data': {
            'grant_type': 'password',
            'username': '',
            'password': ''
        },
    },
    'test': {
        'server': 'https://admgtest.nasa-impact.net',
        'client_id': '',
        'client_secret': '',
        'data': {
            'grant_type': 'password',
            'username': '',
            'password': ''
        },
    },
    'local': {
        'server': 'http://localhost:8000',
        'client_id': '',
        'client_secret': '',
        'data': {
            'grant_type': 'password',
            'username': '',
            'password': ''
        },
    },
}

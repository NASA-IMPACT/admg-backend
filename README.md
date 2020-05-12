# admg_webapp

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

 - go to /authenticate/applications/register
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
 

 ## Automatic deployment

 - Change the webserver IP in the hosts file. If no hosts file exists, create one [see hosts.sample file]
 - Run the command `ansible-playbook --private-key private_key_file.pem -i hosts playbook.yml -v`
     - `private_key_file.pem` is the private key for the webserver

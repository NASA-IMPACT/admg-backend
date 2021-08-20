from drf_yasg import openapi

description = """
<h2>Overview</h2>Welcome to the ADMG CASEI API Documentation. This page gives an overview of how to use the ADMG API as well as specific details for every endpoint and API method.
<h2>Basic Structure</h2>CASEI is built on top of an SQL database with multiple tables that each contain fields and foriegn keys. Each endpoint in the API will point to a different table. 
Requesting a bare endpoint, such as `/campaign/` will return a list of all the metadata for every campaign in the inventory.

Below is a contrived example of the results from a campaign query, with ... indicating the continuation of additional metadata and additional campaigns. 
```
{
    'success': True,
    'message': '',
    'data': [
        {
            'uuid': 'd031186d-1a41-430b-ae02-1c76f4cfa441',
            'short_name': 'Fake Campaign Short Name',
            'long_name': 'Fake Campaign Long Name',
            'aliases': [
                '927479e5-b0c7-4aef-9d31-4a6850dea804',
                '3ad6b6e4-23a3-42af-a7a6-b597c476d8ea'
            ],
        ...
        },
        ...
    ]
}
```
<h2>Response Content</h2>All API responses contain `success` boolean, a `message` string, and a `data` list. 
<h4>success</h4>A `success` value of `True` only indicates that your reqeust was completed, and nothing on the backend threw an error. It does not indicate that a query returned any result data.
Values of `False` are used to indicate that an action was not allowed, such as if you are attempting to POST to an endpoint and your token is not associated with an account that has the correct permisions. 
<h4>message</h4>The message field will contain a description of the failure if `sucess` was returned as `True` and it will sometimes give a description about the action if it was successful.
<h2>Using UUIDs</h2>As you can see from the above example, some fields return a human readable value, while others return a UUID. If you see a human readable value, then this is all the information contained
in that field. However, if a UUID is listed, then this indicated this field is linked to an object with additional metadata.

Every object in the database is uniquely identified with a UUID. This UUID is used throughout the API to reference objects that have been linked from other tables.
So, if you want a particular campaign instead of all the campaigns, you can query using its specific UUID:

`/campaign/d031186d-1a41-430b-ae02-1c76f4cfa441`

Likewise, if there is a linked object within the metadata, such as `aliases` in our example, you can retrieve the linked object using the same method:

`/alias/927479e5-b0c7-4aef-9d31-4a6850dea804`

It is generally the case that if a linked field is singular, it will correspond perfectly with it's table, and if it is plural it will need to be singularized. So 'respositories' becomes 'repository', 'seasons' becomes 'season', and 'deployment' remains 'deployment'.
<h2>Using short_name Searches</h2>The API also supports limited search functionality. Specifically, many endpoints allow

`/endpoint?short_name=value`

for example

`/campaign?short_name=ACES`.
<h2>Permissions: POST vs GET</h2>
<h2>API Content and Field Names</h2>
Below this section, there is a listing of every API endpoint and the available methods. If you are trying to figure out what data is available from the api, this is the place to look.
If you click on an endpoint, it will enlarge and you will be able to see all the fields that are available.
Each field has several values listed:
 - field name - the field name returned by the api
 - data type - for example string or integer
 - title - a human readable title for the field name
 - other parameters - values such as maxLength and minLength will appear here
 - description - A sentence or paragraph long description of what the field contains, and any clarifications that might be needed

"""

api_info = openapi.Info(
    title="ADMG API Documentation",
    default_version="v1",
    description=description,
    terms_of_service="https://www.google.com/policies/terms/",
    contact=openapi.Contact(email="contact@snippets.local"),
    license=openapi.License(name="BSD License"),
)

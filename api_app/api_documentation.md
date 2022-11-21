<h2>Overiew</h2>Welcome to the ADMG CASEI API Documentation. This page gives an overview of how to use the CASEI API as well as specific details for every endpoint and API method.
<h2>Basic Structure</h2>CASEI is built on top of an SQL database with multiple tables that each contain fields and foriegn keys. Each endpoint in the API will point to a different table. 
Requesting a bare endpoint, such as `/campaign/` will return a list of all the metadata for every campaign in the inventory.<br>
Below is a contrived example of the results from a campaign query, with ... indicating the continuation of additional metadata and additional campaigns.<br>
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
<h2>Using UUIDs</h2>Every object in the database is uniquely identified with a UUID. This UUID is used throughout the API to reference objects that have been linked from other tables.<br>
So, if you want a particular campaign instead of all the campaigns, you can query using its specific UUID:<br>
`/campaign/d031186d-1a41-430b-ae02-1c76f4cfa441`<br>
As you can see from the above example, some fields return a human readable value, while others such as `aliases` return a UUID. If you see a human readable value, then this is all the information contained in that field. However, if a UUID is listed, then the field is linked to an object with additional metadata.<br>
This object and its metadata can be retrieved by sending its UUID to the appropriate endpoint, as in the following example with aliases:
`/alias/927479e5-b0c7-4aef-9d31-4a6850dea804`<br>
Here, you can see that the field was named `aliases` however the endpoint queried was called `alias`. It is generally the case that if a linked field is singular, it will correspond perfectly with it's table, because this represents a one to one relationship. Meanwhile if the field is plural then it has a one/many to many relationship, and it will need to be singularized to obtain the table name. So 'repositories' becomes 'repository' and 'seasons' becomes 'season', while 'deployment' remains 'deployment'.<br>
If you are ever in doubt, there is a full guide to every endpoint and field further in this document.<br>
<h2>Using short_name Searches</h2>The API also supports limited search functionality. Specifically, many endpoints allow<br>
`/endpoint?short_name=value`<br>
for example<br>
`/campaign?short_name=ACES`.<br>
Specifically, the following endpoints and fields are searchable<br>
<ul>
    <li>`campaign`</li>
        <ul>
            <li>`short_name`, `long_name`, `description_short`, and `focus_phenomena`,</li>
        </ul>
    <li>`platform`</li>
        <ul>
            <li>`short_name`, `long_name`, and `description`</li>
        </ul>
    <li>`instrument`</li>
        <ul>
            <li>`short_name`, and `long_name`</li>
        </ul>
</ul>
<h2>Permissions: POST vs GET</h2>Every endpoint is publicly accessible via the GET method, although some fields, such as `notes_internal` are for internal use only and will not be returned. The POST method is not publically accessible, and requires an authenticated user with a properly scoped token. If you have a need to use the POST method, please contact the ADMG team.<br>
<h2>API Content and Field Names</h2>Below this section, there is a listing of every API endpoint and the available methods. If you are trying to figure out what data is available from the api, this is the place to look. If you click on an endpoint, it will enlarge and you will be able to see all the fields that are available.<br>
Each field has several values listed:<br>
<ul>
    <li>field name: the field name returned by the api</li>
    <li>data type: for example string or integer</li>
    <li>title: a human readable title for the field name</li>
    <li>other parameters: values such as maxLength and minLength will appear here</li>
    <li>description: A sentence or paragraph long description of what the field contains, and any clarifications that might be needed</li>
</ul>
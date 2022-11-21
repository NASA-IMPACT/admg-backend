# Overview

CASEI is built on top of a PostgreSQL database with multiple tables that each contain fields and foreign keys. Each endpoint in the API will point to a corresponding table. All the available models and fields can be seen at the bottom of this page.

The base API can be found at https://admg.nasa-impact.net/api/

Requesting a bare table endpoint, such as `https://admg.nasa-impact.net/api/campaign/` will return a list of all the metadata item in the table, in this case, for every campaign in the inventory. Specific objects can be retrieved by adding a known UUID after the table name, and string match searching is available for most fields. Further details on all search types can be found in the [Queries](#Queries) section.

# Queries
## Full Table Query
As mentioned above, the most basic query returns the full data from a table. For example `https://admg.nasa-impact.net/api/campaign/` will return a list of all published campaign items in the database.

Below is a contrived example of the results from a `/campaign/` query, with ... indicating the continuation of additional metadata and additional campaigns.

```
{ 
    'success': True, 
    'message': '', 
    'data': [
        { 
            'uuid': '30ba471c-0844-447a-91fd-b63a2f42b715',
            'short_name': 'ACES',
            'long_name': 'Altus Cumulus Electrification Study',
            'partner_orgs': [
                '005762a5-68e5-4a59-b839-0c8f418b263e'
            ],
            ...
        }, 
    ...
    ]
}
```
## UUIDs and Related Objects

In the example results from the Campaign table, we saw several UUIDs listed: one `uuid` for the campaign itself, and one for the `partner_orgs` list.

This is because every item has it's own identifying UUID, and related objects linked from other tables are always specified using a UUID. For example, each Campaign might have been conducted in conjunction with a Partner Org. However, Partner Org is not a simple string value. It is an independent object with its own table and additional metadata. So the Campaign API response will list Partner Org as a UUID to the relevant object.

If you would like to see the details on that Partner Org, you must query the `/partner_org/` endpoint with the given UUID. Using the metadata shown above, we would make the following query:
```
https://admg.nasa-impact.net/api/partner_org/005762a5-68e5-4a59-b839-0c8f418b263e
```
Likewise, if we wanted to only see data for this exact campaign, and not the list of all the campaigns, we could do:
```
https://admg.nasa-impact.net/api/campaign/30ba471c-0844-447a-91fd-b63a2f42b715
```
You may have noticed that `campaign` had a plural field called `partner_orgs` but the table name was the singular `partner_org`. Table names are *always* singular, but related fields can be a singular or plural version of the table name depending on whether only one or many items are linked.

But what if you don't know the UUID of the item you want to query?

## String Match Queries
In practice, it is unlikely that you will know the UUID of the Campaign or Partner Org you are interested in. Instead you will probably know the short name, long name, or maybe a keyword from the description.

Because all datatypes are serialized into strings, most fields can be searched using basic string matching. A native datetype becomes the searchable string `2022-01-15`. 

By default, searches are not case sensitive and use a contain logic. For example, the field value of `the yellow clouds` will match to the search string `cloud`. 

The following parameters are used when constructing a query.

### search_term
- Contains the actual search string, for example: `aces`, `cloud`, `2022-01-05`

### search_type
- Optional, default=plain
- plain: terms are treated as separate keywords
- phrase: terms are treated as a single phrase
- raw: formatted search query with terms and operators
- websearch: formatted search query, similar to the one used by web search engines. 
- Refer to the PostgreSQL docs for more details on differences and syntax

### search_fields
- Optional, defaults to predefined fields in each model
- Specifies the exact field to be searched: `short_name`, `description`, `start_date`
- Example Queries
- Campaign short name search
- UUID Search
- Multi-Item Search


## Example Queries
We've seen a few examples already above, but in this section we will demonstrate all the common usecases.

### Query an entire table
This query will return metadata for all the campaigns.
```
https://admg.nasa-impact.net/api/campaign/
```
### Query by UUID
This query will return metadata for the exact campaign specified by UUID.
```
https://admg.nasa-impact.net/api/campaign/30ba471c-0844-447a-91fd-b63a2f42b715
```
### Query by default search fields
Each table has a list of default search fields, usually `short_name`, `long_name`, `description`, and any other text fields. This query will search all of those fields for the listed term.
```
https://admg.nasa-impact.net/api/campaign/search_term=ACES
```
### Query by specific field
If you know the exact field and want to search it specifically, use the search_fields parameter.
```
https://admg.nasa-impact.net/api/campaign/search_term=ACES&search_fields=short_name
```
### Query by specific field list
You can also search by a specific list of fields, just join them with a comma.
```
https://admg.nasa-impact.net/api/campaign/search_term=ice&search_fields=short_name,description
```

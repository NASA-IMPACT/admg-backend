## Overview

CASEI is built on top of a PostgreSQL database with multiple tables that each contain fields and foreign keys. Each endpoint in the API will point to a corresponding table. All the available models and fields can be seen at the bottom of this page

The base API can be found at https://admg.nasa-impact.net/api/

Requesting a bare endpoint, such as `/campaign/` will return a list of all the metadata for every campaign in the inventory. Specific objects can be retrieved by adding a known UUID after the tablename, and string match searching is available for most fields. Further details on all search types can be found in the [Queries](#Queries) section.

Understanding the Query Results and Related Objects

Below is a contrived example of the results from a campaign query, with ... indicating the continuation of additional metadata and additional campaigns.

Related objects are often specified using a UUID. For example, each Campaign might have been conducted in conjunction with a Partner Org. However, Partner Org is not a simple string value. It is an independent object with its own table and additional metadata. So the Campaign API response will list Partner Org as a UUID to the relevant object.

If you would like to see the details on that Partner Org, you must query the /partner_org/ endpoint with the given UUID.
## Queries
### Full Table Query
The most basic query returns the full data from a table, for example
api/campaign 
Will return a list of all published campaign items in the database.

Any non-abstract table can be queried in this way (give or point to list of tables).

### Specific Object Query
If you already know the UUID of a specific object, it can be queried directly 
api/campaign?uuid

However, in practice, you will often need to find the UUID through a String Match Query. 
### String Match Queries
Because all datatypes are serialized into strings, most fields can be searched using basic string matching. A native datetype becomes the searchable string ‘2022-01-15’. 

By default, searches are not case sensitive and use a contain logic. For example, the field value of ‘the yellow clouds’ will match to the search string ‘cloud’. 

The following parameters are used when constructing a query.

#### search_term
- Contains the actual search string, for example: ‘aces’, ‘cloud’, ‘2022-01-05’

#### search_type
- Optional, default=plain
- plain: terms are treated as separate keywords
- phrase: terms are treated as a single phrase
- raw: formatted search query with terms and operators
- websearch: formatted search query, similar to the one used by web search engines. 
- Refer to the PostgreSQL docs for more details on differences and syntax

#### Search_fields
- Optional, defaults to predefined fields in each model
- Specifies the exact field to be searched: ‘short_name’, ‘description’, ‘start_date’
- Example Queries
- Campaign short name search
- UUID Search
- Multi-Item Search
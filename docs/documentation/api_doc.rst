=================
API documentation
=================

Introduction
------------
The CASEI API provides access to the metadata stored in the CASEI PostgreSQL database. The database consists of multiple tables, each containing fields and foreign keys. 
Each API endpoint corresponds to a specific table in the database. You can find the available models and fields at the bottom of this page.

Retrieving Data from Table Endpoints
------------------------------------
To retrieve data from a table endpoint, make a request to the corresponding URL. For example, accessing the URL `<https://admg.nasa-impact.net/api/campaign>`_ 
will return a list of all metadata items in the "campaign" table, representing the available campaigns in the inventory.. 

If you have the UUID of a specific object, you can retrieve it by appending the UUID to the table name in the URL. Alternatively, string match searching is available for most fields, 
allowing you to search for specific data based on partial matches. More information on the available search types and example queries can be found below.

Performing Full Table Queries
-----------------------------
To retrieve the complete data from a table, simply access the corresponding endpoint. For instance, accessing `<https://admg.nasa-impact.net/api/campaign>`_ will return a list of all published campaign 
items in the database.

Here's a contrived example that demonstrates the results of a campaign query. The ellipsis (...) indicates the presence of additional metadata and campaigns. You can see summarized metadata for two campaigns, namely OLYMPEX and ACES.

.. code-block:: python
    
    { 
        "success": True, 
        "message": ", 
        "data": [
            { 
                "uuid": "2552174b-213c-4bfc-b36a-632fb16c5ec2",
                "short_name": "OLYMPEX",
                "long_name": "Olympic Mountains Experiment",
                "start_date": "2015-11-01",
                "partner_orgs": [
                    "d6ffd2fa-1230-4971-a0a4-832b27b3a6c1"
                ],
                ...
            }, 
            { 
                "uuid": "30ba471c-0844-447a-91fd-b63a2f42b715",
                "short_name": "ACES",
                "long_name": "Altus Cumulus Electrification Study",
                "start_date": "2002-08-02"
                "partner_orgs": [],
                ...
            }, 
        ...
        ]
    }

UUIDs and Related Objects
-------------------------
In the example results from the Campaign table, we encountered several UUIDs: one that identifies each campaign, and another UUID within the "partner_orgs" list for the OLYMPEX campaign.

Each item in the CASEI database has its own unique UUID, and related objects linked from other tables are referenced using their respective UUIDs. For instance, a Campaign might have been conducted in collaboration with a Partner Org. However, the Partner Org is not represented as a simple string value. It is an independent object with its own table and additional metadata. Therefore, the Campaign API response includes the UUID of the relevant Partner Org.

If you wish to view the details of a specific Partner Org, you need to query the "partner_org" endpoint with the provided UUID. Based on the metadata shown above, you can make the following query:

`<https://admg.nasa-impact.net/api/partner_org/d6ffd2fa-1230-4971-a0a4-832b27b3a6c1>`_.

This query will retrieve the metadata for the related Partner Org, in this case, ECCC (Environment and Climate Change Canada).

.. code-block:: python

    {
    "success": true,
    "message": "",
    "data": {
        "uuid": "d6ffd2fa-1230-4971-a0a4-832b27b3a6c1",
        "aliases": [
        "14aa21a2-de5a-4987-af11-d2c7c7a0c20f"
        ],
        "campaigns": [
        "1d26f72f-d9d5-45cc-b5ac-1c91ed05b76f",
        "118d9d82-5e90-466b-8b82-530276b76ecc",
        "2552174b-213c-4bfc-b36a-632fb16c5ec2"
        ],
        "short_name": "ECCC",
        "long_name": "Environment and Climate Change Canada",
        "website": "https://www.canada.ca/en/environment-climate-change.html"
        }
    }

As you can see, the Partner Org has its own informative metadata, including a long name, aliases, a website, and even a list of all the campaigns it is associated with.

You may have observed that the Campaign table has a plural field named "partner_orgs," while the table name itself is singular, "partner_org,".
In CASEI, table names are always singular, but related fields can be either singular or plural depending on the number of items linked.

But what if you do not have the UUID of the item you wish to query?

String Match Queries
--------------------
In most cases, you may not have the UUIDs of the Campaign or Partner Org you are interested in. Instead, you are more likely to know the short name, long name, or perhaps a keyword from the description.

CASEI supports string matching queries, allowing you to search for relevant data using basic string matching techniques. Since all data types are serialized into strings, most fields can be searched using simple string matching. Even native date types can be searched by converting them into searchable strings, such as "2022-01-15".

By default, the search is case-insensitive and follows a containment logic. For instance, a field value of "yellow clouds" will match the search string "cloud".

When constructing a query, you can utilize the following parameters:

.. code-block:: rst

    `search_term` : Contains the actual search string, for example: aces, cloud, 2022-01-05.

    `search_type` : Optional parameter with a default value of "plain". Other options include "phrase", 
        "raw", and "websearch". Each option determines how the search terms are treated. 
        You can refer to the PostgreSQL docs for detailed information on the differences and syntax.
            plain: terms are treated as separate keywords
            phrase: terms are treated as a single phrase
            raw: formatted search query with terms and operators
            websearch: formatted search query, similar to the one used by web search engines.

    `search_fields`: Optional parameter that defaults to predefined fields in each model. It specifies the exact field to be searched, such as "short_name", "description", or "start_date".

Example Queries
---------------
We have already seen a few examples above, but let's explore common use cases with additional queries.

Querying an entire table
++++++++++++++++++++++++
This query will return metadata for all the campaigns.

    `<https://admg.nasa-impact.net/api/campaign>`_

Query by UUID
+++++++++++++
This query will return metadata for the exact campaign specified by UUID.

    `<https://admg.nasa-impact.net/api/campaign/30ba471c-0844-447a-91fd-b63a2f42b715>`_

Query by default search fields
++++++++++++++++++++++++++++++
Each table has a list of default search fields, usually `short_name`, `long_name`, `description`, and any other text fields. This query will search all of those fields for the listed term.

    `<https://admg.nasa-impact.net/api/campaign/search_term=ACES>`_

Query by specific field
+++++++++++++++++++++++
If you know the exact field and want to search it specifically, use the `search_fields` parameter. Here we are looking for the term "ACES" in the `short_name` field of any campaign.

    `<https://admg.nasa-impact.net/api/campaign/search_term=ACES&search_fields=short_name>`_

Query by specific field list
++++++++++++++++++++++++++++
You can also search by a specific list of fields, just join them with a comma. In this example we are searching for the term ice anywhere in the `short_name` or `description` field of any campaign.

    `<https://admg.nasa-impact.net/api/campaign/search_term=ice&search_fields=short_name,description>`_

Link to API
-----------
`Base URL`: `<admgstaging.nasa-impact.net/api>`_
    `<https://admgstaging.nasa-impact.net/api/docs/?format=openapi>`_
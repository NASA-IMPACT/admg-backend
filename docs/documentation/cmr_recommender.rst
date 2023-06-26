CMR Recommender
===============

The CMR Recommender is an automated feature on the MI that queries suggested data products that link to each campaign, platform, and instrument. 

Users can access CMR recommender by logging into the MI website and select a campaign then click on the "Generate DOIs +"

To view the code follow the path admg-backend > cmr > cmr.py

Functionality
-------------

Once the CMR recommender starts, the QueryCounter class runs an if function that calculates the number of hits returned in the current CMR page. The function's arguements are num_hits which returns an integer of the number of hits from the CMR API metadata request. Next is page_size and page_number which both return integers of the page size and page number from the user query. Next is naive which is a boolean that selects for naive calculation. 

If the naive argument is true then it calculates page number and size then returns the number of results on the current page. 

The next function that runs in the class QueryCounter is iterate. Iterate updates the self.page_num and self.finished after a new page containing new hits is returned. The functions arguement is num_hits which is an integer of number of hits returned from the most recent query. 

Get_json takes the CMR query url and returns the response JSON as a dictionary. Its arguement cmr_url is a string of CMR query url then returns a dictionary of data. 

The next function is universal_query that contains the arguments query_parameter and query_value. Query_parameter is a string for 'project', 'instrument', and 'platform.' Then query_value is a value that is associate with parameter including campaign short_name, 'ABOVE' for query_parameter='project'. This function queries CMR for a specific query_parameter and value then aggergates all the collection metadata. This functions then returns a list of xml_trees.

In the universal_query the variables counter is set to the class QueryCounter, base_url is set to the json url from cmr, and results are set to an empty list.

.. code-block:: python
    
    counter = QueryCounter()
    base_url = "https://cmr.earthdata.nasa.gov/search/collections.umm_json?"
    results = []

After get_json retrieves the results from the url and appends to the response to results. The function iterates through the number of hits appended in the counter.

Extract_concept_ids_from_universal_query takes the results from an initial collections query and extracts each concept_id mentioned. This function has the intent that the collections are subsequently queried individually for their detailed metadata. The arguement collections_json is a Python dictionary generated from the json from universal_query(). This functions returns a list of concept_id strings.

The main CMR query is a bulk query that uses multiple aliases. The aggregate_concept_ids_queries queries CMR for the concept_ids associated with a single alias. The concept_ids are then aggregated by the intended calling function. The function's arguments are strings query_parameter of the CMR query parameter in ['project', 'instrument', 'platform'] and query_value which is one alias associated with the parameter, such as 'ACES' for 'project.' The function returns concept_id_list which is a list of concept_id strings returned from CMR.

Bulk_cmr_query is the primary CMR query function which takes a parameter and a list of aliases. The function queries each alias and then aggregates the results. The functions arguements is query_parameter that queries the CMR parameter in ['project', 'instrument', 'platform']. The other arguement is query_value_list which is a list containing the alias strings associated with the parameters in query_paramter. This function returns a list named metadata_list containing metadata for data products returned from CMR.

Cmr_parameter_transform takes a table name from the database and transforms it into the associated cmr query parameter. If there are invalid table names the function raises an error message "ValueError: Raises an error if input_str is not in ['project', 'instrument', 'platform']". The function's arguments are input_str and reverse. Input_str is the database table_name in ['project', 'instrument', 'platform']. Reverse is a boolean and if true the function will convert backwards. This function returns the cmr query parameter matching the input_str.

FInally query_and_process_cmr takes a database table name and a list of aliases and runs cmr queries for each alias. The function then aggregates the results before filtering out the unused metadata. The function's arguments are query_parameter which is CMR query parameter in ['project', 'instrument', 'platform'] and aliases which is list of alias strings associated with the parameter. For exmpale 'ACES' falls under 'project.' The function returns a list of processed metadata for data products returned from CMR.
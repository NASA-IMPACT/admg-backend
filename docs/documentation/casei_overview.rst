
Catalog of Archived Suborbital Earth Science Investigations
===========================================================

The Catalog of Archived Suborbital Earth Science Investigations (CASEI), is a centralized airborne and field data inventory that streamlines discovery of non-satellite NASA Earth Science data 
by providing contextual information on events, motivations, and potential data caveats. With CASEI, users can search and browse NASA’s airborne and field data archives, 
regardless of which data repository (or DAAC) is responsible for their stewardship.

CASEI consists of two major components: the backend architecture and the curation of inventory content

The backend architecture of CASEI is implemented using Django, a powerful web framework written in Python. It provides the foundation for the system, 
incorporating essential functionalities and tools to handle data management, relational databases, and APIs.

    1. Django's models and relational databases APIs: These components incorporate metadata from the Common Metadata Repository (CMR) and the Airborne Science Program's (ASP) information. 
    They enable the integration of CMR metadata and ASP data into the CASEI database, and facilitate data information retrieval for CMR and ASP.   

    2. Maintenance Interface (MI): The MI serves as a maintenance tool for entering and updating the database content. 
    It provides an interface for curators to efficiently manage and update information in the CASEI database.

    3. Public User Interface (UI): The UI allows users to submit queries using search terms, review information, and access links to data products. 
    It serves as the portal for users to interact with the CASEI system.

The curation of inventory content is the second vital component of CASEI. This process involves careful organization and management of suborbital observation metadata for NASA Earth Science products. 
Skilled curators diligently categorize the data into campaigns, platforms, and instruments, following a structured hierarchy, precise definitions, and decision trees. 
Through a meticulous curation process, data quality and consistency are ensured. Multiple rounds of quality reviews further validate the information before its finally published. 
The Maintenance Interface (MI) plays a crucial role in facilitating this curation process, allowing curators to efficiently manage and update the inventory content. 
.. And, once the data is finalized, it is seamlessly integrated into the User Interface (UI) for user access.

These two components work in harmony to provide a comprehensive  User Interface (UI) and user-friendly experience within CASEI. The backend architecture handles the technical aspects, 
integrating data sources and providing a robust foundation, while the curation of inventory content ensures accurate organization and metadata representation. 
Together, they form a cohesive system that streamlines data discovery, access, and exploration for non-satellite NASA Earth Science data.



.. The backend component consists of five components:
.. Django’s models and relational databases APIs (serializers) to incorporate Common Metadata Repository (CMR) metadata and Airborne Science Program's (ASP) information. Then returns the database information back to CMR and ASP.
.. A maintenance interface (MI) for both entering and updating database content
.. A public user data discovery portal or user interface (UI) for submitting queries with search terms, reviewing information, and accessing data product links

.. The second part of CASEI is the curation of inventory content. All information in CASEI follows a common data model through a careful curation process along with multiple quality reviews to support the diverse data formats. First a curator compiles suborbital observation metadata for NASA Earth Science products by efficiently categorizing it into campaigns, platforms, and instruments. They follow a structured hierarchy, set of definitions, and decision tree to properly organize this data then submit it for a first and final admin review. All of this effort is conducted through the MI and once it is finally published it’s streamlined into the UI for user access.

To access the CASEI User Interface, visit the following link: : `<https://impact.earthdata.nasa.gov/casei/>`_
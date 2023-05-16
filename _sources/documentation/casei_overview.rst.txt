
Catalog of Archived Suborbital Earth Science Investigations
===========================================================

The Catalog of Archived Suborbital Earth Science Investigations (CASEI), is a centralized airborne and field data inventory that streamlines discovery of non-satellite NASA Earth Science data by providing contextual information on events, motivations, and potential data caveats. With CASEI, users can search and browse NASA’s airborne and field data archives, regardless of which data repository (or DAAC) is responsible for their stewardship.

CASEI has two major components. The first is the backend architecture written with Python and comprised of five components:
Django’s models and relational databases
APIs (serializers) to incorporate Common Metadata Repository (CMR) metadata and Airborne Science Program's (ASP) information. Then returns the database information back to CMR and ASP.
A maintenance interface (MI) for both entering and updating database content
A public user data discovery portal or user interface (UI) for submitting queries with search terms, reviewing information, and accessing data product links

The second part of CASEI is the curation of inventory content. All information in CASEI follows a common data model through a careful curation process along with multiple quality reviews to support the diverse data formats. First a curator compiles suborbital observation metadata for NASA Earth Science products by efficiently categorizing it into campaigns, platforms, and instruments. They follow a structured hierarchy, set of definitions, and decision tree to properly organize this data then submit it for a first and final admin review. All of this effort is conducted through the MI and once it is finally published it’s streamlined into the UI for user access.

Link to CASEI User Interface: `<https://impact.earthdata.nasa.gov/casei/>`_

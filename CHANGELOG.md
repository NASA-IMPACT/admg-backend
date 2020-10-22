# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased
Consolidated ingest pipeline

## 0.1.6 - 2020-10-22
### Fixed
- CREATE change requests now log the linked database object

### Added
- `api/change_request/{uuid}/validate` endpoint to validate specific change request
- `api/validate` endpoint to validate json

### Changed
- db objects generated from a CREATE change request now inherit the uuid of the change request for linking purposes
- error message details are now returned as processed json instead of strings
- image endpoint now returns `{'success': boolean, 'message': string, 'data': []}` for get and post
- change requests can now hold invalid data until the push operation

## 0.1.5 - 2020-10-09
### Fixed
- linking behavior of image objects has been changed from CASCADE to SET_NULL
- update bounding box coordinate ordering serializer

### Added
- `/api/campaign` will now return an aggregated field, `dois`, containing DOIs from the linked `collection_periods`

## 0.1.4 - 2020-09-24
### Added
- DOI.long_name text field  

### Changed
- `/change_request` endpoint now returns a JSON response
- DOI.doi changed to DOI.short_name

## 0.1.3 - 2020-08-24

### Added
- Support for https using letsencrypt
- Multistage build capabilities to Dockerfile
- Functionality to use PostgreSQL Full Text Search in API calls based on multiple columns
    - Search method to DataModel
    - Default search_fields to DataModel (short_name, long_name)
    - Additional search_fields to Campaign (short_name, long_name, description_short, description_long, focus_phenomena)
    - Additional search_fields to Platform (short_name, long_name, description)
    - Filter by search to GenericCreateGetAllView

### Changed
- Dockerfile to use the more lightweight Linux Alpine distro

## 0.1.2 - 2020-08-13

### Fixed
- Django will no longer automatically append '/'s to incorrect urls, and will instead return 404

### Changed
- Image.image is now a required field for posting to the `/api/image` endpoint
- Image.short_name has been changed to Image.description, in order to generate alt text

### Added
- added UUID endpoint for images at `/api/image/<image_uuid>`

## 0.1.1 - 2020-08-05
### Fixed
- removed deprecated serializer references to geophysical_concept.instruments and gcmd_phenomena.campaigns

## 0.1.0 - 2020-08-04
### Changed
#### Requirements
- repo now requires boto3 and botocore; see [requirements/base.txt](https://github.com/NASA-IMPACT/admg_webapp/blob/master/requirements/base.txt)


#### APIs
- read access no longer requires a token or login
- new image endpoint at `/api/image`
- new DOI endpoint at `/api/doi`

#### Utils
- new functions to access CMR API and process the results

#### Ingest
- ingest code has been updated for new models and new validation

#### Env
- new local and production .env files with additional variables

#### User Models
- id now uses UUID instead of int

#### Data Models
##### Added Tables
- Image
    - image
    - short_name
    - owner
- DOI
    - doi

##### Added/Removed Fields
- PartnerOrg
    - other_resources
- Campaign endpoints
    - logo
    - cmr_metadata (removed)
    - gcmd_phenomenas (removed)
- Platform endpoints
    - image
    - dois
- Instrument endpoints
    - image
    - overview_publication
    - arbitrary_characteristics
    - dois
    - geophysical_concepts (removed)
- Deployment
    - study_region_map
    - ground_sites_map
    - flight_tracks
- CollectionPeriod
    - dois

##### Optional to Required
- PartnerOrg
    - website
- GcmdProject
    - bucket
- GcmdInstrument
    - short_name
- GcmdPlatform
    - short_name
    - category
    - description
- GcmdPhenomena
    - category
- DataModel
    - short_name
- Campaign
    - funding_agency
    - lead_investigator
    - nasa_led
    - focus_areas
    - seasons
    - repositories
    - platform_types
    - geophysical_concepts
- Platform
    - description
- Instrument
    - description
    - technical_contact
    - instrument_types
    - gcmd_phenomenas
    - measurement_regions
    - geophysical_concepts
- IopSe
    - short_name
- CollectionPeriod
    - auto_generated

##### Required to Optional
- DataModel.long_name

##### CharField to TextField
- all models notes_public
- all models notes_internal
- all models *description

##### TextField to UUIDField
- PlatformType.gcmd_uuid
- InstrumentType.gcmd_uuid  
- Repository.gcmd_uuid    
- MeasurementRegion.gcmd_uuid
- GeographicalRegion.gcmd_uuid
- GeophysicalConcept.gcmd_uuid
- GcmdProject.gcmd_uuid
- GcmdInstrument.gmcd_uuid
- GcmdPlatform.gcmd_uuid
- GcmdPhenomena.gcmd_uuid

##### Max Char Length from 65535 to 256
- Platform.lead_investigator
- Instrument.lead_investigator

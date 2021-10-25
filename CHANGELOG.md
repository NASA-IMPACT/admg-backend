# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.2.1 - 2021.08.31

### Changed

- the following fields have been removed from public get requests, however can still be posted to by authenticated users with an appropriatly scoped token
  - `notes_internal` on all endpoints
  - `campaign.description_long`
  - `collection_period.platform_identifier`
  - `collection_period.home_base`

## 0.2.0 - 2021.04.28

### Change Models

- Change Objects have a new `IN_TRASH` state and associated `trash` and `untrash` actions
- Change objects have new field `field_status_tracking` and associated actions `generate_field_status_tracking_dict` and `get_field_status_str`
- ApprovalLog has new actions, `TRASH` and `UNTRASH`

### Data Models

- `/api/gcmd_project`
  - `short_name` is now optional
  - `gcmd_uuid` is now unique
- `/api/gcmd_instrument`
  - `short_name` is no longer unique
  - `gcmd_uuid` is unique
- `/api/gcmd_phenomena`
  - `gcmd_uuid` is now unique
- `/api/website`
  - `website_types` list field has been replaced with `website_type` which returns a UUID
  - `title` is now optional
- `/api/campaign`
  - `funding_agency` is now optional
  - `number_collection_periods` has been replaced by a new, read only, field `number_ventures`
  - `number_data_products` is now read only
- `/api/instrument`
  - `arbitrary_characteristics` is now `additional_metadata`
- `/api/deployment`
  - has a new field, `spatial_bounds` which functions the same as campaign.spatial_bounds
  - `number_collection_periods` has been removed
- `/api/collection_period`
  - `asp_long_name` has been removed. any data previous stored here is now in `aliases`
  - `num_ventures` has become `number_ventures` to maintain consistency with other models

## 0.1.12 - 2021.03.31

- `/api/campaign` has a new field `website_details` which returns a list of dicts with website information, including priority
- all limited tables now have a field `order_priority` which can optionally be used to order them for display on CASIE

## 0.1.11 - 2021.03.19

### Added

- `/api/platform` has a new field `search_category` which returns one of the 6 custom categories for each platform

## 0.1.10 - 2021.03.12

### Added

- `/api/platform_type` has new field, `patriarch` which outputs the highest level parent in the hierarchy
- `/api/platform` has a new field `search_category` which outputs one of the 6 custom ADMG search categories

## 0.1.9 - 2021.03.02

### Changed

- new `/api/change_request/<uuid>` endpoints
  - `/submit`
  - `/claim`
  - `/unclaim`
  - `/review`
  - `/publish`
  - `/reject`
- new `/api/approval_log/` endpoint
- `doi` endpoint now has the following fields
  - `concept_id`
  - `doi`
  - `long_name`, an optional field to provide a custom ADMG name
  - `cmr_short_name`, `cmr_entry_title`, `cmr_projects`, `cmr_dates`, `cmr_plats_and_insts`
  - `date_queried`
  - many to many links to `platform`, `instrument`, `collection_period`, and `campaign`
- new integrated cmr app supports doi recommendations for `platform`, `instrument`, `collection_period`, and `campaign`
- `campaign.doi` has been renamed `campaign.campaign_doi` for clarity and standardization with `instrument` and `platform`
- `campaign` endpoint has lost the following fields:
  - `repository_website`
  - `project_website`
  - `tertiary_website`
  - `publication_links`
  - `other_resources`
  - these are replaced by the many to many field `websites`
- new `website` endpoint
  - `url`
  - `title`
  - `description`
  - `website_type`
- new `website_type` endpoint
  - `long_name`
  - `description`
- new `campaign_website` endpoint
  - `campaign`
  - `website`
  - `priority`
  - this endpoint shows the link between a campaign and website and allows the assignment of a priorty for each website relative to the campaign it is linked to, so that the display order of the websites can be adjusted.

### Removed

- removed `/api/change_request/<uuid>` endpoints
  - `/approve`
  - `/reject`
  - `/push`

## 0.1.8 - 2021-01-06

### Changed

- `nasa_mission` endpoint removed. `campaign.nasa_missions` now returns a string instead of a list of uuids
- `notes_internal` field standardized accross all limited field endpoints
- `alias` endpoint now accepts `model_name` instead of `content_type`
- `gcmd_platform.short_name` is now optional

## 0.1.7 - 2020-10-30

### Added

- `aliases` field to `campaign`, `instrument`, `platform`, `deployment`, and `partner_org`

### Changed

- `alias` endpoint
  - removed `long_name`
  - increase length `short_name` to 512 char and remove unique restriction
  - change `source` to unlimited length

## 0.1.7 - 2020-10-29

### Fixed

- linking error between measurements and instruments

### Added

- new text field for the `image` endpoint, `source_url`

## 0.1.6 - 2020-10-27

### Fixed

- CREATE change requests now log the linked database object

### Added

- `api/change_request/{uuid}/validate` endpoint to validate specific change request
- `api/validate` endpoint to validate json
- new endpoints, `measurment_type` and `measurement_style` to replace `instrument_type`

### Changed

- db objects generated from a CREATE change request now inherit the uuid of the change request for linking purposes
- error message details are now returned as processed json instead of strings
- image endpoint now returns `{'success': boolean, 'message': string, 'data': []}` for get and post
- change requests can now hold invalid data until the push operation
- all `example` fields have max_length increased from 256 to 1024 char
- `gcmd_platform.description` is now an optional field

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
- all models \*description

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

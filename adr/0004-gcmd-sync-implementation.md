# 4. GCMD Sync Technical Implementation

- Status: Accepted
- Deciders: @JohnHedman @alukach
- Date: 2022-09-14

Technical Story: [#297](https://github.com/NASA-IMPACT/admg-backend/issues/297)

## Context and Problem Statement

This ADR documents the implementation of this feature. For the design and decision drivers, see [ADR #2](./0002-gcmd-sync-design-process.md).

## Workflow

### Background processing

<a name="background-processing-workflow"></a>
The GCMD Sync background process fetches items from the GCMD Keyword Management Service API and compares them to records in our database. If items are new, they are added as a Create Draft. If they are already present in the DB, but have been modified, an Update Draft is created. If any items in the DB are no longer available through the KMS API, a Delete Draft is created.

```plantuml
@startuml
start

:Sync GCMD Button;
:Schedule sync_gcmd task;

while (For each GCMD Scheme ("instruments", "platforms", "projects", "sciencekeywords"))

    :GET Request to GCMD API
    https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/<scheme>;

    while (Loop through keywords)
        if (Keyword UUID in DB) then (yes)
            if (Keyword Properties match DB Record) then (yes)
                :No action;
            else (no)
                :Create "Update" Draft for Keyword;
            endif
        else (no)
            :Create "Create" Draft for Keyword;
            if (Recommended objects related to keyword?) then (yes)
            else (no)
                :Autopublish Draft;
            endif
        endif
    endwhile (Done)

    :Create set of all UUIDs of returned keywords;
    :Retrieve all GCMD Items of the relevant type;
    while (Loop through GCMD Items)
        if (UUID of GCMD Item not in set of UUIDs) then (yes)
            :Create "Delete" Draft for GCMD Item;
        else (no)
            :No action;
        endif
    endwhile (Done)

endwhile (Done)

:Send notification email to admins with count of items added, updated, deleted and auto-published;

stop
@enduml
```

### Interface

After GCMD Keywords have been synced, admins can review the proposed changes at `/gcmd_list/draft`. Reviewers can view each proposed keyword change and make note of any changes. They can also review CASEI models (Campaigns, Platforms, Instruments) associated with the keyword (referred to as Affected Records) and indicate whether to continue associating each model with that keyword. Once all Affected Records have been addressed, the reviewer can publish the changes.

![Screenshot of Keyword Draft Editing interface](./images/keyword-edit.png)

## Components

### Asynchronous Tasks

This system consists of two asynchronous Celery tasks:

1. `sync_gcmd` is the main process that interacts with the GCMD Keyword Management Service API (https://gcmd.earthdata.nasa.gov/kms/) and the MI database. This task is currently run manually, but could be configured to run on a schedule.

2. `email_gcmd_sync_results` is scheduled at the end of a successful `sync_gcmd` run and sends a notification by email to MI administrators with the results of the sync.

### GcmdSync Class

Every run of the GCMD Sync process creates a `GcmdSync` object for each `gcmd_scheme` ("instruments", "projects", "platforms", "sciencekeywords"). Each object fetches the keyword list for its scheme and processes it according to the [Background Processing Workflow above](#background-processing-workflow). The object stores lists of created, updated, deleted and auto-published keywords, which are then used in the `email_gcmd_sync_results` task.

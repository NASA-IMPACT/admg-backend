# GCMD Sync Design Process

This is an adapted version of an ADR to document interface design decisions

+ **Status:** developed | Technical Story: #297
+ **Deciders:** Heidi Mok, John Hedman, Anthony Lukach, Stephanie Wingo, Deborah Smith, Shelby Bagwell, Carson Davis
+ **Date:** 2022-05-31

**Design Story:** #234


## Broader Project Summary
The Airborne Data Management Group (ADMG) curates and distributes metadata for field operations conducted by the Earth Science Project Office (ESPO). ADMG wants to make it easier for scientists to access this data by creating an inventory of standardizing campaign metadata and a single search interface. Previous to the interface, data collection was managed in a massive Google Sheet and the IMPACT dev team imported it into the database. Development Seed helped build a search interface called CASEI and a maintenance interface (MI) where the inventory team can add new campaigns of metadata. 

## Context and Problem Statement
Sometimes keywords being searched in CASEI get out of sync from NASA’s GCMD database (a keyword management system). [GCMD keywords](https://www.earthdata.nasa.gov/learn/find-data/idn/gcmd-keywords) are a hierarchical set of controlled Earth Science vocabularies that help ensure Earth science data, services, and variables are described in a consistent and comprehensive manner. We wanted to make sure that CASEI was using the same keywords as the GCMD database so we built a back end tool ([#216](https://github.com/NASA-IMPACT/admg-backend/pull/216)) that does a GCMD sync. This runs a job to fetch and compare instruments in our system with the GCMD database, then creates results of differences between records, and outputs a new draft record. However, there was nowhere on the maintenance interface to allow admins to review keyword changes and resolve any affected records.

![GCMDKeywordViewer](https://user-images.githubusercontent.com/10764915/172685673-b12a33d0-cddc-40a2-9b25-a4cfcba6c104.png)
_Image of the GCMD Keyword Viewer_

## Pain Points
1. Curator’s don’t know that a GCMD sync has occurred.
2. Curator’s don’t know what is the impact of a GCMD keyword on other dependent records already in CASEI. 
3. Curators don’t want to accidentally change GCMD keyword data in the MI.

## User Stories
1. As an admin, I want to know when a GCMD sync has occurred, resulting in new draft records, so that I can quickly go and review those records.
2. As an admin, when looking at a new draft record related to GCMD, I want to know the implications of the change proposed (particularly Update and Delete records) so that I can fix the other dependencies and publish the draft.
3. As an admin, when looking at a new draft record related to GCMD, I don’t want to change something that shouldn’t be changed.

## Project Considerations
+ **New members.** New Development Seed members working on this — Heidi and John.
+ **Cross-project sharing.** Other NASA Impact Teams will potentially want to reuse aspects of this solution because GCMD syncs are going to affect other projects.

## Decision Drivers
+ **Scope** - Working within the existing maintenance interface as of today and not redesigning broader aspects of the MI beyond what’s needed for GCMD. 
+ **Admin feedback** - Feedback through design sessions with Deborah, Stephanie, and Shelby who are key users of this functionality.
+ **Priority of GCMD keywords** - Curators shouldn’t be able to change GCMD keyword data as it takes precedence over keywords in CASEI.

## Process Timeline
+ **Jan 21** - Created design investigation ticket for this problem [Design Issue #234 ](https://github.com/NASA-IMPACT/admg-backend/issues/234)
+ **Jan 21** - Investigated the problem by mapping out a flow of the GCMD backend sync tool in Figma. Learned a little more about GCMD keywords. Resulted in three high level pain points and user stories. [Figma investigation link. ](https://www.figma.com/file/Q2dT0uf0tUbPVO5FSEkzv8/CASEI---Back-End-MI?node-id=6%3A5)
+ **Jan 26 - Feb 8** - Three weeks of Deep Dive sessions between Heidi and ADMG (Stephanie, Deborah) to further understand the ideal GCMD review flow, and work through the solution. [Reference Figma ideation link.](https://www.figma.com/file/Q2dT0uf0tUbPVO5FSEkzv8/CASEI---Back-End-MI?node-id=6%3A100) 
+ **Feb 14 - 24** - Acceptance Criteria written and mockups at 80%-90% design, ready for development with changes anticipated as development progresses
+ **Feb 18** - Development Epic written in GitHub by John [Epic #297.](https://github.com/NASA-IMPACT/admg-backend/issues/297)
+ **Apr 28** - Adjustments to mockups after discussions. [Figma final mockup link.](https://www.figma.com/file/Q2dT0uf0tUbPVO5FSEkzv8/CASEI---Back-End-MI?node-id=443%3A14332)

## Key Learnings Guiding the Solution
+ **Keywords aren’t just one word, but represented as a full path.** Any part of that path is the keyword (think of the keyword as the entire string). we need to highlight the difference showing what’s changed, not just the new keyword in isolation. We need to always show a full path like: Earth Remote Sensing Instruments > Active Remote Sensing > Altimeters > Radar Altimeters > [CloudSat-CPR](https://gcmd.earthdata.nasa.gov/KeywordViewer/scheme/all/f9941038-62ff-4a59-b82d-6b2f9a4546d2?gtm_keyword=CloudSat-CPR&gtm_scheme=instruments)
+ **Three types of keyword changes can occur: modifications, deletions, and new keywords.** Only modifications and deletions may directly affect existing records in the system but new keywords can be recommended to be added to existing records.

## Notable Design Decisions and Alternatives

**1. To notify admins about a GCMD change, we will send an email to admins that directs them to a new subpage in the MI** where they can see the changes and take action. 
+ **Rationale:** GCMD changes are considered a high priority and admins may not be aware that changes have taken place. While there are existing GCMD sub pages in the MI, having a filtered view just for GCMD changes can serve as a to-do list. 
+ **An alternative** is to design an in-app notifications system which is something that could be beneficial in the future if there are other types of changes that are of the same level of importance. We didn’t explore this because it would be a new scope of work and GCMD was already a fairly large change. 

**2. There is no admin approval process for GCMD changes.** The normal process of moving from “in progress>In Review>In Admin Review> Published” is not needed for GCMD keywords. Instead, new GCMD keywords are automatically published, and modified and deleted keywords are automatically published upon clicking “Done” on a keyword draft. Affected records are also automatically published upon clicking “Done”. 
+ **Rationale:** Since GCMD keywords are not changeable, there isn’t editing to be done and since only admins can edit the GCMD changes, the approval process is not necessary.
+ **In alternative designs** we had manual approval process just like the existing way of doing things. We were also cautious of implications if affected records had in-progress drafts. But ultimately we decided to reduce unnecessary clicks for admins.

**3. Admins need to click “Done” and confirm changes in order for the GCMD items to be removed from the review list.** Instead of automatically removing items from the new GCMD Review page, admins should be the ones to determine when they have verified that all the affected records of a keyword are correctly associated and confirm it.  
+ **Rationale:** It gives admins more control over the final decision of how GCMD changes should affect CASEI. If admins change their mind about an association as they are reviewing, we don’t want the page to suddenly disappear without them acknowledging it.
+ **An alternative option** is for admins to not have to click “Done” and it to automatically happen once all of the affected records have been associated. 

## Flow and UI Mockups

**Get notified about keyword changes**

After each sync, an email will be sent to admins of CASEI (admg@uah.edu). The email will include three sections each type of GCMD change: modified, deleted, or new changes.

![Solution-EmailNotification](https://user-images.githubusercontent.com/10764915/172690936-c9864012-205d-43e1-8178-4af1cd64e42a.png)

The email links admins to a new “Review GCMD Changes” subpage in the MI. The subpage follows the same layout of a table as all the other pages but it’s a filtered list of all of the draft keyword records that have been changed. The page only shows changes with one or more affected records.

![Solution-NewSubpage](https://user-images.githubusercontent.com/10764915/172690990-bad43073-ccce-4726-8ec5-66827896cd9a.png)

**Review keyword and associations**

To review a keyword change, admins click into the keyword short name and it takes them to a page view of the draft GCMD sync record. This page looks similar to other records in the MI but information about the keywords are read-only to prevent admins from changing GCMD information. New and previous paths are also included with red text for what’s changed so that admins can compare the difference. 

The bottom table is a new section that only applies to GCMD keyword change records. The idea is to show which records that are currently published in CASEI might be affected by the keyword change. Admins can click to manually view each record and then decide whether they want to keep (or add) the association. Saving will mark progress (and add to the resolved count) and clicking Done will automatically publish this record all the changes to the affected records. A confirmation message appears because once you confirm it will be a manual process to make changes afterwards. 

![Solution-ModifiedKeyword](https://user-images.githubusercontent.com/10764915/172691588-c993bc12-f9a3-4e7a-8f8a-82a2cf6a4ea6.png)


Upon clicking done, the new keyword is removed from the Review GCMD keywords page and the admin action is done and they can move on to the next keyword.


![Solution-Confirmation](https://user-images.githubusercontent.com/10764915/172691631-8a6fdf5c-3ecd-46c3-bc05-4a6f54bc73be.png)





# MI Workflow Change Design Process
This is an adapted version of an ADR to document interface design decisions.

- **Status:** Designs completed (to “80%”) for room for change
- **Design deciders:** Stephanie Wingo, Deborah Smith, Shelby Bagwell, Heidi Mok
- **Input:** Ed Keeble, John Hedman, other members of ADMG
- **Implementation:** Ed Keeble, John Hedman
- **Date:** May 31, 2022 - Aug 8, 2022

**EPIC:** [MI Workflow Redesign: #270](https://github.com/NASA-IMPACT/admg-backend/issues/270)


## Project Context
The NASA [Airborne Data Management Group (ADMG)](https://www.earthdata.nasa.gov/esds/impact/admg) makes it possible for scientists to access metadata for field operations conducted by the Earth Science Project Office (ESPO) on the [CASEI website](https://impact.earthdata.nasa.gov/casei/). To do this, ADMG curators use the Maintenance Interface (MI) to add, review, publish, and manage that information to keep CASEI up-to-date. The main kind of metadata include field Campaigns, Platforms, and Instruments.

### Motivation for Change
The Maintenance Interface was originally built with a focus on required functionality. The UI/UX reflects this by presenting information like how the data model works, where all content is displayed as a record or “draft” (i.e. create draft, update draft). As more of these drafts get added over time, they become harder to keep track of on the UI. There also exists parent/child/peer relationships between drafts that add to the confusion. Overtime, curators brought up quality of life issues that trickled up to a broader workflow challenge: how to help curators keep track of published versions of Campaigns, Platforms, and Instruments, and whether there are edits in progress to attend to.

**Summary of pain points:**
- There are too many drafts that aren’t organized in a way that matches the workflow of a curator. Curators want to keep track of what’s published, what’s being changed, and deprioritize what’s no longer relevant.
- Campaigns, Platforms, and Instruments metadata can have peer relationships to one another, but also parent/child associations. The current presentation of all metadata as drafts that you click into one by one makes it confusing to see the broader groupings or “family” of information.

### Solution Goal
Improve the curator workflow for finding, updating, and keeping track of Campaigns, Platforms, and Instruments.
- Take a more holistic design approach instead of making one-off fixes here and there
- Design with fresh eyes - Challenge existing concepts (like “drafts”) that curators have gotten used to, but that don’t typically make sense to those onboarding to the project.
- Don’t make significant changes to the existing backend
- Involve the ADMG team for feedback - Since curators are the main users, their feedback throughout the design process is what shaped the new design.


### Process Timeline
- **Jan 21, 2022** - Initial issue created #270 
- **Apr 26, 2022** - [Ideation session and initial user flow mapping in Miro](https://miro.com/app/board/uXjVOHZO4p8=/?moveToWidget=3458764524072498993&cot=14) to better understand what problem(s) we are trying to solve
- **May 12-19, 2022**  - Three Deep Dive Sessions to get feedback on [design prototypes](https://www.figma.com/proto/zY7BS9fR1huZ0CieHf3Dm8/MI-Workflow-Change?page-id=0%3A1&node-id=0%3A1&scaling=min-zoom&starting-point-node-id=2%3A309&show-proto-sidebar=1)
- **Jun 2, 2022** - [80% done design](https://www.figma.com/file/zY7BS9fR1huZ0CieHf3Dm8/?node-id=175%3A26643), ready for final comments and implementation discussions.
- **July 18, 2022** - Meeting with Heidi, Ed, John to talk about breaking down designs
- **Aug 9, 2022** - Drafting stories in GitHub
- **Aug 22, 2022** - Heidi<>Ed<>John meeting to review stories and revising
- **Aug 24, 2022** - Design process document and epic 'ready for development'


### Key Learnings Guiding the Solution
- **Prioritize the most relevant content** - The most important information to prioritize is what is currently published and edits in progress. History is nice only as a reference.
- **Enhancing the dashboard** - A dashboard for each “family” of campaigns, platforms and instruments is a helpful way to create a logical flow for finding and editing information.
- **Using a more visual status indicator** - A desired way to keep track of the overall curation approval process. There was interest in exploring a status indicator at the form level, but it was out of scope.
- **Creating more of a workflow** - While all the information in the MI are interrelated, it doesn’t mean the interface should just have everything presented equally. We still need to help curators navigate through ever growing content without it being overwhelming.

## Current 
To demonstrate the current state pain points, we look at screenshots of a Campaign called “ACTIVATE” as an example.

![Campaigns-Activate](https://user-images.githubusercontent.com/10764915/186510675-4b1fafaf-6f62-4b13-bd90-1b68c9043798.png)
This is a view of all Campaign Drafts in the Maintenance Interface. Everything is listed here as a “draft”. In the screenshot, the ACTIVATE campaign is filtered. 
- **Problem:** Notice there are many versions of the ACTIVATE campaign because it was published and then updated several times. There is a lot of outdated information displayed. It is easy to accidentally click on a past version and create a new change from that out-of-date version. 
- **Problem:** To know what is the latest version to click, you need to rely on the columns “Draft Action” and “Status”. But they share the same status keywords for both columns which can be quite confusing to interpret.

![Campaigns-Activate-Published](https://user-images.githubusercontent.com/10764915/186510734-c3a2e6e8-8d34-4111-b262-d026d90fb370.png)
The Published Content tab on the same page is where you can find the version of the ACTIVATE campaign that is currently live on the website.
- **Problem:** Separating published versions from drafts at this navigation level means you have to search for ACTIVATE across pages in order to cross-reference them and see if an edit is currently in progress.

![Campaign-Draft-Published](https://user-images.githubusercontent.com/10764915/186510862-8a7f163c-f01e-44ec-8bb4-48743e9616ed.png)
When clicking into the actual content of the ACTIVATE campaign, you can now edit the form.
- **Problem:** If you accidentally clicked into an outdated version, you can get quite confused about where this version fits against the overall campaign evolution. 

![Campaign-Deployments](https://user-images.githubusercontent.com/10764915/186510889-e7f060b2-c93e-406b-952c-7681c8320430.png)
![Campaign-DOI](https://user-images.githubusercontent.com/10764915/186510893-661e20fc-57d4-4270-9824-61f80fc4465a.png)
As another option instead of clicking into the ACTIVATE form, an alternative is clicking into a dashboard for the ACTIVATE campaign that focuses on other information related to, but not directly part of the campaign. 
- **Problem:** Typically a Dashboard view is a place where the entirety of something is represented at a high level. In this case only information associated with a campaign is part of the Dashboard which makes the content appear very disjointed.
- **Problem:** As seen on the screenshots, there are two subtabs of content and both present a lot of information and form inputs. While it can be convenient once you understand what this content is, it’s also overwhelming and you need a very large screen and focus to keep track of your actions.

## New
To demonstrate the new solution, we follow the same ACTIVATE campaign example. 

### Finding a Campaign
![ACTIVATE-1-Created](https://user-images.githubusercontent.com/10764915/186511770-bda3d02f-802d-434a-8933-fa3cb12c387a.png)
This is the new campaign homepage where you can search for ACTIVATE. 

In the new design, there is no separation of drafts and published content. Instead, the ACTIVATE campaign is displayed only once. 
- **Rationale:** To streamline the search process. Given this is the highest level of navigation for all Campaigns, it’s helpful to create a hierarchy of information so that versions of the same campaign are secondary to the main focus of just finding that campaign.

The column headers are slightly different. Now there is only one status column with a visual marker representing where this campaign is along a review process.
- **Rationale:** Reduce the cognitive load of trying to interpret the status of a given campaign. Don’t make curators have to work so hard to decide which campaign version to select. By referencing the 'Last Published Date' and 'Last Edit Date', it is easy to know the campaign is net new or an update.


### Reviewing and Editing a Campaign
![ACTIVATE-2-Edit](https://user-images.githubusercontent.com/10764915/186511856-2bba4ea2-6175-40b8-9dc1-19cc3196811f.png)
![ACTIVATE-3-Published](https://user-images.githubusercontent.com/10764915/186512087-fcb92bdc-be26-46b2-818e-0ca4499c26c8.png)

When you click the ACTIVATE campaign you now arrive at a centralized dashboard that represents the full picture of that campaign.
- **Rationale:** To emphasize key information about a campaign. Other related information (the Details and DOIs tab) are still there but prioritized after the actual campaign itself. Finally, a new history tab consolidates all past versions associated with the campaign so that you can reference it only if needed. The hope is that this new dashboard will create a workflow that makes sense to curators who are constantly bouncing back and forth between what is published and edits.

Once edits to the ACTIVATE campaign have been approved and published, it appears as read-only content in the Published tab.
- **Rationale:** To always keep a dedicated view of what is live on the website at all times while also making it easy to know if edits are being made.

### Referencing the history of a campaign
![ACTIVATE-4-History](https://user-images.githubusercontent.com/10764915/186512265-ffccbc68-d3fc-4ad7-a957-f0f2108ac98c.png)

Looking deeper into the new History tab, this is where past versions of a campaign and its associated information are now separated.
- **Rationale:** Since curators mainly care about what’s published and if there’s an edit, all the past versions only create confusion so keeping it separate helps with version control. 

The history table includes new information about who made the change and a “Change Summary”. 
- **Rationale:** If we can offer a quick helpful description by auto-naming (i.e. Campaign-Update-Logo), it could make this History page more valuable because you can get a high level sense of how significant the change was.

### Adding and managing Campaign associations - Details and DOIs
![ACTIVATE-5-Details](https://user-images.githubusercontent.com/10764915/186512358-2c1e8b4f-81fe-4565-92d7-74366ebe48d6.png)
![ACTIVATE-6-DOIs](https://user-images.githubusercontent.com/10764915/186512362-d726ea03-01b8-4958-9c67-d8d14ce90b8c.png)

The Campaign details tab is largely the same as today’s view where curators can create and keep track of Campaign Deployments, and subsequent set of Intensive Operation Periods (IOPs), Significant Events, and Continuous Data Collection Period (CDPIs). The main changes include visual clean-up on the UI.
- **Rationale:** Since there is so much information to keep track of on these UIs, the simplification of the UI helps hone in on the most important information to show, and progressively show details only when you are ready to actually edit that information.

The Campaign DOIs tab has a bigger UI change. The goal of the Digital Object Identifier (DOI) tab is to link Campaign deployments, Instruments, Platforms with unique identifiers created by NASA Earth Science Data System (ESDS), ultimately keeping the system up-to-date.
- **Rationale:** The design goal was to keep consistency with the UI of the Details tab because even though the content is different the general steps of creating and managing the content is the same. In both cases it’s helpful to remain as high-level as possible and let you drill into details only when you are ready to edit that information.

## Design Reference

- The overall 80% done design file is located in [Figma](https://www.figma.com/file/zY7BS9fR1huZ0CieHf3Dm8/MI-Workflow-Change?node-id=175%3A26643). 
- It’s marked as 80% done not because it’s unfinished work but based on the principle that the visual design should leave room for realistic changes as development occurs.
- [Figma process work](https://www.figma.com/file/zY7BS9fR1huZ0CieHf3Dm8/MI-Workflow-Change?node-id=0%3A1)is available on a different page in the same file
![Figma-80-Done-Designs](https://user-images.githubusercontent.com/10764915/186511468-880a6c0b-794b-4dd7-9cfc-779348d8051a.png)

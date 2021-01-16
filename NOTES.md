# Notes

## Proposal

1. Use the admin interface for all data editing
   1. Clean up admin for more streamlined interaction
   2. Use actions for approving edits

## Proof of Concept

1. Cleaning up a few views:
   - Campaign
   - Platform
   - Collection Period
1. Integration with Change model:
   1. When a user hits "save" on a model within the Admin, that record should NOT be changed. Rather, a change record should be created.

## Questions

- How will the Change model work with relationships? E.g. I want to create a `Campaign` and a `Deployment` (which references the new `Campaign`)
  - _Idea:_ When a `CREATE` change is created, a new UUID is generated for that object that is to be created. Update the admin to FK fields to refer to either the already existing records or potential records that are to be created when a change is approved. A change can NOT be approved if it depends on another change (that other change must first be approved).

---

- Allow users to work with unfinished data
  - Broken links, missing items
  - Can take a week + to get supporting data, want to be able to store in-progress data
- Change Requests
- Be able to link to draft or real record
  - Campaign must have season (fall, winter), new season
  - More complicated relationships (e.g. instrument) would also follow draft pattern
  - Research campaign first, then get more specific
- Validation endpoint takes a change object and will verify that it's ready to go

---

- Hard parts:
  - Referencing draft content
  - Enforcing permissions
  - Quality display of information, particularly around draft
    - See campaigns that are available for review
    - See tree of resources that need to be approved
    - Need to track what they can approve

---

Tests:

1. Create a record
   1. Can save partial create (i.e. does not pass validation)
2. Update a record
   1. Can save partial patch (not all details required)
3. Delete a record
   1. Model form displays previous values but as read-only (with message stating can't change values for Delete record)
4. General change view
   1. FK and M2M fields can refer to both existing records and relevant change records
5. Permissions
   1. Create "Staff" member, has permissions to read records but can't Create, Update, or Delete records (except for Change records).
   2. Add convenient way to create a Change record when user tries to Create, Update, or Delete existing record.
6. Superuser can approve/reject changes
   1. Runs approve/reject on model: https://github.com/NASA-IMPACT/admg_webapp/blob/eff089dcf09696d685a6cb5d0958161c171719f6/api_app/models.py#L233-L284

--
Deployment: https://docs.github.com/en/free-pro-team@latest/rest/reference/actions#create-a-workflow-dispatch-event

```sh
curl \
  -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token 0d735f532f2dad12d7da33f9a8f876f0112f680f" \
  https://api.github.com/repos/developmentseed/admg-inventory/actions/workflows/deploy.yaml/dispatches \
  -d '{"ref":"develop"}'
```


```py

# Editor Group
group = Group.objects.create(
    name='Editor',
)
group.permissions.add(*Permission.objects.filter(content_type__app_label__in=['data_models'], codename__startswith='view_'))
group.permissions.add(*Permission.objects.filter(content_type__app_label='api_app').exclude(codename__startswith='delete_'))

# Admin Group

# TODO: Add deploy permission
```

## TODO


### Change Record

1. ???Display approved status under each change
1. Datetime field not rendering with datetime selector
   ```js
   calendar.js:10 Uncaught ReferenceError: gettext is not defined
      at calendar.js:10
   DateTimeShortcuts.js:12 Uncaught ReferenceError: gettext_noop is not defined
      at DateTimeShortcuts.js:12
    ```
2. Regarding spatial bounds, support raw text entry, multipolygon
   1. E.g. `[30, -30, 135, -155], [24, 24, -82, -82]`
3. For Campaign, render related Platforms & Deployments & Instruments as links

### Potential Tickets

1. Implement Approval Workflow
   2. Allow Admin to publish a change record (if it has been approved)
   3. Reviewer needs to be able to make changes to other's drafts
2. Create Draft from existing data
3. Support intermittent approval (field-level approval)
   1. Allow user to mark a field reviewed
4. DOI Integration
5. Display FK change records alongside published data
   1. Allow user to create drafts of related models natively from Change Record admin (e.g. create new season while creating platform)
6. Support for content from Langley
   1. Q: What will that look like? Is this a new state before "In Progress"?
7. Support parent -> child heirarchy for "Platform Type" widget, or at least order by heirarchy (most descendent first)


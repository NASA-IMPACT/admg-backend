# this file generates a list of unpublished drafts which point to the same root object

from api_app.models import Change

changes = Change.objects.exclude(status=6)

instances = {}
for change in changes:
    if change.model_instance_uuid:
        instances[change.model_instance_uuid] = instances.get(change.model_instance_uuid, [])
        instances[change.model_instance_uuid].append(change)

results = [{uuid: set(drafts)} for uuid, drafts in instances.items() if len(set(drafts)) > 1]

for result in results:
    print([d.uuid for d in result])

""" the following is the results of this script after running on prod data
test =  [
    {
        UUID('474f0bdf-590c-40f7-9137-5ecd13f5de95'):
            {
                <Change: Instrument >> 045d176f-fc0f-46c3-bc85-4cac1f054cef>,
                <Change: Instrument >> f0ff9e55-cfe5-4500-b2de-52683b037586>
            }
    },
    {
        UUID('505f2dc7-cfa8-4b73-a3ed-9f4ab024f4ca'):
            {
                <Change: Instrument >> 1ff1b7c7-e46c-4945-a729-1483a1ade7a0>,
                <Change: Instrument >> 282691b4-acb3-423f-98a3-3b69c95ab3ce>
            }
    },
    {
        UUID('5bfc58f7-078f-469d-8f4a-3e04e1249c0e'):
            {
                <Change: DOI >> 4b7ff8eb-05ff-4423-877f-73f7785f86a0>,
                <Change: DOI >> 5bfc58f7-078f-469d-8f4a-3e04e1249c0e>
            }
    },
    {
        UUID('8ee8e3fa-2c05-4251-a460-679a3f884496'):
            {
                <Change: DOI >> 9eb01849-cfb1-4fdf-ad9a-729a8921aa0c>,
                <Change: DOI >> f1d13f51-44ad-4760-8e53-06577aac883f>
            }
    },
    {
        UUID('fda9c474-ffe6-49f9-a038-e6a689b0df3a'):
            {
                <Change: IOP >> ad6d836c-3cac-4026-8e0a-a34343ae94f1>,
                <Change: IOP >> d4432fc4-04a9-415e-ad5d-c99e2e84cad2>
            }
    },
    {
        UUID('70a781dd-0114-4b26-95ea-e6e971247a3d'):
            {
                <Change: Website >> c3f3002a-909a-4a4c-bf40-54d580707c9f>,
                <Change: Website >> fb4fc3b7-faab-4d6c-a1f5-643e77a6dcaa>
            }
    }
   
]
"""

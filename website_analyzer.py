import re
import requests

from data_models import models

fields_to_validate = {
    "PartnerOrg": {
        "website",
    },
    "Image": {
        "source_url",
    },
    "FocusArea": {
        "url",
    },
    "Website": {
        "url",
    },
    "Platform": {
        "online_information",
    },
    "Instrument": {
        "calibration_information",
        "overview_publication",
        "online_information",
    },
    "IOP": {
        "published_list",
        "reports",
    },
    "SignificantEvent": {
        "published_list",
        "reports",
    },
    "CollectionPeriod": {
        "instrument_information_source",
    },
}


def extract_urls(text):
    # https://stackoverflow.com/a/48769624
    url_regex = '(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+'
    return re.findall(url_regex, potential_url_field)


def add_url_scheme(url):
    if url.startswith('http'):
        return url
    return 'http://' + url


def validate_url(url):
    # providing a header is required to prevent some sites, like http://www.ipy.org/ from throwing a ConnectionError
    # headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"}
    try:
        request = requests.head(url)
    except Exception as e:
        return f'error: {e}'
    return request.status_code != 404


done = 0
validation_results = []
for model_name, field_names in fields_to_validate.items():
    model = getattr(models, model_name)
    objects = model.objects.all()
    for object in objects:
        for field_name in field_names:
            potential_url_field = getattr(object, field_name)
            urls = extract_urls(potential_url_field)
            for url in urls:
                print('trying', url)
                url = add_url_scheme(url)
                is_valid = validate_url(url)
                validation_results.append(
                    {
                        'model_name': model_name,
                        'field_name': field_name,
                        'url': url,
                        'uuid': object.uuid,
                        'valid': is_valid,
                    }
                )

                print(is_valid)
                done += 1
                print(done)

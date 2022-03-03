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
    """URLs might be written amongst other words in a body of text. This
    function takes in a text string and returns a list of identified urls.

    Args:
        text (str): text string which may contain urls

    Returns:
        list: list of strings, where each string is a url
    """

    # https://stackoverflow.com/a/48769624
    url_regex = '(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+'

    return re.findall(url_regex, potential_url_field)


def add_url_scheme(url):
    """Some URLs in the database are lacking http(s) and cannot be accessed via the
    requests module. This function detects if http is missing and adds it.

    Args:
        url (str): url string which may be missing 'http'

    Returns:
        str: url string that has http at the beginning
    """

    if not url.startswith('http'):
        url = 'http://' + url

    return url


def validate_url(url):
    """URLs in the MI might no longer point to a valid webpage. This function
    takes a URL and requests a status code from the webpage. If the request is
    sucessful, the function retuns a True/False value depending on whether the
    link was still active. If the function fails for some reason, the error is
    returned instead.

    Args:
        url (str): url to be validated

    Returns:
        bool/text: bool if check was successful, otherwise an error code # TODO this seems like a bad way to do this
    """

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

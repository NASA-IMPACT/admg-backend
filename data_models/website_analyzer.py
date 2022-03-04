import re
import requests

from django.contrib.contenttypes.models import ContentType

from data_models import models

FIELDS_TO_VALIDATE = {
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


def extract_urls(text_with_urls):
    """URLs might be written amongst other words in a body of text. This
    function takes in a text string and returns a list of identified urls.

    Args:
        text (str): text string which may contain urls

    Returns:
        list: list of strings, where each string is a url
    """

    # https://stackoverflow.com/a/48769624
    url_regex = r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+'

    return re.findall(url_regex, text_with_urls)


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
        bool/text: bool if check was successful, otherwise an error code
    """

    # providing a header is required to prevent some sites, like http://www.ipy.org/ from throwing a ConnectionError
    # headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"}

    try:
        request = requests.head(url)
        details = ""
        valid = request.status_code != 404
    except Exception as e:
        details = f'validator encountered an error of: {e}'
        valid = False

    return {
        'valid': valid,
        'details': details,
    }


def compile_urls_list(fields_to_search=FIELDS_TO_VALIDATE):
    """The MI contains many fields which may or may not contain one or more urls.
    This function takes a dictionary of models and fields and extracts urls from
    each field.

    Args:
        fields_to_search (dict, optional): dictionary of fields which may contain
        urls. Defaults to FIELDS_TO_VALIDATE.

    Returns:
        list of dicts: list of dictionaries, [{uuid, model_name, field_name, url}, ..]
    """

    urls_to_validate = []
    for model_name, field_names in fields_to_search.items():
        model = getattr(models, model_name)
        objects = model.objects.all()

        for object in objects:

            for field_name in field_names:
                potential_url_field = getattr(object, field_name)

                for url in extract_urls(potential_url_field):
                    urls_to_validate.append(
                        {
                            'uuid': object.uuid,
                            'model_name': model_name,
                            'content_type': ContentType.objects.get_for_model(model),
                            'field_name': field_name,
                            'url': add_url_scheme(url),
                        }
                    )
    return urls_to_validate


def validate_urls(url_list):
    """Takes a list of dictionaries, where the dictionary contains a url and the
    source model/field/uuid and validates each entry. The original dictionary is
    supplemented with the validation results.

    Args:
        url_list (list): list of urls output from compile_urls_list

    Returns:
        list[dict]: list of dictionaries, [{uuid, model_name, field_name, url, valid}, ..]
    """

    for url_data in url_list:
        validation_results = validate_url(url_data['url'])
        url_data['valid'] = validation_results['valid']
        url_data['details'] = validation_results['details']

    return url_list


def run_validator_and_store():

    url_list = compile_urls_list(FIELDS_TO_VALIDATE)
    validation_data = validate_urls(url_list)

    for url_data in validation_data:
        models.UrlValidation.objects.create(
            url_content_type=url_data['content_type'],
            url_object_id=url_data['uuid'],
            url_source_field=url_data['field_name'],
            url=url_data['url'],
            is_active=url_data['valid'],
            details=url_data['details'],
        )

    return validation_data

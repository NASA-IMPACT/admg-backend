import mimetypes
import pickle

import requests


def filter_image_list(db, table_name):
    # remove missing links
    db[table_name] = db[table_name][
        db[table_name]['image-link'] != 'Information Not Available'
    ]

    # only accept the first image in the list
    db[table_name]['image-link'] = db[table_name]['image-link'].apply(
        lambda link: link.split(',')[0]
    )


def valid_response(response):
    return response.status_code == 200  # if response else False


def valid_image(extension):
    valid_extensions = ['.tif', '.tiff', '.jpg', '.jpeg', '.png', '.bmp']
    return extension.lower() in valid_extensions


def download_image(image_url):
    try:
        response = requests.get(image_url)
    except:
        response = None

    return response


def get_extension(response):
    content_type = response.headers.get('content-type')
    extension = mimetypes.guess_extension(content_type)
    return extension


def generate_save_path(table_name, short_name, extension):
    return f'images/{table_name}/{short_name + extension}'


def save_image(response, path):
    try:
        file = open(path, "wb")
        file.write(response.content)
        file.close()
        success = True
    except:
        success = False

    return success


def download_all_images(db_path):
    log = open("image_log.txt", "w")
    db = pickle.load(open(db_path, "rb"))

    for table_name in ['platform', 'instrument', 'campaign']:
        log.write(table_name + "\n")
        print(table_name)
        filter_image_list(db, table_name)

        for index, row in db[table_name].iterrows():
            short_name = row['short_name']
            image_url = row['image-link']

            if response := download_image(image_url):
                valid_response(response)
                if extension := get_extension(response):
                    save_path = generate_save_path(table_name, short_name, extension)
                    if save_image(response, save_path):
                        message = f"  success {short_name}"
                    else:
                        message = f"    failed {short_name} - save"
                else:
                    message = f"    failed {short_name} - extentension"
            else:
                message = f"    failed {short_name} - download"

            log.write(message + "\n")
            print(message)

    log.close()


if __name__ == "__main__":
    download_all_images(db_path='../data_models/utils/ingest_data/db_20201028')

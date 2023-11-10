import os
import requests
import fnmatch


def process_data_recursive(data):
    """
    Processes data, extracts file URLs and file names.

    :param data: Data to be processed.
    :type data: list, dict or str
    :return: List of file URLs and list of file names.
    :rtype: tuple
    """
    file_urls = []
    file_names = []

    def process_item(item):
        if isinstance(item, list):
            for sub_item in item:
                print(sub_item)
                process_item(sub_item)
        elif isinstance(item, dict):
            for key, value in item.items():
                process_item(value)
        elif isinstance(item, str):
            if item.startswith('https://www.patreon.com/file?h'):
                file_urls.append(item)
            elif any(fnmatch.fnmatch(item, pattern) for pattern in ['*.package', '*.zip', '*.rar']):
                file_names.append(item)

    for item in data:
        process_item(item)

    return file_urls, file_names


def download_file(content_to_download: dict, download_folder_path: str):
    """
    The function downloads files.

    :param content_to_download: Dictionary with data for downloading files, the key - file name, the value - file URL.
    :type content_to_download: dict
    :param download_folder_path: Path to the folder where you want to save the downloaded files.
    :type download_folder_path: str
    """
    for name, url in content_to_download.items():
        response = requests.get(url)
        if response.status_code == 200:

            file_name = name
            file_path = os.path.join(download_folder_path, file_name)
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f'Saved: |{file_path}|')
            else:
                print(f'The file |{name}| already exists.')
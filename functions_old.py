import os
import requests


def unpack_data(data: dict):
    """
    Parses data and returns an internal list from dictionaries.
    :param data: Dictionary of data from which to extract the internal list.
    :type data: dict
    :return: Internal list from dictionaries.
    :rtype: list
    Разбирает данные и возвращает внутренний список из словарей.
    :param data: Словарь данных, из которых нужно извлечь внутренний список.
    :type data: dict
    :return: Внутренний список из словарей.
    :rtype: list
    """
    scrapped_data, inner_list, attributes, info = data.items()
    return inner_list


def process_data(data: list):
    """
    Processes data, extracts file URLs and file names.
    :param data: Data to be processed.
    :type data: list
    :type data: list, dict or str
    :return: List of file URLs and list of file names.
    :rtype:tuple


    Обрабатывает данные, извлекает URL файлов и имена файлов.
    :param data: Данные для обработки.
    :type data: list
    :return: Список URL файлов и список имен файлов.
    :rtype: tuple
    """
    file_url = []
    file_name = []
    file_urls = []
    file_names = []

    for inner_list in data:
        if isinstance(inner_list, list):
            for dictionaries in inner_list:
                for post_type, post_info in dictionaries.items():
                    if post_type == 'attributes':
                        for key, value in post_info.items():
                            if isinstance(value, str):
                                if value.startswith('https://www.patreon.com/file?h'):
                                    file_url.append(value)
                                elif value.endswith(('.package', '.zip', '.rar')):
                                    file_name.append(value)

    return file_urls, file_names


def download_file(content_to_download: dict, download_folder_path: str):
    """
    The function downloads files.
    :param content_to_download: Dictionary with data for downloading files, the key - file name, the value - file URL.
    :type content_to_download: dict
    :param download_folder_path: Path to the folder where you want to save the downloaded files.
    :type download_folder_path: str


    Функция скачивает файлы.
    :param content_to_download: Словарь с данными для загрузки файлов, где ключ - имя файла, а значение - URL файла.
    :type content_to_download: dict
    :param download_folder_path: Путь к папке, в которую нужно сохранить загруженные файлы.
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
                print(f'Saved: {file_path}')
                print(f'Saved: |{file_path}|')
            else:
                print(f'The file |{name}| already exists.')
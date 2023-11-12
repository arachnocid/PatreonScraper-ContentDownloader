import os
import sys
import re
import datetime
import fnmatch
import asyncio

import requests
import aiohttp

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QCoreApplication
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLabel, QLineEdit, QPushButton,
                             QTextEdit, QProgressBar, QFileDialog)


class CustomTextEdit(QTextEdit):
    def write(self, text):
        """
         Appends the specified text to the end of the text edit.

         :param text: The text to be appended.
         :type text: str
         """
        self.insertPlainText(text)


class InitApp(QWidget):
    url_added = pyqtSignal()
    extension_added = pyqtSignal()

    def __init__(self):
        """
        Initializes the InitApp class.

        Sets up the initial state of the application, including default values for API URL, download folder,
        and initializes various UI elements.

        Signals:
        - url_added: Emitted when a URL is added.
        - extension_added: Emitted when a file extension is added.
        """
        super().__init__()
        self.api_url = 'https://www.patreon.com/api/posts'
        self.download_folder = r'C:\Downloaded Content --by PatreonScraper'
        self.urls = []
        self.extensions = []

        self.log_output = CustomTextEdit()
        self.log_output.setReadOnly(True)

        self.progress_bar = QProgressBar()

        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface with layout, labels, input fields, buttons, and sets window properties.
        """
        layout = QVBoxLayout()

        self.url_label = QLabel('\nEnter the urls like "https://www.patreon.com/creator\'s-name" (one by one):')
        self.url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.url_input = QLineEdit()
        self.btn_add_url = QPushButton('Add URL')
        self.btn_add_url.clicked.connect(self.add_url)

        self.extension_label = QLabel('\nEnter file extensions like "zip" (one by one):')
        self.extension_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.extension_input = QLineEdit()
        self.btn_choose_extension = QPushButton('Add extensions')
        self.btn_choose_extension.clicked.connect(self.choose_extension)

        self.folder_label = QLabel('\nChoose custom downloading folder:')
        self.folder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.folder_input = QLineEdit()
        self.btn_choose_folder = QPushButton('Choose Folder')
        self.btn_choose_folder.clicked.connect(self.choose_folder)

        self.btn_clear_log = QPushButton('Clear Log')
        self.btn_clear_log.clicked.connect(self.log_output.clear)


        self.btn_finish = QPushButton('Start')
        self.btn_finish.clicked.connect(self.finish)

        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.btn_add_url)

        layout.addWidget(self.extension_label)
        layout.addWidget(self.extension_input)
        layout.addWidget(self.btn_choose_extension)

        layout.addWidget(self.folder_label)
        layout.addWidget(self.folder_input)
        layout.addWidget(self.btn_choose_folder)

        layout.addWidget(self.log_output)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.btn_finish)

        layout.addWidget(self.btn_clear_log)

        self.setLayout(layout)

        self.setWindowTitle('PatreonScraper --by arachnocid')
        self.setGeometry(100, 100, 400, 300)

        icon = QIcon('icon.png')
        self.setWindowIcon(icon)

        self.show()

    def choose_folder(self):
        """
        Opens a file dialog for selecting a custom download folder and updates the download folder path.

        :return: None
        """
        folder = QFileDialog.getExistingDirectory(self, 'Select Download Folder', self.download_folder)
        if folder:
            self.download_folder = folder
            self.log_output.write(f'\nDownload folder changed to: {folder}\n')

    def choose_extension(self):
        """
        Adds user-inputted file extension to the list of extensions.

        :return: None
        """
        user_input = self.extension_input.text().strip()
        self.log_output.write(f'\nExtension added: {user_input}\n')

        self.extensions.append(f"*.{user_input}")
        self.extension_added.emit()
        self.extension_input.clear()

    def add_url(self):
        """
        Adds user-inputted URL to the list of URLs.

        :return: None
        """
        user_input = self.url_input.text().strip()
        self.log_output.write(f'\nUrl added: {user_input}\n')

        self.urls.append(user_input)
        self.url_added.emit()
        self.url_input.clear()

    def finish(self):
        """
        Initiates the download process, creates the download folder if not exists, and starts the download manager.

        :return: None
        """
        folder_path = os.path.join(self.download_folder,
                                   f'Downloaded at {datetime.datetime.now().strftime("%d-%m-%Y")}')

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            self.log_output.write(f'\n- Folder created: {folder_path}\n')

        self.log_output.write(f'\n- Folder is ready!\n')

        loop = asyncio.get_event_loop()
        downloader = DownloadManager(self.api_url, folder_path, self.urls,
                                     self.extensions, self.log_output, self.progress_bar)
        loop.run_until_complete(downloader.download_files())
        self.url_added.emit()


class DownloadManager(QObject):

    def __init__(self, api_url, download_folder, urls, extensions, log_output, progress_bar):
        """
        Initializes the DownloadManager.

        :param api_url: Patreon API URL for fetching posts data.
        :type api_url: str
        :param download_folder: Default or Custom download folder path.
        :type download_folder: str
        :param urls: List of Patreon URLs.
        :type urls: list
        :param extensions: List of file extensions to be considered during data processing.
        :type extensions: list
        :param log_output: Custom text edit widget for displaying logs.
        :type log_output: CustomTextEdit
        :param progress_bar: QProgressBar widget for displaying download progress.
        :type progress_bar: QProgressBar
        """
        super().__init__()
        self.download_folder = download_folder
        self.api_url = api_url
        self.urls = urls
        self.extensions = extensions

        self.log_output = log_output
        self.progress_bar = progress_bar

        self.data = self.process_urls()
        self.inner_list = self.unpack_data(self.data)
        self.content_to_download = self.process_data_recursive(self.inner_list)

    def process_urls(self):
        """
        Processes Patreon URLs and fetches posts data, and prepares it for further processing.

        :return: List of Patreon campaign data.
        :rtype: list
        """
        self.log_output.write('\n- Urls processing started...\n')
        data_list = []

        for url in self.urls:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; Google-Podcast)'}

            with requests.session() as s:
                html_text = s.get(url, headers=headers).text
                campaign_id = re.search(r'https://www\.patreon\.com/api/campaigns/(\d+)', html_text).group(1)
                data = s.get(self.api_url, headers=headers, params={'filter[campaign_id]': campaign_id,
                                                                    'sort': '-published_at'}).json()
                data_list.append(data)

        self.log_output.write('\n- Data is ready!\n')
        return data_list

    def unpack_data(self, data_list):
        """
        Unpacks data obtained from Patreon.

        :param data_list: List of Patreon campaign data.
        :type data_list: list
        :return: List of inner data.
        :rtype: list
        """
        self.log_output.write('\n- Data unpacking started...\n')
        inner_list = []

        for data in data_list:
            values = list(data.values())
            if len(values) == 4:
                scrapped_data, inner, attributes, info = values
            elif len(values) == 3:
                scrapped_data, inner, attributes = values
            else:
                self.log_output.write("\nValueError: Unexpected number of items in data!\n")
                continue

            inner_list.extend(inner)

        self.log_output.write('\n- Data unpacking finished.\n')
        return inner_list

    def process_data_recursive(self, data):
        """
        Processes data, extracts file URLs and file names.

        :param data: Data to be processed.
        :type data: list, dict or str
        :return: List of file URLs and list of file names.
        :rtype: tuple
        """
        self.log_output.write('\n- Data processing started...\n')

        file_urls = []
        file_names = []

        def process_item(item):
            if isinstance(item, list):
                for sub_item in item:
                    process_item(sub_item)
            elif isinstance(item, dict):
                for key, value in item.items():
                    process_item(value)
            elif isinstance(item, str):
                if item.startswith('https://www.patreon.com/file?h'):
                    file_urls.append(item)
                elif any(fnmatch.fnmatch(item, pattern) for pattern in self.extensions):
                    file_names.append(item)

        for item in data:
            process_item(item)

        content_to_download = dict(zip(file_names, file_urls))

        self.log_output.write('\n- Data processing finished.\n')
        return content_to_download

    async def download_files(self):
        """
        Downloads files.

        :return: None
        """
        self.log_output.write('\n- Downloading...\n')
        total_files = len(self.content_to_download)
        completed_files = 0

        for name, url in self.content_to_download.items():
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        file_name = name
                        file_path = os.path.join(self.download_folder, file_name)
                        if not os.path.exists(file_path):
                            with open(file_path, 'wb') as f:
                                f.write(await response.read())
                            self.log_output.write(f'\n- Saved: | {name} |\n')
                        else:
                            self.log_output.write(f'\n- The file | {name} | already exists.\n')

            completed_files += 1
            progress_percentage = int((completed_files / total_files) * 100)
            self.progress_bar.setValue(progress_percentage)

            QCoreApplication.processEvents()
            await asyncio.sleep(0.1)

        self.log_output.write('\n- Download completed!\n')
        self.log_output.write('*' * 5)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = InitApp()
    sys.exit(app.exec())

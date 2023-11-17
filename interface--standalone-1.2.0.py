import asyncio
import os
import sys
import re
import datetime
import fnmatch

import requests
import aiohttp

from PyQt6.QtGui import QIcon, QGuiApplication, QTextCursor
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QCoreApplication, QThread
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLabel, QLineEdit, QPushButton,
                             QTextEdit, QProgressBar, QFileDialog)


def resource_path(relative_path):
    """
    Gets the absolute path to a resource file.
    Used in the code to keep the window icon after compiling with pyinstaller.

    :param relative_path: The relative path to the resource file.
    :return: The absolute path to the resource file.
    """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class CustomTextEdit(QTextEdit):
    """
    Subclasses the QTextEdit widget.

    Provides a custom text edit for displaying logs.
    """
    def write(self, text):
        """
         Appends the specified text to the end of the text edit.

         :param text: The text to be appended.
         :type text: str
         """
        self.insertPlainText(text + '\n')

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        self.setTextCursor(cursor)


class InitApp(QWidget):
    """
    Subclasses the QWidget widget.

    Provide a graphical user interface.

    Signals:
        - url_added: Emitted when a URL is added.
        - extension_added: Emitted when a file extension is added.
    """

    url_added = pyqtSignal()
    extension_added = pyqtSignal()

    def __init__(self):
        """
        Initializes the InitApp class.

        Sets up the initial state of the application, including default values for API URL, download folder,
        and initializes various UI elements.

        :self api_url: Default Patreon API URL for fetching posts data.
        :self download_folder: Default or custom download folder path.
        :self urls: List of Patreon URLs.
        :self extensions: List of file extensions to be considered during data processing.
        :self log_output: Custom text edit widget for displaying logs.
        :self progress_bar: QProgressBar widget for displaying download progress.
        :self worker: DownloadWorker instance for handling the download process.
        """
        super().__init__()
        self.api_url = 'https://www.patreon.com/api/posts'
        self.download_folder = r'C:\Downloaded Content --by PatreonScraper'
        self.urls = []
        self.extensions = []

        self.log_output = CustomTextEdit()
        self.log_output.setReadOnly(True)

        self.progress_bar = QProgressBar()

        self.worker = DownloadWorker(self.api_url, self.download_folder, self.urls,
                                     self.extensions, self.log_output, self.progress_bar)

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

        self.extension_label = QLabel('Enter file extensions like "zip" (one by one):')
        self.extension_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.extension_input = QLineEdit()
        self.btn_choose_extension = QPushButton('Add extensions')
        self.btn_choose_extension.clicked.connect(self.choose_extension)

        self.folder_label = QLabel('Choose custom downloading folder:')
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

        icon = QIcon(resource_path('icon.png'))
        self.setWindowIcon(icon)

        styles = """
                    QWidget {
                        background-color: #101334;
                        font-family: Century Gothic;
                        font-weight: bold;
                        font-size: 13px;
                        border-radius: 10px;
                        color: #F2F5FA;
                    }

                    QLineEdit {
                        background-color: #2B3773;
                        border: 3px solid #2B3773;
                        height: 30px;
                        margin-bottom: 10px;
                    }

                    QTextEdit {
                        background-color: #2B3773;
                        border: 3px solid #2B3773;
                        padding: 10px;
                        font-size: 13px;
                        border-radius: 10px;
                        color: #F2F5FA;
                        margin-bottom: 10px;
                    }

                    QPushButton {
                        background-color: #6693D4;
                        color: #F2F5FA;
                        border: none;
                        padding: 10px;
                        height: 18px;
                        font-size: 14px;
                        border-radius: 12px;
                        margin-bottom: 10px;
                    }

                    QPushButton:pressed {
                        background-color: #2B3773;
                        border: 3px solid #FD7865;
                        color: #F2F5FA;
                    }

                    QProgressBar {
                        background-color: #2B3773;
                        border: 3px solid #FD7865;
                        text-align: center;
                        margin-bottom: 10px;
                        height: 30px;
                        color: #FFFFFF;
                        font-size: 14px;
                    }

                    QProgressBar::chunk {
                        background-color: #FD7865;
                        border: 3px;
                        border-radius: 8px;
                    }

                    QTextEdit#output_text {
                        background-color: #2B3773;
                        border: 5px solid #2B3773;
                        padding: 10px;
                        font-size: 13px;
                        height: 100px;
                        border-radius: 10px;
                        color: #F2F5FA;
                        margin-bottom: 10px;
                    }

                        QScrollBar:horizontal {
                        border: 1px solid #2B3773;
                        background: #2B3773;
                        height: 12px;
                        margin: 0px 16px 0 16px;
                    }

                    QScrollBar:vertical {
                        border: 1px solid #2B3773;
                        background: #2B3773;
                        width: 12px;
                        margin: 16px 0 16px 0;
                    }

                    QScrollBar::handle:horizontal {
                        background: #FD7865;
                        border-radius: 6px;
                        min-width: 50px;
                    }

                    QScrollBar::handle:vertical {
                        background: #FD7865;
                        border-radius: 6px;
                        min-height: 50px;
                    }

                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        border: none;
                        background: none;
                    }

                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                        background: none;
                    }
                """

        self.setStyleSheet(styles)
        self.set_geometry_centered()

        self.show()

    def set_geometry_centered(self):
        """
        Centers the main window on the screen.
        """
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2

        self.setGeometry(x, (y - 75), 550, 600)

    def choose_folder(self):
        """
        Opens a file dialog for selecting a custom download folder and updates the download folder path.

        :return: None
        """
        folder = QFileDialog.getExistingDirectory(self, 'Select Download Folder', self.download_folder)
        if folder:
            self.download_folder = folder
            self.log_output.write(f'Download folder changed to: {folder}')

    def choose_extension(self):
        """
        Adds user-inputted file extension to the list of extensions.

        :return: None
        """
        user_input = self.extension_input.text().strip()

        if not user_input:
            self.log_output.write('Provide a valid extension!')
            return

        if '.' in user_input or ',' in user_input or ' ' in user_input:
            self.log_output.write('Invalid characters in extension!')
            return

        if len(user_input.split()) > 1:
            self.log_output.write('Provide only one extension at a time!')
            return

        self.log_output.write(f'Extension added: {user_input}')

        self.extensions.append(f"*.{user_input}")
        self.extension_added.emit()
        self.extension_input.clear()

    def add_url(self):
        """
        Adds user-inputted URL to the list of URLs.

        :return: None
        """
        user_input = self.url_input.text().strip()

        if not user_input:
            self.log_output.write('Provide a valid URL.')
            return

        if not any(fnmatch.fnmatch(user_input, pattern)
                   for pattern in ['https://www.patreon.com/*', 'http://www.patreon.com/*']):
            self.log_output.write('Invalid URL format!')
            return

        self.log_output.write(f'URL added: {user_input}')

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
            self.log_output.write(f'- Folder created: {folder_path}')

        self.log_output.write(f'- Folder is ready!')

        self.worker.start()

    def worker_finished(self):
        """
        Slot method connected to the 'finished' signal of the worker.

        This method is called when the worker has finished its execution. It emits the 'url_added' signal
        to notify that the worker has completed its task.

        :return: None
        """
        self.worker.finished.connect(self.worker_finished)
        self.url_added.emit()


class DownloadWorker(QThread):
    """
    Subclasses QThread class.

    Performs the download process in a separate thread.

    Signals:
        - finished: Emitted when a download process is finished.
    """
    finished = pyqtSignal()

    def __init__(self, api_url, download_folder, urls, extensions, log_output, progress_bar):
        """
        Initializes a DownloadWorker instance.

        :param api_url: Patreon API URL for fetching posts data.
        :type api_url: str
        :param download_folder: Default or custom download folder path.
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
        self.api_url = api_url
        self.download_folder = download_folder
        self.urls = urls
        self.extensions = extensions
        self.log_output = log_output
        self.progress_bar = progress_bar

    def run(self):
        """
        Runs the download process in a separate thread.

        Creates an instance of DownloadManager, which handles the file download, and starts the download process.
        After the download is complete, emits the `finished` signal to notify the completion of the worker.

        :return: None
        """
        downloader = DownloadManager(self.api_url, self.download_folder, self.urls,
                                     self.extensions, self.log_output, self.progress_bar)
        downloader.download_files()
        self.finished.emit()


class DownloadManager(QObject):
    """
    Subclasses the QObject class.

    Handles the file download process.

    Signals:
        - finished: Emitted when a download process is finished.
    """
    finished = pyqtSignal()

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

    def run(self):
        """
        Runs the download process in a separate thread.

        Creates an instance of DownloadManager, which handles the file download, and starts the download process.
        After the download is complete, emits the 'finished' signal to notify the completion of the worker.

        :return: None
        """
        downloader = DownloadManager(self.api_url, self.download_folder, self.urls,
                                     self.extensions, self.log_output, self.progress_bar)
        downloader.download_files()
        self.finished.emit()

    def process_urls(self):
        """
        Processes Patreon URLs and fetches posts data, and prepares it for further processing.

        :return: List of Patreon campaign data.
        :rtype: list
        """
        self.log_output.write('- Urls processing started...')
        data_list = []

        for url in self.urls:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; Google-Podcast)'}

            with requests.session() as s:
                html_text = s.get(url, headers=headers).text
                campaign_id = re.search(r'https://www\.patreon\.com/api/campaigns/(\d+)', html_text).group(1)
                data = s.get(self.api_url, headers=headers, params={'filter[campaign_id]': campaign_id,
                                                                    'sort': '-published_at'}).json()
                data_list.append(data)

        self.log_output.write('- Data is ready!')
        return data_list

    def unpack_data(self, data_list):
        """
        Unpacks data obtained from Patreon.

        :param data_list: List of Patreon campaign data.
        :type data_list: list
        :return: List of inner data.
        :rtype: list
        """
        self.log_output.write('- Data unpacking started...')
        inner_list = []

        for data in data_list:
            values = list(data.values())
            if len(values) == 4:
                scrapped_data, inner, attributes, info = values
            elif len(values) == 3:
                scrapped_data, inner, attributes = values
            else:
                self.log_output.write("ValueError: Unexpected number of items in data!")
                continue

            inner_list.extend(inner)

        self.log_output.write('- Data unpacking finished.')
        return inner_list

    def process_data_recursive(self, data):
        """
        Processes data, extracts file URLs and file names.

        :param data: Data to be processed.
        :type data: list, dict or str
        :return: List of file URLs and list of file names.
        :rtype: tuple
        """
        self.log_output.write('- Data processing started...')

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

        self.log_output.write('- Data processing finished.')
        return content_to_download

    @staticmethod
    async def download_file(session, url, file_path):
        """
        Downloads a file asynchronously using the specified 'session' and saves it to the specified 'file_path'.

        :param session: aiohttp ClientSession for making asynchronous requests.
        :type session: aiohttp.ClientSession
        :param url: URL of the file to be downloaded.
        :type url: str
        :param file_path: Local path where the downloaded file will be saved.
        :type file_path: str
        :return: None
        """
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)

    async def download_files_async(self):
        """
        Asynchronously downloads files from the content_to_download dictionary.

        The method uses aiohttp to perform asynchronous file downloads. The progress is updated using a progress bar,
        and the completion is indicated in the log. After completing the downloads, the 'finished' signal is emitted.

        :return: None
        """
        total_files = len(self.content_to_download)
        completed_files = 0

        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, url in self.content_to_download.items():
                file_name = name
                file_path = os.path.join(self.download_folder, file_name)

                if not os.path.exists(file_path):
                    task = self.download_file(session, url, file_path)
                    tasks.append(task)
                else:
                    self.log_output.write(f'- The file | {name} | already exists.')

                completed_files += 1
                progress_percentage = int((completed_files / total_files) * 100)

                await asyncio.sleep(0.2)
                QCoreApplication.processEvents()
                self.progress_bar.setValue(progress_percentage)

            await asyncio.gather(*tasks)

            self.log_output.write('- Download completed!')
            self.log_output.write('*' * 5)
            self.finished.emit()

    def download_files(self):
        """
        Initiates the asynchronous download process.

        This method runs the asynchronous download process using asyncio. It is called to start the download of files.
        """
        asyncio.run(self.download_files_async())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = InitApp()
    sys.exit(app.exec())
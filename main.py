import re
import datetime
from functions import *

urls = []
default_folder = r'C:\Sims 4 Mods -by PatreonScraper'
extensions = []

while True:
    urls_input = input(
        'Enter the urls like "https://www.patreon.com/creator\'s-name". Type "end" to finish.\nYour url: ')
    if urls_input == 'end':
        break
    urls.append(urls_input)

while True:
    extensions_input = input(
        'Enter extensions like "zip". Type "end" to finish.\nYour extension: '
    )

    if extensions_input == 'end':
        break
    extensions.append(f'*.{extensions_input}')

while True:
    folder_input = input(
        'Enter download folder path like "C:\\User\\Folder".\nType "default" to use default download folder path (C:\\Sims 4 Mods -by PatreonScraper).\nYour download folder path: '
    )
    if folder_input == 'default':
        break
    default_folder = folder_input
    break

current_date = datetime.datetime.now()
date_str = current_date.strftime('%d-%m-%Y')
folder_path = os.path.join(default_folder, f'Downloaded at {date_str}')


if not os.path.exists(folder_path):
    os.makedirs(folder_path)

print(f'Folder created: {folder_path}')


api_url = 'https://www.patreon.com/api/posts'


for url in urls:
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Google-Podcast)'
    }

    with requests.session() as s:
        html_text = s.get(url, headers=headers).text
        campaign_id = re.search(r'https://www\.patreon\.com/api/campaigns/(\d+)', html_text).group(1)
        data = s.get(api_url, headers=headers,
                     params={'filter[campaign_id]': campaign_id,
                             'sort': '-published_at'}).json()

        #print(json.dumps(data, indent=4))

    inner_list = unpack_data(data)
    file_names, file_urls = process_data_recursive(inner_list, extensions)
    content_to_download = dict(zip(file_names, file_urls))
    download_file(content_to_download, default_folder)

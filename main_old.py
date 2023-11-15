import datetime
import re

from functions_old import *


run = True
urls = []
while run:
    user_input = input('Enter the urls like "https://www.patreon.com/creators-name". Type "end" to finish.\nYour urls: ')
    if user_input == 'end':
        break
    urls.append(user_input)


download_folder = 'C:\\Sims 4 Mods -by PatreonScraper'
current_date = datetime.datetime.now()
date_str = current_date.strftime('%d-%m-%Y')
folder_path = os.path.join(download_folder, f'Downloaded at {date_str}')

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

    # An attempt to handle parsing data error while extracting an internal list
    try:
        scrapped_data, inner_list, attributes, info = data.items()
    except:
        scrapped_data, inner_list, attributes = data.items()

    unpacked_data = unpack_data(data)
    file_url, file_name = process_data(unpacked_data)
    content_to_download = dict(zip(file_name, file_url))
    download_file(content_to_download, folder_path)

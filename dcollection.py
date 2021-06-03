from release_object import ReleaseObject
from lib.credentials import Credentials
import argparse
from datetime import datetime
from pathlib import Path
from csv import writer
from discogs_client.exceptions import HTTPError
from time import time
import pandas as pd
import discogs_client


def args_parser():
    description = "Review most valuable records in Discogs collection"
    token_h = "Paste your developer token (get your token at https://www.discogs.com/settings/developers)"
    user_h = "User name"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-t', '--token', dest="token", type=str, help=token_h)
    parser.add_argument('-u', '--user', dest="user", type=str, help=user_h)

    args = parser.parse_args()
    token = args.token
    user = args.user

    if args.token is None:
        token = Credentials().token

    if args.user is None:
        user = Credentials().user

    return user, token


user, developer_token = args_parser()


def get_releases():
    try:
        discogs_cl = discogs_client.Client("PricelistDiscogs/0.9.1", user_token=developer_token)
        return discogs_cl.user(user).collection_folders[0]
    except HTTPError:
        print('paste your user/token in arguments or edit "lib/credentials.py"')
        quit()


releases = get_releases()


csv_headers = 'id,title,start,avg_rating,rating_count,low,med,high,want,have,last_sold,for_sale,url\n'
temp_path = Path('lib/collection_temp.csv')
temp_path.parent.mkdir(parents=True, exist_ok=True)
if not temp_path.exists():
    temp_path.touch()
    temp_path.write_text(csv_headers)

temp_df = pd.read_csv(temp_path, encoding='utf-8')


def create_db( df, location ):
    try:
        df.to_csv(location, index=False)
        print('File was successfully created -- {}'.format(location))
    except ValueError:
        print("Empty file, not created -- {}".format(location), ValueError)
        pass


def write_and_clean(loc):
    df = pd.read_csv(temp_path, encoding='utf-8')
    print(len(df.index))
    create_db(df, loc)
    if Path(loc).exists():
        temp_path.unlink()


for each in releases.releases:
    if each.id in temp_df['id'].values:
        print('duplicate')
        pass
    else:
        release_object = ReleaseObject(each.release.id, each.release.title)
        print(release_object.csv_object())
        row = release_object.csv_object()
        with temp_path.open('a', newline='', encoding='utf-8') as temp:
            csv_writer = writer(temp)
            csv_writer.writerow(row)

t = time()
timestamp = datetime.fromtimestamp(t).strftime('_%d%m%y')
out_path = Path('out/collection{}.csv'.format(timestamp))
out_path.parent.mkdir(parents=True, exist_ok=True)
write_and_clean(out_path)

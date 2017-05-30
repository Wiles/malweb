from urllib.request import urlopen
import xmltodict
import re
from py2neo import Graph
import time
from argparse import ArgumentParser
from pathlib import Path
import traceback

statuses = ['0', 'watching', 'completed', 'on hold', 'dropped', '5', 'plan to watch']


def fetch_anime_staff(html_text):
    anime_name = None
    staff = {}

    anime_name = re.findall('(.*) - Characters &amp; Staff - MyAnimeList.net', html_text)[0]
    try:
        html_text = html_text[html_text.index('Add staff'):]
        for m in re.findall('/people/\d+/[^"]+', html_text):
            _, id, name = m[1:-1].split('/')
            staff[id] = name
    except:
        pass

    return anime_name, staff


def update_shows(client):
    count = 0
    anime_list = client.run('''
        MATCH (anime:Anime)
        WHERE anime.last_updated < (timestamp() / 1000.0 - (60 * 60 * 24 * 7))
        RETURN anime.id as id
        ORDER BY id ASC
    ''').data()
    total = len(anime_list)
    start_time = time.time()
    for anime in anime_list:
        try:
            anime_id = anime['id']
            page = None

            anime_file = Path(f'volumes/pages/anime/{anime_id}.html')
            if anime_file.is_file():
                with open(f'volumes/pages/anime/{anime_id}.html', 'r') as text_file:
                    page = text_file.read()
            else:
                print(f'Fetching anime page {anime_id}')
                with urlopen(f'https://myanimelist.net/anime/{anime_id}/placeholder/characters', timeout=5) as response:
                    html_content = response.read()
                    encoding = response.headers.get_content_charset('utf-8')
                    page = html_content.decode(encoding, errors='ignore')

                with open(f'volumes/pages/anime/{anime_id}.html', 'w') as text_file:
                    text_file.write(page)

            anime_name, staff = fetch_anime_staff(page)
            for staff_id, name in staff.items():
                client.run('MERGE (staff:Staff {id: toInteger({staff_id})})', {
                    'staff_id': staff_id
                })
            client.run('''
                MERGE (anime:Anime {id: toInteger({anime_id})})
                SET anime.last_updated = (timestamp() / 1000.0)
                REMOVE anime.page
            ''', {
                'anime_id': anime_id
            })

            count += 1
            print(f'anime: {anime_id} {anime_name}')
            average = (time.time() - start_time) / count
            minutes = (average * (total - count)) / 60
            print(f'Remaining: {total - count} Min: {round(minutes)} Average: {round(average, 2)}')
        except:
            traceback.print_exc()

    return count


def fetch_staff_anime(html_text):
    staff_name = None
    anime = {}

    staff_name = re.findall('(.*) - MyAnimeList.net', html_text)[0]
    staff_text = html_text[html_text.index('Anime Staff Positions'):]
    for m in re.findall('<a href="\/anime\/(\d+)\/([^"]+)">.+<\/a><div class="spaceit_pad">\s+<a href="[^"]+" title="[^"]+" class="[^"]+">add<\/a>(.+)<\/div>', staff_text):
        anime_id = m[0]
        position = m[2].replace('<small>', '').replace('</small>', '')
        if (anime_id in anime):
            anime[anime_id]['positions'].append(position)
        else:
            anime[anime_id] = {'positions': [position]}

    return staff_name, anime


def update_staff(client):
    count = 0
    staff_list = client.run('''
        MATCH (staff:Staff)
            WHERE staff.last_updated < (timestamp() / 1000.0 - (60 * 60 * 24 * 7))
        RETURN staff.id as id ORDER BY id
    ''').data()

    client.run('''
        MATCH (staff:Staff)-[:HAS_JOB]->(j:Job)
            WHERE staff.last_updated < (timestamp() / 1000.0 - (60 * 60 * 24 * 7))
        DETACH DELETE j
    ''')
    total = len(staff_list)
    start_time = time.time()
    for staff in staff_list:
        try:
            staff_id = staff['id']
            page = None

            staff_file = Path(f'volumes/pages/staff/{staff_id}.html')
            if staff_file.is_file():
                with open(f'volumes/pages/staff/{staff_id}.html', 'r') as text_file:
                    page = text_file.read()
            else:
                print(f'Fetching staff page {staff_id}')
                with urlopen(f'https://myanimelist.net/people/{staff_id}', timeout=5) as response:
                    html_content = response.read()
                    encoding = response.headers.get_content_charset('utf-8')
                    page = html_content.decode(encoding, errors='ignore')

                with open(f'volumes/pages/staff/{staff_id}.html', 'w') as text_file:
                    text_file.write(page)

            staff_name, anime_list = fetch_staff_anime(page)
            for anime_id, anime in anime_list.items():
                positions = anime['positions']
                client.run('MERGE (anime:Anime {id: toInteger({anime_id})})', {
                    'anime_id': anime_id
                })

                client.run('''
                    MATCH (anime:Anime {id: toInteger({anime_id})})
                    MATCH (staff:Staff {id: toInteger({staff_id})})
                    CREATE (job:Job)
                    CREATE (staff)-[:HAS_JOB]->(job)-[:FOR]->(anime)
                    FOREACH (p in {positions} | MERGE (po:Position {name: TRIM(p)}) CREATE (job)-[:HAS]->(po))
                ''', {
                    'anime_id': anime_id,
                    'staff_id': staff_id,
                    'positions': positions
                })

            client.run('''
                MERGE (staff:Staff {id: toInteger({staff_id})})
                SET staff.last_updated = (timestamp() / 1000.0)
                SET staff.name = {name} REMOVE staff.page
            ''', {
                'staff_id': staff_id,
                'name': staff_name
            })

            count += 1
            print(f'staff: {staff_id} {staff_name}')
            average = (time.time() - start_time) / count
            minutes = (average * (total - count)) / 60
            print(f'Remaining: {total - count} Min: {round(minutes)} Average: {round(average, 2)}')
        except:
            traceback.print_exc()

    return count


def fetch_anime_list(html_text):
    anime_list = xmltodict.parse(html_text)['myanimelist']
    user = anime_list.pop('myinfo')
    return user, anime_list['anime']


def handle_anime(client, user_id, anime):
    anime_id = anime['series_animedb_id']
    rating = anime['my_score']

    client.run('MERGE (anime:Anime {id: toInteger({anime_id})})', {
        'anime_id': anime_id
    })

    status = statuses[int(anime['my_status'])]
    client.run('MATCH (user:User {id: toInteger({user_id})}) MATCH (anime:Anime {id: toInteger({anime_id})}) CREATE (user)-[r:Rated]->(anime) SET r.score = toFloat({rating}) SET r.status = {status}', {
        'user_id': user_id,
        'anime_id': anime_id,
        'rating': rating,
        'status': status
    })


def update_user(client, name):
    print(f'User: {name}')
    try:
        staff_file = Path(f'volumes/pages/user/{name}.html')
        page = None
        if staff_file.is_file():
            with open(f'volumes/pages/user/{name}.html', 'r') as text_file:
                page = text_file.read()
        else:
            print(f'Fetching user page {name}')
            with urlopen(f'https://myanimelist.net/malappinfo.php?u={name}&status=all&type=anime', timeout=5) as response:
                html_content = response.read()
                encoding = response.headers.get_content_charset('utf-8')
                page = html_content.decode(encoding, errors='ignore')

            with open(f'volumes/pages/user/{name}.html', 'w') as text_file:
                text_file.write(page)

        user, anime_list = fetch_anime_list(page)

        user_id = user['user_id']
        name = user['user_name']
        client.run('MERGE (user:User {id: toInteger({user_id})}) SET user.name = {name}', {
            'user_id': user_id,
            'name': name
        })
        client.run('MATCH (user:User {id: toInteger({user_id})})-[r:Rated]->(anime:Anime) DELETE r', {
            'user_id': user_id
        })
        for anime in anime_list:
            handle_anime(client, user_id, anime)
    except:
        traceback.print_exc()


def update_metascores(client, name):
    print(f'Metascore: {name}')
    client.run('''
        MATCH (user:User {name: {name}})-[s:META_SCORED]->()
        DETACH DELETE s
    ''', {
        'name': name
    })

    positions = [
        'Original Creator',
        'Director',
        'Key Animation',
        'Music',
        'Character Design',
        'Script',
        'Sound Director',
        'Storyboard',
        'Animation Director',
        'Series Composition',
        'Original Character Design',
        'Art Director',
        'Producer',
        'Screenplay',
        'Chief Animation Director',
        'Mechanical Design',
        'Planning',
        'Sound Effects',
        'Color Design',
        'Creator',
        'Director of Photography',
        'Director (Chief Director)'
    ]

    client.run('''
        MATCH (user:User {name: {name}})-[rating:Rated]->(anime:Anime)<-[:FOR]-(job:Job)<-[:HAS_JOB]-(staff:Staff), (job)-[:HAS]->(position:Position)
        WHERE rating.score > 0
        WITH
            user,
            staff,
            anime,
            rating,
            collect(position.name) as positions
        WHERE
            ANY(x in positions WHERE (x in {positions}))
        WITH
            user,
            count(anime) as count,
            count(rating) as ratings,
            staff,
            avg(rating.score) as metascore
        CREATE (user)-[score:META_SCORED]->(staff)
        SET score.value = ((metascore * ratings) + (6.91 * 10)) / (ratings + 10)
        SET score.count = count
    ''', {
        'name': name,
        'positions': positions
    })

    client.run('''
        MATCH (user:User {name: {name}})-[staff_score:META_SCORED]->(staff:Staff)-[:HAS_JOB]->(:Job)-[:FOR]->(anime:Anime)
        WITH
            user,
            count(staff) as count,
            count(staff_score) as scores,
            anime,
            avg(staff_score.value) as metascore
        CREATE (user)-[score:META_SCORED]->(anime)
        SET score.value = ((metascore * scores) + (6.91 * 100)) / (scores + 100)
        set score.count = count
    ''', {
        'name': name
    })


def handle_args():
    parser = ArgumentParser(description='MAL scrapper')

    parser.add_argument('-u', '--username', type=str, dest='username', help='MAL username to parse', required=True)

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = handle_args()

    username = args.username

    graph = Graph()
    update_user(graph, username)
    while True:
        staff_count = update_staff(graph)
        print(f'Updated {staff_count} staff')
        anime_count = update_shows(graph)
        print(f'Updated {anime_count} anime')
        if (staff_count == 0 and anime_count == 0):
            break
    update_metascores(graph, username)

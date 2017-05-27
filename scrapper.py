from urllib.request import urlopen
import xmltodict
import re
from py2neo import Graph
import time
from argparse import ArgumentParser

statuses = ['0', 'watching', 'completed', 'on hold', 'dropped', '5', 'plan to watch']


def fetch_anime_staff(html_text):
    anime_name = None
    staff = {}

    anime_name = re.findall('(.*) - Characters &amp; Staff - MyAnimeList.net', html_text)[0]
    html_text = html_text[html_text.index('Add staff'):]
    for m in re.findall('/people/\d+/[^"]+', html_text):
        _, id, name = m[1:-1].split('/')
        print(f'staff: {id} {name}')
        staff[id] = name

    return anime_name, staff


def update_shows(client):
    count = 0
    anime_list = client.run('MATCH (anime:Anime) WHERE anime.last_updated < (timestamp() / 1000.0 - (60 * 60 * 24 * 7)) RETURN anime.id as id, anime.page as page ORDER BY id ASC LIMIT 100')
    for anime in anime_list:
        count += 1
        try:
            anime_id = anime['id']
            page = anime['page']
            if page in None:
                print(f'Fetching staff page {anime_id}')
                with urlopen(f'https://myanimelist.net/anime/{anime_id}/placeholder/characters', timeout=5) as response:
                    html_content = response.read()
                    encoding = response.headers.get_content_charset('utf-8')
                    page = html_content.decode(encoding, errors='ignore')
            anime_name, staff = fetch_anime_staff(page)
            print(f'anime: {anime_id} {anime_name}')
            for staff_id, name in staff.items():
                print(f'staff: {staff_id} {name}')
                client.run('MERGE (staff:Staff {id: toInteger({staff_id})}) SET staff.name = {name}', {
                    'staff_id': staff_id,
                    'name': name
                })
            client.run('MERGE (anime:Anime {id: toInteger({anime_id})}) SET anime.last_updated = {now} SET anime.page = {page}', {
                'anime_id': anime_id,
                'page': page,
                'now': time.time()
            })
        except Exception as e:
                print(e)

    return count


def fetch_staff_anime(html_text):
    staff_name = None
    anime = {}

    staff_name = re.findall('(.*) - MyAnimeList.net', html_text)[0]
    staff_text = html_text[html_text.index('Anime Staff Positions'):]
    for m in re.findall('<a href="\/anime\/(\d+)\/([^"]+)">.+<\/a><div class="spaceit_pad">\s+<a href="[^"]+" title="[^"]+" class="[^"]+">add<\/a>(.+)<\/div>', staff_text):
        anime_id = m[0]
        name = m[1]
        position = m[2].replace('<small>', '').replace('</small>', '')
        if (anime_id in anime):
            anime[anime_id]['positions'].append(position)
        else:
            anime[anime_id] = {'positions': [position], 'name': name}

    return staff_name, anime


def update_staff(client):
    count = 0
    staff_list = client.run('MATCH (staff:Staff) WHERE staff.last_updated < (timestamp() / 1000.0 - (60 * 60 * 24 * 7)) RETURN staff.id as id, staff.page as page ORDER BY id LIMIT 100')
    for staff in staff_list:
        count += 1
        try:
            staff_id = staff['id']
            page = staff['page']

            if page is None:
                print(f'Fetching staff page {staff_id}')
                with urlopen(f'https://myanimelist.net/people/{staff_id}', timeout=5) as response:
                    html_content = response.read()
                    encoding = response.headers.get_content_charset('utf-8')
                    page = html_content.decode(encoding, errors='ignore')

            client.run('MATCH (:Staff {id: toInteger({staff_id})})-[r:WorkedOn]->() DELETE r', {
                'staff_id': staff_id
            })
            staff_name, anime_list = fetch_staff_anime(page)
            print(f'staff: {staff_id} {staff_name}')
            for anime_id, anime in anime_list.items():
                name = anime['name']
                print(f'anime: {anime_id} {name}')
                positions = anime['positions']
                client.run('MERGE (anime:Anime {id: toInteger({anime_id})})', {
                    'anime_id': anime_id
                })
                for position in positions:
                    client.run('MATCH (anime {id: toInteger({anime_id})}) MATCH (staff:Staff {id: toInteger({staff_id})}) CREATE (staff)-[r:WorkedOn]->(anime) SET r.position = trim({position})', {
                        'anime_id': anime_id,
                        'staff_id': staff_id,
                        'position': position
                    })

            client.run('MERGE (staff:Staff {id: toInteger({staff_id})}) SET staff.last_updated = {now} SET staff.name = {name} SET staff.page = {page}', {
                'staff_id': staff_id,
                'name': staff_name,
                'page': page,
                'now': time.time()
            })
        except Exception as e:
            print(e)

    return count


def fetch_anime_list(request):
    with urlopen(request, timeout=5) as response:
        html_content = response.read()
        encoding = response.headers.get_content_charset('utf-8')
        html_text = html_content.decode(encoding, errors='ignore')
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
        list_page = f'https://myanimelist.net/malappinfo.php?u={name}&status=all&type=anime'
        user, anime_list = fetch_anime_list(list_page)

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
    except Exception as e:
        print(e)


def update_metascores(client, name):
    print(f'Metascore: {name}')
    client.run('MATCH (user:User {name: {name}})-[s:META_SCORED]->() DETACH DELETE s', {
        'name': name
    })

    positions = [
        'Key Animation',
        'Director',
        'Original Creator',
        'Character Design',
        'Art Director',
        'Script',
        'Animation Director',
        'Storyboard',
        'Series Composition',
        'Episode Director',
        'Producer',
        'Color Design',
        'Chief Animation Director',
        'Director of Photography',
        'Music',
        'Sound Effects',
        'Mechanical Design',
        'Director (Chief Director)'
    ]

    client.run('''
        MATCH (user:User {name: {name}})-[rating:Rated]->(anime:Anime)<-[position:WorkedOn]-(staff:Staff)
        WHERE position.position in {position}
        WITH
            user,
            count(anime) as count,
            staff,
            avg(rating.score) as metascore
        CREATE (user)-[score:META_SCORED]->(staff)
        SET score.value = metascore
        SET score.count = count
    ''', {
        'name': name,
        'position': positions
    })

    client.run('MATCH ()-[meta:META_SCORED]-() WHERE meta.count <= 5 DETACH DELETE meta')

    client.run('''
        MATCH (user:User {name: {name}})-[score:META_SCORED]->(staff:Staff)-[:WorkedOn]->(anime:Anime)
        WITH
            user,
            count(staff) as count,
            anime,
            avg(score.value) as metascore
        CREATE (user)-[score:META_SCORED]->(anime)
        SET score.value = metascore
        set score.count = count
    ''', {
        'name': name
    })

    client.run('MATCH ()-[meta:META_SCORED]-() WHERE meta.count <= 5 DETACH DELETE meta')


def handle_args():
    parser = ArgumentParser(description='MAL scrapper')

    parser.add_argument('-u', '--username', type=str, dest='username', help='MAL username to parse', required=True)

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = handle_args()

    username = args.username

    try:
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
    finally:
        pass

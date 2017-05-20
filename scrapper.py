from urllib.request import urlopen
import xmltodict
import re
from py2neo import Graph
import time
from lxml import etree

statuses = ['0', 'watching', 'completed', 'on hold', 'dropped', '5', 'plan to watch']

graph = Graph("http://localhost:7474/db/data/")


def fetch_anime_staff(request):
    staff = {}
    with urlopen(request) as response:
        html_content = response.read()
        encoding = response.headers.get_content_charset('utf-8')
        html_text = html_content.decode(encoding, errors='ignore')
        html_text = html_text[html_text.index('Add staff'):]
        for m in re.findall('"/people/\d+/[^"]+"', html_text):
            _, _, id, name = m[1:-1].split('/')
            staff[id] = name

    return staff


def update_shows(client):
    now = time.time()
    anime_list = client.run('MATCH (anime:Anime) WHERE coalesce(anime.last_updated, 0) < ({now} - 60 * 60 * 24) RETURN anime.id as id, anime.name as name ORDER BY anime.name ASC', {
        'now': now
    })
    for anime in anime_list:
        anime_id = anime['id']
        staff = fetch_anime_staff(f'https://myanimelist.net/anime/{anime_id}/placeholder/characters')
        for staff_id, name in staff.items():
            client.run('MERGE (staff:Staff {id: toInteger({staff_id})}) SET staff.name = {name}', {
                'staff_id': staff_id,
                'name': name
            })
        client.run('MERGE (anime:Anime {id: toInteger({anime_id})}) SET anime.last_updated = {now}', {
            'anime_id': anime_id,
            'now': now
        })


def fetch_staff_anime(request):
    anime = {}
    with urlopen(request) as response:
        html_content = response.read()
        encoding = response.headers.get_content_charset('utf-8')
        html_text = html_content.decode(encoding, errors='ignore')
        html_text = html_text[html_text.index('Anime Staff Positions'):]
        for m in re.findall('<a href="\/anime\/(\d+)\/([^"]+)">.+<\/a><div class="spaceit_pad">\s+<a href="[^"]+" title="[^"]+" class="[^"]+">add<\/a>(.+)<\/div>', html_text):
            anime_id = m[0]
            name = m[1]
            position = m[2].replace('<small>', '').replace('</small>', '')
            if (anime_id in anime):
                anime[anime_id]['positions'].append(position)
            else:
                anime[anime_id] = {'positions': [position], 'name': name}

    return anime


def update_staff(client):
    now = time.time()
    staff_list = client.run('MATCH (staff:Staff) WHERE coalesce(staff.last_updated, 0) < ({now} - 60 * 60 * 24) RETURN staff.id as id, staff.name as name ORDER BY name ASC', {
        'now': now
    })
    for staff in staff_list:
        staff_id = staff['id']
        name = staff['name']

        print(f'staff: {name}')
        client.run('MATCH (:Staff {id: toInteger({staff_id})})-[r:WorkedOn]->() DELETE r', {
            'staff_id': staff_id
        })
        anime_list = fetch_staff_anime(f'https://myanimelist.net/people/{staff_id}')
        for anime_id, anime in anime_list.items():
            name = anime['name']
            positions = anime['positions']
            client.run('MERGE (anime:Anime {id: toInteger({anime_id})}) SET anime.name = {name}', {
                'anime_id': anime_id,
                'name': name
            })
            for position in positions:
                client.run('MATCH (anime {id: toInteger({anime_id})}) MATCH (staff:Staff {id: toInteger({staff_id})}) CREATE (staff)-[r:WorkedOn]->(anime) SET r.position = {position}', {
                    'anime_id': anime_id,
                    'staff_id': staff_id,
                    'position': position
                })

        client.run('MERGE (staff:Staff {id: toInteger({staff_id})}) SET staff.last_updated = {now}', {
            'staff_id': staff_id,
            'now': now
        })


def fetch_anime_list(request):
    with urlopen(request) as response:
        html_content = response.read()
        encoding = response.headers.get_content_charset('utf-8')
        html_text = html_content.decode(encoding, errors='ignore')
        anime_list = xmltodict.parse(html_text)['myanimelist']
        user = anime_list.pop('myinfo')
        return user, anime_list['anime']


def handle_anime(client, user_id, anime):
    anime_id = anime['series_animedb_id']
    name = anime['series_title']
    rating =anime['my_score']

    client.run('MERGE (anime:Anime {id: toInteger({anime_id})}) SET anime.name = {name}', {
        'anime_id': anime_id,
        'name': name
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
    list_page = f'https://myanimelist.net/malappinfo.php?u={name}&status=all&type=anime'
    user, anime_list = fetch_anime_list(list_page)
    index = 0
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


def update_metascores(client, name):
    client.command('')

if __name__ == "__main__":
    try:
        update_user(graph, 'Wiles')
        update_shows(graph)
        update_staff(graph)
        # update_metascores(client, 'Wiles')
    finally:
        # graph.close()
        pass

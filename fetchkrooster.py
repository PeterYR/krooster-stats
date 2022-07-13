import requests

def get_roster(username: str) -> dict:
    '''Make HTTP requests and return Krooster roster JSON'''

    uuid = requests.get(f'https://ak-roster-default-rtdb.firebaseio.com/phonebook/{username.lower()}.json').json()
    if not uuid:
        raise ValueError(f'Invalid username: {username}')
    return requests.get(f'https://ak-roster-default-rtdb.firebaseio.com/users/{uuid}/roster.json').json()

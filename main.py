import requests
from pathlib import Path


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def main():
    Path('./books').mkdir(parents=True, exist_ok=True)
    book_id = 0

    for _ in range(10):
        book_id += 1
        payload = {'id': book_id}
        url = 'https://tululu.org/txt.php'
        try:
            response = requests.get(url, params=payload)
            response.raise_for_status()
            check_for_redirect(response)
        except requests.HTTPError:
            continue
        
        filename = f'books/id{book_id}.txt'
        with open(filename, 'wb') as file:
            file.write(response.content)


if __name__ == '__main__':
    main()

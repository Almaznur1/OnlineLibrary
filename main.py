import requests
from pathlib import Path
from bs4 import BeautifulSoup
import os
from pathvalidate import sanitize_filename


def check_for_redirect(url):
    response = requests.get(url)
    response.raise_for_status()
    if response.history:
        raise requests.HTTPError
    return response


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()
    filepath = f'{os.path.join(folder, sanitize_filename(filename))}.txt'
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def main():
    Path('./books').mkdir(parents=True, exist_ok=True)
    book_id = 0

    for _ in range(10):
        book_id += 1
        book_page = f'https://tululu.org/b{book_id}/'
        book_url = f'https://tululu.org/txt.php?id={book_id}'

        try:
            response = check_for_redirect(book_page)
            check_for_redirect(book_url)
        except requests.HTTPError:
            continue

        soup = BeautifulSoup(response.text, 'lxml')
        title_tag = soup.find('div', id='content').find('h1')
        title_end_index = title_tag.text.index('::')
        title = f'{book_id}. {title_tag.text[:title_end_index].strip()}'

        download_txt(book_url, title)


if __name__ == '__main__':
    main()

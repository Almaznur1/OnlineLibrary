import requests
from pathlib import Path
from bs4 import BeautifulSoup
import os
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse, urlsplit


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


def download_image(url, folder='images/'):
    response = requests.get(url)
    response.raise_for_status()
    path = urlparse(url).path
    image = path[path.rfind('/') + 1:]
    filepath = os.path.join(folder, image)
    with open(filepath, 'wb') as file:
        file.write(response.content)


def main():
    Path('./books').mkdir(parents=True, exist_ok=True)
    Path('./images').mkdir(parents=True, exist_ok=True)
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

        image = soup.find('div', class_='bookimage').find('img')['src']
        image_url = urljoin('https://tululu.org/', image)

        comment_tags = soup.find_all('div', class_='texts')
        comments = [comment_tag.span.text for comment_tag in comment_tags]

        download_txt(book_url, title)
        download_image(image_url)


if __name__ == '__main__':
    main()

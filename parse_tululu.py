import requests
from pathlib import Path
from bs4 import BeautifulSoup
import os
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse, unquote
import argparse
import sys
import time


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_txt(url, params, filename, folder='books/'):
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_redirect(response)
    filepath = f'{os.path.join(folder, sanitize_filename(filename))}.txt'
    with open(filepath, 'wb') as file:
        file.write(response.content)


def download_image(url, folder='images/'):
    response = requests.get(url)
    response.raise_for_status()
    path = urlparse(unquote(url)).path
    image = path[path.rfind('/') + 1:]
    filepath = os.path.join(folder, image)
    with open(filepath, 'wb') as file:
        file.write(response.content)


def parse_book_page(book_page_url, response):
    soup = BeautifulSoup(response.text, 'lxml')

    title_tag = soup.select_one('div#content h1').text
    title_end_index = title_tag.index('::')
    title = title_tag[:title_end_index].strip()

    author = title_tag[title_end_index + 2:].strip()

    image = soup.select_one('div.bookimage img')['src']
    image_url = urljoin(book_page_url, image)

    temporary_path = urlparse(unquote(image_url)).path
    img_scr = f'images/{temporary_path[temporary_path.rfind("/") + 1:]}'

    book_path = f'books/{title}.txt'

    comment_tags = soup.select('div.texts span')
    comments = [comment_tag.text for comment_tag in comment_tags]

    genres_tag = soup.select('span.d_book a')
    genres = [genre_tag.text for genre_tag in genres_tag]
    book = {
        'title': title,
        'author': author,
        'image_url': image_url,
        'img_scr': img_scr,
        'book_path': book_path,
        'comments': comments,
        'genres': genres,
    }
    return book


def main():
    parser = argparse.ArgumentParser(
        description='download books from https://tululu.org')
    parser.add_argument('start_id',
                        nargs='?',
                        default=1,
                        type=int,
                        help='put here the first book id')
    parser.add_argument('end_id',
                        nargs='?',
                        default=10,
                        type=int,
                        help='put here the last book id')
    args = parser.parse_args()

    Path('./books').mkdir(parents=True, exist_ok=True)
    Path('./images').mkdir(parents=True, exist_ok=True)

    for book_id in range(args.start_id, args.end_id + 1):
        book_page_url = f'https://tululu.org/b{book_id}/'
        book_url = 'https://tululu.org/txt.php'
        params = {'id': book_id}

        try:
            response = requests.get(book_page_url)
            response.raise_for_status()
            check_for_redirect(response)
            book = parse_book_page(book_page_url, response)
            download_txt(book_url, params, book['title'])
            download_image(book['image_url'])
        except requests.exceptions.HTTPError:
            print(f'Кажется книга №{book_id} недоступна для скачивания. '
                  'Переходим к следующей\n', file=sys.stderr)
            continue
        except requests.exceptions.ConnectionError:
            print('Возникли проблемы с сетью! Проверьте ваше соединение. '
                  'Мы попробуем скачать следующую книгу через 10 секунд',
                  file=sys.stderr)
            time.sleep(10)
            continue

        print('Название:', book['title'])
        print('Автор:', book['author'], '\n')


if __name__ == '__main__':
    main()

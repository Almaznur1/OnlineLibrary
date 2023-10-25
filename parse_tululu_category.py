import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from pathlib import Path
import time
import sys
import json
import argparse
from parse_tululu import (download_image, download_txt, check_for_redirect,
                          parse_book_page)


def fetch_fantasy_books_url_with_id(start_page_number, end_page_number):
    book_page_urls_with_ids = set()

    for page_number in range(start_page_number, end_page_number):
        url = f'https://tululu.org/l55/{page_number}'
        try:
            response = requests.get(url)
            response.raise_for_status()
            check_for_redirect(response)
        except requests.exceptions.HTTPError:
            print(f'Кажется страницы №{page_number} не существует. '
                  'Переходим к следующей.\n', file=sys.stderr)
            continue
        except requests.exceptions.ConnectionError:
            print('Возникли проблемы с сетью! Проверьте ваше соединение. '
                  'Мы попробуем открыть следующую страницу через 10 секунд',
                  file=sys.stderr)
            time.sleep(10)
            continue

        soup = BeautifulSoup(response.text, 'lxml')
        books = soup.select('div#content table a[href^="/b"]')

        for book in books:
            book_path = book['href']
            book_page_url = urljoin(url, book_path)
            book_id = book_path[2:-1]
            book_page_urls_with_ids.add((book_page_url, book_id))

    return book_page_urls_with_ids


def main():
    parser = argparse.ArgumentParser(
        description='download fantasy books from https://tululu.org')
    parser.add_argument('--start_page',
                        type=int,
                        default=1,
                        help='put here start page number')
    parser.add_argument('--end_page',
                        type=int,
                        default=701,
                        help='put here end page number')
    parser.add_argument('--dest_folder',
                        type=str,
                        default='.',
                        help='specify the destination folder')
    parser.add_argument('--skip_txt',
                        action='store_true',
                        help='download without txt files')
    parser.add_argument('--skip_imgs',
                        action='store_true',
                        help='download without images')

    args = parser.parse_args()

    Path(args.dest_folder).mkdir(parents=True, exist_ok=True)
    if not args.skip_txt:
        books_folder = Path(f'{args.dest_folder}/books')
        books_folder.mkdir(parents=True, exist_ok=True)
    if not args.skip_imgs:
        images_folder = Path(f'{args.dest_folder}/images')
        images_folder.mkdir(parents=True, exist_ok=True)

    book_url = 'https://tululu.org/txt.php'
    books = []

    book_pages_url_with_id = fetch_fantasy_books_url_with_id(args.start_page,
                                                             args.end_page + 1)

    for book_page_url, book_id in book_pages_url_with_id:
        params = {'id': book_id}
        try:
            response = requests.get(book_page_url)
            response.raise_for_status()
            check_for_redirect(response)
            book = parse_book_page(book_page_url, response)
            if not args.skip_txt:
                download_txt(book_url, params, book['title'], books_folder)
            if not args.skip_imgs:
                download_image(book['image_url'], images_folder)
            books.append(book)

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

    with open(f'{args.dest_folder}/books.json', 'w', encoding='utf8') as file:
        json.dump(books, file, ensure_ascii=False)


if __name__ == '__main__':
    main()

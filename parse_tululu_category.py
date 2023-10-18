import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from pathlib import Path
import time
import sys
import json
from parse_tululu import download_image, download_txt, check_for_redirect


def fetch_fantasy_books_url_with_id():
    base_url = 'https://tululu.org/'
    book_pages_url_with_id = []

    for page in range(1, 5):
        url = f'https://tululu.org/l55/{page}'
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        books = soup.select('div#content table a[href^="/b"]')

        temp_books_id = []

        for book in books:
            book_id = book['href']
            if book_id in temp_books_id:
                continue
            else:
                temp_books_id.append(book_id)
            book_page_url = urljoin(base_url, book_id)
            book_pages_url_with_id.append((book_page_url, book_id[2:-1]))

    return book_pages_url_with_id


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
    Path('./books').mkdir(parents=True, exist_ok=True)
    Path('./images').mkdir(parents=True, exist_ok=True)

    book_pages_url_with_id = fetch_fantasy_books_url_with_id()
    book_url = 'https://tululu.org/txt.php'
    books = []

    for book_page_url, book_id in book_pages_url_with_id:
        params = {'id': book_id}
        try:
            response = requests.get(book_page_url)
            response.raise_for_status()
            check_for_redirect(response)
            book = parse_book_page(book_page_url, response)
            books.append(book)
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
    books_json = json.dumps(books, ensure_ascii=False)

    with open('books.json', 'w', encoding='utf8') as file:
        file.write(books_json)


if __name__ == '__main__':
    main()

import requests
from pathlib import Path
from bs4 import BeautifulSoup
import os
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse, unquote
import argparse


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
    path = urlparse(unquote(url)).path
    image = path[path.rfind('/') + 1:]
    filepath = os.path.join(folder, image)
    with open(filepath, 'wb') as file:
        file.write(response.content)


def parse_book_page(response, book_id):
    soup = BeautifulSoup(response.text, 'lxml')

    title_tag = soup.find('div', id='content').find('h1')
    title_end_index = title_tag.text.index('::')
    title = f'{book_id}. {title_tag.text[:title_end_index].strip()}'

    author = title_tag.text[title_end_index + 2:].strip()

    image = soup.find('div', class_='bookimage').find('img')['src']
    image_url = urljoin('https://tululu.org/', image)

    comment_tags = soup.find_all('div', class_='texts')
    comments = [comment_tag.span.text for comment_tag in comment_tags]

    genres_tag = soup.find('span', class_='d_book').find_all('a')
    genres = [genre_tag.text for genre_tag in genres_tag]
    book = {
        'title': title,
        'author': author,
        'image_url': image_url,
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

    book_id = args.start_id - 1
    books_count = args.end_id - book_id

    Path('./books').mkdir(parents=True, exist_ok=True)
    Path('./images').mkdir(parents=True, exist_ok=True)

    for _ in range(books_count):
        book_id += 1
        book_page = f'https://tululu.org/b{book_id}/'
        book_url = f'https://tululu.org/txt.php?id={book_id}'

        try:
            response = check_for_redirect(book_page)
            check_for_redirect(book_url)
        except requests.HTTPError:
            continue

        book = parse_book_page(response, book_id)
        download_txt(book_url, book['title'])
        download_image(book['image_url'])

        print('Название:', book['title'])
        print('Автор:', book['author'], '\n')


if __name__ == '__main__':
    main()

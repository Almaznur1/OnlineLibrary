import requests
from pathlib import Path


Path('./books').mkdir(parents=True, exist_ok=True)
book_id = 32168

for _ in range(10):
    url = f'https://tululu.org/txt.php?id={str(book_id)}'
    response = requests.get(url)
    response.raise_for_status()

    filename = f'books/book_{book_id}.txt'
    with open(filename, 'wb') as file:
        file.write(response.content)

    book_id += 1

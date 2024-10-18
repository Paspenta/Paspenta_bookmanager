import requests

def get_books(q=None, intitle=None, inauthor=None, isbn=None, page=0):
    URL = "https://www.googleapis.com/books/v1/volumes"
    MAX_RESULT = 10
    parms = dict()

    if q is not None:
        parms["q"] = q
    else:
        keyword = []
        if intitle is not None:
            keyword.append(f"intitle:{intitle}")
        if inauthor is not None:
            keyword.append(f"inauthor:{inauthor}")
        if isbn is not None:
            keyword.append(f"isbn:{isbn}")
        if keyword:
            q = "+".join(keyword)
            parms["q"] = q
        else:
            return []
    parms["maxResults"] = MAX_RESULT
    parms["startIndex"] = page

    response = requests.get(URL, params=parms)
    books = response.json()

    ret = []

    for book in books.get("items", []):
        ret.append(parse_book(book))
    
    return ret

def parse_book(book):
    ret = dict()
    volumeInfo = book.get("volumeInfo", {})
    ret["title"] = volumeInfo.get("title", "")
    ret["author"] = ",".join(volumeInfo.get("authors", []))
    ret["publisher"] = volumeInfo.get("publisher", "")
    ret["publishe_date"] = volumeInfo.get("publishedDate", "")
    isbns = volumeInfo.get("industryIdentifiers", [])
    isbn = None
    for i in isbns:
        if i["type"] in ("ISBN_10", "ISBN_13"):
            isbn = i["identifier"]
    ret["isbn"] = isbn if isbn is not None else ""

    return ret


if __name__ == "__main__":
    keyword = input("Search:")
    books = get_books(q=keyword)
    for book in books:
        for key, value in book.items():
            print(f"{key}:{value}")
        print("-----")
import requests

def get_books(q=None, intitle=None, inauthor=None, isbn=None, page=0):
    URL = "https://www.googleapis.com/books/v1/volumes"
    MAX_RESULT = 30
    parms = dict()
    keyword = []

    if q is not None and q:
        keyword.append(q)
    if intitle is not None and intitle:
        keyword.append(f"intitle:{intitle}")
    if inauthor is not None and inauthor:
        keyword.append(f"inauthor:{inauthor}")
    if isbn is not None and isbn:
        keyword.append(f"isbn:{isbn}")
    if keyword:
        q = "+".join(keyword)
        parms["q"] = q
    else:
        return []
    parms["maxResults"] = MAX_RESULT
    parms["startIndex"] = MAX_RESULT * page

    response = requests.get(URL, params=parms)
    print(response.url)
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
    isbn_10 = isbn_13 = None
    for i in isbns:
        if i["type"] == "ISBN_10":
            isbn_10 = i["identifier"]
        elif i["type"] == "ISBN_13":
            isbn_13 = i["identifier"]
    ret["isbn_10"] = isbn_10
    ret["isbn_13"] = isbn_13

    return ret


if __name__ == "__main__":
    keyword = input("Search:")
    books = get_books(q=keyword)
    for book in books:
        for key, value in book.items():
            print(f"{key}:{value}")
        print("-----")
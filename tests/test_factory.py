from bookmanager import create_app

def test_config():
    # create_appに引数与えなかった場合、テストモードになっていないか
    assert not create_app().testing

    # create_appに引数を与えて、テストモードになるかどうか
    assert create_app({"TESTING": True}).testing


def test_hello(client):
    response = client.get("/hello")
    assert response.data == b"Hello, World!"
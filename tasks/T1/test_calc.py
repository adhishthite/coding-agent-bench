from calc import add, mean

def test_add():
    assert add(2, 3) == 5

def test_mean():
    assert mean([2, 4, 6]) == 4


if __name__ == "__main__":
    test_add()
    test_mean()
    print("2 passed")

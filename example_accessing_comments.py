
def get_comments(tokens):
    for t in tokens:

        for c in t.leading_comments:
            print("Leading comment:", c)

        for c in t.trailing_comments:
            print("Trailing comment:", c)


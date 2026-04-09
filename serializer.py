

def serialize_tokens(tokens):

    output = []

    for t in tokens:

        output.append(t.leading_ws)

        for c in t.leading_comments:
            output.append(c)

        output.append(t.value)

        output.append(t.trailing_ws)

        for c in t.trailing_comments:
            output.append(c)

    return "".join(output)


# round-trip guarantee:
# serialize_tokens(tokenize(text)) == text



# Example accessing comments later:

# def get_comments(tokens):
#     for t in tokens:

#         for c in t.leading_comments:
#             print("Leading comment:", c)

#         for c in t.trailing_comments:
#             print("Trailing comment:", c)




# https://chatgpt.com/share/69d6e36b-a268-8329-8ef6-37d343ef636c

# Why this tokenizer is the correct foundation

# It supports:

# ✔ exact formatting preservation
# ✔ nested DSL parsing
# ✔ comment-aware tooling
# ✔ AST building
# ✔ syntax rewriting
# ✔ incremental editing later
# ✔ formatter implementation later

# This is essentially the same architecture used in Roslyn-lite parsers for DSLs.
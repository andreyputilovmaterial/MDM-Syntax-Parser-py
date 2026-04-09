

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


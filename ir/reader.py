# read strings into Token

import binascii
import enum

from clvm import to_sexp_f


class Type(enum.IntEnum):
    CONS = 1
    INT = 2
    HEX = 3
    QUOTES = 4
    SYMBOL = 5


def consume_whitespace(s: str, offset):
    """
    This also deals with comments.
    """
    while True:
        while offset < len(s) and s[offset].isspace():
            offset += 1
        if offset >= len(s) or s[offset] != ";":
            break
        while offset < len(s) and s[offset] not in "\n\r":
            offset += 1
    return offset


def consume_until_whitespace(s: str, offset):
    start = offset
    while offset < len(s) and not s[offset].isspace() and s[offset] != ")":
        offset += 1
    return s[start:offset], offset


DOT_SYMBOL = to_sexp_f([Type.SYMBOL, b"."]).as_python()


def tokenize_cons(stream, offset):
    r = []

    while True:
        for token, offset in stream:
            break
        else:
            raise SyntaxError("the ( at %d is missing a )" % offset)

        if token == ")":
            return r

        sexp = tokenize_sexp(token, offset, stream)
        if sexp.as_python() == DOT_SYMBOL:
            # handle the cons box case here
            if len(r) == 1:
                for token, offset in stream:
                    break
                else:
                    raise SyntaxError("unexpected end of stream at %d" % offset)
                sexp = tokenize_sexp(token, offset, stream)
                for token, offset in stream:
                    break
                else:
                    raise SyntaxError("unexpected end of stream at %d" % offset)
                if token == ")":
                    return to_sexp_f((r[0], sexp))
                raise SyntaxError("illegal expression in cons box at %d" % offset)

        r.append(sexp)


def tokenize_int(token, offset):
    try:
        return int(token)
    except (ValueError, TypeError):
        return None


def tokenize_hex(token, offset):
    if token[:2].upper() == "0X":
        try:
            token = token[2:]
            if len(token) % 2 == 1:
                token = "0%s" % token
            return binascii.unhexlify(token)
        except Exception:
            raise SyntaxError("invalid hex at %s: %s" % (offset, token))


def tokenize_quotes(token, offset):
    if len(token) < 2:
        return None
    c = token[:1]
    if c not in "\'\"":
        return None

    if token[-1] != c:
        raise SyntaxError("unterminated string starting at %d: %s" % (offset, token))

    return token.encode("utf8")


def tokenize_symbol(token, offset):
    return token.encode("utf8")


def tokenize_sexp(token, offset, stream):

    if token == "(":
        type = Type.CONS
        r = tokenize_cons(stream, offset)

    else:
        for type, f in [
            (Type.INT, tokenize_int),
            (Type.HEX, tokenize_hex),
            (Type.QUOTES, tokenize_quotes),
            (Type.SYMBOL, tokenize_symbol),
        ]:
            r = f(token, offset)
            if r is not None:
                break

    sexp = to_sexp_f([type, r])
    sexp._offset = offset
    return sexp


def token_stream(s: str):
    offset = 0
    while offset < len(s):
        offset = consume_whitespace(s, offset)
        c = s[offset]
        if c in "(.)":
            yield c, offset
            offset += 1
            continue
        if c in "\"'":
            start = offset
            initial_c = s[start]
            offset += 1
            while offset < len(s) and s[offset] != initial_c:
                offset += 1
            if offset < len(s):
                yield s[start:offset+1], initial_c
                offset += 1
                continue
            else:
                raise SyntaxError("unterminated string starting at %d: %s" % (start, s[start:]))
        token, end_offset = consume_until_whitespace(s, offset)
        yield token, offset
        offset = end_offset


def read_tokens(s: str):
    stream = token_stream(s)

    for token, offset in stream:
        return tokenize_sexp(token, offset, stream)
    else:
        raise SyntaxError("unexpected end of stream")

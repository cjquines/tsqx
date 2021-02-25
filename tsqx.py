##########
## TSQX ##
##########

# original TSQ by evan chen

import enum, re, sys


class Op:
    def _join_exp(self, exp, join_str):
        return join_str.join(self._emit_exp(e) for e in exp)

    def _emit_exp(self, exp):
        if not isinstance(exp, list):
            return exp
        if "," in exp:
            return "(" + self._join_exp(exp, " ") + ")"
        head, *tail = exp
        if not tail:
            return head
        return head + "(" + self._join_exp(tail, ", ") + ")"

    def emit_exp(self):
        return self._join_exp(self.exp, "*")

    def emit(self):
        raise Exception("Operation not recognized")

    def post_emit(self):
        return None


class Blank(Op):
    def emit(self):
        return ""


class Point(Op):
    def __init__(self, name, exp, **options):
        self.name = name
        self.exp = exp
        self.dot = options.get("dot", True)
        self.label = options.get("label", name)
        self.direction = options.get("direction", None)

    def emit(self):
        return f"pair {self.name} = {self.emit_exp()};"

    def post_emit(self):
        args = [self.name]
        if self.label:
            args.append(f'"${self.label}$"')
            args.append(self.direction)
        if self.dot:
            return "dot(" + ", ".join(args) + ");"
        if len(args) > 1:
            return "label(" + ", ".join(args) + ");"


class Draw(Op):
    def __init__(self, exp, **options):
        self.exp = exp
        self.fill = options.get("fill", None)
        self.outline = options.get("outline", None)

    def emit(self):
        exp = self.emit_exp()
        if self.fill:
            outline = self.outline or "defaultpen"
            return f"filldraw({exp}, {self.fill}, {outline});"
        elif self.outline:
            return f"draw({exp}, {self.outline});"
        else:
            return f"draw({exp});"


class Parser:
    def __init__(self):
        # TODO add options
        pass

    def tokenize(self, line):
        line = line.strip() + " "
        for old, new in [
            ("=", " = "),
            ("(", "( "),
            (")", " ) "),
            (",", " , "),
            (" +", "+"),
            ("+ ", "+"),
            (" -", "-"),
            ("- ", "-"),
            (" *", "*"),
            ("* ", "*"),
            # ensures slashes in draw ops remain as tokens
            (" / ", "  /  "),
            (" /", "/"),
            ("/ ", "/"),
            # TODO prime support
        ]:
            line = line.replace(old, new)
        return list(filter(None, line.split()))

    def parse_name(self, tokens):
        if not tokens:
            raise SyntaxError("Can't parse point name")
        name, *rest = tokens

        aliases = {"": "dl", ":": "", ".": "d", ";": "l"}
        if rest:
            *rest, opts = rest
            if opts not in aliases.keys() and opts not in aliases.values():
                rest.push(opts)
                opts = ""
        else:
            opts = ""
        opts = aliases.get(opts, opts)
        # TODO prime support for label
        options = {"dot": "d" in opts, "label": "l" in opts and name}

        if rest:
            dirs, *rest = rest
            if dir_pairs := re.findall(r"(\d+)([A-Z]+)", dirs):
                options["direction"] = "+".join(f"{n}*plain.{w}" for n, w in dir_pairs)
            elif dirs.isdigit():
                options["direction"] = f"dir({dirs})"
            else:
                options["direction"] = f"plain.{dirs}"
        else:
            options["direction"] = f"dir({name})"

        if rest:
            raise SyntaxError("Can't parse point name")
        return name, options

    def parse_draw(self, tokens):
        try:
            idx = tokens.index("/")
            fill = tokens[:idx]
            outline = tokens[idx + 1 :]
        except ValueError:
            fill = []
            outline = tokens
        # TODO a fillpen with a digit should be opacity
        return {"fill": "+".join(fill), "outline": "+".join(outline)}

    def parse_subexp(self, tokens, idx, func_mode=False):
        token = tokens[idx]
        if token[-1] == "(":
            is_func = len(token) > 1
            res = []
            idx += 1
            if is_func:
                res.append(token[:-1])
            while tokens[idx] != ")":
                exp, idx = self.parse_subexp(tokens, idx, is_func)
                res.append(exp)
            return res, idx + 1
        if token == "," and func_mode:
            return "", idx + 1
        return token, idx + 1

    def parse_exp(self, tokens):
        if tokens[0][-1] != "(":
            tokens = ["(", *tokens, ")"]
        res = []
        idx = 0
        while idx != len(tokens):
            try:
                exp, idx = self.parse_subexp(tokens, idx)
                res.append(list(filter(None, exp)))
            except IndexError:
                raise SyntaxError("Unexpected end of line")
        return res

    def parse(self, line):
        line, *comment = line.split("#", 1)
        tokens = self.tokenize(line)
        if not tokens:
            return Blank(), comment
        # point
        try:
            idx = tokens.index("=")
            name, options = self.parse_name(tokens[:idx])
            exp = self.parse_exp(tokens[idx + 1 :])
            return Point(name, exp, **options), comment
        except ValueError:
            pass
        # draw with options
        try:
            idx = tokens.index("/")
            exp = self.parse_exp(tokens[:idx])
            options = self.parse_draw(tokens[idx + 1 :])
            return Draw(exp, **options), comment
        except ValueError:
            pass
        # draw without options
        exp = self.parse_exp(tokens)
        return Draw(exp), comment


def main():
    from argparse import ArgumentParser

    argparser = ArgumentParser(description="Generate Asymptote code.")
    argparser.add_argument(
        "-p",
        "--pre",
        help="Adds an Asymptote preamble.",
        action="store_true",
        dest="preamble",
        default=False,
    )
    argparser.add_argument(
        "-n",
        "--no-trans",
        help="Temporarily disables the transparencies.",
        action="store_true",
        dest="notrans",
        default=False,
    )
    argparser.add_argument(
        "fname",
        help="If provided, reads from the designated file rather than stdin",
        metavar="filename",
        nargs="?",
        default="",
    )
    argparser.add_argument(
        "-s",
        "--size",
        help="If provided, sets the image size in the preamble. (Use with -p.)",
        action="store",
        dest="size",
        default="8cm",
    )
    argparser.add_argument(
        "-sl",
        "--soft-label",
        help="Does not mark points, only labels them.",
        action="store_true",
        dest="softlabel",
        default=False,
    )
    args = argparser.parse_args()

    if args.preamble:
        print("import olympiad;")
        print("import cse5;")
        print("size(%s);" % args.size)
        print("defaultpen(fontsize(9pt));")
        print('settings.outformat="pdf";')
    if args.fname:
        stream = open(args.fname, "r")
    else:
        stream = sys.stdin

    parser = Parser()
    ops = [parser.parse(line) for line in stream]
    for op, comment in ops:
        print(op.emit())
    print("")
    for op, comment in ops:
        if op.post_emit():
            print(op.post_emit())


if __name__ == "__main__":
    main()

import re
import sys
from io import TextIOWrapper
from typing import Any, Generator, TextIO, TypedDict


def generate_points(kind: str, n: int) -> list[str]:
    if kind == "triangle":
        return ["dir(110)", "dir(210)", "dir(330)"]
    elif kind == "regular":
        return [f"dir({(90 + i * 360 / n) % 360})" for i in range(n)]
    raise SyntaxError("Special command not recognized")


T_TOKEN = str | list[str] | list["T_TOKEN"]


class T_OPSTRUCT(TypedDict):
    op: "Op"
    comment: str


GENERIC_PREAMBLE = r"""
usepackage("amsmath");
usepackage("amssymb");
settings.tex="pdflatex";
settings.outformat="pdf";
// Replacement for olympiad+cse5 which is not standard
import geometry;
// recalibrate fill and filldraw for conics
void filldraw(picture pic = currentpicture, conic g, pen fillpen=defaultpen, pen drawpen=defaultpen)
    { filldraw(pic, (path) g, fillpen, drawpen); }
void fill(picture pic = currentpicture, conic g, pen p=defaultpen)
    { filldraw(pic, (path) g, p); }
// some geometry
pair foot(pair P, pair A, pair B) { return foot(triangle(A,B,P).VC); }
pair orthocenter(pair A, pair B, pair C) { return orthocentercenter(A,B,C); }
pair centroid(pair A, pair B, pair C) { return (A+B+C)/3; }
// cse5 abbreviations
path CP(pair P, pair A) { return circle(P, abs(A-P)); }
path CR(pair P, real r) { return circle(P, r); }
pair IP(path p, path q) { return intersectionpoints(p,q)[0]; }
pair OP(path p, path q) { return intersectionpoints(p,q)[1]; }
path Line(pair A, pair B, real a=0.6, real b=a) { return (a*(A-B)+A)--(b*(B-A)+B); }
size(%s);
""".strip()

ARITHMETIC_OPERATORS = {"plus": "+", "minus": "-", "mult": "*", "divide": "/"}


class Op:
    exp: T_TOKEN

    def _join_exp(self, exp: T_TOKEN, join_str: str) -> str:
        return join_str.join(self._emit_exp(e) for e in exp)

    def _emit_exp(self, exp: T_TOKEN) -> str:
        if not isinstance(exp, list):
            return exp
        if "," in exp:
            return f"({self._join_exp(exp, ' ')})"
        head, *tail = exp
        if not tail:
            return self._emit_exp(head) if isinstance(head, list) else head
        elif tail[0] in ["--", "..", "^^"]:
            return self._join_exp(exp, ", ")
        elif (binop := ARITHMETIC_OPERATORS.get(str(head))) is not None:
            return "(" + self._join_exp(tail, binop) + ")"
        else:
            return f"{head}({self._join_exp(tail, ', ')})"

    def emit_exp(self) -> str:
        res = self._join_exp(self.exp, "*")
        for j in ["--", "..", "^^"]:
            res = res.replace(f", {j}, ", j)
        return res

    def emit(self) -> str:
        raise Exception("Operation not recognized")

    def post_emit(self):
        return None


class Blank(Op):
    def emit(self):
        return ""


class DirectCommand(Op):
    def __init__(self, exp: str):
        self.exp = exp

    def emit(self):
        return self.exp

    def post_emit(self):
        return None


class Point(Op):
    def __init__(
        self,
        name: str,
        exp: T_TOKEN,
        dot: bool = True,
        label: bool = True,
        direction: str = "",
    ):
        self.name = name
        self.exp = exp
        self.dot = dot
        self.label = name if label is True else None
        if self.label:
            self.label = self.label.replace("_prime", "'")
            self.label = self.label.replace("_asterisk", r"^{\ast}")
        self.direction = direction or f"dir({name})"

    def emit(self) -> str:
        return f"pair {self.name} = {self.emit_exp()};"

    def post_emit(self):
        args = [self.name]
        if self.label:
            args = [f'"${self.label}$"', *args, self.direction]
        if self.dot:
            return f"dot({', '.join(args)});"
        if len(args) > 1:
            return f"label({', '.join(args)});"
        return ""


class Draw(Op):
    def __init__(
        self,
        exp: T_TOKEN,
        fill: str | None = None,
        outline: str | None = None,
    ):
        self.exp = exp
        self.fill = fill
        self.outline = outline

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
    def __init__(self, soft_label: str | None = None, **_: Any):
        self.soft_label = soft_label
        self.alias_map = {"": "dl", ":": "", ".": "d", ";": "l"}
        if self.soft_label:
            self.alias_map |= {"": "l", ";": "dl"}
        self.aliases = self.alias_map.keys() | self.alias_map.values()

    def tokenize(self, line: str) -> list[T_TOKEN]:
        line = line.strip() + " "
        for old, new in [
            # ~ and = are separate tokens
            ("~", " ~ "),
            ("=", " = "),
            # for tsqx syntax processing
            ("(", "( "),
            (")", " ) "),
            (",", " , "),
            # spline joiners
            ("--", " --  "),
            ("..", " .. "),
            ("^^", " ^^ "),
            # no spaces around asymptote arithmetic
            (" +", "+"),
            ("+ ", "+"),
            ("- ", "-"),
            (" *", "*"),
            ("* ", "*"),
            # but slashes in draw ops should remain tokens
            (" / ", "  /  "),
            (" /", "/"),
            ("/ ", "/"),
            # ' not allowed in variable names
            ("'", "_prime"),
            ("&", "_asterisk"),
        ]:
            line = line.replace(old, new)
        return list(filter(None, line.split()))

    def parse_subexp(
        self,
        tokens: list[T_TOKEN],
        idx: int,
        func_mode=False,
    ) -> tuple[T_TOKEN, int]:
        token = tokens[idx]
        if token[-1] == "(":
            is_func = len(token) > 1
            res: list[T_TOKEN] = []
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

    def parse_exp(self, tokens: list[T_TOKEN]):
        if tokens[0][-1] != "(" or tokens[-1] != ")":
            tokens = ["(", *tokens, ")"]
        res: list[T_TOKEN] = []
        idx = 0
        while idx != len(tokens):
            try:
                exp, idx = self.parse_subexp(tokens, idx)
                res.append(list(filter(None, exp)))
            except IndexError:
                raise SyntaxError(f"Unexpected end of line: {tokens}")
        return res

    def parse_special(
        self,
        tokens: list[T_TOKEN],
        comment: str,
    ) -> Generator[T_OPSTRUCT, None, None]:
        if not tokens:
            raise SyntaxError("Can't parse special command")
        head, *tail = tokens
        if comment != "":
            yield {"op": Blank(), "comment": comment}
        if head in ["triangle", "regular"]:
            for name, exp in zip(tail, generate_points(head, len(tail))):
                assert isinstance(name, str)
                yield {"op": Point(name, [exp]), "comment": f"via ~{head}"}
            return
        else:
            raise SyntaxError(f"Special command {head} not recognized")

    def parse_name(self, tokens: list[T_TOKEN]) -> tuple[str, dict[str, Any]]:
        if not tokens:
            raise SyntaxError("Can't parse point name")
        name, *rest = tokens
        assert isinstance(name, str)

        if rest and rest[-1] in self.aliases:
            *rest, opts = rest
            assert isinstance(opts, str)
        else:
            opts = ""
        opts = self.alias_map.get(opts, opts)
        options = {
            "dot": "d" in opts,
            "label": "l" in opts,
            "direction": f"dir({name})",  # default direction
        }

        if rest:
            dirs, *rest = rest
            assert isinstance(dirs, str)
            if m := re.fullmatch(r"([\d\.]+)R([\d\.]+)", dirs):
                options["direction"] = f"{m.groups()[0]}*dir({m.groups()[1]})"
            elif dir_pairs := re.findall(r"(\d+)([A-Z]+)", dirs):
                options["direction"] = "+".join(f"{n}*plain.{w}" for n, w in dir_pairs)
            elif dirs.isdigit():
                options["direction"] = f"dir({dirs})"
            elif re.fullmatch(r"N?S?E?W?", dirs):
                options["direction"] = f"plain.{dirs}"
            else:
                rest.append(dirs)

        if rest:
            raise SyntaxError("Can't parse point name")
        return name, options

    def parse_draw(self, tokens: list[T_TOKEN]):
        try:
            idx = tokens.index("/")
        except ValueError:
            fill_: list[T_TOKEN] = []
            outline_ = tokens
        else:
            fill_ = tokens[:idx]
            outline_ = tokens[idx + 1 :]

        assert all(isinstance(_, str) for _ in outline_)
        outline: list[str] = [
            str(_) for _ in outline_
        ]  # this is idiotic, what did i miss?

        fill: list[str] = []
        for pen in fill_:
            assert isinstance(pen, str)
            if re.fullmatch(r"\d*\.?\d*", pen):
                fill.append(f"opacity({pen})")
            else:
                fill.append(pen)

        return {"fill": "+".join(fill), "outline": "+".join(outline)}

    def parse(self, line: str) -> Generator[T_OPSTRUCT, None, None]:
        # escape sequence
        if line.startswith("!"):
            yield {
                "op": DirectCommand(line[1:].strip()),
                "comment": "",
            }
            return

        if "#" in line:
            line, comment = line.split("#", 1)
        else:
            comment = ""
        tokens = self.tokenize(line)
        if not tokens:
            yield {"op": Blank(), "comment": comment}
            return
        # special
        if tokens[0] == "~":
            yield from self.parse_special(tokens[1:], comment)
            return
        # point
        try:
            idx = tokens.index("=")
            name, options = self.parse_name(tokens[:idx])
            exp = self.parse_exp(tokens[idx + 1 :])
            yield {
                "op": Point(name, exp, **options),
                "comment": comment,
            }
            return
        except ValueError:
            pass
        # draw with options
        try:
            idx = tokens.index("/")
            exp = self.parse_exp(tokens[:idx])
            options = self.parse_draw(tokens[idx + 1 :])
            yield {"op": Draw(exp, **options), "comment": comment}
            return
        except ValueError:
            pass
        # draw without options
        exp = self.parse_exp(tokens)
        yield {"op": Draw(exp), "comment": comment}
        return


class Emitter:
    def __init__(
        self,
        lines: TextIOWrapper | TextIO,
        **args: Any,
    ):
        self.lines = lines
        self.preamble = args.get("preamble", False)
        self.size = args.get("size", "8cm")
        self.parser = Parser(**args)
        self.terse = args.get("terse", False)

    def emit(self):
        if self.preamble:
            print(GENERIC_PREAMBLE % self.size)

        original_raw = ""
        op_structs = []
        for line in self.lines:
            original_raw += line
            for op_struct in self.parser.parse(line):
                op_structs.append(op_struct)

        for op_struct in op_structs:
            print(
                (
                    op_struct["op"].emit()
                    + (f" // {c}" if (c := op_struct["comment"].rstrip()) else "")
                ).strip()
            )
        print()

        for op_struct in op_structs:
            if out := op_struct["op"].post_emit():
                print(out)

        if not self.terse:
            print("")
            print(r"/* --------------------------------+")
            print(r"| TSQX: by CJ Quines and Evan Chen |")
            print(r"| https://github.com/vEnhance/tsqx |")
            print(r"+----------------------------------+")
            print(original_raw.strip())
            print("*/")


def main():
    from argparse import ArgumentParser

    argparser = ArgumentParser(description="Generate Asymptote code.")
    argparser.add_argument(
        "-p",
        "--pre",
        help="Adds a preamble.",
        action="store_true",
        dest="preamble",
        default=False,
    )
    argparser.add_argument(
        "fname",
        help="Read from file rather than stdin.",
        metavar="filename",
        nargs="?",
        default="",
    )
    argparser.add_argument(
        "-s",
        "--size",
        help="Set image size in preamble.",
        action="store",
        dest="size",
        default="8cm",
    )
    argparser.add_argument(
        "-b",
        "--soft-label",
        help="Don't draw dots on points by default.",
        action="store_true",
        dest="soft_label",
        default=False,
    )
    argparser.add_argument(
        "-t",
        "--terse",
        help="Hide the advertisement and orig source",
        action="store_true",
        dest="terse",
        default=False,
    )

    args = argparser.parse_args()
    stream = open(args.fname, "r") if args.fname else sys.stdin
    emitter = Emitter(stream, **vars(args))
    emitter.emit()


if __name__ == "__main__":
    main()

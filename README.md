# TSQX

[Asymptote](https://www.artofproblemsolving.com/wiki/index.php/Asymptote_(Vector_Graphics_Language)) preprocessor, based on [TSQ](https://github.com/vEnhance/dotfiles/blob/main/py-scripts/tsq.py). Sample:

```
~triangle A B C
D = foot A B C
E = midpoint A--B
F = extension A D C E

A--B--C--cycle 0.2 lightblue / black
A--D
C--E
B--F dashed blue
```

![Sample TSQX diagram](http://i.imgur.com/JxLfxxh.png)

## Usage

Run ```python3 tsqx.py filename.txt > filename.asy```; see extra arguments in the file itself.

[Here](https://github.com/cjquines/tsqx/wiki/Documentation) is a working draft for the documentation of TSQX.

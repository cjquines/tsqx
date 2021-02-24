# TSQX

[Asymptote](https://www.artofproblemsolving.com/wiki/index.php/Asymptote_(Vector_Graphics_Language)) preprocessor, based on [TSQ](https://github.com/vEnhance/dotfiles/blob/main/py-scripts/tsq.py). Sample:

```
~triangle A B C
D := foot A B C
E .= midpoint A--B
F ;= extension A (foot A B C) C E

A--B--C--cycle / black
circle A B C / 0.2 lightblue /
A--D
C--E
B--F / dashed blue
```

<!-- ![Sample TSQX diagram](http://i.imgur.com/JxLfxxh.png) replace with generatede code / actual diagram -->

## Usage

Run ```python3 tsqx.py filename.txt > filename.asy```. See [wiki](https://github.com/cjquines/tsqx/wiki/Documentation) for more info.

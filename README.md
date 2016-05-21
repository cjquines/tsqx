# TSQX

Asymptote preprocessor, based on Evan Chen’s TSQ.

### Wait, what?

[Asymptote](https://www.artofproblemsolving.com/wiki/index.php/Asymptote_(Vector_Graphics_Language)) is a vector graphics language. Lots of people use it to make diagrams for geometry problems. It works by a making a diagram from code. [TSQ](https://github.com/vEnhance/dotfiles/blob/master/py-scripts/tsq.py) is an Asymptote preprocessor created by Evan Chen – it’s used to make Asymptote code easier to write and neater to look at. And TSQX is an extension of TSQ, which I made because I thought TSQ was a nice idea, and it can be made even better! Check how easy it is to make a diagram in TSQX:

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

### How do I install TSQX?

To start off, you need to have a [Python 2.7 installation](https://www.python.org/downloads/) on your machine. You need an [Asymptote](https://www.artofproblemsolving.com/wiki/index.php/Asymptote_(Vector_Graphics_Language)) installation if you want to be able to view the diagrams. Save your TSQX code to any plain text file, making sure that ```tsqx.py``` is in the same folder, and then run ```python tsqx.py filename.txt > filename.asy``` on the command line. After that, you can either include ```filename.asy``` on a TeX file, or just do ```asy filename.asy``` directly on the command line to generate your diagram.

### How do I use TSQX?

(I'm going to write docs for using TSQX, do remind me to do that.)

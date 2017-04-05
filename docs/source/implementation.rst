.. _design:
.. _designing_the_language:

Implementation of the Language
==============================

Let's recap how does the language looks like:

::

  Hello {{ first_name }},
  {% if last_name %}
    {{ last_name }}
  {% elif title %}
    {{ title }}
  {% else %}
    Doe
  {% /if %}!

  Here is the list of stuff I like:

  {% loop stuff %}
      - {{ item.key }} (because of {{ item.value }})
  {% /loop %}


The main goal of Curly is to make a little toy template language with
a limited set of abilities just to show an idea of how to build such
stuff. It has to be as simple as possible:

#. User who knows nothing about lexing and parsing, LALR, LR, LL and
   other stuff from compiler and language processing theory.

   I, for example, have no big practical experience in implementation of
   such things (university maybe but not that much) but know how to work
   with regular expressions very well. For my point of view, this is a
   minimal prerequisite for understanding of Curly implementation.

#. No formal grammar. Formal grammar rocks but people from point 1
   do not know them. My idea was to avoid formal grammar as much as
   possible: this could make parser complex. Anyway, we want to implement
   everything from scratch (except of regular expressions) and to
   understand how parser work, you do not need formal grammars to catch
   the ideas.

#. I want to give a tech talks on that and I am pretty limited in time
   of such talks. I want to cover all aspects and show all crucial parts
   in ~30 minutes. No way I would explain EBNFs and LR(0) stuff.

   Seriously, all that are simply names. I want to show an idea. Title
   ideas after, but do not produce yet another monads.

So, let's pretend that no theory is created and our compilers and
interpreters were delivered by UFOs or found in Maya tombs. How would
you implement such template language?


Text Interpretation
+++++++++++++++++++

Let's consider our templater as a black box. Input - the text, template.
Output - something which can render required text (insert stuff from
given context, loop where necessary, manage conditionals). Well, here
are several ways on how to do that but any way involves recognizing of
controlling patterns like interpretation of ``{{ tags }}`` and various
``{% block constructions %}``.

The most straightforward implementation are going layers: a product of
bottom layer is an input of the top layer. And each layer goes in more
concrete abstractions till we get something evaluable.

This implementation proposes 3 layers:

#. Lexing
#. Parsing
#. Evaluation


Lexing
++++++

The main idea of the lexing is to split raw unstructured text into
defined typed chunks, a parts. This separation is context free, does not
imply any semantics analysis. It just splits.

Let's check the text we are going to process again:

.. image:: /images/dtl-raw-template.png

We have a print statements here, if and loops. So we have a mix of
template own statements and expressions along with literal text we need
to output as is. Curly interprets them as a tokens. Yes, whole blocks
like ``{{ first_name }}``. Why does it do it in this way? Well, more
granular tokenization like ``{{`` leads to more complex parser and I
cannot explain whole template engine in 30-40 minutes. Therefore we have
to go barbarian even if it could drive nuts someone.

Let's consider literal token as a blue color; print statement as an
orange one. Open block tag would be green and close - red. In that case,
we could get the following picture.

.. image:: /images/dtl-hl-tokens.png

This is a structure of out text: literal, print, if start block, literal
(yes, whitespaces), print and so on. Our raw text can be split into a
list of chunks (we can use words *token stream* to define that list).

Let's split it. If you are hurry to implement regular expressions to
parse such *tokens* you almost immediately face with problem that
regular expression for literal text is quite hard to write correctly.
You can do some tricks with ordering but I would suggest you to...
refuse to implement regular expressions for literal text at all. This
leads to the most simple lexer you can implement. But let's get back to
lexing (remember: we do not implement any expressions for literal text!)

How to extract ``{{ first_name }}`` from the text? ``{% function
expression %}``? Well, let's define *expression* and *function*
first. Function (``if``, ``loop`` etc) can use following regexp:
:regexp:`[a-zA-Z0-9_-]+`. Expression may have spaces between words
and may have some escape symbols (if we want ``{`` to be the part
of expression, then we need to escape it with ``\``: ``\{``). So,
expression is :regexp:`(?:\\\\.|[^\\{\\}])+`.

Nice, now let's define our print statement. Print statement
is an ``{{ expression }}`` but we want to be liberal on
whitespaces near braces so :regexp:`{{\\s*([a-zA-Z0-9_-]+)\\s*}}`.
Implementing regular expressions for all possible tokens,
we can construct big regular expression for tokenization:

::

  (?P<print>{{\\s*([a-zA-Z0-9_-]+)\\s*}})|(?P<start_block>...)|(?P<end_block>...)...

Now, to do lexing, we must go through all text extracting one
non-overlapping pattern match by another till we get all tokens.

Nice, what about literal tokens? Let's get back to out text. Let's
pretend that red box is a match we are working with.

.. image:: /images/dtl-hl-match1.png

From the start, we've jumped to ``{{ first_name }}`` skipping the
literal. To obtain literal, we need just to take text from position 0
till the match start: this would be out literal.

Let's generalize this idea a little bit more. Considering
green box as a previous match and red box as a current
one, we can extract skipped literal text just as a
``text[position_of_previous_match_end:position_of_current_match_start]``.

.. image:: /images/dtl-hl-match2.png

We've almost done. Last leftover is how to extract ``And that
is all!`` piece of text (matching has to be stopped and ``{%
/loop %}``) block. This is simple: our leftover literal is
``text[position_of_previous_match_end:end_of_the_text]``.

After that procedure, we will get following stream of tokens:

.. image:: /images/dtl-tokens.png

.. note::

  To save a screen space, token stream is represented as a stack.
  Start is on the top of the stack, finish - at the bottom.


Parsing
+++++++

.. _design:
.. _designing_the_language:

Designing the language
======================

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


Lexing and parsing
++++++++++++++++++

Let's consider our templater as a black box. Input - the text, template.
Output - something which can render required text (insert stuff from
given context, loop where necessary, manage conditionals)

TODO: Finish that article

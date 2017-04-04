Welcome to curly's documentation!
=================================

:abbr:`Curly (also abbreviated as {urly)` is a toy templating language
with a single goal: to show how to implement template languages. It
has minimal practical set of actions which allows to tell about its
usefulness. It is fine: features are not the goal, but simplicity and
clearness of implementation are.

`Jinja2 <http://jinja.pocoo.org>`_ and `Mako
<http://makotemplates.org>`_ laughs over Curly: from the point of view
of these template languages, Curly is a dumb and rigid. As a language
it is close to `Mustache <http://mustache.github.io>`_ and `Handlebars
<http://handlebarsjs.com>`_, but these minimal languages have even more
features than Curly. Yes, they are. Reference implementation of Curly
has no even primitive if/else constuctions (only ifs).

Here is a full example of the supported language features:

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

  And that is all!


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   design
   api/index


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

# curly

[![Build Status](https://travis-ci.org/9seconds/curly.svg?branch=master)](https://travis-ci.org/9seconds/curly) [![codecov](https://codecov.io/gh/9seconds/curly/branch/master/graph/badge.svg)](https://codecov.io/gh/9seconds/curly)

An example of the minimal template engine, mostly to show an idea how to
implement such stuff.

```
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
```

* [Official website](https://9seconds.github.io/curly/)
* [Documentation](https://curly.readthedocs.io)

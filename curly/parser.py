# -*- coding: utf-8 -*-
"""Parser has another main Curly's function, :py:func:`parse`.

The main idea of parsing is to take a stream of
tokens and convert it into `abstract syntax tree
<https://en.wikipedia.org/wiki/Abstract_syntax_tree>`_. Each node in the
tree is present by :py:class:`Node` instances and each instance has a
list of nodes (therefore - tree).

:py:func:`parse` produces such tree and it is possible to render it with
method :py:meth:`Node.process`.

Example:

.. code-block:: python3

  >>> from curly.lexer import tokenize
  >>> from curly.parser import parse
  >>> text = '''\\
  ...     Hello! My name is {{ name }}.\\
  ... {% if likes %}And I like these things: {% loop likes %}\\
  ... {{ item }},{% /loop %}{% /if %}'''
  >>> tokens = tokenize(text)
  >>> print(repr(parse(tokens)))
  [{'done': True,
   'nodes': [],
   'raw_string': "<LiteralToken(raw='    Hello! My name is ', contents={\
'text': "
                 "'    Hello! My name is '})>",
   'text': '    Hello! My name is ',
   'type': 'LiteralNode'},
   {'done': True,
   'expression': ['name'],
   'nodes': [],
   'raw_string': "<PrintToken(raw='{{ name }}', contents={'expression': "
                 "['name']})>",
   'type': 'PrintNode'},
   {'done': True,
   'nodes': [],
   'raw_string': "<LiteralToken(raw='.', contents={'text': '.'})>",
   'text': '.',
   'type': 'LiteralNode'},
   {'done': True,
   'else': {},
   'expression': ['likes'],
   'nodes': [{'done': True,
              'nodes': [],
              'raw_string': "<LiteralToken(raw='And I like these things: ', "
                            "contents={'text': 'And I like these things: '})>",
              'text': 'And I like these things: ',
              'type': 'LiteralNode'},
             {'done': True,
              'expression': ['likes'],
              'nodes': [{'done': True,
                         'expression': ['item'],
                         'nodes': [],
                         'raw_string': "<PrintToken(raw='{{ item }}', "
                                       "contents={'expression': ['item']})>",
                         'type': 'PrintNode'},
                        {'done': True,
                         'nodes': [],
                         'raw_string': "<LiteralToken(raw=',', contents=\
{'text': "
                                       "','})>",
                         'text': ',',
                         'type': 'LiteralNode'}],
              'raw_string': "<StartBlockToken(raw='{% loop likes %}', "
                            "contents={'expression': ['likes'], 'function': "
                            "'loop'})>",
              'type': 'LoopNode'}],
   'raw_string': "<StartBlockToken(raw='{% if likes %}', contents=\
{'expression': "
                 "['likes'], 'function': 'if'})>",
   'type': 'IfNode'}]
"""


import collections
import pprint
import subprocess

from curly import exceptions
from curly import lexer
from curly import utils


class ExpressionMixin:
    """A small helper mixin for :py:class:`Node` which adds
    expression related methods.
    """

    @property
    def expression(self):
        """*expression* from underlying token."""
        return self.token.contents["expression"]

    def evaluate_expression(self, context):
        """Evaluate *expression* in given context.

        :param dict context: Variables for template rendering.
        :return: Evaluated expression.
        """
        value = subprocess.list2cmdline(self.expression)
        value = utils.resolve_variable(value, context)

        return value


class Node(collections.UserList):
    """Node of an AST tree.

    It has 2 methods for rendering of the node content:
    :py:meth:`Node.emit` and :py:meth:`Node.process`. First one
    is the generator over the rendered content, second one just
    concatenates them into a single string. So, if you defines your
    own node type, you want to define :py:meth:`Noed.emit` only,
    :py:meth:`Node.process` stays the same.

    If you want to render template to the string, use
    :py:meth:`Node.process`. This is a thing you are looking for.

    :param token: Token which produced that node.
    :type token: :py:class:`curly.lexer.Token`
    """

    def __init__(self, token):
        super().__init__()
        self.token = token
        self.done = False

    def __str__(self):
        return ("<{0.__class__.__name__}(done={0.done}, token={0.token!r}, "
                "data={0.data!r})>").format(self)

    def __repr__(self):
        return pprint.pformat(self._repr_rec())

    def _repr_rec(self):
        return {
            "raw_string": repr(self.token) if self.token else "",
            "type": self.__class__.__name__,
            "done": self.done,
            "nodes": [node._repr_rec() for node in self.data]}

    @property
    def raw_string(self):
        """Raw content of the related token.

        For example, for token ``{{ var }}`` it returns literally ``{{
        var }}``.
        """
        return self.token.raw_string

    def process(self, context):
        """Return rendered content of the node as a string.

        :param dict context: Dictionary with a context variables.
        :return: Rendered template
        :rtype: str
        """
        return "".join(self.emit(context))

    def emit(self, context):
        """Return generator which emits rendered chunks of text.

        Axiom: ``"".join(self.emit(context)) == self.process(context)``

        :param dict context: Dictionary with a context variables.
        :return: Generator with rendered texts.
        :rtype: Generator[str]
        """
        for node in self:
            yield from node.emit(context)


class RootNode(Node):
    """Node class for the most top-level node, root.

    :param list[Node] nodes: Nodes for root.
    """

    def __init__(self, nodes):
        super().__init__(None)
        self.data = nodes
        self.done = True

    def __repr__(self):
        return pprint.pformat(self.data)


class LiteralNode(Node):
    """Node which presents literal text.

    This is one-to-one representation of
    :py:class:`curly.lexer.LiteralToken` in AST tree.

    :param token: Token which produced that node.
    :type token: :py:class:`curly.lexer.LiteralToken`
    """

    def __init__(self, token):
        super().__init__(token)
        self.done = True

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["text"] = self.text

        return struct

    @property
    def text(self):
        """Rendered text."""
        return self.token.contents["text"]

    def emit(self, _):
        yield self.text


class PrintNode(ExpressionMixin, Node):
    """Node which presents print token.

    This is one-to-one representation of
    :py:class:`curly.lexer.PrintToken` in AST tree. Example of such node
    is the node for ``{{ var }}`` token.

    :param token: Token which produced that node.
    :type token: :py:class:`curly.lexer.PrintToken`
    """

    def __init__(self, token):
        super().__init__(token)
        self.done = True

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["expression"] = self.expression

        return struct

    def emit(self, context):
        yield str(self.evaluate_expression(context))


class BlockTagNode(ExpressionMixin, Node):
    """Node which presents block tag token.

    Block tag example: ``{% if something %}``. This, with ``{%`` stuff.

    This is one-to-one representation of
    :py:class:`curly.lexer.StartBlockToken` token.
    """

    @property
    def function(self):
        """*function* from underlying token."""
        return self.token.contents["function"]


class ConditionalNode(BlockTagNode):
    """Node which represent condition.

    This is a not real node in AST tree, this is a preliminary node
    which should be popped on closing and be replaced by actual
    :py:class:`IfNode`.

    Such fictional node is required to simplify logic of parsing
    for if/elif/elif/else blocks. If conditions are nested, we
    need to identify the groups of conditional flows and attach
    :py:class:`IfNode` and :py:class:`ElseNode` for correct parents.

    :param token: Token, which starts to produce that node. Basically,
        it is a first token from the ``if`` block.
    :type token: :py:class:`curly.lexer.BlockTagNode`
    """

    def __init__(self, token):
        super().__init__(token)
        self.ifnode = None

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["if"] = self.ifnode._repr_rec() if self.ifnode else {}

        return struct

    def emit(self, context):
        return self.ifnode.emit(context)


class IfNode(BlockTagNode):
    """Node which represents ``if`` statement. And ``elif``.

    Actually, since we have :py:class:`ConditionalNode`, it is possible
    to use only 1 node type for ifs. Here is why:

    .. code-block:: json

        {
            "conditional": [
                {
                    "if": "expression1",
                    "nodes": []
                },
                {
                    "if": "expression2",
                    "nodes": []
                },
                {
                    "else": "",
                    "nodes": []
                }
            ]
        }

    Here is an idea how does ``if``/``elif``/``else`` looks like with
    conditional You have a list of :py:class:`IfNode` instances and one
    (optional) :py:class:`ElseNode` at the end. So if first ``if`` does
    not match, you go to the next one. If it is ``true``, emit its nodes
    and exit ``conditional``.
    """

    def __init__(self, token):
        super().__init__(token)
        self.elsenode = None

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["else"] = self.elsenode._repr_rec() if self.elsenode else {}
        struct["expression"] = self.expression

        return struct

    def emit(self, context):
        if self.evaluate_expression(context):
            yield from super().emit(context)
        elif self.elsenode:
            yield from self.elsenode.emit(context)


class ElseNode(BlockTagNode):
    """Node which represents ``else`` statement.

    For idea how it works, please check description of
    :py:class:`IfNode`.
    """


class LoopNode(BlockTagNode):
    """Node which represents ``loop`` statement.

    This node repeats its content as much times as elements found in its
    evaluated expression. Every iteration it injects ``item`` variable
    into the context (incoming context is safe and untouched).

    For dicts, it emits `{"key": k, "value": v}` where ``k`` and ``v``
    are taken from ``expression.items()``. For any other iterable
    it emits item as is.
    """

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["expression"] = self.expression

        return struct

    def emit(self, context):
        resolved = self.evaluate_expression(context)
        context_copy = context.copy()

        if isinstance(resolved, dict):
            for key, value in sorted(resolved.items()):
                context_copy["item"] = {"key": key, "value": value}
                yield from super().emit(context_copy)
        else:
            for item in resolved:
                context_copy["item"] = item
                yield from super().emit(context_copy)


def parse(tokens):
    """One of the main functions (see also :py:func:`curly.lexer.tokenize`).

    The idea of parsing is simple: we have a flow of well defined tokens
    taken from :py:func:`curly.lexer.tokenize` and now we need to build
    `AST tree <https://en.wikipedia.org/wiki/Abstract_syntax_tree>`_
    from them.

    Curly does that maintaining a single stack. There could be different
    implementations, some of them more efficient, but we are using
    single stack implementation because it is most obvious way of
    representing and idea on current scale of the template language. If
    you decide to fork one day, please consider other options.

    Please read following stuff before (at least Wikipedia articles):

    * https://en.wikipedia.org/wiki/Shift-reduce_parser
    * https://en.wikipedia.org/wiki/LR_parser
    * https://en.wikipedia.org/wiki/Shunting-yard_algorithm
    * https://en.wikipedia.org/wiki/Operator-precedence_parser
    * http://blog.reverberate.org/2013/09/\
ll-and-lr-in-context-why-parsing-tools.html
    * http://blog.reverberate.org/2013/07/ll-and-lr-parsing-demystified.html

    Current implementation is *LR(0)* parser. Feel free to compose
    formal grammar if you want (:py:class:`curly.lexer.LiteralToken`
    is terminal, everything except of it - non terminal). I am going
    to describe just a main idea in a simple words pretendind that no
    theory was created before.

    Now, algorithm.

    #. Read from the Left (look, ma! *L* from *LR*!) of stream,
       without returning back. This allow us to use ``tokens`` as
       an iterator.
    #. For any token, check its class and call corresponding function
       which manages it.

       .. list-table::
         :header-rows: 1

         * - Token type
           - Parsing function
         * - :py:class:`curly.lexer.LiteralToken`
           - :py:func:`parse_literal_token`
         * - :py:class:`curly.lexer.PrintToken`
           - :py:func:`parse_print_token`
         * - :py:class:`curly.lexer.StartBlockToken`
           - :py:func:`parse_start_block_token`
         * - :py:class:`curly.lexer.EndBlockToken`
           - :py:func:`parse_end_block_token`

    #. After all tokens are consumed, check that all nodes in the
       stack are done (``done`` attribute) and build resulting
       :py:class:`RootNode` instance.

    The main idea is to maintain stack. Stack is a list of the
    children for the root node. We read a token by token and put
    corresponding nodes into stack. Each node has 2 states: done or
    not done. Done means that node is ready and processed, not
    done means that further squashing will be performed when
    corresponding terminating token will come to the parser.

    So, let's assume that we have a following list of tokens (stack on
    the left, incoming tokens on the right. Top of the token stream is
    the same one which is going to be consumed).

    Some notation: exclamation mark before a node means that node is
    finished; it means that it is ready to participate into rendering,
    finalized.

    ::

      |                     |        |    LiteralToken             |
      |                     |        |    StackBlockToken(if)      |
      |                     |        |    PrintToken               |
      |                     |        |    StartBlockToken(elif)    |
      |                     |        |    StartBlockToken(loop)    |
      |                     |        |    PrintToken               |
      |                     |        |    EndBlockToken(loop)      |
      |                     |        |    EndBlockToken(if)        |

    Read ``LiteralToken``. It is fine as is, so wrap it into
    :py:class:`LiteralNode` and put it into stack.

    ::

      |                     |        |                             |
      |                     |        |    StackBlockToken(if)      |
      |                     |        |    PrintToken               |
      |                     |        |    StartBlockToken(elif)    |
      |                     |        |    StartBlockToken(loop)    |
      |                     |        |    PrintToken               |
      |                     |        |    EndBlockToken(loop)      |
      |    !LiteralNode     |        |    EndBlockToken(if)        |

    And now it is a time for :py:class:`curly.lexer.StartBlockToken`.
    A kind remember, this is a start tag of ``{% function expression
    %}...{% /function %}`` construction. The story about such tag is
    that it has another tokens it encloses. So other tokens has to
    be subnodes of related node. This would be done of reduce phase
    described in a few paragraphs below but right now pay attention to
    ``done`` attribute of the node: if it is ``False`` it means that we
    still try to collect all contents of this block subnodes. ``True``
    means that node is finished.

    Function of this token is ``if`` so we need to add
    :py:class:`ConditionalNode` as a marker of the closure and the first
    :py:class:`IfNode` in this enclosement.

    ::

      |                         |        |                             |
      |                         |        |                             |
      |                         |        |    PrintToken               |
      |                         |        |    StartBlockToken(elif)    |
      |                         |        |    StartBlockToken(loop)    |
      |     IfNode              |        |    PrintToken               |
      |     ConditionalNode     |        |    EndBlockToken(loop)      |
      |    !LiteralNode         |        |    EndBlockToken(if)        |

    The upcoming :py:class:`curly.lexer.PrintToken` is a single
    functional node: to emit rendered template, we need to resolve
    its *expression* in given context. This is one finished node
    :py:class:`PrintNode`.

    ::

      |                         |        |                             |
      |                         |        |                             |
      |                         |        |                             |
      |                         |        |    StartBlockToken(elif)    |
      |    !PrintNode           |        |    StartBlockToken(loop)    |
      |     IfNode              |        |    PrintToken               |
      |     ConditionalNode     |        |    EndBlockToken(loop)      |
      |    !LiteralNode         |        |    EndBlockToken(if)        |

    Now it is a time for next :py:class:`curly.lexer.StartBlockToken`
    which is responsible for ``{% elif %}``. It means, that
    scope of first, initial ``if`` is completed, but not for
    corresponding :py:class:`ConditionalNode`! Anyway, we can
    safely add :py:class:`PrintNode` from the top of the stack to
    nodelist of :py:class:`IfNode`. To do so, we pop stack till that
    :py:class:`IfNode` and add popped content to the nodelist. After
    that, we can finally mark :py:class:`IfNode` as done.

    ::

      |                         |        |                             |
      |                         |        |                             |
      |                         |        |                             |
      |                         |        |    StartBlockToken(elif)    |
      |                         |        |    StartBlockToken(loop)    |
      |    !IfNode(!PrintNode)  |        |    PrintToken               |
      |     ConditionalNode     |        |    EndBlockToken(loop)      |
      |    !LiteralNode         |        |    EndBlockToken(if)        |

    Stack was rewinded and we can add new :py:class:`IfNode` to
    condition.

    ::

      |                         |        |                             |
      |                         |        |                             |
      |                         |        |                             |
      |                         |        |                             |
      |     IfNode              |        |    StartBlockToken(loop)    |
      |    !IfNode(!PrintNode)  |        |    PrintToken               |
      |     ConditionalNode     |        |    EndBlockToken(loop)      |
      |    !LiteralNode         |        |    EndBlockToken(if)        |

    Next token is a loop (``{% loop items %}``). The same story as with
    :py:class:`IfNode`: emit :py:class:`LoopNode` to the top of the
    stack.

    ::

      |                         |        |                             |
      |                         |        |                             |
      |                         |        |                             |
      |     LoopNode            |        |                             |
      |     IfNode              |        |                             |
      |    !IfNode(!PrintNode)  |        |    PrintToken               |
      |     ConditionalNode     |        |    EndBlockToken(loop)      |
      |    !LiteralNode         |        |    EndBlockToken(if)        |

    Add :py:class:`curly.lexer.PrintToken` as a :py:class:`PrintNode`.

    ::

      |                         |        |                             |
      |                         |        |                             |
      |     PrintToken          |        |                             |
      |     LoopNode            |        |                             |
      |     IfNode              |        |                             |
      |    !IfNode(!PrintNode)  |        |                             |
      |     ConditionalNode     |        |    EndBlockToken(loop)      |
      |    !LiteralNode         |        |    EndBlockToken(if)        |

    Next token is :py:class:`curly.lexer.EndBlockToken` for the loop
    ( ``{% /loop %}``). So we can rewind the stack to the loop node,
    putting all popped nodes as a nodelist for :py:class:`LoopNode`.

    ::

      |                           |        |                             |
      |                           |        |                             |
      |                           |        |                             |
      |    !LoopNode(!PrintNode)  |        |                             |
      |     IfNode                |        |                             |
      |    !IfNode(!PrintNode)    |        |                             |
      |     ConditionalNode       |        |                             |
      |    !LiteralNode           |        |    EndBlockToken(if)        |

    And it is a time for :py:class:`curly.lexer.EndBlockToken` for
    ``if`` (``{% /if %}``). Now we need to rewind stack twice. First
    rewind is to complete :py:class:`IfNode` which is almost on the top
    of the stack.

    ::

      |                             |        |                             |
      |                             |        |                             |
      |                             |        |                             |
      |    !LoopNode(!PrintNode)    |        |                             |
      |    !IfNode(!LoopNode(...))  |        |                             |
      |    !IfNode(!PrintNode)      |        |                             |
      |     ConditionalNode         |        |                             |
      |    !LiteralNode             |        |    EndBlockToken(if)        |

    And the second rewind is to finish nearest
    :py:class:`ConditionalNode`.

    ::

      |                                       |        |                     |
      |                                       |        |                     |
      |                                       |        |                     |
      |                                       |        |                     |
      |                                       |        |                     |
      |                                       |        |                     |
      |    !ConditionalNode(!IfNode,!IfNode)  |        |                     |
      |    !LiteralNode                       |        |                     |

    And that is all. Token list is empty, so it is a time to compose
    relevant :py:class:`RootNode` with the contents of the stack.

    ::

      !RootNode(!LiteralNode, !ConditionalNode(!IfNode, !IfNode))

    We've just made AST tree.

    :param token: A stream with tokens.
    :type token: Iterator[:py:class:`curly.lexer.Token`]
    :return: Parsed AST tree.
    :rtype: :py:class:`RootNode`
    :raises:
        :py:exc:`curly.exceptions.CurlyParserError`: if token is unknown.
    """
    stack = []

    for token in tokens:
        if isinstance(token, lexer.LiteralToken):
            stack = parse_literal_token(stack, token)
        elif isinstance(token, lexer.PrintToken):
            stack = parse_print_token(stack, token)
        elif isinstance(token, lexer.StartBlockToken):
            stack = parse_start_block_token(stack, token)
        elif isinstance(token, lexer.EndBlockToken):
            stack = parse_end_block_token(stack, token)
        else:
            raise exceptions.CurlyParserUnknownTokenError(token)

    root = RootNode(stack)
    validate_for_all_nodes_done(root)

    return root


def parse_literal_token(stack, token):
    """This function does parsing of :py:class:`curly.lexer.LiteralToken`.

    Since there is nothing to do with literals, it is just put
    corresponding :py:class:`LiteralNode` on the top of the stack.

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.LiteralToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    """
    stack.append(LiteralNode(token))

    return stack


def parse_print_token(stack, token):
    """This function does parsing of :py:class:`curly.lexer.PrintToken`.

    Since there is nothing to do with literals, it is just put
    corresponding :py:class:`PrintNode` on the top of the stack.

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.PrintToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    """
    stack.append(PrintNode(token))

    return stack


def parse_start_block_token(stack, token):
    """This function does parsing of :py:class:`curly.lexer.StartBlockToken`.

    Actually, since this token may have different behaviour, dependend
    on *function* from that token.

    .. list-table::
      :header-rows: 1

      * - Token function
        - Parsing function
      * - if
        - :py:func:`parse_start_if_token`
      * - elif
        - :py:func:`parse_start_elif_token`
      * - else
        - :py:func:`parse_start_else_token`
      * - loop
        - :py:func:`parse_start_loop_token`

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.StartBlockToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    :raises:
        :py:exc:`curly.exceptions.CurlyParserUnknownStartBlockError`: if
        token function is unknown.
    """
    function = token.contents["function"]

    if function == "if":
        return parse_start_if_token(stack, token)
    elif function == "elif":
        return parse_start_elif_token(stack, token)
    elif function == "else":
        return parse_start_else_token(stack, token)
    elif function == "loop":
        return parse_start_loop_token(stack, token)
    else:
        raise exceptions.CurlyParserUnknownStartBlockError(token)


def parse_end_block_token(stack, token):
    """This function does parsing of :py:class:`curly.lexer.EndBlockToken`.

    Actually, since this token may have different behaviour, dependend
    on *function* from that token.

    .. list-table::
      :header-rows: 1

      * - Token function
        - Parsing function
      * - if
        - :py:func:`parse_end_if_token`
      * - loop
        - :py:func:`parse_end_loop_token`

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.EndBlockToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    :raises:
        :py:exc:`curly.exceptions.CurlyParserUnknownEndBlockError`: if
        function of end block is unknown.
    """
    function = token.contents["function"]

    if function == "if":
        return parse_end_if_token(stack, token)
    elif function == "loop":
        return parse_end_loop_token(stack, token)
    else:
        raise exceptions.CurlyParserUnknownEndBlockError(token)


def parse_start_if_token(stack, token):
    """Parsing of token for ``{% if function expression %}``.

    It puts 2 nodes on the stack: :py:class:`ConditionalNode` and
    :py:class:`IfNode`. Checks docs for :py:func:`parse` to understand
    why.

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.StartBlockToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    """
    stack.append(ConditionalNode(token))
    stack.append(IfNode(token))

    return stack


def parse_start_elif_token(stack, token):
    """Parsing of token for ``{% elif function expression %}``.

    It rewinds stack with :py:func:`rewind_stack_for` till previous
    :py:class:`IfNode` first and appends new one. Checks docs for
    :py:func:`parse` to understand why.

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.StartBlockToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    """
    stack = rewind_stack_for(stack, search_for=IfNode)
    stack.append(IfNode(token))

    return stack


def parse_start_else_token(stack, token):
    """Parsing of token for ``{% else %}``.

    It rewinds stack with :py:func:`rewind_stack_for` till previous
    :py:class:`IfNode` first and appends new :py:class:`ElseNode`.
    Checks docs for :py:func:`parse` to understand why.

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.StartBlockToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    """
    stack = rewind_stack_for(stack, search_for=IfNode)
    stack.append(ElseNode(token))

    return stack


def parse_end_if_token(stack, token):
    """Parsing of token for ``{% /if %}``.

    Check :py:func:`parse` for details. Also, it pops out redundant
    :py:class:`ConditionalNode` and make chaining of :py:class:`IfNode`
    and :py:class:`ElseNode` verifying that there is only one possible
    else and it placed at the end.

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.EndBlockToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    """
    stack = rewind_stack_for(stack, search_for=(IfNode, ElseNode))
    stack = rewind_stack_for(stack, search_for=ConditionalNode)

    cond = stack.pop()
    previous_node, *rest_nodes = cond
    for next_node in rest_nodes:
        if isinstance(previous_node, ElseNode):
            raise ValueError(
                "If statement {0} has multiple elses".format(
                    cond[0].raw_string))
        previous_node.elsenode = next_node
        previous_node = next_node

    stack.append(cond[0])

    return stack


def parse_start_loop_token(stack, token):
    """Parsing of token for ``{% loop iterable %}``.

    Check :py:func:`parse` for details.

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.StartBlockToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    """
    stack.append(LoopNode(token))

    return stack


def parse_end_loop_token(stack, token):
    """Parsing of token for ``{% /loop %}``.

    Check :py:func:`parse` for details. Stack rewinding is performed
    with :py:func:`rewind_stack_for`.

    :param stack: Stack of the parser.
    :param token: Token to process.
    :type stack: list[:py:class:`Node`]
    :type token: :py:class:`curly.lexer.EndBlockToken`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    """
    return rewind_stack_for(stack, search_for=LoopNode)


def rewind_stack_for(stack, *, search_for):
    """Stack rewinding till some node found.

    This function performes stack reducing on parsing. Idea is quite
    simple: we pop out nodes until some not done is found. If it has a
    type of node we are looking for, we are good: it basically means
    that we've found the node which should have popped results as
    subnodes. Otherwise: exception.

    At the end of the procedure updated node is placed on the top of the
    stack.

    :param stack: Stack of the parser.
    :param search_for: Type of the node we are searching for.
    :type stack: list[:py:class:`Node`]
    :type search_for: :py:class:`Node`
    :return: Updated stack.
    :rtype: list[:py:class:`Node`]
    :raises:
        :py:exc:`curly.exceptions.CurlyParserNoUnfinishedNodeError`: if
        not possible to find open start statement.

        :py:exc:`curly.exceptions.CurlyParserUnexpectedUnfinishedNodeError`: if
        we expected to find one open statement but found another.
    """
    nodes = []
    node = None

    while stack:
        node = stack.pop()
        if not node.done:
            break
        nodes.append(node)
    else:
        raise exceptions.CurlyParserNoUnfinishedNodeError()

    if not isinstance(node, search_for):
        raise exceptions.CurlyParserUnexpectedUnfinishedNodeError(
            search_for, node)

    node.done = True
    node.data = nodes[::-1]
    stack.append(node)

    return stack


def validate_for_all_nodes_done(root):
    """Validates that all nodes in given AST trees are marked as done.

    It simply does in-order traversing of the tree, verifying attribute.

    :param root: Root of the tree.
    :type root: :py:class:`RootNode`
    :raises:
        :py:exc:`curly.exceptions.CurlyParserFoundNotDoneError`: if
        node which is not closed is found.
    """
    for node in root:
        if not node.done:
            raise exceptions.CurlyParserFoundNotDoneError(node)
        for subnode in root:
            validate_for_all_nodes_done(subnode)

import warnings
try:
    from collections.abc import Sequence
except ImportError:
    from collections import Sequence
from itertools import chain

from django.conf import settings
from django.forms.widgets import MediaDefiningClass
from django.template.base import NodeList
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from six import with_metaclass

# Allow "component.AlreadyRegistered" instead of having to import these everywhere
from django_components.component_registry import AlreadyRegistered, ComponentRegistry, NotRegistered  # noqa

# Django < 2.1 compatibility
try:
    from django.template.base import TokenType
except ImportError:
    from django.template.base import TOKEN_BLOCK, TOKEN_TEXT, TOKEN_VAR

    class TokenType:
        TEXT = TOKEN_TEXT
        VAR = TOKEN_VAR
        BLOCK = TOKEN_BLOCK


class BaseComponent(with_metaclass(MediaDefiningClass)):
    __cached_slot_nodes = None

    def __init__(self, component_name):
        self.__component_name = component_name

    def context(self):
        return {}

    def template(self, context):
        raise NotImplementedError("Missing template() method on component")

    def render_dependencies(self):
        """Helper function to access media.render()"""

        return self.media.render()

    def render_css_dependencies(self):
        """Render only CSS dependencies available in the media class."""

        return mark_safe("\n".join(self.media.render_css()))

    def render_js_dependencies(self):
        """Render only JS dependencies available in the media class."""

        return mark_safe("\n".join(self.media.render_js()))

    @staticmethod
    def slots_in_template(template):
        return {node.name: node.nodelist for node in template.template.nodelist if is_slot_node(node)}

    def render(self, context, slots_filled=None):
        slots_filled = dict(slots_filled) or {}

        template = get_template(self.template(context))
        slots_in_template = self.slots_in_template(template)

        defined_slot_names = {slots_in_template.keys()}
        filled_slot_names = {slots_filled.keys()}
        unexpected_slots = filled_slot_names - defined_slot_names
        if unexpected_slots:
            if settings.DEBUG:
                warnings.warn(
                    "Component {} was provided with unexpected slots: {}".format(
                        self.__component_name, unexpected_slots
                    )
                )
            for unexpected_slot in unexpected_slots:
                del slots_filled[unexpected_slot]

        combined_slots = dict(slots_in_template, **slots_filled)
        # Replace slot nodes with their nodelists, then combine into a single, flat nodelist
        node_iterator = ([node] if not is_slot_node(node) else combined_slots[node.name]
                         for node in template.template.nodelist)
        flattened_nodelist = NodeList(chain.from_iterable(node_iterator))

        return flattened_nodelist.render(context)

    class Media:
        css = {}
        js = []


def is_slot_node(node):
    return node.token.token_type == TokenType.BLOCK and node.token.split_contents()[0] == "slot"


# This variable represents the global component registry
registry = ComponentRegistry()


class Component(BaseComponent):
    """Base class for creating Components.

    Subclasses must:
    -Provide a list of allowed positional arguments, with required arguments as strings and optional arguments
    as tuples in the form (name: str, value: any)
    -Provide a dict of allowed keyword arguments and their default values (or Ellipsis for required keyword arguments)
    or else set the class attribute allow_arbitrary_keyword_props to True.
    -Provide the template to render by setting the template_name property or overriding the template method. The
    superclass template method should not be called if the template_name property is not used.
    -Specify the name for the component by setting the component_name property.

    Subclasses may:
    -Override the context method to modify the context prior to rendering.
    -Provide a list of nonshadowing_keyword_props. These are keyword props that are accepted if passed, but if they
    are not passed, then they will not be included in the context. This allows the component to look for the
    variable in the external context."""

    positional_props = []
    keyword_props = {}
    nonshadowing_keyword_props = []

    allow_arbitrary_keyword_props = False
    passthrough_styles_allowed = True
    linkable_component = True

    def __init_subclass__(cls, **kwargs):
        """Validate and process props at class declaration time."""

        super(cls, Component).__init_subclass__(**kwargs)
        # Check that no required positional arguments are after optional arguments
        arg_iterator = iter(arg for arg in cls.positional_props)
        try:
            while not is_optional_arg(next(arg_iterator)):
                pass
            if not all(is_optional_arg(arg) for arg in arg_iterator):
                raise SyntaxError(f'Required positional argument follows optional argument')
        # Raised when there are no optional arguments, which is fine
        except StopIteration:
            pass

        # For use in argument parsing in context() method
        cls._positional_prop_defaults = {}
        cls._positional_prop_names = []
        for prop in cls.positional_props:
            if not is_iterable(prop):
                prop_name = prop
                default_value = Ellipsis
            else:
                prop_name, default_value = prop
            cls._positional_prop_defaults[prop_name] = default_value
            cls._positional_prop_names.append(prop_name)

        # Register as a component for use in templates
        registry.register(name=cls.component_name, component=cls)

    def context(self, *args, **kwargs):
        """Build context from args, kwargs, and defaults. Raise TypeError if args and kwargs are not acceptable."""

        if len(args) > len(self._positional_prop_names):
            raise TypeError('Received unexpected positional props: {}'.format(
                args[len(self._positional_prop_names) - 1:]))

        provided_positional_props = {name: value for name, value in zip(self._positional_prop_names, args)}
        final_positional_args = {}

        # Merge positional args in following priority: first, provided positional args, then provided keyword args,
        # then default positional props, then default keyword props
        for name in self._positional_prop_names:
            if name in provided_positional_props:
                if name in kwargs:
                    raise TypeError('Received multiple values for argument {}'.format(name))
                final_positional_args[name] = provided_positional_props[name]
                continue
            elif name in kwargs:
                final_positional_args[name] = kwargs[name]
                continue
            elif name in self._positional_prop_defaults:
                final_positional_args[name] = self._positional_prop_defaults[name]
            elif name in self.keyword_props:
                final_positional_args[name] = self.keyword_props[name]
            if final_positional_args.get(name, Ellipsis) is Ellipsis:
                raise TypeError('Missing required positional argument {}'.format(name))

        extra_kwargs = (set(kwargs) - set(self._positional_prop_names) - set(self.keyword_props)
                        - set(self.nonshadowing_keyword_props))
        if extra_kwargs and not self.allow_arbitrary_keyword_props:
            raise TypeError('Received unexpected positional arguments: {}'.format(extra_kwargs))

        missing_kwargs = {kwarg for kwarg, value in self.keyword_props.items()
                          if kwarg not in kwargs and value is Ellipsis}
        if missing_kwargs:
            raise TypeError('Missing required keyword arguments: {}'.format(missing_kwargs))

        all_args = dict(final_positional_args, **self.keyword_props)
        all_args.update(**kwargs)

        return all_args

    def template(self, _context):
        return self.template_name

    @property
    def template_name(self):
        raise NotImplementedError('Subclasses of Component must define a template_name property or override the '
                                  'template method')


def is_iterable(item):
    try:
        str = basestring
    except NameError:
        pass
    return isinstance(item, Sequence) and not isinstance(item, str)


def is_optional_arg(arg):
    return is_iterable(arg) and arg[1] is not Ellipsis


def capitalize(s):
    return s[0].upper() + s[1:]


def snake_case_to_camel(s):
    return ''.join(capitalize(word) for word in s.split('_'))
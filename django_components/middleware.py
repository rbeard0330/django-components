import re

from django.conf import settings
from django.forms import Media

RENDERED_COMPONENTS_CONTEXT_KEY = "_COMPONENT_DEPENDENCIES"
CSS_DEPENDENCY_PLACEHOLDER = '<link name="CSS_PLACEHOLDER" href="#">'
JS_DEPENDENCY_PLACEHOLDER = '<src name="JS_PLACEHOLDER" href="#">'

SCRIPT_TAG_REGEX = re.compile('<script')


class ComponentDependencyMiddleware:
    """Middleware that inserts CSS/JS dependencies for all rendered components at points marked with template tags."""

    dependency_regex = re.compile(bytes('{}|{}'.format(CSS_DEPENDENCY_PLACEHOLDER, JS_DEPENDENCY_PLACEHOLDER),
                                        encoding='utf-8'))

    def __init__(self, get_response):
        self.get_response = get_response
        self.import_scripts_as_modules = getattr(settings, 'IMPORT_SCRIPTS_AS_MODULES', False)

    def __call__(self, request):
        return self.get_response(request)

    def process_template_response(self, _request, response):
        if response.context_data is None:
            response.context_data = {}
        response.context_data[RENDERED_COMPONENTS_CONTEXT_KEY] = set()

        def component_dependency_callback(rendered_response):
            rendered_components = rendered_response.context_data.get(RENDERED_COMPONENTS_CONTEXT_KEY, [])
            required_media = join_media(rendered_components)

            replacer = DependencyReplacer(''.join(required_media.render_css()), ''.join(required_media.render_js()),
                                          use_modules=self.import_scripts_as_modules)
            response.content = re.sub(self.dependency_regex, replacer, response.content)

        response.add_post_render_callback(component_dependency_callback)

        return response


def add_module_attribute_to_scripts(scripts):
    return re.sub(SCRIPT_TAG_REGEX, '<script type="module"', scripts)


class DependencyReplacer:
    """Replacer for use in re.sub that replaces the first placeholder CSS and JS
    tags it encounters and removes any subsequent ones."""

    CSS_PLACEHOLDER = bytes(CSS_DEPENDENCY_PLACEHOLDER, encoding='utf-8')
    JS_PLACEHOLDER = bytes(JS_DEPENDENCY_PLACEHOLDER, encoding='utf-8')

    def __init__(self, css_string, js_string, use_modules):
        self.use_modules = use_modules
        if self.use_modules:
            js_string = add_module_attribute_to_scripts(js_string)
        self.js_string = bytes(js_string, encoding='utf-8')
        self.css_string = bytes(css_string, encoding='utf-8')

    def __call__(self, match):
        if match[0] == self.CSS_PLACEHOLDER:
            replacement, self.css_string = self.css_string, b""
        elif match[0] == self.JS_PLACEHOLDER:
            replacement, self.js_string = self.js_string, b""
        else:
            raise AssertionError('Invalid match for DependencyReplacer' + match)
        return replacement


def join_media(components):
    """Return combined media object for iterable of components."""

    return sum([component.media for component in components], Media())

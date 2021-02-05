# django-reusable-components
<a href="https://github.com/EmilStenstrom/django-components/actions?query=workflow%3ABuild"><img align="right" src="https://github.com/EmilStenstrom/django-components/workflows/Build/badge.svg"></a>
<a href="https://pepy.tech/project/django-reusable-components"><img align="right" src="https://pepy.tech/badge/django-reusable-components"></a>

A way to create simple reusable template components in Django.

It lets you create "template components", that contains both the template, the Javascript and the CSS needed to generate the front end code you need for a modern app. Components look like this:

```htmldjango
{% component name="calendar" date="2015-06-19" %}
```

And this is what gets rendered (plus the CSS and Javascript you've specified):

```html
<div class="calendar-component">Today's date is <span>2015-06-19</span></div>
```

Read on to learn about the details!

# Installation

Install the app into your environment:

> ```pip install django_reusable_components```

Then add the app into INSTALLED APPS in settings.py

```
INSTALLED_APPS = [
    ...,
    "django_components",
    ...
]
```

## Optional

To avoid loading the app in each template using ``` {% load django_components %} ```, you can add the tag as a 'builtin' in settings.py

```
TEMPLATES = [
    {
        ...,
        'OPTIONS': {
            'context_processors': [
                ...
            ],
            'builtins': [
                'django_components.templatetags.component_tags',
            ]
        },
    },
]
```

# Contributors

<!-- readme: contributors -start --> 
<table>
<tr>
    <td align="center">
        <a href="https://github.com/EmilStenstrom">
            <img src="https://avatars.githubusercontent.com/u/224130?v=4" width="100;" alt="EmilStenstrom"/>
            <br />
            <sub><b>Emil StenstrC6m</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/ryanhiebert">
            <img src="https://avatars.githubusercontent.com/u/425099?v=4" width="100;" alt="ryanhiebert"/>
            <br />
            <sub><b>Ryan Hiebert</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/rbeard0330">
            <img src="https://avatars.githubusercontent.com/u/2442690?v=4" width="100;" alt="rbeard0330"/>
            <br />
            <sub><b>Rbeard0330</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/BradleyKirton">
            <img src="https://avatars.githubusercontent.com/u/6583221?v=4" width="100;" alt="BradleyKirton"/>
            <br />
            <sub><b>Bradley Stuart Kirton</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/danjac">
            <img src="https://avatars.githubusercontent.com/u/249779?v=4" width="100;" alt="danjac"/>
            <br />
            <sub><b>Dan Jacob</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/telenieko">
            <img src="https://avatars.githubusercontent.com/u/10505?v=4" width="100;" alt="telenieko"/>
            <br />
            <sub><b>Marc Fargas</b></sub>
        </a>
    </td></tr>
</table>
<!-- readme: contributors -end -->

# Compatiblity

| Python version | Django version                |
|----------------|-------------------------------|
| 2.7            | 1.11                          |
| 3.5            | 1.11, 2.0, 2.1, 2.2           |
| 3.6            | 1.11, 2.0, 2.1, 2.2, 3.0, 3.1 |
| 3.7            | 1.11, 2.0, 2.1, 2.2, 3.0, 3.1 |
| 3.8            | 2.1, 2.2, 3.0, 3.1            |
| 3.9            | 2.1, 2.2, 3.0, 3.1            |

# Create your first component

A component in django-components is the combination of four things: CSS, Javascript, a Django template, and some Python code to put them all together.

First you need a CSS file. Be sure to prefix all rules with a unique class so they don't clash with other rules.

```css
/* In a file called style.css */
.calendar-component { width: 200px; background: pink; }
.calendar-component span { font-weight: bold; }
```

Then you need a javascript file that specifies how you interact with this component. You are free to use any javascript framework you want. A good way to make sure this component doesn't clash with other components is to define all code inside an anonymous function that calls itself. This makes all variables defined only be defined inside this component and not affect other components.

```js
/* In a file called script.js */
(function(){
    $(".calendar-component").click(function(){ alert("Clicked calendar!"); })
})()
```

Now you need a Django template for your component. Feel free to define more variables like `date` in this example. When creating an instance of this component we will send in the values for these variables. The template will be rendered with whatever template backend you've specified in your Django settings file.

```htmldjango
{# In a file called calendar.html #}
<div class="calendar-component">Today's date is <span>{{ date }}</span></div>
```

Finally, we use django-components to tie this together. Start by creating a file called `components.py` in any of your apps. It will be auto-detected and loaded by the app.

Inside this file we create a Component by inheriting from the Component class and specifying the context method. We also register the global component registry so that we easily can render it anywhere in our templates.

```python
from django_components import component


class Calendar(component.Component):
    def context(self, date):
        return {
            "date": date,
        }

    def template(self, context):
        return "[your app]/components/calendar/calendar.html"

    class Media:
        css = {'all': ['[your app]/components/calendar/calendar.css']}
        js = ['[your app]/components/calendar/calendar.js']


component.registry.register(name="calendar", component=Calendar)
```

And voilC!! We've created our first component.

# Use the component in a template

First load the `component_tags` tag library, then use the `component_dependencies` and `component` tags to render the component to the page.

```htmldjango
{% load component_tags %}
<!DOCTYPE html>
<html>
<head>
    <title>My example calendar</title>
    {% component_dependencies %}
</head>
<body>
    {% component name="calendar" date="2015-06-19" %}
</body>
<html>
```

The output from the above template will be:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My example calendar</title>
    <link href="style.css" type="text/css" media="all" rel="stylesheet">
    <script src="script.js"></script>
</head>
<body>
    <div class="calendar-component">Today's date is <span>2015-06-19</span></div>
</body>
<html>
```

This makes it possible to organize your front-end around reusable components. Instead of relying on template tags and keeping your CSS and Javascript in the static directory.

# Using slots in templates

Components support something called slots. They work a lot like Django blocks, but only inside components you define. Let's update our calendar component to support more customization, by updating our calendar.html template:

```htmldjango
<div class="calendar-component">
    <div class="header">
        {% slot "header" %}Calendar header{% endslot %}
    </div>
    <div class="body">
        {% slot "body" %}Calendar body{% endslot %}
    </div>
</div>
```

When using the component, you specify what slots you want to fill and where you want to use the defaults from the template. It looks like this:

```htmldjango
{% component_block %}
    {% slot "body" %}Today's date is <span>{{ date }}</span>{% endslot %}
{% endcomponent_block %}
```

Since the header block is unspecified, it's taken from the base template. If you put this in a template, and send in date=2020-06-06, this is what's rendered:

```html
<div class="calendar-component">
    <div class="header">
        Calendar header
    </div>
    <div class="body">
        Today's date is <span>2020-06-06</span>
    </div>
</div>

```

As you can see, component slots lets you write reusable containers, that you fill out when you use a component. This makes for highly reusable components, that can be used in different circumstances.

# Component context

By default, components can access context variables from the parent template, just like templates that are included with the `{% include %}` tag. Just like with `{% include %}`, if you don't want the component template to have access to the parent context, add `only` to the end of the `{% component %}` (or `{% component_block %}` tag):

```htmldjango
   {% component name="calendar" date="2015-06-19" only %}
```

NOTE: `{% csrf_token %}` tags need access to the top-level context, and they will not function properly if they are rendered in a component that is called with the `only` modifier.

Components can also access the outer context in their context methods by accessing the property `outer_context`.

# Configuring the library location

If you want to, you can configure the location where components are loaded. To do this, add a COMPONENTS variable to you settings.py with a list of libraries to look for. This allows you to build a structure of components that are independent from your apps.

```python
COMPONENTS = {
    "libraries": [
        "mysite.components.forms",
        "mysite.components.buttons",
        "mysite.components.cards",
    ]
}
```

# Running the tests

To quickly run the tests install the local dependencies by running

```sh
pip install -r requirements-dev.txt
./pytest
```

The library is also tested across many versions of Python and Django. To run tests that way:

```sh
pip install -r requirements-dev.txt
tox
```

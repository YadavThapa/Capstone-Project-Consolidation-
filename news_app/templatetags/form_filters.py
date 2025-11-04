from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    """Add a CSS class to a form field's widget in templates: {{ form.field|add_class:"form-control" }}"""
    try:
        existing = field.field.widget.attrs.get('class', '')
        if existing:
            css = existing + ' ' + css
        field.field.widget.attrs['class'] = css
        return field
    except Exception:
        return field

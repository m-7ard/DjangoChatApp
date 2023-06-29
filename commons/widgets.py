from django import forms
from django.utils import formats

class ChannelKindSelect(forms.RadioSelect):
    template_name = "commons/widgets/channel-kind-select.html"


class FormTextInput(forms.TextInput):
    template_name = "commons/widgets/form-text-input.html"

    def format_value(self, value):
        # taken from https://github.com/django/django/blob/main/django/forms/widgets.py#L249
        # Archive: https://archive.is/x2PAG
        """
        Return a value as it should appear when rendered in a template.
        """
        if value == "" or value is None:
            return ""
        if self.is_localized:
            return formats.localize_input(value)
        return str(value)


class FormNumberInput(forms.NumberInput):
    template_name = "commons/widgets/form-number-input.html"

    def format_value(self, value):
        # taken from https://github.com/django/django/blob/main/django/forms/widgets.py#L249
        # Archive: https://archive.is/x2PAG
        """
        Return a value as it should appear when rendered in a template.
        """
        if value == "" or value is None:
            return ""
        if self.is_localized:
            return formats.localize_input(value)
        return str(value)


class FormSelect(forms.Select):
    template_name = "commons/widgets/form-select.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["field"] = self.field
        
        return context
    
class FormCheckbox(forms.CheckboxInput):
    template_name = "commons/widgets/form-checkbox.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["field"] = self.field

        return context
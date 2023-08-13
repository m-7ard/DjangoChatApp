from django import forms
from django.utils import formats


class ChannelKindSelect(forms.RadioSelect):
    template_name = "commons/widgets/channel-kind-select.html"


class FormInput(forms.TextInput):
    template_name = "commons/widgets/form-input.html"

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
    

class FormLabeledSlider(forms.CheckboxInput):
    template_name = "commons/widgets/form-labeled-slider.html"
    

class FormPasswordInput(forms.PasswordInput):
    template_name = "commons/widgets/form-password-input.html"


class FormDateInput(forms.DateTimeInput):
    template_name = "commons/widgets/form-date-input.html"

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


class FormEmailInput(forms.EmailInput):
    template_name = "commons/widgets/form-email-input.html"

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

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
    

class FormSlider(forms.CheckboxInput):
    template_name = "commons/widgets/form-slider.html"
    horizontal = True
    

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


class FormImageInput(forms.FileInput):
    template_name = "commons/widgets/form-image-input.html"


class FormSelect(forms.Select):
    template_name = "commons/widgets/form-select.html"


class FormTriStateSwitch(forms.NumberInput):
    template_name = "commons/widgets/form-tri-state-switch.html"
    horizontal = True

class FormBiStateSwitch(forms.NumberInput):
    template_name = "commons/widgets/form-bi-state-switch.html"
    horizontal = True

class FormMutliselect(forms.SelectMultiple):
    template_name = 'commons/widgets/form-multiselect.html'


class FormColorPicker(forms.TextInput):
    template_name ='commons/widgets/form-color-picker.html'

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
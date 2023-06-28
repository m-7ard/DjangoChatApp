from django import forms


class ChannelKindSelect(forms.RadioSelect):
    template_name = "commons/widgets/channel-kind-select.html"


class FormTextInput(forms.TextInput):
    template_name = "commons/widgets/form-text-input.html"


class FormNumberInput(forms.NumberInput):
    template_name = "commons/widgets/form-number-input.html"


class FormSelect(forms.Select):
    template_name = "commons/widgets/form-select.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["optgroups"] = self.optgroups(
            name, context["widget"]["value"], attrs
        )
        context["field"] = self.field
        
        return context
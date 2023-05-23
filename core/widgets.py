from django import forms


class AvatarInput(forms.FileInput):
    template_name = 'core/widgets/avatar-input.html'
    
    def render(self, name, value, attrs=None, renderer=None):
        if value and hasattr(value, 'url'):
            attrs['file_url'] = value.url
        else:
            attrs['file_url'] = ''

        return super().render(name, value, attrs, renderer)
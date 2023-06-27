from django import forms


class ChannelKindSelect(forms.RadioSelect):
    template_name = "rooms/widgets/channel-kind-select.html"
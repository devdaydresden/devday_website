from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit, HTML
from django import forms
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class SponsoringContactForm(forms.Form):
    organization = forms.CharField(
        label=_('Your organization'), max_length=100)
    email = forms.EmailField(label=_('Contact email address'))
    body = forms.CharField(
        label=_('Your request'), widget=forms.Textarea(attrs={'rows': 5}))

    event = None

    def __init__(self, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(**kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'sponsoring_view', kwargs={'event': self.event.slug})
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML('<h1>{}</h1>'.format(_('Sponsoring request'))),
                        css_class='offset-lg-2 col-lg-8 col-12',
                    ),
                    css_class='form-row'
                ),
                Div(
                    Field(
                        'organization',
                        wrapper_class='offset-lg-2 col-lg-8 col-12',
                    ),
                    css_class='form-row'
                ),
                Div(
                    Field(
                        'email',
                        wrapper_class='offset-lg-2 col-lg-8 col-12',
                    ),
                    css_class='form-row'
                ),
                Div(
                    Field(
                        'body',
                        wrapper_class='offset-lg-2 col-lg-8 col-12',
                    ),
                    css_class='form-row'
                ),
                Div(
                    Div(
                        Submit(
                            'submit', _('Send sponsoring request'),
                            css_class='m-0 btn btn-primary',
                        ),
                        css_class='offset-lg-2 col-lg-8 col-12',
                    ),
                    css_class='form-row'
                )
            )
        )

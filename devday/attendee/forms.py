from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Field, Submit, Hidden, HTML
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_registration.forms import RegistrationFormUniqueEmail

from attendee.models import DevDayUser, Attendee
from devday.forms import AuthenticationForm

User = get_user_model()


class DevDayRegistrationForm(RegistrationFormUniqueEmail):
    accept_general_contact = forms.BooleanField(
        label=_("Contact for other events"),
        help_text=_(
            "I would like to receive updates related to events organized by"
            " the T-Systems Multimedia Solutions GmbH Software Engineering"
            " Community via email."
        ),
        required=False,
    )

    class Meta(RegistrationFormUniqueEmail.Meta):
        model = User
        fields = ["email", "password1", "password2"]


class DevDayUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """

    class Meta:
        model = DevDayUser
        fields = ("email",)
        field_classes = {"email": forms.EmailField}

    def __init__(self, *args, **kwargs):
        super(DevDayUserCreationForm, self).__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"autofocus": True})

    def save(self, commit=True):
        user = super(DevDayUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class DevDayUserChangeForm(UserChangeForm):
    class Meta:
        model = DevDayUser
        fields = "__all__"
        field_classes = {"email": forms.EmailField}


class AttendeeInlineForm(ModelForm):
    class Meta:
        model = Attendee
        fields = ["event", "source"]
        widgets = {"source": forms.Textarea(attrs={"cols": 40, "rows": 1})}


class AttendeeProfileForm(ModelForm):
    """
    This form is used to register an anonymous user as DevDayUser and for an
    event.
    """

    accept_general_contact = forms.BooleanField(
        label=_("Contact for other events"),
        help_text=_(
            "I would like to receive updates related to events organized by"
            " the T-Systems Multimedia Solutions GmbH Software Engineering"
            " Community via email."
        ),
        required=False,
    )

    class Meta:
        model = DevDayUser
        fields = ["contact_permission_date", "date_joined"]
        labels = {"contact_permission_date": _("Contact permission granted on")}

    def __init__(self, *args, **kwargs):
        super(AttendeeProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = "user_profile"
        self.helper.form_method = "post"
        self.helper.html5_required = True
        self.fields["date_joined"].required = False
        self.fields["date_joined"].disabled = True
        self.fields["contact_permission_date"].disabled = True
        buttons = Div(css_class="col-12 col-sm-6 order-2 order-sm-1")
        buttons.append(
            HTML(
                '<a href={} class="btn btn-outline-danger ml-0">{}</a>'.format(
                    reverse("attendee_delete"), _("Delete your account")
                )
            )
        )
        buttons.append(
            HTML(
                '<a href="{}" class="btn btn-outline-secondary mr-0">{}</a>'.format(
                    reverse("auth_password_change"), _("Change password")
                )
            )
        )
        self.helper.layout = Layout(
            HTML("<hr/>"),
            Div(
                Field("accept_general_contact", wrapper_class="col-12"),
                css_class="form-row",
            ),
            Div(
                Field("contact_permission_date", wrapper_class="col-12 col-sm-6"),
                Field("date_joined", wrapper_class="col-12 col-sm-6"),
                css_class="form-row",
            ),
            Div(
                buttons,
                Div(
                    Submit(
                        "submit",
                        _("Update your profile"),
                        css_class="btn btn-primary float-left float-sm-right" " mr-0",
                    ),
                    css_class="col-12 col-sm-6 order-1 order-sm-2",
                ),
                css_class="form-row",
            ),
        )

    def save(self, commit=True):
        user = super().save(False)
        if self.cleaned_data.get("accept_general_contact"):
            if user.contact_permission_date is None:
                user.contact_permission_date = timezone.now()
        else:
            user.contact_permission_date = None
        if commit:
            user.save()
        return user


class EventRegistrationForm(ModelForm):
    """
    This form is used to register an existing DevDayUser for an event.
    """

    class Meta:
        model = Attendee
        fields = []

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        self.user = kwargs.pop("user")
        super(EventRegistrationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy(
            "attendee_registration", kwargs={"event": self.event.slug}
        )
        self.helper.form_method = "post"
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(
                        _(
                            '<p class="text-info">By registering as an'
                            " attendee, I agree to be contacted by the Dev Day"
                            " organizers about conference details."
                            "</p>"
                        )
                    )
                ),
                Submit("submit", _("Register as attendee")),
                css_class="col-md-12 offset-lg-2 col-lg-8 text-center",
            )
        )

    def save(self, commit=True):
        attendee = Attendee(event=self.event, user=self.user)
        if commit:
            attendee.save()
        return attendee


class RegistrationAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        event = kwargs.pop("event")
        super(RegistrationAuthenticationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy(
            "login_or_register_attendee", kwargs={"event": event.slug}
        )
        self.helper.form_method = "post"
        self.helper.field_template = "devday/form/field.html"
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Hidden(
                    "next",
                    value=reverse(
                        "attendee_registration", kwargs={"event": event.slug}
                    ),
                ),
                Field(
                    "username", template="devday/form/field.html", autofocus="autofocus"
                ),
                Field("password", template="devday/form/field.html"),
            ),
            Div(
                Submit("submit", _("Login"), css_class="btn-default"),
                css_class="text-center",
            ),
        )


class DevDayUserRegistrationForm(DevDayRegistrationForm):
    """
    This form is used to register a DevDayUser without assigning it to
    a specific event.
    """

    next = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy("registration_register")
        self.helper.form_method = "post"
        self.helper.html5_required = True
        self.fields["email"].help_text = None
        self.fields["email"].label = _("E-Mail")
        self.fields["password1"].help_text = None
        self.fields["password2"].help_text = None
        self.fields["accept_general_contact"].label = _("Permit contact")
        self.fields["accept_general_contact"].initial = False

        self.helper.layout = Layout(
            Field("next"),
            Div(
                Field("email", autofocus="autofocus", wrapper_class="col-12"),
                css_class="form-row",
            ),
            Div(
                Field("password1", wrapper_class="col-12 col-md-6"),
                Field("password2", wrapper_class="col-12 col-md-6"),
                css_class="form-row",
            ),
            Div(
                Field("accept_general_contact", wrapper_class="col-12"),
                css_class="form-row",
            ),
            Div(
                Submit("submit", _("Register for an account")),
                css_class="col-12 text-center",
            ),
        )

    def save(self, commit=True):
        user = super().save(False)
        user.is_active = False
        if self.cleaned_data.get("accept_general_contact"):
            user.contact_permission_date = timezone.now()
        if commit:
            user.save()
        return user


class AttendeeRegistrationForm(DevDayRegistrationForm):
    """
    This form is used to register a DevDayUser and create an registration for
    a specific event.
    """

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        super(AttendeeRegistrationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy(
            "attendee_registration", kwargs={"event": self.event.slug}
        )
        self.helper.form_method = "post"
        self.helper.html5_required = True
        self.fields["email"].help_text = None
        self.fields["email"].label = _("E-Mail")
        self.fields["password1"].help_text = None
        self.fields["password2"].help_text = None
        self.fields["accept_general_contact"].initial = False

        self.helper.layout = Layout(
            Div(
                Field("email", autofocus="autofocus", wrapper_class="col-12"),
                css_class="form-row",
            ),
            Div(
                Field("password1", wrapper_class="col-12 col-md-6"),
                Field("password2", wrapper_class="col-12 col-md-6"),
                css_class="form-row",
            ),
            Div(
                Div(
                    HTML(
                        _(
                            '<p class="text-info">By registering as an'
                            " attendee, I agree to be contacted by the Dev Day"
                            " organizers about conference details.</p></label>"
                        )
                    ),
                    css_class="col-12 col-md-6",
                ),
                Field("accept_general_contact", wrapper_class="col-12 col-md-6"),
                css_class="form-row",
            ),
            Div(
                Submit("submit", _("Register as attendee")),
                css_class="col-12 text-center",
            ),
        )

    def save(self, commit=True):
        user = super(AttendeeRegistrationForm, self).save(False)
        user.is_active = False
        if self.cleaned_data.get("accept_general_contact"):
            user.contact_permission_date = timezone.now()
        if commit:
            user.save()
        return user


class CheckInAttendeeForm(forms.Form):
    attendee = forms.CharField(label="Check in code or email address", max_length=100)

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy(
            "attendee_checkin", kwargs={"event": self.event.slug}
        )
        self.helper.form_method = "post"
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Field(
                    "attendee",
                    autofocus="autofocus",
                    help_text=_("Attendee check in code or  email address"),
                    wrapper_class="col-12 col-md-6",
                ),
                css_class="form-row",
            ),
            Div(
                Submit("submit", _("Check in this attendee")),
                css_class="col-12 text-center",
            ),
        )

    def clean_attendee(self):
        checkin_code = self.cleaned_data["attendee"]
        attendee = Attendee.objects.get_by_checkin_code_or_email(
            checkin_code, self.event
        )
        if not attendee:
            raise ValidationError(
                _(
                    "Unknown checkin code or email address, or attendee is not"
                    " registered for the current event."
                )
            )
        if attendee.checked_in is not None:
            raise ValidationError(_("{} is already checked in!".format(attendee.user)))

        return attendee

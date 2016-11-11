from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from django import forms


class DevDayFormHelper(FormHelper):
    def __init__(self, form=None):
        super(DevDayFormHelper, self).__init__(form)
        self.field_template = 'devday/form/field.html'


class DevDayField(Field):
    def __init__(self, *args, **kwargs):
        super(DevDayField, self).__init__(*args, **kwargs)
        if not 'template' in kwargs:
            self.template = 'devday/form/field.html'


class CombinedFormBase(forms.Form):
    """
    Idea from http://stackoverflow.com/a/24349234
    """
    form_classes = []

    def __init__(self, *args, **kwargs):
        super(CombinedFormBase, self).__init__(*args, **kwargs)
        for f in self.form_classes:
            name = f.__name__.lower()
            setattr(self, name, f(*args, **kwargs))
            form = getattr(self, name)
            self.fields.update(form.fields)
            self.files.update(form.files)
            self.initial.update(form.initial)

    def is_valid(self):
        isValid = True
        for f in self.form_classes:
            name = f.__name__.lower()
            form = getattr(self, name)
            if not form.is_valid():
                isValid = False
            self.files.update(form.files)
        # is_valid will trigger clean method
        # so it should be called after all other forms is_valid are called
        # otherwise clean_data will be empty
        if not super(CombinedFormBase, self).is_valid():
            isValid = False
        for f in self.form_classes:
            name = f.__name__.lower()
            form = getattr(self, name)
            self.errors.update(form.errors)
        return isValid

    def clean(self):
        cleaned_data = super(CombinedFormBase, self).clean()
        for f in self.form_classes:
            name = f.__name__.lower()
            form = getattr(self, name)
            cleaned_data.update(form.cleaned_data)

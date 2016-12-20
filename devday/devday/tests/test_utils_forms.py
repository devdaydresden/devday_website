from django import forms
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from devday.utils.forms import DevDayFormHelper, DevDayField, CombinedFormBase

try:
    from unittest import mock
except ImportError:  # Python2 has no integrated mock
    import mock


class DevDayFormHelperTest(SimpleTestCase):
    """
    Tests for devday.utils.forms.DevDayFormHelper.

    """

    def test_field_template(self):
        helper = DevDayFormHelper()
        self.assertEqual(helper.field_template, 'devday/form/field.html')


class DevDayFieldTest(SimpleTestCase):
    """
    Tests for devday.utils.forms.DevDayField.

    """

    def test_default_template(self):
        field = DevDayField()
        self.assertEqual(field.template, 'devday/form/field.html')

    def test_override_template(self):
        field = DevDayField(template='test_field.html')
        self.assertEqual(field.template, 'test_field.html')


class Form1(forms.Form):
    test1 = forms.CharField()

    def clean_test1(self):
        data = self.cleaned_data['test1']
        return data


class Form2(forms.Form):
    test2 = forms.CharField()

    def clean_test2(self):
        data = self.cleaned_data['test2']
        return data


class CombinedFormBaseTest(SimpleTestCase):
    """
    Tests for devday.utils.forms.CombinedFormBase.

    """

    def setUp(self):
        self.patcher1 = mock.patch.object(Form1, 'clean_test1')
        self.patcher2 = mock.patch.object(Form2, 'clean_test2')
        self.form1_clean_test1 = self.patcher1.start()
        self.form2_clean_test2 = self.patcher2.start()

    def tearDown(self):
        self.patcher2.stop()
        self.patcher1.stop()

    def test_constructor(self):
        class TestCombined(CombinedFormBase):
            form_classes = [Form1, Form2]

        form = TestCombined(data={'test1': 'test1', 'test2': 'test2'})
        self.assertEqual(len(form.fields), 2)
        self.assertIn('test1', form.fields)
        self.assertIn('test2', form.fields)
        self.assertTrue(form.is_bound)

    def test_is_valid_subforms_invalid(self):
        class TestCombined(CombinedFormBase):
            form_classes = [Form1, Form2]

        form = TestCombined(data={'test1': 'test1', 'test2': 'test2'})

        self.form1_clean_test1.side_effect = ValidationError('test1 is invalid')
        self.form2_clean_test2.side_effect = ValidationError('test2 is invalid')

        self.assertFalse(form.is_valid())
        self.assertEqual(self.form1_clean_test1.call_count, 1)
        self.assertEqual(self.form2_clean_test2.call_count, 1)

    def test_is_valid_subforms_one_valid(self):
        class TestCombined(CombinedFormBase):
            form_classes = [Form1, Form2]

        form = TestCombined(data={'test1': 'test1', 'test2': 'test2'})
        self.form1_clean_test1.side_effect = ValidationError('test1 is invalid')

        self.assertFalse(form.is_valid())
        self.assertEqual(self.form1_clean_test1.call_count, 1)
        self.assertEqual(self.form2_clean_test2.call_count, 1)

    def test_is_valid_subforms_all_valid(self):
        class TestCombined(CombinedFormBase):
            form_classes = [Form1, Form2]

        form = TestCombined(data={'test1': 'test1', 'test2': 'test2'})

        self.assertTrue(form.is_valid())
        self.assertEqual(self.form1_clean_test1.call_count, 1)
        self.assertEqual(self.form2_clean_test2.call_count, 1)

    def test_is_valid_form_invalid(self):
        class TestCombined(CombinedFormBase):
            missing = forms.CharField()
            form_classes = [Form1, Form2]

        form = TestCombined(data={'test1': 'test1', 'test2': 'test2'})

        self.assertFalse(form.is_valid())
        self.assertEqual(self.form1_clean_test1.call_count, 1)
        self.assertEqual(self.form2_clean_test2.call_count, 1)

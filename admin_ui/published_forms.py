from django.forms import ModelForm
from .config import MODEL_CONFIG_MAP


def GenericFormClass(model_name):
    class MyFormClass(ModelForm):
        def get_form(self, form_class=None):
            form = super().get_form()
            for field in form.fields:
                # Set html attributes as needed for all fields
                form.fields[field].widget.attrs['readonly'] = 'readonly'          
                form.fields[field].widget.attrs['disabled'] = 'disabled'

            return form
        class Meta:
            model = MODEL_CONFIG_MAP[model_name]["model"]
            fields = '__all__'
        
    return MyFormClass

from django.forms import ModelForm
from .config import MODEL_CONFIG_MAP


def GenericFormClass(model_name="", model=None):
    MainModel = model_name and MODEL_CONFIG_MAP[model_name]["model"] or model

    class MyFormClass(ModelForm):
        class Meta:
            model = MainModel
            fields = '__all__'

    return MyFormClass

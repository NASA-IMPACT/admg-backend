from django.forms import ModelForm, modelform_factory
# from django.forms.models import (
#     BaseInlineFormSet, inlineformset_factory, modelform_defines_fields,
#     modelform_factory, modelformset_factory,
# )
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import ModelFormMixin

from api_app.models import Change


class ChangeListView(ListView):
    model = Change
    template_name = "admin/change_list.html"
    paginate_by = 50


class ChangeDetailView(ModelFormMixin, DetailView):
    model = Change
    template_name = "admin/change_detail.html"
    pk_url_kwarg = "uuid"
    fields = ['uuid']

    def get_form_class(self):
        # https://github.com/django/django/blob/354c1524b38c9b9f052c1d78dcbfa6ed5559aeb3/django/contrib/admin/options.py#L670-L711
        # https://github.com/django/django/blob/354c1524b38c9b9f052c1d78dcbfa6ed5559aeb3/django/forms/models.py#L483
        # return modelform_factory(self.object.__class__)
        cls = modelform_factory(self.object.content_type.model_class(), exclude=[])
        print(cls)
        return cls

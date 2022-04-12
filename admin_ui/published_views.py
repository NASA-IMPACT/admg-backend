from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from api_app.models import Change

from . import utils, published_forms, mixins


class GenericListView(mixins.DynamicModelMixin, SingleTableMixin, FilterView):
    template_name = "api_app/published_list.html"

    def get_table_class(self):
        return self._model_config["published_table"]

    def get_filterset_class(self):
        return self._model_config["published_filter"]

    def get_context_data(self, **kwargs):
        conf = self._model_config
        return {
            **super().get_context_data(**kwargs),
            "display_name": conf["display_name"],
            "model_name": self._model_name,
            "url_name": conf["singular_snake_case"],
        }


class ModelObjectView(mixins.DynamicModelMixin, DetailView):
    fields = "__all__"

    def _initialize_form(self, form_class, disable_all=False, **kwargs):
        form_instance = form_class(**kwargs)

        # prevent fields from being edited
        if disable_all:
            for fieldname in form_instance.fields:
                form_instance.fields[fieldname].disabled = True

        return form_instance

    def _get_form(self, disable_all=False, **kwargs):
        form_class = published_forms.GenericFormClass(self._model_name)
        return self._initialize_form(form_class, disable_all, **kwargs)

    def get_object(self):
        return self._model_config['model'].objects.get(uuid=self.kwargs['pk'])


    def get_queryset(self):
        return self._model_config['model'].objects.all()

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "request": self.request,
        }


@method_decorator(login_required, name="dispatch")
class GenericDetailView(ModelObjectView):
    template_name = "api_app/published_detail.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "model_form": self._get_form(instance=kwargs.get("object"), disable_all=True),
            "model_name": self._model_name,
            "display_name": self._model_config["display_name"],
            "url_name": self._model_config["singular_snake_case"],
        }


@method_decorator(login_required, name="dispatch")
class GenericEditView(ModelObjectView):
    template_name = "api_app/published_edit.html"

    def post(self, request, **kwargs):
        # set object because the super().get_context_data looks for a self.object
        self.object = self.get_object()

        # getting form with instance and data gives a lot of changed fields
        # however, getting a form with initial and data only gives the required changed fields
        old_form = self._get_form(instance=self.object)
        new_form = self._get_form(data=request.POST, initial=old_form.initial, files=request.FILES)

        if not len(new_form.changed_data):
            context = self.get_context_data(**kwargs)
            context["message"] = "Nothing changed"
            return render(request, self.template_name, context)

        diff_dict = self._create_diff_dict(new_form)
        change_object = Change.objects.create(
            content_object=self.object,
            status=Change.Statuses.CREATED,
            action=Change.Actions.UPDATE,
            model_instance_uuid=kwargs.get("pk"),
            update=diff_dict,
            previous=old_form.data
        )
        return redirect(reverse("change-update", kwargs={"pk": change_object.uuid}))

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "model_form": self._get_form(instance=kwargs.get("object")),
            "model_name": self._model_name,
            "display_name": self._model_config["display_name"],
            "url_name": self._model_config["singular_snake_case"],
        }

    def _create_diff_dict(self, form):
        updated_values = utils.serialize_model_form(form)
        return {changed_key: updated_values[changed_key] for changed_key in form.changed_data}


@method_decorator(login_required, name="dispatch")
class GenericDeleteView(View):
    def dispatch(self, *args, **kwargs):
        model_to_query = self._model_config["model"]
        content_type = ContentType.objects.get_for_model(model_to_query)
        change_object = Change.objects.create(
            content_type=content_type,
            status=Change.Statuses.CREATED,
            action=Change.Actions.DELETE,
            model_instance_uuid=kwargs.get("pk"),
            update={},
        )
        change_object.save()
        return redirect(
            reverse("change-list", kwargs={'model': self._model_config['singular_snake_case']})
        )

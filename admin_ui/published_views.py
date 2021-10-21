from api_app.models import CREATED_CODE, IN_TRASH_CODE, PUBLISHED_CODE, UPDATE, Change
from data_models import serializers
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.views.generic.edit import ModelFormMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .config import MODEL_CONFIG_MAP
from .forms import TransitionForm
from .published_forms import GenericFormClass
from .utils import compare_values


def GenericListView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericListViewClass(SingleTableMixin, FilterView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = "api_app/published_list.html"
        table_class = MODEL_CONFIG_MAP[model_name]["table"]
        filterset_class = MODEL_CONFIG_MAP[model_name]["filter"]

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
                "model": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
                "url_name": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
            }

    return GenericListViewClass


class ModelObjectView(ModelFormMixin, DetailView):
    fields = "__all__"

    @staticmethod
    def is_published_or_trashed(change_instance):
        return (
            change_instance.status == PUBLISHED_CODE
            or change_instance.status == IN_TRASH_CODE
        )

    def _initialize_form(self, form_class, disable_all=False, **kwargs):
        form_instance = form_class(**kwargs)

        # prevent fields from being edited
        if disable_all:
            for fieldname in form_instance.fields:
                form_instance.fields[fieldname].disabled = True

        return form_instance

    def _get_form_from_model_name(self, model_name, disable_all=False, **kwargs):
        form_class = GenericFormClass(model_name)
        return self._initialize_form(form_class, disable_all, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "object": self.get_object(),
            "request": self.request,
        }

    def _create_diff_dict(self, form):
        diff_dict = {}
        for changed_key in form.changed_data:
            processed_value = Change._get_processed_value(form[changed_key].value())
            diff_dict[changed_key] = processed_value

        return diff_dict


def GenericDetailView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericDetailViewClass(ModelObjectView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = "api_app/published_detail.html"

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "model_form": self._get_form_from_model_name(
                    model_name, instance=kwargs.get("object"), disable_all=True
                ),
                "model_name": model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
            }

    return GenericDetailViewClass


def GenericEditView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericEditViewClass(ModelObjectView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = "api_app/published_edit.html"

        def post(self, request, **kwargs):
            model_instance = self.model.objects.get(uuid=kwargs.get("pk"))

            # do this here because the super().get_context_data looks for a self.object
            self.object = model_instance

            # getting form with instance and data gives a lot of changed fields
            # however, getting a form with initial and data only gives the required changed fields
            old_form = self._get_form_from_model_name(
                model_name, instance=model_instance
            )
            new_form = self._get_form_from_model_name(
                model_name, data=request.POST, initial=old_form.initial
            )

            kwargs = {**kwargs, "object": model_instance}
            context = self.get_context_data(**kwargs)
            if new_form.is_valid():
                if len(new_form.changed_data) > 0:
                    diff_dict = self._create_diff_dict(new_form)
                    model_to_query = MODEL_CONFIG_MAP[model_name]["model"]
                    content_type = ContentType.objects.get_for_model(model_to_query)
                    change_object = Change.objects.create(
                        content_type=content_type,
                        status=CREATED_CODE,
                        action=UPDATE,
                        model_instance_uuid=kwargs.get("pk"),
                        update=diff_dict,
                    )
                    change_object.save()
                    return redirect(
                        reverse(
                            f"{MODEL_CONFIG_MAP[model_name]['singular_snake_case']}-list-draft"
                        )
                    )

                context["message"] = "Nothing changed"
                return render(request, self.template_name, context)

            context["model_form"] = new_form
            return render(request, self.template_name, context)

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "model_form": self._get_form_from_model_name(
                    model_name, instance=kwargs.get("object")
                ),
                "model_name": model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
            }

    return GenericEditViewClass


@method_decorator(login_required, name="dispatch")
class DiffView(ModelObjectView):
    model = Change
    template_name = "api_app/published_diff.html"

    def _compare_forms(self, updated_form, original_form, field_names_to_compare):
        for field_name in field_names_to_compare:
            if not compare_values(
                original_form[field_name].value(), updated_form[field_name].value()
            ):
                updated_form.add_class(field_name, "changed-item")

    def _get_context_from_data(
        self, change_instance, editable_form, noneditable_published_form, **kwargs
    ):
        return {
            **super().get_context_data(**kwargs),
            "editable_update_form": editable_form,
            "noneditable_published_form": noneditable_published_form,
            "model_name": change_instance.model_name,
            "display_name": MODEL_CONFIG_MAP[change_instance.model_name][
                "display_name"
            ],
            "transition_form": TransitionForm(
                change=change_instance, user=self.request.user
            ),
            "disable_save": self.is_published_or_trashed(change_instance),
        }

    def initialize_forms(self, change_instance):
        model_instance = change_instance.content_object

        serializer_class = getattr(
            serializers, f"{change_instance.model_name}Serializer"
        )
        serializer_obj = serializer_class(
            instance=model_instance,
            data=change_instance.update,
            partial=True,
        )

        old_data_form = self._get_form_from_model_name(
            change_instance.model_name,
            disable_all=True,
            instance=model_instance,
            auto_id="readonly_%s",
        )

        if serializer_obj.is_valid():
            editable_form = self._get_form_from_model_name(
                change_instance.model_name,
                disable_all=self.is_published_or_trashed(change_instance),
            )
            editable_form.initial = {
                **old_data_form.initial,
                **{
                    key: serializer_obj.validated_data.get(key)
                    for key in change_instance.update
                },
            }

            # if published or trashed then the old data doesn't need to be from the database, it
            # needs to be from the previous field of the change_object
            if self.is_published_or_trashed(change_instance):
                for key, val in change_instance.previous.items():
                    old_data_form.initial[key] = val

                self._compare_forms(
                    editable_form, old_data_form, change_instance.previous
                )
            else:
                self._compare_forms(
                    editable_form, old_data_form, change_instance.update
                )
        else:
            raise Exception("Exception here")

        return editable_form, old_data_form

    def post(self, request, **kwargs):
        change_instance = self.model.objects.get(uuid=kwargs.get("pk"))
        _, noneditable_published_form = self.initialize_forms(change_instance)

        updated_form = self._get_form_from_model_name(
            change_instance.model_name,
            data=request.POST,
            initial=noneditable_published_form.initial,
        )

        if updated_form.is_valid():
            diff_dict = {
                **change_instance.update,
                **self._create_diff_dict(updated_form),
            }

            self._compare_forms(
                updated_form, noneditable_published_form, updated_form.changed_data
            )

            change_instance.update = diff_dict
            change_instance.save()

        # the super get_context_data wants an object
        self.object = change_instance
        context = self._get_context_from_data(
            change_instance, updated_form, noneditable_published_form, **kwargs
        )

        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        change_instance = kwargs.get("object")
        editable_form, noneditable_published_form = self.initialize_forms(
            change_instance
        )

        return self._get_context_from_data(
            change_instance, editable_form, noneditable_published_form, **kwargs
        )

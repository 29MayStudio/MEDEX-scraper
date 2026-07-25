import json
import datetime
import string

from django.contrib import admin
from admin_auto_filters.filters import AutocompleteFilter

from django.http import HttpResponse

from crawler.models import Medicine, Generic, Manufacturer, DosageForm, Indication, DrugClass


# change selection list count
# https://stackoverflow.com/questions/36474515/how-to-get-filtered-queryset-in-django-admin/36476084#36476084

# filtering
# https://gist.github.com/ahmedshahriar/4240f0451261c4bb8364dd5341c7cf59
# https://books.agiliq.com/projects/django-admin-cookbook/en/latest/filtering_calculated_fields.html


class AlphabetFilter(admin.SimpleListFilter):
    title = 'Name Alphabetically'
    parameter_name = 'alphabet'

    def lookups(self, request, model_admin):
        abc = list(string.ascii_lowercase)
        return ((c.upper(), c.upper()) for c in abc)

    def queryset(self, request, queryset):
        if self.value() and (queryset.model is Medicine):
            return queryset.filter(brand_name__startswith=self.value())
        if self.value() and (queryset.model is Generic):
            return queryset.filter(generic_name__startswith=self.value())
        if self.value() and (queryset.model is Manufacturer):
            return queryset.filter(manufacturer_name__startswith=self.value())


class MedicineItemInline(admin.StackedInline):
    model = Medicine


class GenericItemInline(admin.TabularInline):
    model = Generic


def export_to_json(model_admin, request, queryset):
    opts = model_admin.model._meta
    content_disposition = f'attachment; filename={opts.verbose_name_plural}.json'
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = content_disposition

    fields = [field for field in opts.get_fields() if not field.many_to_many \
              and not field.one_to_many]

    data = []
    for obj in queryset:
        row = {}
        for field in fields:
            value = getattr(obj, field.name)
            if value is None:
                row[field.name] = None
            elif isinstance(value, (int, float, bool, str)):
                row[field.name] = value
            elif isinstance(value, datetime.datetime):
                row[field.name] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, datetime.date):
                row[field.name] = value.strftime('%Y-%m-%d')
            else:
                row[field.name] = str(value)
        data.append(row)

    response.write(json.dumps(data, indent=4, ensure_ascii=False))
    return response


export_to_json.short_description = 'Export to JSON'


class GenericFilter(AutocompleteFilter):
    title = 'Generic'  # display title
    field_name = 'generic'  # name of the foreign key field


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('brand_id', 'brand_name', 'dosage_form', 'generic', 'manufacturer', 'type')
    list_filter = (GenericFilter, AlphabetFilter, 'type', 'created', 'dosage_form', )
    search_fields = ('brand_name', 'dosage_form')
    prepopulated_fields = {'slug': ('brand_name',)}
    raw_id_fields = ('generic', 'manufacturer')
    date_hierarchy = 'created'
    ordering = ('created',)
    actions = [export_to_json]


@admin.register(Generic)
class GenericAdmin(admin.ModelAdmin):
    list_display = ('generic_id', 'generic_name', 'monograph_link', 'drug_class', 'indication', 'descriptions_count')
    list_filter = ('created', 'descriptions_count', AlphabetFilter)
    search_fields = ('generic_name',)
    prepopulated_fields = {'slug': ('generic_name',)}
    raw_id_fields = ('drug_class', 'indication')
    date_hierarchy = 'created'
    ordering = ('created',)
    actions = [export_to_json]
    # readonly_fields = ('desc_count',) # add `desc_count` to list_display to display the number of descriptions
    # https://books.agiliq.com/projects/django-admin-cookbook/en/latest/filtering_calculated_fields.html


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('manufacturer_id', 'manufacturer_name', 'generics_count', 'brand_names_count')
    list_filter = ('created', AlphabetFilter,)
    search_fields = ('manufacturer_name',)
    prepopulated_fields = {'slug': ('manufacturer_name',)}
    date_hierarchy = 'created'
    ordering = ('created',)
    actions = [export_to_json]
    inlines = [MedicineItemInline]


@admin.register(DosageForm)
class DosageFormAdmin(admin.ModelAdmin):
    list_display = ('dosage_form_id', 'dosage_form_name', 'brand_names_count')
    list_filter = ('created', AlphabetFilter,)
    search_fields = ('dosage_form_name',)
    prepopulated_fields = {'slug': ('dosage_form_name',)}
    date_hierarchy = 'created'
    ordering = ('created',)
    actions = [export_to_json]


@admin.register(Indication)
class IndicationAdmin(admin.ModelAdmin):
    list_display = ('indication_id', 'indication_name', 'generics_count')
    list_filter = ('created', AlphabetFilter,)
    search_fields = ('indication_name',)
    prepopulated_fields = {'slug': ('indication_name',)}
    date_hierarchy = 'created'
    ordering = ('created',)
    actions = [export_to_json]
    inlines = [GenericItemInline]


@admin.register(DrugClass)
class DrugClassAdmin(admin.ModelAdmin):
    list_display = ('drug_class_id', 'drug_class_name', 'generics_count')
    list_filter = ('created', AlphabetFilter,)
    search_fields = ('drug_class_name',)
    prepopulated_fields = {'slug': ('drug_class_name',)}
    date_hierarchy = 'created'
    ordering = ('created',)
    actions = [export_to_json]

import json
import datetime
import logging
from django.core.management import BaseCommand
from crawler.models import Medicine, Generic, DosageForm, DrugClass, Indication, Manufacturer

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Export model data to JSON"

    def add_arguments(self, parser):
        parser.add_argument('model_name',
                            type=str,
                            help='model name for the json export, e.g. medicine, generic, dosage_form, drug_class, '
                                 'indication, manufacturer')

        parser.add_argument('outfile',
                            nargs='?',
                            type=str,
                            help='Save path, like </path/to/outfile.json> or "/data/medicine.json"')

    def handle(self, *args, **options):
        model_name = options['model_name']
        export_file = f"{options['outfile']}.json" if options['outfile'] else '{}.json'.format(model_name)
        logger.info("Exporting... %s" % model_name)

        model_dict = {
            'medicine': Medicine,
            'generic': Generic,
            'dosage_form': DosageForm,
            'drug_class': DrugClass,
            'indication': Indication,
            'manufacturer': Manufacturer
        }

        if model_name not in model_dict:
            logger.error(f"Invalid model name: {model_name}")
            return

        model_class = model_dict[model_name]

        fields = [field for field in model_class._meta.get_fields() if not field.many_to_many and not field.one_to_many]

        data = []
        for obj in model_class.objects.all():
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
                elif hasattr(value, '_meta'):
                    row[field.name] = str(value)
                    if field.name == 'generic':
                        row['generic_id'] = getattr(value, 'generic_id', None)
                    elif field.name == 'manufacturer':
                        row['manufacturer_id'] = getattr(value, 'manufacturer_id', None)
                else:
                    row[field.name] = str(value)
            data.append(row)

        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"{export_file} exported successfully.")

import pickle
import json
import requests
import numpy as np
import datetime
import pandas as pd
from api import Api

HEIRARCHICAL_TABLES = [
    {
        'table_name':'platform_type',
        'field_name':'foreign-platform_type-short_name'
    },
    {
        'table_name':'measurement_type',
        'field_name':'foreign-measurement_type-short_name'
    },
    {
        'table_name':'measurement_style',
        'field_name':'foreign-measurement_style-short_name'
    }
]

class Ingest:
    def __init__(self, df_file):
        self.api = Api('test')
        # self.db = pickle.load(open('ingest_data/db_20201028', 'rb')) # fresh_data_filtered
        self.db_raw = df_file # pickle.load(open('db_olympex_20201028', 'rb')) # fresh_data_filtered
        self.db = self.db_raw.copy()

        self.remove_multiple_gcmd_entries()
        self.handle_blank_values()
        self.order_tables()

        self.primary_key_map = json.load(open("config/mapping_primary.json"))
        self.foreign_key_uuid_map = self.get_foreign_key_map(generate_blank=True)
        self.ingest_order = json.load(open("config/ingest_order.json"))

        self.raw_validation_results = {}
        self.filtered_validation_results = {}

        self.ingest_log = []


    def pluralize_table_name(self, table_name):
        """many_to_many fields names are plural versions of the linked foreign table
        in the django orm. this will convert between the foreign table name and the
        correct pluralized form used for the m2m field name

        Args:
            table_name (str): table name

        Returns:
            str: pluralized table name
        """

        exceptions = {
            'repositorys': 'repositories'
        }

        plural = table_name + 's'
        plural = exceptions.get(plural, plural)

        return plural


    def format_table_name(self, table_name):
        """Table names need a special format to go through the validation endpoint:
        PartnerOrg instead of partner_org. This function handles this conversion as
        well as some exceptions.

        Args:
            table_name (str): table name in format partner_org

        Returns:
            str: table name in format PartnerOrg
        """

        exceptions = {
            'Iop': 'IOP',
            'Doi': 'DOI'
        }

        formatted_table_name = ''.join([word.capitalize() for word in table_name.split('_')])
        formatted_table_name = exceptions.get(formatted_table_name, formatted_table_name)

        return formatted_table_name


    def convert_nans(self, data):
        """convert all nans in input dict into 0

        Args:
            data (dict): {'field_name': value}

        Returns:
            filtered_data (dict): {'field_name': value}
        """

        filtered_data = {}
        for field_name, value in data.items():
            filtered_data[field_name] = value
            try:
                if np.isnan(value):
                    filtered_data[field_name] = 0
            except TypeError:
                pass

        return filtered_data


    def convert_dates(self, data):
        filtered_data = {}
        for field_name, value in data.items():
            filtered_data[field_name] = value
            if isinstance(value, datetime.datetime):
                filtered_data[field_name] = value.isoformat().split('T')[0]
                
        return filtered_data


    def remove_ignored_fields(self, data):
        """this is doing too many things. first it is removing unneeded data
        from the sheets import which is tagged with 'ignore' in the field name
        it also cleans up nan values and converts them to 0

        Args:
            data ([type]): [description]

        Returns:
            [type]: [description]
        """
        
        filtered_data = {}
        for field_name, value in data.items():
            if field_name == "ignore_code":
                filtered_data[field_name] = value
            elif 'ignore' not in field_name:
                filtered_data[field_name] = value
                
        return filtered_data


    def remove_nones(self, data):
        print('\n ----- Removing Nones')
        return {key:value for key, value in data.items() if value != 'none' and value != "Information Not Available"}


    def remove_field(self, data, field_name, field_value=None):
        """Accepts json data of fields and field values, along with a 
        field_value to be removed and an optional field_value to narrow
        the removal criteria.

        Args:
            data (dict): dict of field_names: field_values
            field_name (str): field name or column header from sheets
            field_value (str/int/?, optional): value to match against as a pre
                requisite for field removeal. Defaults to None which will execute
                a broad match.

        Returns:
            dict: dict with the removed field
        """
        
        if field_name in data.keys():
            if field_value:
                if data[field_name]==field_value:
                    data.pop(field_name)
            else:
                data.pop(field_name)
        return data


    def correct_values(self, table_name, column, wrong_value, correct_value):
        self.db[table_name][column] = self.db[table_name][column].apply(lambda x: x if x!=wrong_value else correct_value)


    def update_uuid_map(self, table_name, data, create_response):
        uuid = create_response['data']['action_info']['uuid_changed']
        primary_key = self.primary_key_map[table_name] # gets the correct column, usually short_name
        primary_value = data[primary_key] # finds the actual value for the primary key, usually the short_name

        self.foreign_key_uuid_map[table_name][primary_value] = uuid


    def resolve_many_to_many_keys(self, table_name, data):
        print('\n ----- Resolving Many to Many')
        
        # data should be json of the row
    
        primary_key = self.primary_key_map[table_name]
        primary_value = data[primary_key]
        m2m_table_names = [key for key in self.db[table_name].keys() if "table-" in key]
        
        print(f'{primary_key=}')
        print(f'{primary_value=}')
        print(f'{m2m_table_names=}')
        
        print('foreign info -----')
        for m2m_table_name in m2m_table_names:
            _, foreign_table, foreign_key = m2m_table_name.split("-")
            linking_table = f"{table_name}-to-{foreign_table}"
            foreign_values = self.db[linking_table][self.db[linking_table][table_name] == primary_value][foreign_table]
            
            # get's list of shortnames if running validation or list of uuids if running ingest
            if self._use_short_names:
                mapped_uuids = [i for i in foreign_values] # is actually just short names, not uuids
            else:
                mapped_uuids = [
                    self.foreign_key_uuid_map[foreign_table][val]
                        for val in foreign_values
                            if val != "Information Not Available" and self.foreign_key_uuid_map[foreign_table].get(val)
                ]

            plural_field = self.pluralize_table_name(foreign_table)
            
            # adds a new field with the new values and removes the original field
            data[plural_field] = mapped_uuids
            if data.get(m2m_table_name):
                del data[m2m_table_name]
                
            print(f'{foreign_table=}')
            print(f'{foreign_key=}')
            print(f'{linking_table=}')
            print(f'{foreign_values=}')
            print(f'{mapped_uuids=}')
            print()

        return data


    def resolve_foreign_keys(self, table_name, data):
        print('\n ----- Resolving Foreign Keys')
        # data should be json of the row


        fields = [key for key in data.keys() if "foreign-" in key]

        for field in fields:

            _, foreign_table, foreign_key = field.split("-")
            foreign_value = data[field]

            print()
            print(f'{foreign_value=}')
            print(f'{fields=}')

            # get's list of shortnames if running validation or list of uuids if running ingest
            if self._use_short_names:
                if table_name in ['platform_type', 'instrument_type', 'measurement_type', 'measurement_style']:
                    foreign_table = 'parent'
                data[foreign_table] = foreign_value
            else:
                if self.foreign_key_uuid_map[foreign_table].get(foreign_value):
                    mapped_uuid = self.foreign_key_uuid_map[foreign_table][foreign_value]   
                    if table_name in ['platform_type', 'instrument_type', 'measurement_type', 'measurement_style']:
                        foreign_table = 'parent'
                    data[foreign_table] = mapped_uuid
            del data[field]

        return data


    def remove_multiple_gcmd_entries(self):
        """ modifies self.db in place """

        # remove multiple gcmd links. This will need to be properly implemented in the future

        self.correct_values(
            table_name='platform_type',
            column='gcmd_uuid',
            wrong_value='227d9c3d-f631-402d-84ed-b8c5a562fc27, 06e037ed-f463-4fa3-a23e-8f694b321eb1',
            correct_value='227d9c3d-f631-402d-84ed-b8c5a562fc27')

        self.correct_values(
            table_name='platform_type',
            column='gcmd_uuid',
            wrong_value='57b7373d-5c21-4abb-8097-a410adc2a074, 491d3fcc-c097-4357-b1cf-39ccf359234, 2219e7fa-9fd0-443d-ab1b-62d1ccf41a89',
            correct_value='57b7373d-5c21-4abb-8097-a410adc2a074')

        self.correct_values(
            table_name='geographical_region',
            column='gcmd_uuid',
            wrong_value='d40d9651-aa19-4b2c-9764-7371bb64b9a7, 3fedcf7c-7b0c-4b51-abd2-2c54de713061',
            correct_value='d40d9651-aa19-4b2c-9764-7371bb64b9a7')

        self.correct_values(
            table_name='geophysical_concept',
            column='gcmd_uuid',
            wrong_value='0611b9fd-fd92-4c4d-87bb-bc2f22c548bc, 4dd22dc9-1db4-4187-a2b7-f5b76d666055',
            correct_value='0611b9fd-fd92-4c4d-87bb-bc2f22c548bc')

        self.correct_values(
            table_name='geophysical_concept',
            column='gcmd_uuid',
            wrong_value='c9e429cb-eff0-4dd3-9eca-527e0081f65c, 62019831-aaba-4d63-a5cd-73138ccfa5d0',
            correct_value='c9e429cb-eff0-4dd3-9eca-527e0081f65c')

        self.correct_values(
            table_name='geophysical_concept',
            column='gcmd_uuid',
            wrong_value='0af72e0e-52a5-4695-9eaf-d6fbb7991039, 637ac172-e624-4ae0-aac4-0d1adcc889a2',
            correct_value='0af72e0e-52a5-4695-9eaf-d6fbb7991039')


    def get_foreign_key_map(self, generate_blank):
        # TODO: can I remove the loading of saved maps once it runs smoothly?
        if generate_blank:
            foreign_key_uuid_map = {
                'platform_type': {},
                'home_base': {},
                'repository': {},
                'focus_area': {},
                'season': {},
                'measurement_type': {},
                'measurement_style': {},
                'measurement_region': {},
                'geographical_region': {},
                'geophysical_concept': {},
                'campaign': {},
                'platform': {},
                'instrument': {},
                'deployment': {},
                'iop': {},
                'significant_event': {},
                'partner_org': {},
                'collection_period': {},
                'gcmd_phenomena': {},
                'gcmd_project': {},
                'gcmd_platform': {},
                'gcmd_instrument': {},
                'measurement_keywords': {},
            }   
        else:
            foreign_key_uuid_map = pickle.load(open('foreign_key_uuid_map','rb'))

        return foreign_key_uuid_map   


    def handle_blank_values(self):
        # TODO: update this function after Deborah updates the sheets
        # add the default note for blank values
        columns_to_replace = [
            'description',
            'technical_contact',
            'spatial_resolution',
            'temporal_resolution',
            'radiometric_frequency'
        ]

        for column in columns_to_replace:
            self.correct_values(
                table_name='instrument',
                column=column,
                wrong_value='Information Not Available',
                correct_value='This data will be added in future versions'
            )

        # add the default note for blank values
        columns_to_replace = [
            'description',
            'technical_contact',
            'spatial_resolution',
            'temporal_resolution',
            'radiometric_frequency'
        ]

        for column in columns_to_replace:
            self.correct_values(
                table_name='instrument',
                column=column,
                wrong_value='Information Not Available',
                correct_value='This data will be added in future versions'
            )


    def order_heirarchical_table(self, table_name, field_name):
        """some tables have an internal heirarchy, and the parents need to be ingested first.
        Parents will have a value of 'none' and these will be put at the front of the table.
        modifies self.db in place

        Args:
            table_name (str): name of table to order
            field_name (str): name of field containing heirarchical type
        """

        first = self.db[table_name][self.db[table_name][field_name]=='none']
        second = self.db[table_name][self.db[table_name][field_name]!='none']
        self.db[table_name] = pd.concat([first, second])


    def order_tables(self):
        heirarchical_tables = [
            {
                'table_name':'platform_type',
                'field_name':'foreign-platform_type-short_name'
            },
            {
                'table_name':'measurement_type',
                'field_name':'foreign-measurement_type-short_name'
            },
            {
                'table_name':'measurement_style',
                'field_name':'foreign-measurement_style-short_name'
            }
        ]
        for table_data in heirarchical_tables:
            self.order_heirarchical_table(table_data['table_name'], table_data['field_name'])


    def remove_unwanted_codes(self, validation_dict):
        
        ignored_errors = {
            'code': ['unique', 'does_not_exist'],
            'message': ['valid UUID']
        }
        
        filtered_dict = validation_dict.copy()
        for field, validation_results in validation_dict.items():
            for result in validation_results:
                # loop through errors in ignored_errors dict
                for error_type, error_list in ignored_errors.items():
                    for error in error_list:
                        if error in result[error_type]:
                            filtered_dict.pop(field)

        return filtered_dict


    def filter_validation(self):
        
        filtered_validation = {}
        for table_name, table_values in self.raw_validation_results.items():
            filtered_validation[table_name] = []
            for entry in table_values:
                # filter if necessary
                if entry['validation_results'].get('success', True):
                    validation_dict = {}
                else:
                    print(entry)
                    raw_validation_entry_dict = json.loads(entry['validation_results']['message'])
                    validation_dict = self.remove_unwanted_codes(raw_validation_entry_dict)
                
                if validation_dict:
                    filtered_validation[table_name].append({
                        'original_data': entry['original_data'],
                        'validation_results': validation_dict
                    })

        self.filtered_validation_results = filtered_validation


    def validate_line(self, table_name, api_data):
        formatted_table_name = self.format_table_name(table_name)

        try:
            validation_response = self.api.validate_json(formatted_table_name, api_data, False)
        except:
            import ipdb; ipdb.set_trace()
            assert False
        validation_dict = json.loads(validation_response.content)

        self.raw_validation_results[table_name] = self.raw_validation_results.get(table_name, [])
        self.raw_validation_results[table_name].append({
            'original_data':api_data,
            'validation_results':validation_dict,
        })


    def log_ingest_results(self, api_data, api_response, table_name):
        if not(api_response['success']):

            primary_key = self.primary_key_map[table_name]
            primary_value = api_data.get(primary_key)

            if 'unique' in api_response['message']:
                self.ingest_log.append(f'{table_name}, {primary_value}, not ingested because of duplication')
            else:
                self.ingest_log.append(f'{table_name}, {primary_value}, not ingested because unknown error')
                self.ingest_log.append(f"{table_name}: {primary_value}, {json.dumps(api_data)}")
                self.ingest_log.append(f"{table_name}: {primary_value}, {json.dumps(api_response)}")
        else:
            print(table_name)
            self.update_uuid_map(table_name, api_data, api_response)
            self.ingest_log.append(f"{json.dumps(api_response)}")


    def ingest_line(self, table_name, api_data):
        api_response = self.api.create(table_name, api_data)
        self.log_ingest_results(api_data, api_response, table_name)


    def generate_collection_periods(self):
        """validation True will use short names instead of uuids"""
        collection_periods = {}
        for index, row in self.db["collection_period"].iterrows():
            row_dict = row.to_dict()

            row_dict = self.remove_ignored_fields(row_dict)
            row_dict = self.remove_nones(row_dict)
            row_dict = self.resolve_foreign_keys("collection_period", row_dict)

            row_dict['instruments'] = [row_dict['instrument']]
            del(row_dict['instrument'])

            cp_short_name = row_dict['short_name']
            if collection_periods.get(cp_short_name):
                collection_periods[cp_short_name]['instruments'].extend(row_dict['instruments'])
            else:
                collection_periods[cp_short_name] = row_dict

        return [collection_period for cp_short_name, collection_period in collection_periods.items()]


    def iterate_data(self, func):
        for table_name in self.ingest_order:
            for index, row in self.db[table_name].iterrows():
                print(table_name, index)
                api_data = row.to_dict()
                print(api_data)
                api_data = self.remove_ignored_fields(api_data)
                api_data = self.convert_nans(api_data)
                api_data = self.convert_dates(api_data)
                api_data = self.remove_nones(api_data)

                primary_key = self.primary_key_map[table_name]
                primary_value = api_data.get(primary_key)

                if primary_value:
                    api_data = self.resolve_many_to_many_keys(table_name, api_data)
                    api_data = self.resolve_foreign_keys(table_name, api_data)
        
                    api_data = self.remove_field(api_data, 'end_date', 'ongoing')

                    func(table_name, api_data)

                else:
                    # under what cercumstances does this actually execute?
                    if func == self.ingest_line:
                        self.ingest_log.append(f"{table_name}: {primary_key}, {json.dumps(api_data)}")
        
        collection_period_data = self.generate_collection_periods()
        for collection_period in collection_period_data:
            func('collection_period', collection_period)


        # ingested = []
        # for cp_short_name, collection_period in collection_periods.items():
        #     ingested.append(collection_period)


    def validate(self):
        self._use_short_names = True # modifies get_foriegn and resolve_many_to_many
        self.iterate_data(self.validate_line)
        self.filter_validation()


    def ingest(self):
        # ingests everything except for collection period?
        self._use_short_names = False
        self.iterate_data(self.api.create)


    def purge_database(self):
        # maybe recode this to use the apis once they are sped up?
        from data_models import models

        model_names = [
            'PlatformType',
            'NasaMission',
            'MeasurementType',
            'MeasurementStyle',
            'HomeBase',
            'FocusArea',
            'Season',
            'Repository',
            'MeasurementRegion',
            'GeographicalRegion',
            'GeophysicalConcept',
            'PartnerOrg',
            'GcmdProject',
            'GcmdInstrument',
            'GcmdPlatform',
            'GcmdPhenomena',
            'DOI',
            'Campaign',
            'Platform',
            'Deployment',
            'IOP',
            'SignificantEvent',
            'CollectionPeriod',
            'Instrument'
        ]

        for model_name in model_names:
            model = getattr(models, model_name)
            model.objects.all().delete()

''' Module containing methods to add content to the gcmd models

"import nansencloud.gcmd_keywords.add_lists" in 0001_initial.py and add content
after the last CreateModel command in the initial migration. E.g.,

migrations.RunPython(nansencloud.gcmd_keywords.add_lists.add_gcmd_instruments),
migrations.RunPython(nansencloud.gcmd_keywords.add_lists.add_gcmd_platforms),
migrations.RunPython(nansencloud.gcmd_keywords.add_lists.add_gcmd_science_keywords),
'''
import pythesint

def add_gcmd_platforms(apps, schema_editor):
    Platform = apps.get_model('gcmd_keywords', 'Platform')
    for platform in pythesint.get_list('gcmd_platforms'):
        if platform.keys()[0]=='Revision':
            continue
        pp = Platform(
                category = platform['Category'],
                series_entity = platform['Series_Entity'],
                short_name = platform['Short_Name'],
                long_name = platform['Long_Name']
            )
        pp.save()

def add_gcmd_instruments(apps, schema_editor):
    Instrument = apps.get_model('gcmd_keywords', 'Instrument')
    for instrument in pythesint.get_list('gcmd_instruments'):
        if instrument.keys()[0]=='Revision':
            continue
        ii = Instrument(
                category = instrument['Category'],
                instrument_class = instrument['Class'],
                type = instrument['Type'],
                subtype = instrument['Subtype'],
                short_name = instrument['Short_Name'],
                long_name = instrument['Long_Name']
            )
        ii.save()

def add_gcmd_science_keywords(apps, schema_editor):
    sciencekw = apps.get_model('gcmd_keywords', 'ScienceKeyword')
    for skw in pythesint.get_list('gcmd_science_keywords'):
        if skw.keys()[0]=='Revision':
            continue
        ii = sciencekw(
                category = skw['Category'],
                topic = skw['Topic'],
                term = skw['Term'],
                variable_level_1 = skw['Variable_Level_1'],
                variable_level_2 = skw['Variable_Level_2'],
                variable_level_3 = skw['Variable_Level_3'],
                detailed_variable = skw['Detailed_Variable'],
            )
        ii.save()

def add_data_centers(apps, schema_editor):
    dcs = apps.get_model('gcmd_keywords', 'DataCenter')
    for dc in pythesint.get_list('gcmd_data_centers'):
        if dc.keys()[0]=='Revision':
            continue
        dd = dcs(
                bucket_level0 = dc['Bucket_Level0'],
                bucket_level1 = dc['Bucket_Level1'],
                bucket_level2 = dc['Bucket_Level2'],
                bucket_level3 = dc['Bucket_Level3'],
                short_name = dc['Short_Name'],
                long_name = dc['Long_Name'],
                data_center_url = dc['Data_Center_URL'],
            )
        dd.save()

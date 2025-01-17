
from webbrowser import get
import pandas as pd
import numpy as np
import geopandas as gpd
from fiona import BytesCollection
from tobler.area_weighted import area_interpolate
#from . import load_raw_data
import os
import sys
#current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name
# where the current directory is present.
#parent = os.path.dirname(current)

# adding the parent directory to
# the sys.path.
#sys.path.append(parent)

from BODP_features.load_raw_data import get_maps_csv

"""Functions to merge data from Berlin's open data platform"""

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
dir_path = os.path.join(root_dir,"raw_data", "output_maps")
pr_2021 = get_maps_csv()['pr_2021'][['PLR_ID','BZR_NAME','geometry']]
pr_2021['PLR_ID'] = pr_2021['PLR_ID'].astype(int)
pr_2020 = get_maps_csv()['pr_2020']
pr_2020['RAUMID'] = pd.to_numeric(pr_2020['Plr_Nummer'])

def create_demo_mig_gdf():
    """returns a gdf with migration and demographic data on planungraum level 2021"""

    # Merge demo and migration df
    mig_data = get_maps_csv()['migration_data']
    gen_data = get_maps_csv()['demo_data']
    merged_data = gen_data.drop(
    columns=['BEZ', 'PGR', 'BZR', 'PLR', 'STADTRAUM', 'E_E00_01', 'E_E01_02', 'E_E02_03', 'E_E03_05',
       'E_E05_06', 'E_E06_07', 'E_E07_08', 'E_E08_10', 'E_E10_12', 'E_E12_14',
       'E_E14_15', 'E_E15_18', 'E_E18_21', 'E_E21_25', 'E_E25_27', 'E_E27_30',
       'E_E30_35', 'E_E35_40', 'E_E40_45', 'E_E45_50', 'E_E50_55', 'E_E55_60',
       'E_E60_63', 'E_E63_65', 'E_E65_67', 'E_E67_70', 'E_E70_75', 'E_E75_80',
       'E_E80_85', 'E_E85_90', 'E_E90_95', 'E_E95_110']).merge(
    mig_data.drop(
    columns=['ZEIT', 'BEZ', 'PGR', 'BZR', 'PLR', 'STADTRAUM', 'MH_E00_01', 'MH_E01_02', 'MH_E02_03', 'MH_E03_05',
       'MH_E05_06', 'MH_E06_07', 'MH_E07_08', 'MH_E08_10', 'MH_E10_12',
       'MH_E12_14', 'MH_E14_15', 'MH_E15_18', 'MH_E18_21', 'MH_E21_25',
       'MH_E25_27', 'MH_E27_30', 'MH_E30_35', 'MH_E35_40', 'MH_E40_45',
       'MH_E45_50', 'MH_E50_55', 'MH_E55_60', 'MH_E60_63', 'MH_E63_65',
       'MH_E65_67', 'MH_E67_70', 'MH_E70_75', 'MH_E75_80', 'MH_E80_85',
       'MH_E85_90', 'MH_E90_95', 'MH_E95_110'])
)
    # merge df with planungsräume 2020 geodatagrame (449 rows)
    demo_gdf = pr_2020[['RAUMID','geometry']].merge(
         merged_data, on='RAUMID')

    # interpolate merged gdf into planungsräume 2021 (542 rows)
    interpolate = area_interpolate(
        source_df=demo_gdf,
        target_df= pr_2021,
        extensive_variables=['E_E', 'E_EM', 'E_EW', 'E_EU1', 'E_E1U6', 'E_E6U15',
            'E_E15U18', 'E_E18U25', 'E_E25U55', 'E_E55U65', 'E_E65U80', 'E_E80U110',
            'MH_E', 'MH_EM', 'MH_EW', 'MH_U1', 'MH_1U6', 'MH_6U15', 'MH_15U18',
            'MH_18U25', 'MH_25U55', 'MH_55U65', 'MH_65U80', 'MH_80U110'])
    interpolate['mig_rate'] = interpolate.MH_E / interpolate.E_E
    return interpolate

def create_origin_gdf():
    ''' returns a gdf with the rate of regions of origin among population
    with migration background '''
    origin = get_maps_csv()['origin']
    # merge df with planungsräume 2020 geodatagrame (449 rows)
    merged = pr_2020[['RAUMID','geometry']].merge(
         origin, on='RAUMID')
    # interpolate data drom pr2020 to pr 2021
    interpolate = area_interpolate(
        source_df=merged,
        target_df= pr_2021,
        extensive_variables=['MH_E',
       'HK_EU15', 'HK_EU28', 'HK_Polen', 'HK_EheJug', 'HK_EheSU', 'HK_Turk',
       'HK_Arab', 'HK_Sonst', 'HK_NZOrd'])
    columns = ['HK_EU15', 'HK_EU28', 'HK_Polen', 'HK_EheJug', 'HK_EheSU',
       'HK_Turk', 'HK_Arab', 'HK_Sonst', 'HK_NZOrd']
    # compute rates
    for c in columns:
        interpolate[c] = interpolate[c] / interpolate.MH_E
    # drop unnecessary column
    interpolate.drop(columns='MH_E', inplace=True)
    return interpolate

def create_housing_gdf():
    """ Returns a geodatagrame on planungsräume 2021 with housing data"""
    housing_data = get_maps_csv()['housing_data']
    # change data type to numerical
    columns = ['angebotsmi', 'aenderung_', 'anteil_lei',
       'anteil_soz', 'anteil_sta', 'entwicklun', 'wohndauer', 'wohnungsum',
       'wohnungs_1', 'wohnungsve', 'wohnungs_2']
    for c in columns:
        housing_data[f'{c}'] = pd.to_numeric(housing_data[f'{c}'])
    # interpolate data to planungsräume level
    interpolate = area_interpolate(
    source_df=housing_data,
    target_df=pr_2021,
    intensive_variables=['angebotsmi', 'aenderung_', 'anteil_lei',
       'anteil_soz', 'anteil_sta', 'entwicklun', 'wohndauer', 'wohnungsum',
       'wohnungs_1', 'wohnungsve', 'wohnungs_2'])
    interpolate.columns =  ['ave_rent', 'dyn_wel_po', 'welf_po', 'social_housing',
                            'public_housing', 'dyn_ew', 'five_y_pls', 'rent_to_pr',
                            'dyn_r_to_p', 'sales', 'dyn_sales', 'geometry'
                              ]
    #merged_data_2021 = pr_2021[['geometry']].merge(interpolate, on='geometry')
    return interpolate

def create_social_gdf():
    """ Returns a geodataframe with the social index (unemployment rate, social
    welfare beneficiaries and child poverty on planungsräume 2021 level"""
    social_index = get_maps_csv()['social_index']
    columns = ['EW', 'ant_arbeitslose', 'ant_transfer',
       'Kinderarmut', 'ant_arbeitslose_dyn', 'ant_transfer_dyn',
       'Kinderarmut_dyn']
    for c in columns:
        social_index[f'{c}'] = pd.to_numeric(social_index[f'{c}'])
    social_index['PLR_ID'] = pd.to_numeric(social_index.Nummer)
    social_index.drop(columns=['Nummer', 'Name'], inplace=True)
    social_index.columns = ['EW', 'unempl', 'welfare',
                            'child_pov', 'dyn_unempl',
                            'dyn_welf', 'dyn_child', 'PLR_ID']
    merged = pr_2021.merge(social_index, on='PLR_ID')
    return merged

def create_umwelt_gdf():
    """ Returns a geodataframe with environmental features on planungsräume 2021 """
    environment =  get_maps_csv()['environment']
    environment.drop(columns=['plr_name', 'status', 'anz_bel', 'wohnlage'],
                     inplace= True)

    # area interpolation from blocks to planungsräume 2021
    interpolate =  area_interpolate(environment, pr_2021,
                    categorical_variables=['laerm', 'luft', 'gruen', 'bio'])
    columns = ['laerm_mittel', 'laerm_None', 'laerm_hoch', 'laerm_sehr hoch',
       'laerm_niedrig - sehr niedrig', 'luft_hoch', 'luft_mittel',
       'luft_gering', 'gruen_schlecht, sehr schlecht', 'gruen_gut, sehr gut',
       'gruen_mittel', 'gruen_None', 'bio_hoch', 'bio_mittel', 'bio_gering']

    # rounding probabilities of belonging to each cat --> results in one hot encoding
    for c in columns:
        interpolate[f'{c}']= round(interpolate[f'{c}'])

    # reverse OHE
    interpolate['noise'] = interpolate[['laerm_mittel', 'laerm_None',
                                        'laerm_hoch', 'laerm_sehr hoch',
                                        'laerm_niedrig - sehr niedrig']].idxmax(1)
    interpolate['air'] = interpolate[['luft_hoch', 'luft_mittel',
                                    'luft_gering']].idxmax(1)

    interpolate['green'] = interpolate[['gruen_schlecht, sehr schlecht', 'gruen_gut, sehr gut',
                                        'gruen_mittel', 'gruen_None']].idxmax(1)

    interpolate['bio'] = interpolate[['bio_hoch', 'bio_mittel', 'bio_gering']].idxmax(1)

    # dropping unnecessary columns
    interpolate.drop(columns=['laerm_mittel', 'laerm_None','laerm_hoch',
                            'laerm_sehr hoch','laerm_niedrig - sehr niedrig',
                            'luft_hoch','luft_mittel','luft_gering',
                            'gruen_schlecht, sehr schlecht', 'gruen_gut, sehr gut',
                            'gruen_mittel', 'gruen_None', 'bio_hoch', 'bio_mittel',
                            'bio_gering'], inplace=True)

    # noise load --> 0 is good, 3 is bad
    interpolate['noise'] = interpolate['noise'].map({'laerm_mittel':1, 'laerm_niedrig - sehr niedrig':0, 'laerm_hoch': 2, 'laerm_sehr hoch': 3})

    # bioclimatic load --> 0 is good, 2 is bad
    interpolate['bio'] = interpolate['bio'].map({'bio_mittel':1, 'bio_gering':0, 'bio_hoch': 2})

    # air pollution load --> 0 is good, 2 is bad
    interpolate['air'] = interpolate['air'].map({'luft_mittel':1, 'luft_gering':0, 'luft_hoch': 2})

    # green supply --> 0 is good, 2 is bad
    interpolate['green'] = interpolate['green'].map({'gruen_schlecht, sehr schlecht': 2, 'gruen_mittel': 1, 'gruen_gut, sehr gut': 0})

    return interpolate

def create_building_age_gdp():
    """ Returns a dataframe with building age"""
    building_age = get_maps_csv()['building_age']
    # transforming and imputing values
    building_age.replace(np.nan, 0, inplace=True)
    building_age.x2011_2015 = building_age.x2011_2015.replace([np.nan, '1 - 3'],
                                                              [0,2]).astype(float)
    # creating buffer size 0 to avoid error 'self intersection'
    building_age['buffer'] = building_age.buffer(0)
    building_age.set_geometry('buffer', inplace=True)
    # interpolate from blocks to planungsräume 2021
    interpol = area_interpolate(building_age,
                            pr_2021,
                            extensive_variables=['x_bis_1900', 'x1901_1910', 'x1911_1920', 'x1921_1930',
       'x1931_1940', 'x1941_1950', 'x1951_1960', 'x1961_1970', 'x1971_1980',
       'x1981_1990', 'x1991_2000', 'x2001_2010', 'x2011_2015', 'ew2015'])
    interpol['tot_build'] = np.sum(interpol[['x_bis_1900','x1901_1910',
    'x1911_1920', 'x1921_1930', 'x1931_1940', 'x1941_1950', 'x1951_1960',
    'x1961_1970', 'x1971_1980', 'x1981_1990', 'x1991_2000', 'x2001_2010',
    'x2011_2015']], axis=1)
    interpol['B1940'] = (interpol['x_bis_1900'] + interpol['x1901_1910'] + interpol['x1911_1920'] + interpol['x1921_1930']+ interpol['x1931_1940'])/ interpol['tot_build']
    interpol['B1941_1990'] = (interpol['x1941_1950'] + interpol['x1951_1960'] + interpol['x1961_1970'] + interpol['x1971_1980'] + interpol['x1981_1990'])/ interpol['tot_build']
    interpol['B1991_2015'] = (interpol['x1991_2000'] + interpol['x2001_2010'] + interpol['x2011_2015'])/ interpol['tot_build']
    interpol['B_age'] = interpol[['B1940','B1941_1990','B1991_2015']].idxmax(axis=1)
    return interpol

def create_green_gdf():
    """ Returns a geodatafram with vegetation volume / sqm and the change between 2010 and 2020"""
    green_vol = get_maps_csv()['green_vol']
    reduced = green_vol[['vegproz202','vegvola201', 'vegvola202', 'changegvz', 'geometry']]
    join = reduced.sjoin(pr_2021)
    dissolve = join.dissolve(by='PLR_ID',aggfunc={'vegvola201': 'sum',
                                                    'vegvola202': 'sum',
                                                    'vegproz202': 'mean',
                                                    'changegvz': 'mean'})

    dissolve['area'] = dissolve.area
    dissolve['vegpm20'] = dissolve.vegvola202/dissolve.area
    dissolve['vegpm10'] = dissolve.vegvola201/dissolve.area
    dissolve['change'] = dissolve.vegpm20 - dissolve.vegpm10
    dissolve['ch_rate'] = (dissolve.change * 100) / dissolve.vegpm10

    dissolve = dissolve[[ 'vegpm20', 'vegpm10', 'change', 'ch_rate', 'geometry']].reset_index()

    merged = pr_2021[['PLR_ID','geometry']].merge(
        dissolve.drop(columns='geometry'), on='PLR_ID', how='left').drop(
        columns=['PLR_ID'])

    return merged

def create_school_gdf():
    schools = get_maps_csv()['schools']
    schools['geometry'] = schools.buffer(500)
    school_dummies  = pd.get_dummies(schools[['schultyp']])
    merged = schools.merge(school_dummies, left_index=True, right_index=True)[['schultyp_Andere Schule',
            'schultyp_Berufsschule','schultyp_Grundschule', 'schultyp_Gymnasium','schultyp_Integrierte Sekundarschule',
            'schultyp_Privatschule','schultyp_Schule mit sonderpädagogischem Förderschwerpunkt', 'geometry']]

    joined = pr_2021[['PLR_ID','geometry']].sjoin(merged).drop(columns=('index_right'))
    joined.columns=['PLR_ID','geometry', 'other_sch', 'vocat_sch', 'primary_sch', 'Gymnasium',
                    'secon_sch', 'priv_school', 'sp_nee_sch']

    dissolve = joined.dissolve(
        by='PLR_ID',aggfunc='sum').reset_index()

    merged = pr_2021[['PLR_ID','geometry']].merge(
            dissolve.drop(columns='geometry'), on='PLR_ID', how='left').drop(
            columns=['PLR_ID']).replace(np.nan, 0)

    return merged

def create_kita_gdf():
    ''' returns a GeoDataFrame with the amount of Kindergartens within 500m per Planungsraum '''
    kita = get_maps_csv()['kindergartens']
    kita['geometry'] = kita.buffer(500)
    joined = pr_2021.sjoin(kita)
    amount= pd.DataFrame({'kita':joined.groupby(by='PLR_ID').size()}).reset_index()
    merged = pr_2021[['PLR_ID','geometry']].merge(
        amount, on='PLR_ID', how='left').drop(
        columns=['PLR_ID']).replace(
        np.nan, 0)
    return merged

def create_public_transport():
    stations = gpd.read_file('/Users/Safia/code/Safiaaaaa/YouthInTheCity/raw_data/maps/stations.shp')
    stations['geometry'] = stations.buffer(500)
    joined = pr_2021.sjoin(stations)
    amount= pd.DataFrame({'stations':joined.groupby(by='PLR_ID').size()}).reset_index()
    merged = pr_2021[['PLR_ID','geometry']].merge(
        amount, on='PLR_ID', how='left').drop(
        columns=['PLR_ID']).replace(
        np.nan, 0)
    return merged

def get_bodp_data():
    merged = create_demo_mig_gdf().merge(
        create_origin_gdf(), on='geometry').merge(
        create_housing_gdf(), on='geometry').merge(
        create_social_gdf(), on='geometry').merge(
        create_umwelt_gdf(), on='geometry').merge(
        create_building_age_gdp(), on='geometry').merge(
        create_green_gdf(), on='geometry').merge(
        create_school_gdf(), on='geometry').merge(
        create_kita_gdf(), on='geometry').merge(
        create_public_transport(), on='geometry')

    merged.to_file(os.path.join(dir_path, 'bodp_features.shp'))
    return merged


if __name__ == '__main__':
    create_origin_gdf()
    #print("hello")

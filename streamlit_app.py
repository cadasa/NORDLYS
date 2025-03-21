import streamlit as st

st.set_page_config(page_title="NORDLYS DASHBOARD", page_icon='logo.jpg', layout='wide', initial_sidebar_state='auto')

import matplotlib.pyplot as plt
import matplotlib as mpl
from striplog import Striplog, Legend, Component, Interval, Lexicon
import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
import petrodc.npd as dc
import pandas as pd
#import plotly.express as px
#import plotly.graph_objects as go
import re
import time
import string
import datetime
import os
import streamlit.components.v1 as components
from streamlit_vega_lite import vega_lite_component, altair_component
import altair as alt
import geopandas as gpd
from streamlit_folium import folium_static
import folium
from folium.plugins import MiniMap
#from IPython.display import HTML, display

try:
    from app_secrets import MINIO_ACCESS_KEY, MINIO_ENCRYPT_KEY
except:
    access_key=os.getenv("MINIO_ACCESS_KEY")
    secret_key=os.getenv("MINIO_SECRET_KEY")

@st.cache_resource
def read_welldata():
    well_litho_npd = dc.wellbore(3)
    df_units = pd.read_excel('https://factpages.npd.no/ReportServer_npdpublic?/FactPages/TableView/strat_litho_overview&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=EXCEL&Top100=false&IpAddress=not_used&CultureCode=en')
    df_wells = pd.read_excel('https://factpages.npd.no/ReportServer_npdpublic?/FactPages/Statistics/wellbore_count_figure_entry&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=EXCEL&IpAddress=not_used&CultureCode=en',sheet_name=2, skiprows=[0])
    tbl_wells = df_wells.drop(df_wells.columns[[0,8]], axis=1)
    tbl_wells = tbl_wells.drop(tbl_wells.columns[6:], axis=1)
    tbl_wells = tbl_wells.fillna("")
    tbl_wells.index = tbl_wells.index + 1
    tbl_wells.columns.values[[1,3,5]] = ['Total per Area', 'Total per Type/Area', 'No. of Wells']
    tbl_wells.loc[:,'Total per Area']=tbl_wells.loc[:,'Total per Area'].astype('str').str.replace(r"\.0",'')
    tbl_wells.loc[:,'Total per Type/Area']=tbl_wells.loc[:,'Total per Type/Area'].astype('str').str.replace(r"\.0",'')

    well_his_npd = dc.wellbore(4)
    well_coord_npd = dc.wellbore(10)
    well_doc_npd = dc.wellbore(7)

    well_coord_npd['wlbNsDecDeg']=well_coord_npd['wlbNsDecDeg'].astype(float)
    well_coord_npd['wlbEwDesDeg']=well_coord_npd['wlbEwDesDeg'].astype(float)
    well_coord_npd['wlbEntryDate'] = pd.to_datetime(well_coord_npd['wlbEntryDate'],format='%d.%m.%Y')
    well_coord_npd=well_coord_npd.sort_values(by=['wlbEntryDate'], ascending=True)
    well_coord_npd["wlbPurposePlanned"] = well_coord_npd["wlbPurposePlanned"].fillna("NOT AVAILABLE")
#    well_coord_npd["wlbContent"] = well_coord_npd["wlbContent"].fillna("NOT AVAILABLE")
    well_coord_npd['year']=well_coord_npd['wlbEntryDate'].dt.year
#    well_coord_npd["wlbEntryDate"] = well_coord_npd["wlbEntryDate"].fillna("NOT AVAILABLE")
#    well_coord_npd['year']=well_coord_npd['year'].fillna("")

#    ctr=gpd.read_file("https://github.com/simonepri/geo-maps/releases/download/v0.6.0/countries-coastline-1km.geo.json")
#    no=pd.DataFrame(ctr.loc[ctr.loc[:,'A3']=='NOR',:].reset_index(drop=True)['geometry'])
#    poly=no.geometry[0]
#    df_coasline_no = pd.DataFrame([])
#    for x, y in poly[1].exterior.coords:
#        row=pd.DataFrame([['poly_2',x,y]])
#    df_coasline_no = df_coasline_no.append(row).reset_index(drop=True)
    df_coasline_no = pd.read_csv("nor.csv")
    well_litho_npd.loc[:,'lsuTopDepth']=well_litho_npd.loc[:,'lsuTopDepth'].astype(float)
    well_litho_npd.loc[:,'lsuBottomDepth']=well_litho_npd.loc[:,'lsuBottomDepth'].astype(float)
    well_litho_npd.loc[:,'lsuNpdidLithoStrat']=well_litho_npd.loc[:,'lsuNpdidLithoStrat'].astype(float).astype('Int64')
    well_litho_npd.loc[:,'lsuName']=well_litho_npd.loc[:,'lsuName'].astype('str')
    well_litho_npd.loc[well_litho_npd['lsuBottomDepth']<well_litho_npd['lsuTopDepth'],'lsuBottomDepth'] = well_litho_npd.loc[well_litho_npd['lsuBottomDepth']<well_litho_npd['lsuTopDepth'],'lsuTopDepth']
    return (well_litho_npd, df_wells, tbl_wells, df_units, well_his_npd, well_coord_npd, well_doc_npd, df_coasline_no)

@st.cache_resource
def read_fielddata():
    prod_fields = pd.read_csv('http://hotell.difi.no/download/npd/field/production-yearly-by-field',sep=';')
    df_fields = pd.read_csv('http://hotell.difi.no/download/npd/field/reserves',sep=';')
#    df_dsc = pd.read_csv('https://factpages.npd.no/downloads/csv/dscArea.zip')
    gdf_dsc = gpd.read_file("https://factpages.npd.no/downloads/shape/dscArea.zip")
#    gdf_dsc = gdf_dsc.loc[gdf_dsc.loc[:,'geometry']!=None,:]
    df_field_des = pd.read_csv('http://hotell.difi.no/download/npd/field/description',sep=';')
    df_dsc_des = pd.read_csv('https://factpages.npd.no/ReportServer_npdpublic?/FactPages/TableView/discovery_description&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=not_used&CultureCode=en')
    df_dsc_res = pd.read_csv('https://factpages.npd.no/ReportServer_npdpublic?/FactPages/TableView/discovery_reserves&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&rs:Format=CSV&Top100=false&IpAddress=not_used&CultureCode=en')
    df_fld = pd.read_excel('https://www.norskpetroleum.no/generator/csv.php?lang=en&from=factItemList&type=field&title=Fields&columns=name::Field+name||area::Area||status::Status||discoveryYear::Disc.+year||originalOE::Orig.+res.||remainingOE::Rem.+res.||productionStart::Prod.+start||companyName::Operator', skiprows=[0,1])
    df_dsc = pd.read_excel('https://www.norskpetroleum.no/generator/csv.php?lang=en&from=factItemList&type=discovery&title=Discoveries&columns=name::Discovery+name||area::Area||year::Disc.+year||sumOE::Resource+estimate||hydroCarbonType::Type||resourceClass::Resource+class||status::Activity+status||operatorCompany::Operator', skiprows=[0,1])
    df_dsc.columns.values[[0,1,2,3,4,6,7]] = ['Name', 'Main Area', 'Discovery Year', 'Recoverable OE', 'HC Type', 'Status', 'Operator']
    df_dsc['Remaining OE'] = df_dsc['Recoverable OE']
    df_dsc = df_dsc[['Name', 'Main Area', 'Status', 'Discovery Year', 'Recoverable OE', 'Remaining OE', 'Operator','HC Type']]
    df_fld.columns.values[[0,1,3,4,5,7]] = ['Name', 'Main Area', 'Discovery Year', 'Recoverable OE', 'Remaining OE', 'Operator']
    df_fld = df_fld[['Name', 'Main Area', 'Status', 'Discovery Year', 'Recoverable OE', 'Remaining OE', 'Operator']]
    tmp_dsc = gdf_dsc[['fieldName','Dctype']]
    tmp_dsc = tmp_dsc.loc[tmp_dsc.loc[:,'fieldName'].isin(df_fld['Name'].to_list()),:]
    tmp_dsc = tmp_dsc.drop_duplicates(subset = ['fieldName']).reset_index(drop=True)
    df_fld = df_fld.merge(tmp_dsc,"left",left_on='Name',right_on='fieldName',
                    indicator=False, validate='one_to_one')
    df_fld = df_fld[['Name', 'Main Area', 'Status', 'Discovery Year', 'Recoverable OE', 'Remaining OE', 'Operator', 'Dctype']]
    df_fld.columns.values[7] = 'HC Type'
    df_dsc_fld = pd.concat([df_fld,df_dsc],axis=0).reset_index(drop=True)
    prod_fields.loc[:,'prfPrdOeNetMillSm3']=prod_fields.loc[:,'prfPrdOeNetMillSm3'].str.replace(r"\(",'')
    prod_fields.loc[:,'prfPrdOeNetMillSm3']=prod_fields.loc[:,'prfPrdOeNetMillSm3'].str.replace(r"\)",'')
    prod_fields.loc[:,'prfPrdNGLNetMillSm3']=prod_fields.loc[:,'prfPrdNGLNetMillSm3'].str.replace(r"\(",'')
    prod_fields.loc[:,'prfPrdNGLNetMillSm3']=prod_fields.loc[:,'prfPrdNGLNetMillSm3'].str.replace(r"\)",'')
    prod_fields.loc[:,'prfPrdGasNetBillSm3']=prod_fields.loc[:,'prfPrdGasNetBillSm3'].str.replace(r"\(",'')
    prod_fields.loc[:,'prfPrdGasNetBillSm3']=prod_fields.loc[:,'prfPrdGasNetBillSm3'].str.replace(r"\)",'')
    prod_fields.loc[:,'prfPrdOilNetMillSm3']=prod_fields.loc[:,'prfPrdOilNetMillSm3'].str.replace(r"\(",'')
    prod_fields.loc[:,'prfPrdOilNetMillSm3']=prod_fields.loc[:,'prfPrdOilNetMillSm3'].str.replace(r"\)",'')
    prod_fields.loc[:,'prfPrdCondensateNetMillSm3']=prod_fields.loc[:,'prfPrdCondensateNetMillSm3'].astype('str').str.replace(r"\(",'')
    prod_fields.loc[:,'prfPrdCondensateNetMillSm3']=prod_fields.loc[:,'prfPrdCondensateNetMillSm3'].astype('str').str.replace(r"\)",'')
    prod_fields.loc[:,'prfPrdOeNetMillSm3']=prod_fields.loc[:,'prfPrdOeNetMillSm3'].astype(float)
#    prod_fields.loc[:,'prfYear']=pd.to_datetime(prod_fields.loc[:,'prfYear'], format='%Y')
    prod_fields.loc[:,'Year']=prod_fields.loc[:,'prfYear'].astype(str)
    prod_fields.loc[:,'Field']=prod_fields.loc[:,'prfInformationCarrier'].astype(str)
    cum_prod = prod_fields.groupby('prfInformationCarrier')['prfPrdOeNetMillSm3'].transform(lambda x: x.cumsum())
    prod_fields['Cum_Prod'] = cum_prod
    prod_fields = prod_fields.merge(df_fields,"left",left_on='prfInformationCarrier',right_on='fldName',
                indicator=False, validate='many_to_one')
#    prod_fields = prod_fields[prod_fields['_merge']=='both']
    prod_fields['Remaining_Reserves'] = prod_fields['fldRecoverableOE'] - prod_fields['Cum_Prod']
    prod_fields.loc[prod_fields.loc[:,'Remaining_Reserves']<0.0,'Remaining_Reserves']=0.00
    return (prod_fields,gdf_dsc,df_field_des,df_dsc_des,df_dsc_res,df_fields,df_dsc_fld)

def main():
    st.title("NORDLYS: Norwegian Oil&gas Resource Dashboard and Lithostratigraphic Yielded Solution")
    st.write(" ")
    st.write(" ")
    st.sidebar.image("https://25.media.tumblr.com/tumblr_mbhrgvN68f1qcu8zqo6_r1_250.gif", use_container_width=True)
    st.sidebar.title("Navigation")
    goto = st.sidebar.radio('Go to:',['BASEMAP', 'DISCOVERIES & FIELDS (D&F)', 'WELLS & LYS'])

    if goto == 'BASEMAP':
#        with st.container():
        st.header("BASEMAP OF NORWEGIAN CONTINENTAL SHELF")
        st.subheader("**Resource Map Contains Structural Elements, Blocks, Discoveries, Fields and Wells**")
#            components.iframe("https://cadasa.github.io/", height=975)
        st.write(" ")
        st.markdown(f"""<iframe width="100%" height="600" frameborder="0"
            src="https://cadasa.github.io/lisno_map.html"></iframe>
            """, unsafe_allow_html=True)
        st.sidebar.markdown(
                "**NORDLYS** helps users visualize data from NPD's FactPages as beautifully as seeing the **Northern Lights**(aka Aurora Borealis)"
                )
        st.sidebar.success(
                        '✅ It provides an accessible way to see ***trends***, ***outliers*** and ***patterns*** in data'
                        ' using **interactive visual tools** such as: ***charts***, ***graphs*** and ***maps***.')
        col1, col2, col3 = st.columns([2.5,5,2.5])
        with col2.container():
            with st.spinner("Please discover the map above while NORDLIS uploading data from NPD's FactPages..."):
                time.sleep(5)
        col1, col2, col3,col4,col5 = st.columns([2,1.5,3,1.5,2])
        with col3.container():
            well_litho_npd, df_wells, tbl_wells, df_units, well_his_npd, well_coord_npd, well_doc_npd, df_coasline_no = read_welldata()
            prod_fields,gdf_dsc,df_field_des,df_dsc_des,df_dsc_res,df_fields,df_dsc_fld = read_fielddata()

#    elif goto == 'PRODUCTION FIELDS':
#        with st.container():
#        st.header("PRODUCTION FIELDS")
#        field()

    elif goto == 'DISCOVERIES & FIELDS (D&F)':
#        with st.container():
#        st.header("DISCOVERIES & FIELDS")
        st.sidebar.write(" ")
        col1, col2, col3 = st.sidebar.columns([0.9,7.6,1.5])
        daf = col2.select_slider("Slide to select:",options=['D&F', 'Production Fields'],value='D&F')
        if daf == 'D&F':
            st.header("DISCOVERIES & FIELDS (D&F)")
            overview()
#            st.sidebar.write(" ")
#            st.sidebar.write(" ")
        elif daf == 'Production Fields':
            st.header("PRODUCTION FIELDS")
            field()
            st.sidebar.write(" ")
            st.sidebar.write(" ")

    elif goto == 'WELLS & LYS':
        st.sidebar.write(" ")
        col1, col2, col3 = st.sidebar.columns([0.9,7.6,1.5])
        wal = col2.select_slider("Slide to select:",options=['Wells', 'LYS'],value='Wells')
        if wal == 'Wells':
            st.header("WELLS")
            wellbores()
        elif wal == 'LYS':
            st.header("LITHOSTRATIGRAPHIC YIELDED SOLUTION")
            well()
        st.sidebar.write(" ")
        st.sidebar.write(" ")

    st.sidebar.markdown(
        "**Developed by:** [KHANH NGUYEN](mailto:khanhduc@gmail.com)")
    st.sidebar.markdown(
        "**Based on data from:** [FACTPAGES](https://factpages.npd.no/en/)"
        )
    st.sidebar.markdown('**Sponsored by:**')
    st.sidebar.image('./logo.png', use_container_width=True)
    return None

def field():
    col1, col2,col3 = st.sidebar.columns([0.9,7.7,1.4])
#    well_litho_npd, df_wells, tbl_wells, df_units, well_his_npd, well_coord_npd, well_doc_npd = read_welldata()
    prod_fields,gdf_dsc,df_field_des,df_dsc_des,df_dsc_res,df_fields,df_dsc_fld = read_fielddata()
    prod_fields = prod_fields.dropna()
    prod_fields['Production'] = prod_fields['prfPrdOeNetMillSm3']
    prod_fields.loc[:,'prfPrdOilNetMillSm3']=prod_fields.loc[:,'prfPrdOilNetMillSm3'].astype(float)
    sum_oil = prod_fields.groupby('prfYear')['prfPrdOilNetMillSm3'].transform(lambda x: x.sum())
    prod_fields['Sum_Oil'] = sum_oil
    prod_fields.loc[:,'prfPrdGasNetBillSm3']=prod_fields.loc[:,'prfPrdGasNetBillSm3'].astype(float)
    sum_gas = prod_fields.groupby('prfYear')['prfPrdGasNetBillSm3'].transform(lambda x: x.sum())
    prod_fields['Sum_Gas'] = sum_gas
#        field.loc[:,'fldRecoverableGas']=field.loc[:,'fldRecoverableGas'].astype(float)
#        field.loc[:,'prfPrdGasNetMillSm3']=field.loc[:,'prfPrdGasNetMillSm3'] * 1000.0
    prod_fields.loc[:,'prfPrdNGLNetMillSm3']=prod_fields.loc[:,'prfPrdNGLNetMillSm3'].astype(float)
    sum_NGL = prod_fields.groupby('prfYear')['prfPrdNGLNetMillSm3'].transform(lambda x: x.sum())
    prod_fields['Sum_NGL'] = sum_NGL
    prod_fields.loc[:,'prfPrdCondensateNetMillSm3']=prod_fields.loc[:,'prfPrdCondensateNetMillSm3'].astype(float)
    sum_cond = prod_fields.groupby('prfYear')['prfPrdCondensateNetMillSm3'].transform(lambda x: x.sum())
    prod_fields['Sum_Condensate'] = sum_cond
    Sum_Production = prod_fields.groupby('prfYear')['Production'].transform(lambda x: x.sum())
    prod_fields['Sum_Production'] = Sum_Production
    Sum_Remaining_Reserves = prod_fields.groupby('prfYear')['Remaining_Reserves'].transform(lambda x: x.sum())
    prod_fields['Sum_Remaining_Reserves'] = Sum_Remaining_Reserves
    CumSum_Production = prod_fields.groupby('prfYear')['Cum_Prod'].transform(lambda x: x.sum())
    prod_fields['CumSum_Production'] = CumSum_Production
    Count_Fields = prod_fields.groupby('prfYear')['Field'].transform(lambda x: x.count())
    prod_fields['Count_Fields'] = Count_Fields
    prod_year_sum = prod_fields.drop_duplicates(subset = ['prfYear'])[['prfYear','Year','Count_Fields','Sum_Oil','Sum_Gas','Sum_NGL','Sum_Condensate','Sum_Production','Sum_Remaining_Reserves','CumSum_Production']]
#    st.dataframe(prod_year_sum)
    prod_fieldnames = prod_fields.drop_duplicates(subset = ['fldName'])['fldName'].to_list()
    all = ['ALL']
    prod_fieldnames = all + prod_fieldnames
    fields = col2.selectbox('Select Production Fields:',prod_fieldnames)
    if fields == 'ALL':
        st.subheader(f"""**Production & Remaining Reserves of {"".join(str(len(prod_fieldnames)))} Production Fields from {"".join(str(prod_fields['Year'].min()))} to {"".join(str(prod_fields['Year'].max()))}**""")
#        hover = alt.selection_single(on='mouseover')
        line_scale = alt.Scale(domain=["Sum_Gas", "Sum_Oil",
                                        "Sum_Condensate", "Sum_NGL" ],
                               range=["rgb(220,36,30)",
                                        "rgb(1,114,41)",
                                        "rgb(0,24,168)","orange"])
        color_scale = alt.Scale(scheme="category20b",reverse=True)
        hover = alt.selection_multi(empty='all',fields=['Field'],on='mouseover')
        hover2 = alt.selection_multi(empty='all', encodings=['x'])
        click = alt.selection_multi(empty='all',fields=['Field'])
        base = alt.Chart(prod_fields).add_selection(hover).add_selection(click)

        c1a = base.mark_area(align='left', interpolate='monotone').encode(
                alt.X('year(Year):T',
                    axis=alt.Axis(labelFlush=False,format='%Y',labelAngle=0, title='Producing Year')),
                alt.Y('sum(Remaining_Reserves):Q',
                    axis=alt.Axis(title='Reserves in Millions Standard m³ Oil Equivalent')
                ),
                tooltip=['Field:N','year(Year):T','Production', 'Cum_Prod', 'Remaining_Reserves'],
                color=alt.Color('Field:N', scale=color_scale, legend=None),
                opacity=alt.condition(hover|click, alt.value(1.0), alt.value(0.2))
        ).transform_filter(click).properties(title="YEAR-END REMAINING RESERVES & ANNUAL/CUMULATIVE PRODUCTION",
            width=585, height=320
        ).interactive()

        c1b = alt.Chart(prod_year_sum).mark_point(size=35,clip=False,align='left',color='black',strokeWidth=1.5,shape='triangle-down',yOffset=-3).encode(
                alt.Y('Sum_Remaining_Reserves:Q',
                    axis=alt.Axis(title='Reserves in Millions Standard m³ Oil Equivalent')
                ),
                alt.X('year(Year):T',
                    axis=alt.Axis(format='%Y',labelAngle=0, title='Producing Year')),
                opacity=alt.condition(hover2, alt.value(1.0), alt.value(0.2)),
                tooltip=['year(Year):T','Count_Fields', 'Sum_Production:Q', 'CumSum_Production:Q', 'Sum_Remaining_Reserves:Q'],
                ).add_selection(hover2).transform_filter(click)

        c1c = alt.Chart(prod_year_sum).mark_bar(size=10,align='right').encode(
                alt.Y('sum(value):Q',
                    axis=alt.Axis(title='Annual Production in MSM³OE')
                ),
                alt.X('year(Year):T',
                    axis=alt.Axis(labelFlush=False,bandPosition=0,tickExtra=True,tickBand='extent',format='%Y',labelAngle=0, title='Producing Year')),
                color=alt.Color('key:N', scale=line_scale),
                opacity=alt.condition(hover2, alt.value(1.0), alt.value(0.2)),
                tooltip=['year(Year):T','Count_Fields','Sum_Production','key:N','value:Q'],
#            ).transform_joinaggregate(
#                Sum_Oil='sum(prfPrdOilNetMillSm3)', Sum_Gas='sum(prfPrdGasNetBillSm3)',
#                Sum_NGL='sum(prfPrdNGLNetMillSm3)', Sum_Condensate='sum(prfPrdCondensateNetMillSm3)',
#                groupby=["Year"]
            ).transform_fold(
                ['Sum_Oil', 'Sum_Gas', 'Sum_NGL', 'Sum_Condensate'],
            ).properties(title="ANNUAL TOTAL PRODUCTION",
                width=597, height=120
            ).add_selection(hover2).interactive()
#        c1 = (c1c&(c1a+c1b)).resolve_scale(color='independent')

#        c1d = alt.Chart(prod_year_sum).mark_line().encode(
#            x=alt.Y('CumSum_Production:Q',scale=alt.Scale(type='log'),axis=alt.Axis(title='Cumulative Production in MSM³OE')),
#            y=alt.X('year(Year):T',axis=alt.Axis(title='Producing Year')),
#            tooltip=['year(Year):T','Sum_Production:Q','CumSum_Production:Q'],
#            color=alt.Color(':N', scale=color_scale, legend=None),
#            opacity=alt.condition(hover2, alt.value(1.0), alt.value(0.2))
#            ).properties(title="CUMULATIVE PRODUCTION ",width=200, height=150)

#        c1cd = alt.hconcat(c1d,c1c).resolve_scale(color='independent')

        c2 = base.mark_bar().encode(
            x=alt.X('sum(Production)',scale=alt.Scale(type='log'),axis=alt.Axis(title='Total Production in MSM³OE')),
            y=alt.Y("Field",sort='-x',axis=alt.Axis(labels=False, title='Fields')),
            tooltip=['Field', 'sum(Production)','min(Remaining_Reserves)'],
            color=alt.Color('Field:N', scale=color_scale, legend=None),
            opacity=alt.condition(hover|click, alt.value(1.0), alt.value(0.2))
            ).properties(title="TOTAL PRODUCTION",width=150,height=320)

        c = (c1c&((c1a+c1b)|c2)).resolve_scale(color='independent')
#        c1 = alt.hconcat((c1a+c1b),c2)
#        c = alt.vconcat(c1c,c1).resolve_scale(color='independent')
        # Turn of the dots menu
        st.markdown(
            """
            <style type='text/css'>
                details {
                    display: none;
                }
            </style>
        """,
            unsafe_allow_html=True,
        )
        st.altair_chart(c, use_container_width=True)
        col1, col2, col3 = st.columns([2,6,2])
        if col2.button('⚠️ VISUALISING INSTRUCTIONS'):
            col2.markdown(f"""
                <div style="font-size: medium">
                👉 Hover the cursor over each field to highlight and see its infomation
                (holding 'Shift' while hovering to highlight multiple fields).\n
                <div style="font-size: medium">
                👉 MB1 click on the field to select it ('Shift+MB1' to select multiple fields).\n
                </div><br/>

            """,unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([5,5])
        col2.subheader(f"""**Expand to see {"" .join(str(fields))}'s info:**""")
        with col2.expander("GENERAL", expanded=True):
#            st.markdown("GENERAL")
#            field_info = df_dsc.loc[(df_dsc.loc[:,'fldName']==fields)&((df_dsc.loc[:,'dscCurrentActivityStatus']=='Producing')|(df_dsc.loc[:,'dscCurrentActivityStatus']=='Shut down')),:]
#            field_info = df_dsc.loc[(df_dsc.loc[:,'fldName']==fields),:]
            field_info = gdf_dsc.loc[(gdf_dsc.loc[:,'Name']==fields),:]
#            st.dataframe(field_info)
            field_info = field_info.T
            field_info = field_info.rename(columns=field_info.iloc[3]).drop(field_info.index[3])
            field_info = field_info.iloc[[2,4,13,14,16]]
            field_info.index.values[[0,1,2,3,4]] = ['Current Field Status', 'Discovery Year', 'Operator', 'HC Type', 'Main Area']
            field_info.index.names = ['Discovery Well']
            st.table(field_info)
#        col2.subheader("**Expand to see field description:**")
        with col2.expander("FIELD DESCRIPTION"):
            field_des = df_field_des.loc[(df_field_des.loc[:,'fldName']==fields),:]
#            st.dataframe(field_des)
            for i in field_des.index:
                heading = field_des.loc[i,'fldDescriptionHeading']
                text = field_des.loc[i,'fldDescriptionText']
                st.write(f"""**{"".join(heading)}**""")
                st.write(f"""{"".join(text)}""")
        with col2.expander("RECOVERABLE RESERVES IN MILLIONS STANDARD M³ OE"):
            st.write("See charts below")

        col1.subheader(f"""** {"" .join(str(fields))}'s location**""")
#        st.dataframe(df_dsc)
        with col1.container():
#            dsc_map = gdf_dsc.loc[(gdf_dsc.loc[:,'fieldName']==fields)&((gdf_dsc.loc[:,'curActStat']=='Producing')|(gdf_dsc.loc[:,'curActStat']=='Shut down')),:]
            gdf_dsc = gdf_dsc.loc[gdf_dsc.loc[:,'geometry']!=None,:]
            dsc_map = gdf_dsc.loc[gdf_dsc.loc[:,'fieldName']==fields,:]
            dsc_map2 = dsc_map.iloc[0:1]
#            st.table(dsc_map)
            dsc_map2['center_point'] = dsc_map2['geometry'].centroid
            lon = dsc_map2.center_point.map(lambda p: p.x)
            lat = dsc_map2.center_point.map(lambda p: p.y)
    # center on the middle of the field
            m = folium.Map(width=380,height=580,location=[lat, lon], tiles='cartodbpositron', zoom_start=8)

    # add marker
    #        folium.Marker(
#                [lat, lon], tooltip=tooltip
#            ).add_to(m)
            gdf_dsc['Name'] = gdf_dsc.apply(lambda row: row.fieldName if row.fieldName else row.discName, axis=1)
            tooltip = folium.GeoJsonTooltip(fields=['Name'])
            style_function = lambda x: {'fillColor': "gray", "weight": 0.1, 'color': "gray"}
            highlight_function = lambda x: {'fillColor': "black", "weight": 0.1, 'color': "black"}
            folium.GeoJson(data=gdf_dsc,style_function=style_function,highlight_function =highlight_function, tooltip=tooltip).add_to(m)
            style_function2 = lambda x: {'fillColor': "green" if x['properties']['Dctype']=='OIL' else ( "red" if x['properties']['Dctype']=='GAS' else ("orange" if x['properties']['Dctype']=='OIL/GAS' else "blue")),
                                        "weight": 1,
                                        'color': "green" if x['properties']['Dctype']=='OIL' else ( "red" if x['properties']['Dctype']=='GAS' else ("orange" if x['properties']['Dctype']=='OIL/GAS' else "blue"))}
            highlight_function2 = lambda x: {'fillColor': "darkgreen" if x['properties']['Dctype']=='OIL' else ( "darkred" if x['properties']['Dctype']=='GAS' else ("darkorange" if x['properties']['Dctype']=='OIL/GAS' else "darkblue")),
                                        "weight": 2,
                                        'color': "darkgreen" if x['properties']['Dctype']=='OIL' else ( "darkred" if x['properties']['Dctype']=='GAS' else ("darkorange" if x['properties']['Dctype']=='OIL/GAS' else "darkblue"))}
            folium.GeoJson(data=dsc_map,style_function=style_function2,highlight_function =highlight_function2,popup=fields, tooltip=fields).add_to(m)
    # call to render Folium map in Streamlit
            minimap = MiniMap(toggle_display=True,position="topright",tile_layer="cartodbpositron",zoom_level_offset=-6,width=120, height=150)
            minimap.add_to(m)
            folium_static(m)

#embed NPD map
#            components.iframe(df_dsc.loc[df_dsc.loc[:,'fldName']==fields,'dscFactMapUrl'].to_list()[0], height=515)

        field = prod_fields.loc[prod_fields.loc[:,'fldName']==fields,:]
        field.loc[:,'prfPrdOilNetMillSm3']=field.loc[:,'prfPrdOilNetMillSm3'].astype(float)
        field.loc[:,'prfPrdGasNetBillSm3']=field.loc[:,'prfPrdGasNetBillSm3'].astype(float)
#        field.loc[:,'fldRecoverableGas']=field.loc[:,'fldRecoverableGas'].astype(float)
#        field.loc[:,'prfPrdGasNetMillSm3']=field.loc[:,'prfPrdGasNetMillSm3'] * 1000.0
        field.loc[:,'prfPrdNGLNetMillSm3']=field.loc[:,'prfPrdNGLNetMillSm3'].astype(float)
        field.loc[:,'prfPrdCondensateNetMillSm3']=field.loc[:,'prfPrdCondensateNetMillSm3'].astype(float)

        field['Oil'] = field['fldRecoverableOil'] - field['prfPrdOilNetMillSm3'].cumsum()
        field.loc[field.loc[:,'Oil']<0.0,'Oil']=0.00
        field['Gas'] = field['fldRecoverableGas'] - field['prfPrdGasNetBillSm3'].cumsum()
        field.loc[field.loc[:,'Gas']<0.0,'Gas']=0.00
        field['NGL'] = field['fldRecoverableNGL'] - field['prfPrdNGLNetMillSm3'].cumsum()
        field.loc[field.loc[:,'NGL']<0.0,'NGL']=0.00
        field['Condensate'] = field['fldRecoverableCondensate'] - field['prfPrdCondensateNetMillSm3'].cumsum()
        field.loc[field.loc[:,'Condensate']<0.0,'Condensate']=0.00
#        col2.dataframe(field)
        field = field.loc[:,['Year', 'prfPrdOilNetMillSm3','prfPrdGasNetBillSm3','prfPrdNGLNetMillSm3','prfPrdCondensateNetMillSm3', 'Oil', 'Gas', 'NGL', 'Condensate']]
#        col2.dataframe(field)
        st.subheader(f"""** {"" .join(str(fields))}'s Production & Remaining Reserves from {"".join(str(field['Year'].min()))} to {"".join(str(field['Year'].max()))}**""")

        field1 = field.melt(id_vars=['Year'], value_vars=['Oil', 'Gas', 'NGL', 'Condensate'], value_name='Remaining_Reserves', var_name='Reserves_Type')
        field2 = field.melt(id_vars=['Year'], value_vars=['prfPrdOilNetMillSm3','prfPrdGasNetBillSm3','prfPrdNGLNetMillSm3','prfPrdCondensateNetMillSm3'], value_name='Production', var_name='Prodution_Type')
        field = pd.concat([field1, field2['Production']],axis=1)
#        col2.dataframe(field1)
        hover = alt.selection_multi(empty='all',fields=['Reserves_Type'],on='mouseover')
        click = alt.selection_multi(empty='all',fields=['Reserves_Type'])
        base = alt.Chart(field).add_selection(hover).add_selection(click)
#        hover = alt.selection_single(on='mouseover')
#        // Register a discrete color scheme named "field_res" that can then be used in Vega specs
#        field_color = pd.DataFrame({'#e31a1c', '#1f78b4', '#ff7f00', '#e33a02c'})
        y_scale = field.loc[field.loc[:,'Reserves_Type']=='Oil','Remaining_Reserves'].max()+field.loc[field.loc[:,'Reserves_Type']=='Gas','Remaining_Reserves'].max()+field.loc[field.loc[:,'Reserves_Type']=='NGL','Remaining_Reserves'].max()+field.loc[field.loc[:,'Reserves_Type']=='Condensate','Remaining_Reserves'].max()
        line_scale = alt.Scale(domain=["Gas", "Oil",
                                        "Condensate", "NGL" ],
                               range=["rgb(220,36,30)",
                                        "rgb(1,114,41)",
                                        "rgb(0,24,168)","orange"])
#        col2.dataframe(field)
        c1 = base.mark_bar().encode(
            x=alt.X('Reserves_Type:N',axis=alt.Axis(labelAngle=0)),
            y=alt.Y('sum(Production):Q', axis=alt.Axis(title='Total Production in Millions Standard m³ Oil Equivalent'),
            scale=alt.Scale(domain=(0, y_scale))
            ),
            tooltip=['Reserves_Type:N', 'sum(Production)','min(Remaining_Reserves)'],
            color=alt.Color('Reserves_Type:N', scale=line_scale, legend=None),
            opacity=alt.condition(hover|click, alt.value(1.0), alt.value(0.2))
            ).properties(title="TOTAL PRODUCTION",width=200,height=470)

        c2 = base.mark_area().encode(
                alt.X('year(Year):T',
                    axis=alt.Axis(format='%Y',labelAngle=0, title='Producing Year')),
                alt.Y('sum(Remaining_Reserves)',
                    axis=alt.Axis(title='Reserves in Millions Standard m³ Oil Equivalent'),
                scale=alt.Scale(domain=(0, y_scale))
                ),
                tooltip=['Reserves_Type:N', 'year(Year):T', 'Production', 'Remaining_Reserves'],
                color=alt.Color('Reserves_Type:N', scale=line_scale, legend=alt.Legend(strokeColor='black',padding=5,fillColor='white',title=None,offset=10,orient="top-right")),
                opacity=alt.condition(hover|click, alt.value(1.0), alt.value(0.2))
        ).transform_filter(click).properties(title="YEAR-END REMAINING RESERVES & ANNUAL PRODUCTION",width=500,height=470
        ).interactive()
        c = alt.hconcat(c1,c2).resolve_scale(color='independent')
#        with col2.container():
        # Turn of the dots menu
        st.markdown(
            """
            <style type='text/css'>
                details {
                    display: none;
                }
            </style>
        """,
            unsafe_allow_html=True,
        )

        st.altair_chart(c, use_container_width=True)

        col1, col2, col3 = st.columns([2,6,2])
        if col2.button('⚠️ VISUALISING INSTRUCTIONS'):
            col2.markdown(f"""
                <div style="font-size: medium">
                👉 Hover the cursor over each Reserves_Type to highlight and see its infomation
                (holding 'Shift' while hovering to highlight multiple types).\n
                <div style="font-size: medium">
                👉 MB1 click on a Reserves_Type to select it ('Shift+MB1' to select multiple types).\n
                </div><br/>

            """,unsafe_allow_html=True)

    return None

def overview():
    col1, col2,col3 = st.sidebar.columns([0.9,7.7,1.4])
    well_litho_npd, df_wells, tbl_wells, df_units, well_his_npd, well_coord_npd, well_doc_npd, df_coasline_no = read_welldata()
    prod_fields,gdf_dsc,df_field_des,df_dsc_des,df_dsc_res,df_fields,df_dsc_fld = read_fielddata()
#    prod_fields = prod_fields.dropna()
#    prod_fields['Production'] = prod_fields['prfPrdOeNetMillSm3']
#    st.dataframe(df_dsc_des)
    df_dsc_fld['Remaining_OE'] = df_dsc_fld['Remaining OE'] + 0.01
    df_dsc_fld['Year'] = df_dsc_fld['Discovery Year'].fillna(0).astype(int)
    gdf_dsc['OpLongName'] = gdf_dsc['OpLongName'].fillna('N/A').astype(str)
    gdf_dsc['Name'] = gdf_dsc.apply(lambda row: row.fieldName if row.fieldName else row.discName, axis=1)
#    fieldnames = gdf_dsc.drop_duplicates(subset = ['Name'])['Name'].to_list()
    a = set(gdf_dsc['Name'].unique())
    b = set(prod_fields['fldName'])
    fieldnames = list(a.difference(b))
    all = ['ALL']
    df_res = ['D&F with RRR']
    fieldnames = all + df_res + fieldnames
    fields = col2.selectbox('Select Discoveries/Fields:',fieldnames)
    if fields == 'ALL':
        min_year = int(gdf_dsc['discYear'].min())
        max_year = int(gdf_dsc['discYear'].max())
        st.subheader(f"""**{"".join(str(len(gdf_dsc['discName'].unique())))} D&F have been discovered from {"".join(str(min_year))} to {"".join(str(max_year))}**""")
#        col1.subheader(f"""** {"" .join(str(fields))}'s location**""")
        col1, col2 = st.columns([5,5])
        year = st.slider('Slide to select discovered year(s) :',min_year, max_year, (min_year, max_year))
        df_dsc = gdf_dsc.loc[gdf_dsc.loc[:,'Dctype'].notnull(),:][['Name','discWelNam', 'Dctype', 'OpLongName','discYear','curActStat', 'main_area']]
        df_dsc = df_dsc.loc[(df_dsc.loc[:,'discYear']>=year[0])&(df_dsc.loc[:,'discYear']<=year[1]),:]
        df_dsc.index = df_dsc.index.astype('str')
#        st.dataframe(df_dsc)
#        st.write(df_dsc.info())
        @st.cache(allow_output_mutation=True)
        def altair_bar():
            pts = alt.selection_single(encodings=["y"], name="pts")
            line_scale = alt.Scale(domain=["GAS", "OIL",
                                            "GAS/CONDENSATE", "OIL/GAS" ],
                                   range=["rgb(220,36,30)",
                                            "rgb(1,114,41)",
                                            "rgb(0,24,168)","orange"])
            return(
                alt.Chart(df_dsc).mark_bar(size=12).encode(
                x = alt.X('count():Q',title='Numbers of Discoveries/Fields'),
                y = alt.Y('OpLongName:N', title=None,sort='-x'),
                tooltip=[
                        alt.Tooltip('Dctype:N',title='H/C Type'),
                        alt.Tooltip('count():Q',title='No. of D&F')],
                color=alt.Color('Dctype', scale=line_scale ,legend=alt.Legend(strokeColor='black',padding=5,fillColor='white',title='H/C Type',offset=5,orient='bottom-right')),
                opacity=alt.condition(pts, alt.value(1.0), alt.value(0.2)),
    #            size=alt.Size('Remaining_OE:Q', legend=alt.Legend(title='Remaining Reserves in MSM³OE',orient='bottom'),
    #                            scale=alt.Scale(range=[10, 1000]))
            ).properties(title = 'Discoveries/Fields per Operators',
                width=200,
                height=465
            ).add_selection(
                pts
            )
        )

        with col2.container():
            event_dict = altair_component(altair_chart=altair_bar())
#            st.altair_chart(altair_bar())
        r = event_dict.get("OpLongName")
        gdf_dsc3 = gdf_dsc.loc[gdf_dsc.loc[:,'geometry']!=None,:]
        if r:
            gdf_dsc = gdf_dsc.loc[gdf_dsc.loc[:,'OpLongName']==r[0],:].reset_index(drop=True)
            df_dsc =  df_dsc.loc[df_dsc.loc[:,'OpLongName']==r[0],:].reset_index(drop=True)
            df_dsc.index = df_dsc.index + 1
            st.subheader(f"""**{"".join(str(df_dsc.index.max()))} discoveries/fields of {"".join(str(r[0]))} from {"".join(str(year[0]))} to {"".join(str(year[1]))}**""")
            st.table(df_dsc[['Name','discWelNam', 'Dctype', 'discYear', 'curActStat', 'main_area']])
        else:
            st.markdown(f"""$~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~$👉*Click into each operator bar chart to see details*""")

        with col1.container():
            st.write('')
            gdf_dsc2 = gdf_dsc.loc[gdf_dsc.loc[:,'geometry']==None,:]
            gdf_dsc2 = gdf_dsc2.loc[(gdf_dsc2.loc[:,'discYear']>=year[0])&(gdf_dsc2.loc[:,'discYear']<=year[1]),:]
#            gdf_dsc2['Name'] = gdf_dsc.apply(lambda row: row.fieldName if row.fieldName else row.discName, axis=1)
            dsc_wells = gdf_dsc2.loc[gdf_dsc2.loc[:,'discWelNam']!= '?','discWelNam'].to_list()
            df_dsc_wells = well_coord_npd.loc[well_coord_npd.loc[:,'wlbWellboreName'].isin(dsc_wells),:][['wlbWellboreName','wlbNsDecDeg','wlbEwDesDeg']]
            gdf_dsc2 = gdf_dsc2.merge(df_dsc_wells,"left",left_on='discWelNam',right_on='wlbWellboreName',
                        indicator=False, validate='many_to_many')
#            gdf_dsc2['geometry'] = gpd.points_from_xy(gdf_dsc2.wlbEwDesDeg, gdf_dsc2.wlbNsDecDeg)
#            gdf_dsc2 = gdf_dsc2.set_crs("EPSG:4326")
#            lat = well_coord_npd.loc[well_coord_npd.loc[:,'wlbWellboreName'].isin(dsc_wells),'wlbNsDecDeg']
            gdf_dsc = gdf_dsc.loc[gdf_dsc.loc[:,'geometry']!=None,:]
            gdf_dsc = gdf_dsc.loc[(gdf_dsc.loc[:,'discYear']>=year[0])&(gdf_dsc.loc[:,'discYear']<=year[1]),:]
#            centroid=gdf_dsc.geometry.centroid
# center on the middle of the field
            m = folium.Map(width=400,height=500,location=[66.562, 17.704], tiles='cartodbpositron', zoom_start=4)

            style_function = lambda x: {'fillColor': "gray", "weight": 0.1, 'color': "gray"}
            highlight_function = lambda x: {'fillColor': "black", "weight": 0.1, 'color': "black"}
            tooltip = folium.GeoJsonTooltip(fields=['Name'])
            folium.GeoJson(data=gdf_dsc3,style_function=style_function,highlight_function =highlight_function, tooltip=tooltip).add_to(m)

            tooltip2 = folium.GeoJsonTooltip(fields=['Name','discWelNam','Dctype', 'OpLongName', 'discYear', 'curActStat', 'main_area'],
                                             aliases= ['Name:','Well name:','H/C type:', 'Operator:', 'Disc. year:', 'Status:', 'Main area:'],
                                             localize=True)
            style_function2 = lambda x: {'fillColor': "green" if x['properties']['Dctype']=='OIL' else ( "red" if x['properties']['Dctype']=='GAS' else ("orange" if x['properties']['Dctype']=='OIL/GAS' else "blue")),
                                            "weight": 1,
                                            'color': "green" if x['properties']['Dctype']=='OIL' else ( "red" if x['properties']['Dctype']=='GAS' else ("orange" if x['properties']['Dctype']=='OIL/GAS' else "blue"))}
            highlight_function2 = lambda x: {'fillColor': "darkgreen" if x['properties']['Dctype']=='OIL' else ( "darkred" if x['properties']['Dctype']=='GAS' else ("darkorange" if x['properties']['Dctype']=='OIL/GAS' else "darkblue")),
                                            "weight": 2,
                                            'color': "darkgreen" if x['properties']['Dctype']=='OIL' else ( "darkred" if x['properties']['Dctype']=='GAS' else ("darkorange" if x['properties']['Dctype']=='OIL/GAS' else "darkblue"))}

            if len(gdf_dsc.index) != 0 :
                folium.GeoJson(data=gdf_dsc,style_function=style_function2,highlight_function =highlight_function2, tooltip=tooltip2).add_to(m)

#            tooltip = folium.GeoJsonTooltip(fields=['Name','discWelNam','Dctype', 'OpLongName', 'discYear','main_area'])
#            style_function = lambda x: {'fillColor': "gray", "weight": 0.1, 'color': "gray"}
#            highlight_function = lambda x: {'fillColor': "black", "weight": 0.1, 'color': "black"}
#            folium.GeoJson(data=gdf_dsc2,style_function=style_function2,highlight_function =highlight_function2, tooltip=tooltip).add_to(m)
            for i, v in gdf_dsc2.iterrows():
                popup = """
                <b>Name:</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; %s<br>
                <b>Well name:</b>&nbsp;&nbsp;&nbsp; %s<br>
                <b>H/C type:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b> %s<br>
                <b>Operator:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b> %s<br>
                <b>Disc. year:&nbsp;&nbsp;&nbsp;&nbsp;</b> %d<br>
                <b>Status:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b> %s<br>
                <b>Main area:&nbsp;&nbsp;&nbsp;&nbsp;</b> %s<br>
                """ % (v['Name'], v['discWelNam'], v['Dctype'], v['OpLongName'], v['discYear'], v['curActStat'], v['main_area'])

                if v['Dctype'] == 'GAS':
                    folium.CircleMarker(location=[v['wlbNsDecDeg'], v['wlbEwDesDeg']],
                                        radius=1,
                                        tooltip=popup,
                                        color='red',
                                        fill_color='red',
                                        fill=True).add_to(m)
                elif v['Dctype'] == 'OIL':
                    folium.CircleMarker(location=[v['wlbNsDecDeg'], v['wlbEwDesDeg']],
                                        radius=1,
                                        tooltip=popup,
                                        color='green',
                                        fill_color='green',
                                        fill=True).add_to(m)
                elif v['Dctype'] == 'OIL/GAS':
                    folium.CircleMarker(location=[v['wlbNsDecDeg'], v['wlbEwDesDeg']],
                                        radius=1,
                                        tooltip=popup,
                                        color='orange',
                                        fill_color='orange',
                                        fill=True).add_to(m)
                elif v['Dctype'] == 'GAS/CONDENSATE':
                    folium.CircleMarker(location=[v['wlbNsDecDeg'], v['wlbEwDesDeg']],
                                        radius=1,
                                        tooltip=popup,
                                        color='blue',
                                        fill_color='blue',
                                        fill=True).add_to(m)
        # call to render Folium map in Streamlit
            minimap = MiniMap(toggle_display=True,position="topright",tile_layer="cartodbpositron",zoom_level_offset=-3,width=120, height=150)
            minimap.add_to(m)
            folium_static(m)
#        st.dataframe(df_dsc)
#        st.dataframe(df_dsc_wells)

    elif fields == 'D&F with RRR':
        bin = col2.checkbox('Binned Heatmap?', False)
        st.subheader(f"""**{"".join(str(len(df_dsc_fld['Name'])))} D&F with Remaining/Recoverable Reserves of {"".join(str(round(df_dsc_fld['Remaining OE'].sum(),2)))}/{"".join(str(round(df_dsc_fld['Recoverable OE'].sum(),2)))} MSM³OE**""")
#        st.dataframe(df_dsc_fld)
        min_year = int(df_dsc_fld["Discovery Year"].min())
        max_year = int(df_dsc_fld["Discovery Year"].max())
        line_scale = alt.Scale(domain=["GAS", "OIL",
                                        "GAS/CONDENSATE", "OIL/GAS" ],
                               range=["rgb(220,36,30)",
                                        "rgb(1,114,41)",
                                        "rgb(0,24,168)","orange"])
        color = alt.Color('HC Type:N', scale=line_scale, legend=None)

        pts = alt.selection(type="multi", encodings=['x'])
        pts_y = alt.selection(type="multi", encodings=['y'])
        brush = alt.selection_interval(encodings=['x'])

        # Top panel is scatter plot of temperature vs time
        bas = alt.Chart(df_dsc_fld).transform_filter("datum.Year >= 1966").mark_point().encode(
            x = alt.X('Year:N',title='Discovery Year',axis=alt.Axis(bandPosition=0,labelAngle=0,labelFontSize=8,labelOverlap=True)),
            y = alt.Y('Recoverable OE:Q',title='Recoverable Reserves in MSM³OE', scale = alt.Scale(type='log')),
            tooltip=['Name','Status:N','Discovery Year','Operator:N','Recoverable OE:Q','Remaining OE:Q'],
            color=alt.condition(brush, color, alt.value('lightgray')),
            size=alt.Size('Remaining_OE:Q', legend=alt.Legend(title='Remaining Reserves in MSM³OE',orient='bottom'),
                            scale=alt.Scale(range=[10, 1000]))
        ).properties(
            width=300,
            height=268
        )
        points =bas.add_selection(
            brush
        ).transform_filter(
            pts
        ).transform_filter(
            pts_y
        )

        rect = alt.Chart(df_dsc_fld).mark_rect().encode(
            alt.X('Discovery Year:Q', bin=alt.Bin(maxbins=12)),
            alt.Y('Recoverable OE:Q', bin=alt.Bin(maxbins=16),title='Recoverable Reserves in MSM³OE (binned)'),
            color = alt.Color('count()',
                scale=alt.Scale(scheme='purpleblue'),
                legend=alt.Legend(title='Total No. of D&F',offset=5,orient='top-right')
            ),
            tooltip=['count():Q','sum(Recoverable OE):Q','sum(Remaining OE):Q']
        ).properties(
            width=300,
            height=268
        )

        circ = rect.mark_point().encode(
            alt.ColorValue('grey'),
            alt.Size('count()',
                legend=alt.Legend(title='No. of D&F from selection',orient='bottom')
            ),
            tooltip=['count()','sum(Recoverable OE)','sum(Remaining OE)']
        ).transform_filter(
            pts
        ).transform_filter(
            pts_y
        )

        bar = alt.Chart(df_dsc_fld).mark_bar(size=20).encode(
            x=alt.X('Operator:N',axis=alt.Axis(title=None)),
            tooltip=['Operator:N','count()','sum(Recoverable OE):Q','sum(Remaining OE):Q'],
            color=alt.Color('count()', scale=alt.Scale(scheme='purplebluegreen'),legend=alt.Legend(title='No. of D&F per Operator',offset=48,orient='left',titleOrient='left')),
            opacity=alt.condition(pts, alt.value(1.0), alt.value(0.2)),
            y=alt.Y('sum(Recoverable OE):Q',title='MSM³OE'),
        ).properties(
            width=637,
            height=120
        ).transform_filter(
            pts_y
        ).add_selection(pts)

        tick = alt.Chart(df_dsc_fld).mark_tick(
            color='red',
            thickness=1,
            size=20 * 0.99,  # controls width of tick.
        ).encode(
            x=alt.X('Operator:N',axis=alt.Axis(title='Operators', labelAngle=-20)),
            opacity=alt.condition(pts, alt.value(1.0), alt.value(0.2)),
            y=alt.Y('sum(Remaining_OE):Q',title='MSM³OE', scale = alt.Scale(type='log'))
        ).transform_filter(
            pts_y
        )

        base = alt.Chart(df_dsc_fld).add_selection(pts_y).transform_filter(pts)


        bar3 = base.mark_bar(size=10).encode(
            y=alt.Y('Status:N', title=None),
            color=alt.Color('HC Type:N', scale=line_scale,legend=alt.Legend(title='HC Types',orient='bottom',columns=4)),
            tooltip=['Status:N','HC Type:N','count(HC Type):Q','sum(Recoverable OE)','sum(Remaining OE)'],
            opacity=alt.condition(pts_y, alt.value(1.0), alt.value(0.1)),
            x=alt.X('count():Q', title='Number of Discoveries & Fields'),
            row = 'Main Area:N'
        ).properties(height=80,width=250)

        st.markdown(
            """
            <style type='text/css'>
                details {
                    display: none;
                }
            </style>
        """,
            unsafe_allow_html=True,
        )
        if bin :
            st.altair_chart(
                alt.vconcat(
                alt.hconcat(bar3,(rect + circ)).resolve_legend(color="independent",size="independent"),
                (bar+tick).resolve_legend(color="independent",size="independent")
                )
                , use_container_width=True)
        else :
            chart = alt.vconcat(
            alt.hconcat(bar3.transform_filter(brush),points).resolve_legend(color="independent",size="independent"),
            (bar+tick).transform_filter(brush).resolve_legend(color="independent",size="independent")
            )
#            chart.save('chart.html')
            st.altair_chart(
                chart, use_container_width=True)

        col1, col2, col3 = st.columns([2,6,2])
        if col2.button('⚠️ VISUALISING INSTRUCTIONS'):
            col2.markdown(f"""
                <div style="font-size: medium">
                👉 Hover the cursor over each object to see its infomation.\n
                <div style="font-size: medium">
                👉 MB1 click on an object to select it ('Shift+MB1' to select multiples).\n
                <div style="font-size: medium">
                👉 MB1 click and drag to select an area on the bubble chart
                </div><br/>

            """,unsafe_allow_html=True)
#        st.dataframe(df_dsc_res)
    else:
        st.sidebar.write(" ")
        st.sidebar.write(" ")
        col1, col2 = st.columns([5,5])

        col2.subheader(f"""**Expand to see {"" .join(str(fields))}'s info:**""")
        with col2.expander("GENERAL", expanded=True):
#            st.markdown("GENERAL")
            field_info = gdf_dsc.loc[(gdf_dsc.loc[:,'Name']==fields),:]
#            st.dataframe(df_dsc)
            field_info = field_info.T
            field_info = field_info.rename(columns=field_info.iloc[3]).drop(field_info.index[3])
            field_info = field_info.iloc[[2,4,13,14,16]]
            field_info.index.values[[0,1,2,3,4]] = ['Current Field Status', 'Discovery Year', 'Operator', 'HC Type', 'Main Area']
            field_info.index.names = ['Discovery Well']
            st.table(field_info)
#        col2.subheader("**Expand to see field description:**")
        with col2.expander("DESCRIPTION"):
            field_des = df_field_des.loc[(df_field_des.loc[:,'fldName']==fields),:].reset_index()
            dsc_des = df_dsc_des.loc[(df_dsc_des.loc[:,'dscName']==fields),:].reset_index()
#            st.dataframe(dsc_des)
            if len(field_des.index) != 0 :
                for i in field_des.index:
                    heading = field_des.loc[i,'fldDescriptionHeading']
                    text = field_des.loc[i,'fldDescriptionText']
                    st.write(f"""**{"".join(heading)}**""")
                    st.write(f"""{"".join(text)}""")

            elif len(dsc_des.index) != 0 :
                text = dsc_des.loc[0,'dscDescriptionText']
                st.write(f"""{"".join(text)}""")

            else :
                st.write('Sorry! No description available for this discovery')

        with col2.expander("RECOVERABLE RESERVES IN MILLIONS STANDARD M³ OE"):
            field_res = df_fields.loc[df_fields.loc[:,'fldName']==fields,:]
#            st.dataframe(field_res)
            df_dsc_res.loc[:,'dscName']=df_dsc_res.apply(lambda row: row.dscName.lstrip(), axis=1)
            dsc_res = df_dsc_res.loc[(df_dsc_res.loc[:,'dscName']==fields),:]
            if len(dsc_res.index) != 0 :
                dsc_res = dsc_res.T
#               st.dataframe(dsc_res)
#               st.dataframe(df_dsc_des)
                dsc_res = dsc_res.rename(columns=dsc_res.iloc[0]).drop(dsc_res.index[0])
#               dsc_res = dsc_res.iloc[[2,3,5,14,15,17]]
                dsc_res.index.values[[0,1,2,3,4,5,6,7,8,9]] = ['Resource Category', 'Recoverable Oil', 'Recoverable Gas', 'Recoverable NGL', 'Recoverable Condensate', 'Recoverable OE', 'Resource Updated Date', 'Discovery NPDID', 'Updated Date', 'Date Sync NPD'  ]
                st.table(dsc_res)
            elif len(field_res.index) != 0 :
                field_res = field_res.T
#               st.dataframe(dsc_res)
#               st.dataframe(df_dsc_des)
                field_res = field_res.rename(columns=field_res.iloc[0]).drop(field_res.index[0])
                field_res = field_res.iloc[[0,1,2,3,4,10,11,12]]
                field_res.index.values[[0,1,2,3,4,5,6,7]] = ['Recoverable Oil', 'Recoverable Gas', 'Recoverable NGL', 'Recoverable Condensate', 'Recoverable OE', 'Resource Updated Date', 'Discovery NPDID', 'Date Sync NPD'  ]
                st.table(field_res)
            else :
                st.write('Sorry! No reserve estimation available for this discovery')

        col1.subheader(f"""** {"" .join(str(fields))}'s location**""")
#        st.dataframe(df_dsc)
        with col1.container():
#            dsc_map = gdf_dsc.loc[(gdf_dsc.loc[:,'fieldName']==fields)&((gdf_dsc.loc[:,'curActStat']=='Producing')|(gdf_dsc.loc[:,'curActStat']=='Shut down')),:]
            gdf_dsc2 = gdf_dsc
            gdf_dsc = gdf_dsc.loc[gdf_dsc.loc[:,'geometry']!=None,:]
            dsc_map = gdf_dsc.loc[gdf_dsc.loc[:,'Name']==fields,:]
            dsc_map2 = dsc_map.iloc[0:1]
#            st.table(dsc_map)
            if len(dsc_map2)!=0 :
                dsc_map2['center_point'] = dsc_map2['geometry'].centroid
                lon = dsc_map2.center_point.map(lambda p: p.x)
                lat = dsc_map2.center_point.map(lambda p: p.y)
    # center on the middle of the field
                m = folium.Map(width=380,height=580,location=[lat, lon], tiles='cartodbpositron', zoom_start=8)
                style_function = lambda x: {'fillColor': "gray", "weight": 0.1, 'color': "gray"}
                highlight_function = lambda x: {'fillColor': "black", "weight": 0.1, 'color': "black"}
                tooltip = folium.GeoJsonTooltip(fields=['Name'])
                folium.GeoJson(data=gdf_dsc,style_function=style_function,highlight_function =highlight_function, tooltip=tooltip).add_to(m)
                style_function2 = lambda x: {'fillColor': "green" if x['properties']['Dctype']=='OIL' else ( "red" if x['properties']['Dctype']=='GAS' else ("orange" if x['properties']['Dctype']=='OIL/GAS' else "blue")),
                                            "weight": 1,
                                            'color': "green" if x['properties']['Dctype']=='OIL' else ( "red" if x['properties']['Dctype']=='GAS' else ("orange" if x['properties']['Dctype']=='OIL/GAS' else "blue"))}
                highlight_function2 = lambda x: {'fillColor': "darkgreen" if x['properties']['Dctype']=='OIL' else ( "darkred" if x['properties']['Dctype']=='GAS' else ("darkorange" if x['properties']['Dctype']=='OIL/GAS' else "darkblue")),
                                            "weight": 2,
                                            'color': "darkgreen" if x['properties']['Dctype']=='OIL' else ( "darkred" if x['properties']['Dctype']=='GAS' else ("darkorange" if x['properties']['Dctype']=='OIL/GAS' else "darkblue"))}

                folium.GeoJson(data=dsc_map,style_function=style_function2,highlight_function =highlight_function2,popup=fields, tooltip=fields).add_to(m)

        # call to render Folium map in Streamlit
                minimap = MiniMap(toggle_display=True,position="topright",tile_layer="cartodbpositron",zoom_level_offset=-6,width=120, height=150)
                minimap.add_to(m)
                folium_static(m)
            else :
                dsc_well = gdf_dsc2.loc[gdf_dsc2.loc[:,'Name']==fields,'discWelNam'].to_list()[0]
                dsc_col = gdf_dsc2.loc[gdf_dsc2.loc[:,'Name']==fields,'Dctype'].to_list()[0]
                if dsc_col == 'OIL' :
                    col = 'green'
                elif dsc_col == 'GAS':
                    col = 'red'
                elif dsc_col == 'OIL/GAS':
                    col = 'orange'
                else:
                    col = 'blue'

                if dsc_well == '?' :
                    st.write('Sorry! No map available for this discovery')
                else :
                    lon = well_coord_npd.loc[well_coord_npd.loc[:,'wlbWellboreName']==dsc_well,'wlbEwDesDeg'].to_list()[0]
                    lat = well_coord_npd.loc[well_coord_npd.loc[:,'wlbWellboreName']==dsc_well,'wlbNsDecDeg'].to_list()[0]
#                st.write(dsc_well,lat,lon)
                    m = folium.Map(width=340,height=580,location=[lat, lon], tiles='cartodbpositron', zoom_start=8)
                    style_function = lambda x: {'fillColor': "gray", "weight": 0.1, 'color': "gray"}
                    highlight_function = lambda x: {'fillColor': "black", "weight": 0.1, 'color': "black"}
                    tooltip = folium.GeoJsonTooltip(fields=['Name'])
                    folium.GeoJson(data=gdf_dsc,style_function=style_function,highlight_function =highlight_function, tooltip=tooltip).add_to(m)
#                style_function2 = lambda x: {'fillColor': "green" if x['properties']['Dctype']=='OIL' else ( "red" if x['properties']['Dctype']=='GAS' else ("orange" if x['properties']['Dctype']=='OIL/GAS' else "blue")),
#                                            "weight": 1,
#                                            'color': "green" if x['properties']['Dctype']=='OIL' else ( "red" if x['properties']['Dctype']=='GAS' else ("orange" if x['properties']['Dctype']=='OIL/GAS' else "blue"))}
#                color_function2 = lambda x: {'color': "green" if x['properties']['Dctype']=='OIL' else ( "red" if x['properties']['Dctype']=='GAS' else ("orange" if x['properties']['Dctype']=='OIL/GAS' else "blue"))}
#                highlight_function2 = lambda x: {'fillColor': "darkgreen" if x['properties']['Dctype']=='OIL' else ( "darkred" if x['properties']['Dctype']=='GAS' else ("darkorange" if x['properties']['Dctype']=='OIL/GAS' else "darkblue")),
#                                            "weight": 2,
#                                            'color': "darkgreen" if x['properties']['Dctype']=='OIL' else ( "darkred" if x['properties']['Dctype']=='GAS' else ("darkorange" if x['properties']['Dctype']=='OIL/GAS' else "darkblue"))}

# add marker
                    folium.CircleMarker([lat, lon],radius=3,fill=True,color=col, tooltip=fields,icon='screenshot').add_to(m)
#                folium.Marker([lat, lon],icon= folium.Icon(color=col,icon_color=col,icon='screenshot'), tooltip=fields).add_to(m)
        # call to render Folium map in Streamlit
                    minimap = MiniMap(toggle_display=True,position="topright",tile_layer="cartodbpositron",zoom_level_offset=-6,width=120, height=150)
                    minimap.add_to(m)
                    folium_static(m)
#            gdf_dsc['Name'] = gdf_dsc.apply(lambda row: row.fieldName if row.fieldName else row.discName, axis=1)
    return None

def wellbores():
    col1, col2,col3 = st.sidebar.columns([0.9,7.7,1.4])
    well_litho_npd, df_wells, tbl_wells, df_units, well_his_npd, well_coord_npd, well_doc_npd, df_coasline_no = read_welldata()
    a = set(well_coord_npd['wlbWellboreName'].unique())
    b = set(well_litho_npd['wlbName'])
    wellnames = list(a.difference(b))
    all = ['ALL']
    edw = ['EXP & DEV Wells']
    wellnames = all + edw + wellnames
    well = col2.selectbox('Select Wells:', wellnames)
    if well == 'ALL':
        total_wells = len(well_coord_npd.drop_duplicates(subset = ['wlbWellboreName'])['wlbWellboreName'].to_list())
        min_year = int(well_coord_npd["year"].min())
        max_year = int(well_coord_npd["year"].max())
        st.subheader(f"""\
            **{"" .join(str(total_wells))} Wells Drilled on the Norwegian Continental Shelf from {"".join(str(min_year))} to {"".join(str(max_year))}**""")
#        st.dataframe(well_coord_npd)
#        @st.cache(allow_output_mutation=True)
        def plt_wellbores(well_coord_npd,df_coasline_no):
            min_x = well_coord_npd["wlbEwDesDeg"].min()
            max_x = well_coord_npd["wlbEwDesDeg"].max()
            max_y = well_coord_npd["wlbNsDecDeg"].max()
            well_compnames = well_coord_npd.drop_duplicates(subset = ['wlbDrillingOperator'])['wlbDrillingOperator'].to_list()
            well_compnames = ['Select a company'] + well_compnames
    #        st.dataframe(well_coord_npd)
            brush = alt.selection_interval(on="[mousedown[event.shiftKey], mouseup[event.shiftKey]] > mousemove[event.shiftKey]",name='brush')
    #        interact = alt.selection_interval(on="[mousedown[event.altKey], mouseup[event.altKey]] > mousemove[event.altKey]",name='interact',bind='scales')
            click = alt.selection_multi(empty='all',encodings=["y"])
            click3 = alt.selection_multi(empty='all',encodings=["y"])
            click4 = alt.selection_multi(empty='all',encodings=["y"])
            click2 = alt.selection_multi(empty='all',encodings=["y"])
            hover = alt.selection_multi(empty='all',on='mouseover',encodings=["y"])
            input_dropdown = alt.binding_select(options=well_compnames)
            drop_selection = alt.selection_single(fields=['wlbDrillingOperator'], bind=input_dropdown, name='Name of')
            # A slider filter
            year_slider = alt.binding_range(min=min_year, max=max_year, step=1)
            slider_selection = alt.selection_single(bind=year_slider, fields=['year'], name="Spudded")
            points = alt.Chart(well_coord_npd).mark_point(clip=True,strokeWidth=1,size=30).encode(
                y=alt.Y('wlbNsDecDeg:Q',scale=alt.Scale(domain=(55,max_y))),
                x=alt.X('wlbEwDesDeg:Q',scale=alt.Scale(domain=(min_x,max_x))),
                tooltip=['wlbWellboreName','wlbPurposePlanned:N','wlbWellType:N','wlbMainArea:N','wlbContent:N','wlbDrillingOperator','year'],
                shape=alt.Shape('wlbPurposePlanned:N', legend=alt.Legend(strokeColor='black',padding=5,fillColor='white',title=None,offset=5,orient="bottom",columns=9)),
                opacity=alt.condition(hover, alt.value(1.0), alt.value(0.1)),
    #            fill =alt.condition(brush,'wlbContent:N', alt.value('lightgray'), scale=alt.Scale(scheme="category20b", reverse=True), legend=None),
                color=alt.condition(brush|click2, 'wlbContent:N', alt.value('lightgray'), scale=alt.Scale(scheme="category20b", reverse=True), legend=None)
            ).interactive().add_selection(
                brush,slider_selection,click2,drop_selection
            ).transform_filter(
                slider_selection
            ).transform_filter(
                drop_selection
            ).transform_filter(
                click
            ).transform_filter(
                click3
            ).transform_filter(
                click4
            ).properties(title="WELL LOCATION ON THE NCS",height=403, width=370)

            map = alt.Chart(df_coasline_no).mark_area(
                strokeWidth=0.5,color='gray'
            ).encode(
                y=alt.Y('x:Q',scale=alt.Scale(domain=(55,max_y)), title=None, axis=None),
                x=alt.X('y:Q',scale=alt.Scale(domain=(min_x,max_x)), title=None, axis=None),
                order='0:O'
                ).interactive()

            base = alt.Chart(well_coord_npd).add_selection(hover,slider_selection,drop_selection)
            bar1 = base.mark_bar(size=10).encode(
                y=alt.Y('wlbMainArea:N', title=None),
                color='wlbWellType:N',
                tooltip=['wlbWellType:N','count(wlbWellType):Q'],
                opacity=alt.condition(hover|click, alt.value(1.0), alt.value(0.2)),
                x=alt.X('count(wlbMainArea):Q', title='Number of Wells')
            ).add_selection(
                click
            ).transform_filter(
                slider_selection
            ).transform_filter(
                drop_selection
            ).transform_filter(
                brush
            ).transform_filter(
                click2
            ).transform_filter(
                click3
            ).transform_filter(
                click4
            ).properties(title="WELL TYPE PER MAIN AREA",height=40,width=330)

            bar2 = base.mark_bar(size=10).encode(
                y=alt.Y('wlbWellType:N', title=None),
                color='wlbPurposePlanned:N',
                tooltip=['wlbPurposePlanned:N','count(wlbPurposePlanned):Q'],
                opacity=alt.condition(hover|click3, alt.value(1.0), alt.value(0.2)),
                x=alt.X('count(wlbWellType):Q', title='Number of Wells')
            ).add_selection(
                click3
            ).transform_filter(
                slider_selection
            ).transform_filter(
                drop_selection
            ).transform_filter(
                brush
            ).transform_filter(
                click2
            ).transform_filter(
                click
            ).transform_filter(
                click4
            ).properties(title="WELL PURPOSE PER TYPE",height=40,width=330)

            bar3 = base.mark_bar(size=10).encode(
                y=alt.Y('wlbPurposePlanned:N', title=None),
                color=alt.Color('wlbContent:N', scale=alt.Scale(scheme="category20b", reverse=True)),
                tooltip=['wlbContent:N','count(wlbContent):Q'],
                opacity=alt.condition(hover|click4, alt.value(1.0), alt.value(0.2)),
                x=alt.X('count(wlbPurposePlanned):Q', title='Number of Wells')
            ).add_selection(
                click4
            ).transform_filter(
                slider_selection
            ).transform_filter(
                drop_selection
            ).transform_filter(
                brush
            ).transform_filter(
                click2
            ).transform_filter(
                click
            ).transform_filter(
                click3
            ).properties(title="WELL CONTENT PER PURPOSE",height=180,width=330)
    #        c = (bar1&bar2&bar3).resolve_scale(color='independent')
            return(map,points,bar1,bar2,bar3)

        map,points,bar1,bar2,bar3 = plt_wellbores(well_coord_npd,df_coasline_no)
        st.markdown(
            """
            <style type='text/css'>
                details {
                    display: none;
                }
            </style>
        """,
            unsafe_allow_html=True,
        )
        st.altair_chart((map+points)|(bar1&bar2&bar3), use_container_width=True)

        col1, col2, col3 = st.columns([2,6,2])
        if col2.button('⚠️ VISUALISING INSTRUCTIONS'):
            col2.markdown(f"""
                <div style="font-size: medium">
                👉 Hover the cursor over each well category to highlight and see its infomation
                (holding 'Shift' while hovering to highlight multiple categories).\n
                <div style="font-size: medium">
                👉 MB1 click on a well or well category to select it ('Shift+MB1' to select multiple categories).\n
                <div style="font-size: medium">
                👉'Shift+MB1' and drag to select an area on the location map).\n
                </div><br/>

            """,unsafe_allow_html=True)

#        test = well_coord_npd.loc[well_coord_npd.loc[:,'wlbNsDecDeg']>=50,:]
#        st.dataframe(test)
#        url = "https://raw.githubusercontent.com/deldersveld/topojson/master/countries//norway/norway-new-counties.json"
#        json_data = alt.topo_feature(url=url, feature='Fylker')
#        map = alt.Chart(json_data).mark_geoshape(stroke='gray',fill='lightblue')
#        point2 = alt.Chart(test).mark_point().encode(
#            latitude='wlbNsDecDeg:Q',
#            longitude='wlbEwDesDeg:Q').properties(title="Map",height=580,width=460)
#        st.altair_chart(point2+map)
#        st.subheader(f"""\
#            **{"" .join(str(tbl_wells.iloc[-1,5]))} Exploration & Development Wells Spudded from {"".join(str(df_wells['Spudded'].min()))} to {"".join(str(df_wells['Spudded'].max()))}**""")
    elif well == 'EXP & DEV Wells':
        df_wells.loc[0:5,'Area'] = "NORTH SEA"
        df_wells.loc[6:10,'Area'] = "NORWEGIAN SEA"
        df_wells.loc[11:15,'Area'] = "BARENTS SEA"
        df_wells.loc[(df_wells.loc[:,'Purpose'] == "INJECTION")|(df_wells.loc[:,'Purpose'] == "OBSERVATION")|(df_wells.loc[:,'Purpose'] == "PRODUCTION"),'Type'] = "DEV"
        df_wells.loc[(df_wells.loc[:,'Purpose'] == "APPRAISAL")|(df_wells.loc[:,'Purpose'] == "WILDCAT")|(df_wells.loc[:,'Purpose'] == "WILDCAT-CCS"),'Type'] = "EXP"
        df_wells.loc[:,'Category'] = df_wells.loc[:,'Area'] + "_" + df_wells.loc[:,'Type'] + "_" + df_wells.loc[:,'Purpose']
        df_wells = df_wells.iloc[:-1].drop(df_wells.columns[0:7], axis=1)
        df_wells = df_wells.melt(id_vars=['Category'], value_name='Wells', var_name='Spudded')

#        col1, col2 = st.columns([5,5])
        st.subheader(f"""\
            **{"" .join(str(tbl_wells.iloc[-1,5]))} Exploration & Development Wells Spudded from {"".join(str(df_wells['Spudded'].min()))} to {"".join(str(df_wells['Spudded'].max()))}**""")

        hover = alt.selection_multi(empty='all',fields=['Category'],on='mouseover')
        click = alt.selection_multi(empty='all',fields=['Category'])
        base = alt.Chart(df_wells).add_selection(hover).add_selection(click)

        c1 = base.mark_area(interpolate='monotone').encode(
            alt.X('Spudded:T',
              axis=alt.Axis(labelAngle=0, title='Spudded Year')),
            alt.Y('sum(Wells)', stack='center',
                axis=alt.Axis(title='Number of Wells')),
            tooltip=['Category','Spudded', 'Wells'],
            color=alt.Color('Category:N', scale=alt.Scale(scheme="tableau20",reverse=True), legend=None),
            opacity=alt.condition(hover|click, alt.value(1.0), alt.value(0.2))
            ).transform_filter(click).properties(title="ANNUAL WELL SPUDDED PER WELL CATEGORY",width=500,height=450).interactive()

        c2 = base.mark_bar().encode(
            x=alt.X('sum(Wells)'),
            y=alt.Y("Category",axis=alt.Axis(labels=False, title='Well Category')),
            tooltip=['Category', 'sum(Wells)'],
            color=alt.Color('Category:N', scale=alt.Scale(scheme="tableau20"), legend=None),
            opacity=alt.condition(hover|click, alt.value(1.0), alt.value(0.2))
            ).properties(title="TOTAL WELL SPUDDED",width=250,height=450)

        c = alt.hconcat(c2,c1)
        # Turn of the dots menu
        st.markdown(
            """
            <style type='text/css'>
                details {
                    display: none;
                }
            </style>
        """,
            unsafe_allow_html=True,
        )
#        with st.expander("STREAMGRAPH (hover your mouse to see each well category)", expanded=True):
        st.altair_chart(c, use_container_width=True)

        col1, col2, col3 = st.columns([2,6,2])
        if col2.button('⚠️ VISUALISING INSTRUCTIONS'):
            col2.markdown(f"""
                <div style="font-size: medium">
                👉 Hover the cursor over each well category to highlight and see its infomation
                (holding 'Shift' while hovering to highlight multiple categories).\n
                <div style="font-size: medium">
                👉 MB1 click on a well category to select it ('Shift+MB1' to select multiple categories).\n
                </div><br/>

            """,unsafe_allow_html=True)

        if col2.button('⚠️ STATISTICS FOR E&D WELLS'):
#            tbl_wells.columns.values[[1,3,5]] = ['Total per Area', 'Total per Type/Area', 'No. of Wells']
#            tbl_wells = tbl_wells.fillna("")
#            tbl_wells.loc[:,'Total per Area']=tbl_wells.loc[:,'Total per Area'].astype('str').str.replace(r"\.0",'')
#            tbl_wells.loc[:,'Total per Type/Area']=tbl_wells.loc[:,'Total per Type/Area'].astype('str').str.replace(r"\.0",'')
#            tbl_wells = tbl_wells.to_html()
#            components.html(tbl_wells,height=538, scrolling=True)
            st.table(tbl_wells)

    else :
        col1, col2 = st.columns([4,6])

        col1.subheader(f"""**{"".join(str(well))}'s location**""")
        df_map = well_coord_npd.loc[well_coord_npd.loc[:,'wlbWellboreName']==well,:]
        df_map.columns = df_map.columns.str.replace(r"wlb", "")
        df_map.loc[:,'lat'] = df_map.loc[:,'NsDecDeg']
        df_map.loc[:,'lon'] = df_map.loc[:,'EwDesDeg']
        col1.map(df_map,zoom=2)

        col2.subheader(f"""**Expand to see information for {"".join(str(well))}:**""")
        with col2.expander("WELLBORE DETAILS"):
            df_map = df_map.T
            df_map = df_map.rename(columns=df_map.iloc[18]).drop(df_map.index[18])
            df_map = df_map.iloc[:-3]
            df_map.index.values[[9,11,12,15,19,22,23,24]] = ['Production License', 'NPDID Wellbore', 'Purpose Planned', 'Completion Date', 'Drilling Operator', 'Geodetic Datum', 'Date Sync NPD', 'Main Area'  ]
            st.table(df_map)

        with col2.expander("WELLBORE HISTORY"):
        #his_out
            his = well_his_npd.loc[well_his_npd.loc[:,'wlbName']==well,'wlbHistory'].to_list()
            if len(his) == 0:
                st.write('Sorry! No history available for this well')
            elif his[0] != his[0]:
                st.write('Sorry! No history available for this well')
            else:
                st.markdown(f"""{his[0]}""", unsafe_allow_html=True)
#            his = pypandoc.convert_text(his[0], 'plain', format='html')
#            his_plain = re.sub('[\\r]', ' ', his)
#            ax2.text(0.5,1,his_plain, verticalalignment="top", transform=ax2.transAxes, fontsize=12)

#        col1.subheader(f"""**Other documents for {"".join(str(well))}:**""")
        df_doc = well_doc_npd.loc[well_doc_npd.loc[:,'wlbName']==well,:].reset_index(drop=True)
        df_doc.columns = df_doc.columns.str.replace(r"wlb", "")
        df_doc.index = df_doc.index + 1
        if len(df_doc.index) !=0 :
            for i in df_doc.index :
                df_doc.loc[i,'DocumentUrl'] = re.sub(r'\b((?:https?:\/\/)?(?:www\.)?(?:[^\s.]+\.)+\w{2,4})\b', r'<a href="\1">\1</a>', df_doc.loc[i,'DocumentUrl'])
            df_doc = df_doc.loc[:,['DocumentType', 'DocumentUrl', 'DocumentDateUpdated','datesyncNPD']].to_html(escape=False)
#                st.dataframe(df_doc)
            with col2.expander("OTHER DOCUMENTS"):
                components.html(df_doc,height=306, scrolling=True)
        else :
            with col2.expander("OTHER DOCUMENTS"):
                st.write('Sorry! No other information available for this well')
    return None

def well():
    col1, col2,col3 = st.sidebar.columns([0.9,7.7,1.4])
    well_litho_npd, df_wells, tbl_wells, df_units, well_his_npd, well_coord_npd, well_doc_npd, df_coasline_no = read_welldata()
    litho_wellnames = well_litho_npd.drop_duplicates(subset = ['wlbName'])['wlbName'].to_list()
    all = ['OVERVIEW']
    litho_wellnames = all + litho_wellnames
    well = col2.selectbox('Select LYS from:', litho_wellnames)

    group_sgp=well_litho_npd.loc[(well_litho_npd.loc[:,'lsuLevel']=='GROUP') | (well_litho_npd.loc[:,'lsuLevel']=='SUBGROUP'),:]
    group_sgp.loc[:,('lsuName')] = "TOP " + group_sgp.loc[:,('lsuName')]
    group=well_litho_npd.loc[well_litho_npd.loc[:,'lsuLevel']=='GROUP',:]
    group.loc[:,('lsuName')] = "TOP " + group.loc[:,('lsuName')]
    formation=well_litho_npd.loc[(well_litho_npd.loc[:,'lsuLevel']=='FORMATION') | (well_litho_npd.loc[:,'lsuLevel']=='MEMBER'),:]
    formation.loc[:,('lsuName')] = "TOP " + formation.loc[:,('lsuName')]
    legend_csv = StringIO("""width,hatch, component formation
    2,,TOP BOKNFJORD GP
    3,,TOP VESTLAND GP
    25,o,TOP CROMER KNOLL GP
    8,+,TOP NORDLAND GP
    10,..,TOP ROGALAND GP
    12,,TOP SHETLAND GP
    15,,TOP ZECHSTEIN GP
    20,++,TOP HORDALAND GP
    24,,TOP UNDEFINED GP
    29,,TOP ROTLIEGEND GP
    1,,TOP NO GROUP DEFINED
    33,,TOP HEGRE GP
    32,^,TOP BASEMENT
    31,,TOP TYNE GP
    30,,TOP ADVENTDALEN GP
    28,,TOP KAPP TOSCANA GP
    27,,TOP SASSENDALEN GP
    26,,TOP TEMPELFJORDEN GP
    5,,TOP SOTBAKKEN GP
    23,,TOP NYGRUNNEN GP
    22,,TOP BJARMELAND GP
    21,,TOP GIPSDALEN GP
    19,,TOP BILLEFJORDEN GP
    18,,TOP VIKING GP
    17,,TOP BÅT GP
    16,,TOP GREY BEDS (INFORMAL)
    14,,TOP FANGST GP
    13,,TOP RED BEDS (INFORMAL)
    11,,TOP DUNLIN GP
    9,,TOP STATFJORD GP
    7,,TOP BRENT GP
    6,,TOP NO DATA
    4,,TOP FLADEN GP
    """)

    legend = pd.read_csv(legend_csv, sep=",")
    time = Legend.default()
    l = time[160:193]
    colour_csv=StringIO(l.to_csv())
    colour=pd.read_csv(colour_csv, sep=",")
    legend['colour'] = colour.index
    legend_csv=legend.to_csv(index=False)
    legend = Legend.from_csv(text=legend_csv)

    def lithostrat(well_name):
    #group_out
        group_out=pd.DataFrame([])
        group_out[['top','base','Comp formation','Layer_id']]=group[group['wlbName']==well_name].sort_values(by=['lsuTopDepth','lsuBottomDepth'], ascending=[True,False])[['lsuTopDepth','lsuBottomDepth','lsuName','lsuNpdidLithoStrat']]
    #for_out
        for_out=pd.DataFrame([])
        for_out[['top','base','Comp formation','Layer_id']]=formation[formation['wlbName']==well_name].sort_values(by=['lsuTopDepth','lsuBottomDepth'], ascending=[True,False])[['lsuTopDepth','lsuBottomDepth','lsuName','lsuNpdidLithoStrat']]
    #pd_out
        pd_out=pd.DataFrame([])
        pd_out[['top','base','Comp formation','Layer_id']]=group_sgp[group_sgp['wlbName']==well_name].sort_values(by=['lsuTopDepth','lsuBottomDepth'], ascending=[True,False])[['lsuTopDepth','lsuBottomDepth','lsuName','lsuNpdidLithoStrat']]
    #striplogs
        pdout_csv=pd_out.to_csv(index=False)
        grout_csv=group_out.to_csv(index=False)
        frout_csv=for_out.to_csv(index=False)
        if len(pd_out) == 0:
            tops = "N/A"
        else:
            tops = Striplog.from_csv(text=pdout_csv)
        if len(for_out) == 0:
            formations = "N/A"
        else:
            formations = Striplog.from_csv(text=frout_csv)
        if len(group_out) == 0:
            groups = "N/A"
        else:
            groups = Striplog.from_csv(text=grout_csv)
    #plot
        fig, (ax0, ax1, ax2) = plt.subplots(1, 3, sharey=True, figsize=(3.5, 30.))
        if len(for_out) == 0:
            ax2.text(0.5,1,formations, verticalalignment="top", transform=ax2.transAxes, fontsize=12)
        else:
            ax2 = formations.plot(ax=ax2, style='tops', field='formation',aspect=6)
        if len(group_out) == 0:
            ax0.text(0.4,1,groups, verticalalignment="top", transform=ax0.transAxes, fontsize=12)
            ax0.axis('off')
        else:
            ax0 = groups.plot(ax=ax0, aspect=6, legend=legend, ladder=True)
            ax0 = tops.plot(ax=ax0, style='tops', field='formation',aspect=6)

        ax1.axis('off')
        ax2.axis('off')
    #    ax0.axis('off')
    #    ax4.axis('off')
    #    ax5.axis('off')

        ax0.set_title("Groups", pad=30, fontsize=12,fontweight="bold")
        ax0.set_ylabel("Measured Depth (m)", fontsize=11,fontweight="bold")
        ax2.set_title("Formation Tops", pad=30, fontsize=12, x=0.7,fontweight="bold")
    #    ax4.set_title("Wellbore History", pad=30,fontweight="bold", fontsize=15, x=0.1)
    #    fig.suptitle('LITHOSTRATIGRAPHY & HISTORY FOR WELL: '+well_name, fontsize=18, x=0.5, y=0.95,fontweight="bold")
    #    filename = re.sub('[\/]', '-', well_name)
    #    plt.savefig(filename+".pdf", dpi=300)
    #    plt.show()
        return tops,groups,formations,fig

    if well == 'OVERVIEW':
        st.subheader(f"""\
            **{"" .join(str(len(litho_wellnames)-1))} Wells with Lithostratigraphic Information**""")
#        st.stop()
        well_coord_npd = well_coord_npd.loc[well_coord_npd.loc[:,'wlbWellboreName'].isin(litho_wellnames),:]
#        st.dataframe(well_coord_npd)

        def plt_wellbores(well_coord_npd,df_coasline_no):
            min_year = well_coord_npd["year"].min()
            max_year = well_coord_npd["year"].max()
            min_x = well_coord_npd["wlbEwDesDeg"].min()
            max_x = well_coord_npd["wlbEwDesDeg"].max()
            max_y = well_coord_npd["wlbNsDecDeg"].max()
            well_compnames = well_coord_npd.drop_duplicates(subset = ['wlbDrillingOperator'])['wlbDrillingOperator'].to_list()
            well_compnames = ['Select a company'] + well_compnames
    #        st.dataframe(well_coord_npd)
            brush = alt.selection_interval(on="[mousedown[event.shiftKey], mouseup[event.shiftKey]] > mousemove[event.shiftKey]",name='brush')
    #        interact = alt.selection_interval(on="[mousedown[event.altKey], mouseup[event.altKey]] > mousemove[event.altKey]",name='interact',bind='scales')
            click = alt.selection_multi(empty='all',encodings=["y"])
            click3 = alt.selection_multi(empty='all',encodings=["y"])
            click4 = alt.selection_multi(empty='all',encodings=["y"])
            click2 = alt.selection_multi(empty='all',encodings=["y"])
            hover = alt.selection_multi(empty='all',on='mouseover',encodings=["y"])
            input_dropdown = alt.binding_select(options=well_compnames)
            drop_selection = alt.selection_single(fields=['wlbDrillingOperator'], bind=input_dropdown, name='Name of')
            # A slider filter
            year_slider = alt.binding_range(min=min_year, max=max_year, step=1)
            slider_selection = alt.selection_single(bind=year_slider, fields=['year'], name="Spudded")
            points = alt.Chart(well_coord_npd).mark_point(clip=True,strokeWidth=1,size=30).encode(
                y=alt.Y('wlbNsDecDeg:Q',scale=alt.Scale(domain=(55,max_y))),
                x=alt.X('wlbEwDesDeg:Q',scale=alt.Scale(domain=(min_x,max_x))),
                tooltip=['wlbWellboreName','wlbPurposePlanned:N','wlbWellType:N','wlbMainArea:N','wlbContent:N'],
                shape=alt.Shape('wlbPurposePlanned:N', legend=alt.Legend(strokeColor='black',padding=5,fillColor='white',title=None,offset=5,orient="bottom",columns=9)),
                opacity=alt.condition(hover, alt.value(1.0), alt.value(0.1)),
    #            fill =alt.condition(brush,'wlbContent:N', alt.value('lightgray'), scale=alt.Scale(scheme="category20b", reverse=True), legend=None),
                color=alt.condition(brush|click2, 'wlbContent:N', alt.value('lightgray'), scale=alt.Scale(scheme="category20b", reverse=True), legend=None)
            ).interactive().add_selection(
                brush,slider_selection,click2,drop_selection
            ).transform_filter(
                slider_selection
            ).transform_filter(
                drop_selection
            ).transform_filter(
                click
            ).transform_filter(
                click3
            ).transform_filter(
                click4
            ).properties(title="WELL LOCATION ON THE NCS",height=403, width=370)

            map = alt.Chart(df_coasline_no).mark_area(
                strokeWidth=0.5,color='gray'
            ).encode(
                y=alt.Y('x:Q',scale=alt.Scale(domain=(55,max_y)), title=None, axis=None),
                x=alt.X('y:Q',scale=alt.Scale(domain=(min_x,max_x)), title=None, axis=None),
                order='0:O'
                ).interactive()

            base = alt.Chart(well_coord_npd).add_selection(hover,slider_selection,drop_selection)
            bar1 = base.mark_bar(size=10).encode(
                y=alt.Y('wlbMainArea:N', title=None),
                color='wlbWellType:N',
                tooltip=['wlbWellType:N','count(wlbWellType):Q'],
                opacity=alt.condition(hover|click, alt.value(1.0), alt.value(0.2)),
                x=alt.X('count(wlbMainArea):Q', title='Number of Wells')
            ).add_selection(
                click
            ).transform_filter(
                slider_selection
            ).transform_filter(
                drop_selection
            ).transform_filter(
                brush
            ).transform_filter(
                click2
            ).transform_filter(
                click3
            ).transform_filter(
                click4
            ).properties(title="WELL TYPE PER MAIN AREA",height=40,width=330)

            bar2 = base.mark_bar(size=10).encode(
                y=alt.Y('wlbWellType:N', title=None),
                color='wlbPurposePlanned:N',
                tooltip=['wlbPurposePlanned:N','count(wlbPurposePlanned):Q'],
                opacity=alt.condition(hover|click3, alt.value(1.0), alt.value(0.2)),
                x=alt.X('count(wlbWellType):Q', title='Number of Wells')
            ).add_selection(
                click3
            ).transform_filter(
                slider_selection
            ).transform_filter(
                drop_selection
            ).transform_filter(
                brush
            ).transform_filter(
                click2
            ).transform_filter(
                click
            ).transform_filter(
                click4
            ).properties(title="WELL PURPOSE PER TYPE",height=40,width=330)

            bar3 = base.mark_bar(size=10).encode(
                y=alt.Y('wlbPurposePlanned:N', title=None),
                color=alt.Color('wlbContent:N', scale=alt.Scale(scheme="category20b", reverse=True)),
                tooltip=['wlbContent:N','count(wlbContent):Q'],
                opacity=alt.condition(hover|click4, alt.value(1.0), alt.value(0.2)),
                x=alt.X('count(wlbPurposePlanned):Q', title='Number of Wells')
            ).add_selection(
                click4
            ).transform_filter(
                slider_selection
            ).transform_filter(
                drop_selection
            ).transform_filter(
                brush
            ).transform_filter(
                click2
            ).transform_filter(
                click
            ).transform_filter(
                click3
            ).properties(title="WELL CONTENT PER PURPOSE",height=180,width=330)
    #        c = (bar1&bar2&bar3).resolve_scale(color='independent')
            return(map,points,bar1,bar2,bar3)

        map,points,bar1,bar2,bar3 = plt_wellbores(well_coord_npd,df_coasline_no)
        st.markdown(
            """
            <style type='text/css'>
                details {
                    display: none;
                }
            </style>
        """,
            unsafe_allow_html=True,
        )
        st.altair_chart((map+points)|(bar1&bar2&bar3), use_container_width=True)

    else:
        col1, col2 = st.columns([4,6])

        col1.subheader(f"""**{"".join(str(well))}'s location**""")
        df_map = well_coord_npd.loc[well_coord_npd.loc[:,'wlbWellboreName']==well,:]
        df_map.columns = df_map.columns.str.replace(r"wlb", "")
        df_map.loc[:,'lat'] = df_map.loc[:,'NsDecDeg']
        df_map.loc[:,'lon'] = df_map.loc[:,'EwDesDeg']
        col1.map(df_map,zoom=2)

        col2.subheader(f"""**Expand to see information for {"".join(str(well))}:**""")
        with col2.expander("WELLBORE DETAILS"):
            df_map = df_map.T
            df_map = df_map.rename(columns=df_map.iloc[18]).drop(df_map.index[18])
            df_map = df_map.iloc[:-3]
            df_map.index.values[[9,11,12,15,19,22,23,24]] = ['Production License', 'NPDID Wellbore', 'Purpose Planned', 'Completion Date', 'Drilling Operator', 'Geodetic Datum', 'Date Sync NPD', 'Main Area'  ]
            st.table(df_map)

        with col2.expander("WELLBORE HISTORY"):
        #his_out
            his = well_his_npd.loc[well_his_npd.loc[:,'wlbName']==well,'wlbHistory'].to_list()
            if len(his) == 0:
                st.write('Sorry! No history available for this well')
            elif his[0] != his[0]:
                st.write('Sorry! No history available for this well')
            else:
                st.markdown(f"""{his[0]}""", unsafe_allow_html=True)
#            his = pypandoc.convert_text(his[0], 'plain', format='html')
#            his_plain = re.sub('[\\r]', ' ', his)
#            ax2.text(0.5,1,his_plain, verticalalignment="top", transform=ax2.transAxes, fontsize=12)

#        col1.subheader(f"""**Other documents for {"".join(str(well))}:**""")
        df_doc = well_doc_npd.loc[well_doc_npd.loc[:,'wlbName']==well,:].reset_index(drop=True)
        df_doc.columns = df_doc.columns.str.replace(r"wlb", "")
        df_doc.index = df_doc.index + 1
        if len(df_doc.index) !=0 :
            for i in df_doc.index :
                df_doc.loc[i,'DocumentUrl'] = re.sub(r'\b((?:https?:\/\/)?(?:www\.)?(?:[^\s.]+\.)+\w{2,4})\b', r'<a href="\1">\1</a>', df_doc.loc[i,'DocumentUrl'])
            df_doc = df_doc.loc[:,['DocumentType', 'DocumentUrl', 'DocumentDateUpdated','datesyncNPD']].to_html(escape=False)
#                st.dataframe(df_doc)
            with col2.expander("OTHER DOCUMENTS"):
                components.html(df_doc,height=306, scrolling=True)
        else :
            with col2.expander("OTHER DOCUMENTS"):
                st.write('Sorry! No other information available for this well')

        col1, col2, col3 = st.columns([2.5,6.2,1.3])
        col2.subheader(f"""**Lithostratigraphic Yielded Solution for {"".join(str(well))}**""")
        units,groups,formations,fig = lithostrat(well)
        col1, col2 = st.columns([4,6])
        with col1.expander("LITHOSTRATIGRAPHIC CHART",expanded=True):
            st.pyplot(fig)
#        col3.subheader(f"""**Expand to see more information for {"".join(str(well))}:**""")

        with col2.expander("DESCRIPTION OF LITHOSTRATIGRAPHIC UNITS",expanded=True):
            litho_unit = well_litho_npd.loc[well_litho_npd.loc[:,'wlbName']==well,:].sort_values(by=['lsuTopDepth','lsuBottomDepth'], ascending=[True,False])
            litho_unit = litho_unit.drop_duplicates(subset = ['lsuName'])['lsuName'].to_list()
            Lithostrat_unit = st.selectbox('Select Lithostratigraphic Unit', litho_unit)
            df_strat = df_units.loc[df_units.loc[:,'Lithostrat. unit']==Lithostrat_unit,:].reset_index(drop=True)
            unit_des = df_strat.loc[:,'Description'].to_list()[0]
#            df_strat['Description'] = 'See below'
#            df_strat['NPD FactPage link'] = 'See below description'
            st.markdown("**General**")
            df_strat = df_strat.loc[:,['Lithostrat. unit', 'Level', 'Lithostrat. unit, parent', 'NPDID lithostrat. unit', 'NPDID parent lithostrat. unit']].T
            df_strat = df_strat.rename(columns=df_strat.iloc[0]).drop(df_strat.index[0])
            st.dataframe(df_strat)
            st.markdown("**Description**")
            st.markdown(f"""{unit_des}""", unsafe_allow_html=True)
#            st.write('More info: ', df_strat.loc[0,'FactPage'])


    return None

    # ----------------------
def _max_width_():
    max_width_str = f"max-width: 2000px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}

    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    _max_width_()
    main()

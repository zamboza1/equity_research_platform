from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Any
import io
import re
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from xml.sax.saxutils import escape

router=APIRouter()
class ExportRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    model_type:str=Field(min_length=1,max_length=40)
    ticker:str=Field(min_length=1,max_length=30)
    data:list[dict[str,Any]]=Field(min_length=1,max_length=1000)

def table_data(request):
    columns=list(dict.fromkeys(k for row in request.data for k in row))
    if len(columns)>60: raise ValueError('Export supports at most 60 columns')
    rows=[]
    for row in request.data:
        values=[]
        for key in columns:
            value=row.get(key)
            if isinstance(value,(dict,list)): value=str(value)
            if isinstance(value,str):
                value=value[:10000]
                if value.lstrip().startswith(('=','+','-','@')): value="'"+value
            values.append(value)
        rows.append(values)
    return columns,rows

def filename(request,extension):
    return re.sub(r'[^A-Za-z0-9_-]','_',f'{request.ticker}_{request.model_type}')+extension

@router.post('/excel')
def excel(request:ExportRequest):
    columns,rows=table_data(request)
    workbook=Workbook();sheet=workbook.active;sheet.title='Analysis'
    sheet.append(columns)
    for cell in sheet[1]:cell.font=Font(bold=True)
    for row in rows:sheet.append(row)
    sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    for col in sheet.columns:sheet.column_dimensions[col[0].column_letter].width=min(38,max(15,len(str(col[0].value))+2))
    stream=io.BytesIO();workbook.save(stream);stream.seek(0)
    return StreamingResponse(stream,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':f'attachment; filename="{filename(request,".xlsx")}"'})

@router.post('/pdf')
def pdf(request:ExportRequest):
    columns,rows=table_data(request)
    if len(columns)>8 or len(rows)>100:raise ValueError('PDF export supports at most 8 columns and 100 rows; use Excel for larger models')
    stream=io.BytesIO();styles=getSampleStyleSheet();style=styles['BodyText'];style.fontSize=7
    contents=[Paragraph(escape(request.model_type+' · '+request.ticker),styles['Heading1'])]
    data=[[Paragraph(escape(str(x))[:500],style) for x in row] for row in [columns]+rows]
    table=Table(data,repeatRows=1,colWidths=[740/len(columns)]*len(columns))
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e0e7ff')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.25,colors.lightgrey)]));contents.append(table)
    SimpleDocTemplate(stream,pagesize=landscape(A4),leftMargin=40,rightMargin=40).build(contents);stream.seek(0)
    return StreamingResponse(stream,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="{filename(request,".pdf")}"'})

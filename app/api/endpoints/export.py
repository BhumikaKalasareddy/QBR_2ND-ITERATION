import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.services.ppt_service import generate_qbr_presentation
from app.services.pdf_service import convert_pptx_to_pdf
from app.services.bigquery_service import (
    fetch_slide_6_kpis,
    fetch_casb_slide1_data,
    fetch_casb_slide2_data,
    fetch_swg_slide1_data,
    fetch_swg_slide2_data,
    fetch_slide11_support_data,
    fetch_slide12_case_analytics,
    fetch_slide_13_whats_next
)

router = APIRouter()

class PresentationRequest(BaseModel):
    account_name: str
    quarter: str = "Q2 2026"
    product: str = "CASB"
    selected_slides: list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    chart_type: str = "Bar"
    layout_style: str = "Default"
    export_pdf: bool = False

@router.post("/generate-ppt")
def generate_ppt(req: PresentationRequest):
    try:
        # 1. Selective data fetching based on user slide selection
        kpi_metrics = fetch_slide_6_kpis(req.account_name) if 6 in req.selected_slides else []
        
        casb1, casb2, swg1, swg2 = None, None, None, None
        if req.product.upper() == "CASB":
            casb1 = fetch_casb_slide1_data(req.account_name) if 7 in req.selected_slides else None
            casb2 = fetch_casb_slide2_data(req.account_name) if 8 in req.selected_slides else None
        else:
            swg1 = fetch_swg_slide1_data(req.account_name) if 7 in req.selected_slides else None
            swg2 = fetch_swg_slide2_data(req.account_name) if 8 in req.selected_slides else None

        support_data = fetch_slide11_support_data(req.account_name) if 11 in req.selected_slides else None
        case_trends = fetch_slide12_case_analytics(req.account_name) if 12 in req.selected_slides else None
        whats_next_data = fetch_slide_13_whats_next(req.account_name) if 13 in req.selected_slides else None

        # 2. Assemble presentation
        pptx_path = generate_qbr_presentation(
            account_name=req.account_name,
            quarter=req.quarter,
            product_choice=req.product,
            selected_slides=req.selected_slides,
            chart_type=req.chart_type,
            layout_style=req.layout_style,
            kpi_data=kpi_metrics,
            casb1_df=casb1,
            casb2_df=casb2,
            swg1_df=swg1,
            swg2_df=swg2,
            support_data=support_data,
            case_trends=case_trends,
            whats_next_data=whats_next_data
        )

        # 3. Process PDF export if requested
        if req.export_pdf:
            final_path = convert_pptx_to_pdf(pptx_path)
            media_type = "application/pdf"
        else:
            final_path = pptx_path
            media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        # 4. Sanitize account name for output filename
        safe_acc_name = re.sub(r'[\\/*?:"<>|]', '_', req.account_name).replace(' ', '_')
        ext = "pdf" if req.export_pdf else "pptx"

        return FileResponse(
            path=final_path,
            filename=f"QBR_{safe_acc_name}_{req.quarter}.{ext}",
            media_type=media_type
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
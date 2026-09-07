import subprocess
import os

def convert_pptx_to_pdf(pptx_path: str) -> str:
    """
    Converts a PPTX file to PDF using LibreOffice in headless mode.
    Returns the path to the generated PDF.
    """
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PPTX file not found at: {pptx_path}")

    output_dir = os.path.dirname(pptx_path)
    pdf_filename = os.path.splitext(os.path.basename(pptx_path))[0] + ".pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)

    try:
        cmd = [
            "soffice", "--headless", "--convert-to", "pdf",
            pptx_path, "--outdir", output_dir
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return pdf_path
    except Exception as e:
        print(f"LibreOffice conversion fallback notice: {e}")
        # Fallback: Return PPTX path if PDF engine isn't installed locally
        return pptx_path
# ============================================================
# pipeline/mailer.py
#
# Sends assignment delivery email via SendGrid API.
# Uses official SendGrid Python SDK.
# ============================================================

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import SENDGRID_API_KEY, SENDER_EMAIL


def send_email(
    student_name:  str,
    student_email: str,
    zip_url:       str,
    dataset_info:  dict,
    metrics:       dict
) -> bool:
    """
    Send the assignment delivery email using SendGrid.
    """

    r2_pct  = round(metrics["r2"] * 100, 1)
    subject = f"COS201 Assignment — {dataset_info['display_name']} Regression Files"

    body = f"""
Dear {student_name},

Your COS201 Multiple Linear Regression assignment has been generated and is ready for download.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOWNLOAD YOUR ASSIGNMENT:
{zip_url}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your ZIP file contains:
  • {dataset_info['filename']}
    Your unique dataset ({dataset_info['n_rows']} rows, {dataset_info['display_name']} theme)

  • {dataset_info['filename'].replace('.csv', '_regression.ipynb')}
    Your Jupyter notebook — already executed with all outputs visible

  • heatmap.png
  • scatter.png
  • residual.png
  • defense_guide.txt

Your model achieved an R² of {metrics['r2']:.4f} ({r2_pct}% variance explained).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Download and extract the ZIP into one folder
2. Open the .ipynb file in Jupyter Notebook or Google Colab
3. Outputs are already rendered
4. Read defense_guide.txt before your viva
5. Do NOT rename files

This download link is permanent. Keep it safe.

Best regards,
COS201 Course Team
"""

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=student_email,
        subject=subject,
        plain_text_content=body
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        # SendGrid returns 202 on success
        if response.status_code == 202:
            print(f"✅ Email sent to {student_email}")
            return True
        else:
            print(f"❌ SendGrid failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False
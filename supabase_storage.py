import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from the .env file
load_dotenv()

def init_supabase() -> Client:
    # Get the Supabase URL and API key from environment variables
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # Check if the variables are set
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL and API key must be set in the environment variables")

    # Initialize the Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

# Function to upload a file to Supabase Storage in the specified bucket
def upload_to_supabase(file_path: str, bucket_name: str) -> str:
    # Initialize Supabase client
    supabase = init_supabase()

    # Get the filename
    file_name = os.path.basename(file_path)
    
    # Create a unique name for the file based on timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_file_name = f"{timestamp}_{file_name}"

    # Upload file to the specified bucket in Supabase storage
    try:
        with open(file_path, "rb") as file_data:
            # Ensure correct MIME type for PDF files
            response = supabase.storage.from_(bucket_name).upload(f"{unique_file_name}", file_data.read(), {
                "content-type": "application/pdf"
            })
            print(f"File uploaded to {bucket_name}: {response}")
        
        # Get the public URL of the file
        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_file_name)
        print("Public URL:", public_url)

        return public_url
    except Exception as e:
        print(f"Error uploading file to Supabase: {e}")
        return None

# Usage example
if __name__ == "__main__":

    # Define the folder structure
    parent_folder = "speech_analysis_output"
    pdf_folder = os.path.join(parent_folder, "pdf_reports")

    # Set paths to the PDF reports you want to upload, using the updated folder structure
    report_pdf_path = os.path.join(pdf_folder, "report.pdf")  # Path to your first PDF (for reports bucket)
    final_report_pdf_path = os.path.join(pdf_folder, "final_report.pdf")  # Path to your second PDF (for final_report bucket)

    # Upload to "reports" bucket
    upload_to_supabase(report_pdf_path, "reports")

    # Upload to "final_report" bucket
    upload_to_supabase(final_report_pdf_path, "final_report")

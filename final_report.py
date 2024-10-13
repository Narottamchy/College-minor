import os
from openai import OpenAI
from fpdf import FPDF
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up the OpenAI client using your API key from environment variable
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")  # Get API key from the .env file
)

# Function to read the contents of the speech_report.txt file
def read_speech_report(file_path):
    try:
        with open(file_path, 'r') as file:
            report_text = file.read()
        return report_text
    except FileNotFoundError as e:
        print(f"Error: File not found - {file_path}. {e}")
        return None
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None

# Function to get OpenAI GPT summary, conclusions, and insights based on the speech report
def generate_openai_report(report_text):
    if report_text is None:
        return "Error: No valid speech report content to process."

    prompt = f"Here is a detailed speech analysis report:\n\n{report_text}\n\nPlease provide a brief overview, key insights, summary, conclusions, and necessary actions based on this report."

    try:
        # Using the new API call to generate chat completions
        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="gpt-4",
        )
        # Extract the content from the response correctly
        message_content = response.choices[0].message.content
        return message_content
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "Error: Could not generate a report. Please check the API or try again later."

# Function to generate the final PDF report
def generate_final_report(openai_summary, pdf_filename="final_report.pdf"):
    if openai_summary is None:
        openai_summary = "Error: No valid summary generated."

    try:
        # Create a new PDF for the final report
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Main title
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(200, 10, txt="Final Speech Analysis Report", ln=True, align="C")

        # Add a line break and change font size
        pdf.set_font("Arial", 'B', 16)
        pdf.ln(10)

        # Summary section from OpenAI
        pdf.cell(200, 10, txt="Summary and Key Insights", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, openai_summary)  # Insert the OpenAI generated summary

        # Add graphs to the report from the previous report
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Waveform", ln=True, align="C")
        pdf.ln(10)
        pdf.image("speech_analysis_output/report_images/waveform.png", w=190)

        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Spectrogram and Intensity", ln=True, align="C")
        pdf.ln(10)
        pdf.image("speech_analysis_output/report_images/spectrogram_intensity.png", w=190)

        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Spectrogram and Pitch", ln=True, align="C")
        pdf.ln(10)
        pdf.image("speech_analysis_output/report_images/spectrogram_pitch.png", w=190)

        # Save the final PDF report in the pdf_reports folder
        pdf_output_path = os.path.join("speech_analysis_output/pdf_reports", pdf_filename)
        pdf.output(pdf_output_path)
        print(f"Final report saved as {pdf_output_path}")
    except Exception as e:
        print(f"Error generating the final report: {e}")

# Function for final report generation with error handling
def final_report_generation():
    try:
        # Step 1: Read the content of the speech_report.txt file from text_reports folder
        speech_report_path = os.path.join("speech_analysis_output", "text_reports", "speech_report.txt")
        speech_report_text = read_speech_report(speech_report_path)
        if not speech_report_text:
            print("Error: Speech report content is missing or invalid.")
            return

        # Step 2: Generate the OpenAI-generated content (summary, conclusions, etc.)
        openai_summary = generate_openai_report(speech_report_text)

        # Step 3: Generate the final PDF report
        generate_final_report(openai_summary)
    except Exception as e:
        print(f"Error in final report generation process: {e}")

# Run the final report generation process
if __name__ == "__main__":
    final_report_generation()

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from newapp import ask_question, upload_pdf
from keyword_extractor import extract_keywords  # Import the function from keyword_extractor.py
from keybert import KeyBERT
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import resend

kw_model = KeyBERT(model='all-MiniLM-L6-v2')

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return "Welcome to the InQuiro AI💻🔥"

@app.route('/ask', methods=['POST'])
def ask():
    try:
        result = ask_question()
        return result
    except Exception as e:
        return jsonify({"error": "Error in ask endpoint", "details": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        result = upload_pdf()
        return result
    except Exception as e:
        return jsonify({"error": "Error in upload endpoint", "details": str(e)}), 500

@app.route('/extract_keywords_manual', methods=['POST'])
def extract_keywords_endpoint():
    """API endpoint to extract keywords from provided text and documents."""
    data = request.get_json()
    if not data or 'text' not in data or 'docs' not in data:
        return jsonify({'error': 'No valid text or docs provided'}), 400

    custom_text = data['text']
    docs = data['docs']  # Get documents from the request

    keywords = extract_keywords(custom_text, docs)

    return jsonify(keywords), 200

@app.route('/extract_keywords', methods=['POST'])
def extract_keywords_keybert():
    """API endpoint to extract keywords from provided text using KeyBERT."""
    data = request.get_json()
    
    # Check if the text field is provided in the request
    if not data or 'text' not in data:
        return jsonify({'error': 'No valid text provided'}), 400

    # Extract the document text
    doc = data['text']
    
    # Get the top_n value from the request, or use a default value of 10
    top_n = data.get('keywords', 10)  # Default value is 50 if top_n is not provided

    try:
        # Extract keywords using KeyBERT with the dynamic top_n
        keywords = kw_model.extract_keywords(doc, keyphrase_ngram_range=(1, 1), stop_words=None, top_n=top_n)

        return jsonify({'keywords': keywords}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Function to extract keywords using KeyBERT
def extract_keywords_from_text(text):
    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 1), stop_words=None, top_n=50)
    return [kw[0] for kw in keywords]  # Return only the keyword, not the score

# Function to calculate similarity between documents using cosine similarity
def calculate_similarity(doc_keywords):
    # Create a TF-IDF vectorizer for the keyword lists
    tfidf_vectorizer = TfidfVectorizer()
    
    # Combine all the keywords into documents
    tfidf_matrix = tfidf_vectorizer.fit_transform(doc_keywords)
    
    # Calculate cosine similarity between the documents
    cosine_sim = cosine_similarity(tfidf_matrix)
    return cosine_sim

# Function to generate textual descriptions of the similarity results
def generate_similarity_description(similarity_matrix, docs):
    n_docs = len(docs)
    descriptions = []
    
    for i in range(n_docs):
        for j in range(i + 1, n_docs):
            similarity_percentage = round(similarity_matrix[i][j] * 100, 2)
            descriptions.append(f"Text {i+1} and Text {j+1} have a similarity of {similarity_percentage}%.")

    return descriptions

@app.route('/compare_documents', methods=['POST'])
def compare_documents():
    """API to compare content similarity between two or more documents."""
    data = request.get_json()

    if not data or 'docs' not in data:
        return jsonify({'error': 'No valid texts are provided'}), 400

    docs = data['docs']

    if len(docs) < 2:
        return jsonify({'error': 'At least two text fields are required to compare'}), 400

    try:
        # Step 1: Extract keywords for each document
        doc_keywords = [extract_keywords_from_text(doc) for doc in docs]

        # Step 2: Calculate similarity between the documents
        similarity_matrix = calculate_similarity([" ".join(kw) for kw in doc_keywords])

        # Step 3: Generate textual descriptions of similarity
        similarity_descriptions = generate_similarity_description(similarity_matrix, docs)

        # Step 4: Prepare the response
        return jsonify({
            'similarity_matrix': similarity_matrix.tolist(),
            'similarity_descriptions': similarity_descriptions
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/contact', methods=['POST'])
def contact():
    try:
        # Get the data from the incoming request (assume JSON)
        data = request.get_json()

        resend.api_key = os.getenv('RESEND_API_KEY')

        # Validate the required fields
        if not data or 'name' not in data or 'email' not in data or 'message' not in data:
            return jsonify({'error': 'Name, email, and message are required'}), 400
        
        name = data['name']
        email = data['email']
        message = data['message']

        html_template= f"""
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional //EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<!--[if gte mso 9]>
<xml>
  <o:OfficeDocumentSettings>
    <o:AllowPNG/>
    <o:PixelsPerInch>96</o:PixelsPerInch>
  </o:OfficeDocumentSettings>
</xml>
<![endif]-->
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="x-apple-disable-message-reformatting">
  <!--[if !mso]><!--><meta http-equiv="X-UA-Compatible" content="IE=edge"><!--<![endif]-->
  <title></title>
  
    <style type="text/css">
      
      @media only screen and (min-width: 620px) {{
        .u-row {{
          width: 600px !important;
        }}

        .u-row .u-col {{
          vertical-align: top;
        }}

        
            .u-row .u-col-100 {{
              width: 600px !important;
            }}
          
      }}

      @media only screen and (max-width: 620px) {{
        .u-row-container {{
          max-width: 100% !important;
          padding-left: 0px !important;
          padding-right: 0px !important;
        }}

        .u-row {{
          width: 100% !important;
        }}

        .u-row .u-col {{
          display: block !important;
          width: 100% !important;
          min-width: 320px !important;
          max-width: 100% !important;
        }}

        .u-row .u-col > div {{
          margin: 0 auto;
        }}


}}
    
body{{margin:0;padding:0}}table,td,tr{{border-collapse:collapse;vertical-align:top}}p{{margin:0}}.ie-container table,.mso-container table{{table-layout:fixed}}*{{line-height:inherit}}a[x-apple-data-detectors=true]{{color:inherit!important;text-decoration:none!important}}


table, td {{ color: #000000; }} @media (max-width: 480px) {{ #u_content_heading_1 .v-container-padding-padding {{ padding: 118px 10px 5px !important; }} #u_content_heading_1 .v-font-size {{ font-size: 45px !important; }} #u_content_heading_3 .v-font-size {{ font-size: 55px !important; }} #u_content_heading_2 .v-container-padding-padding {{ padding: 5px 10px 115px !important; }} #u_content_heading_2 .v-font-size {{ font-size: 55px !important; }} #u_content_text_1 .v-container-padding-padding {{ padding: 60px 15px !important; }} #u_content_text_1 .v-text-align {{ text-align: justify !important; }} }}
    </style>
  
  

<!--[if !mso]><!--><link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700&display=swap" rel="stylesheet" type="text/css"><link href="https://fonts.googleapis.com/css?family=Playfair+Display:400,700&display=swap" rel="stylesheet" type="text/css"><!--<![endif]-->

</head>

<body class="clean-body u_body" style="margin: 0;padding: 0;-webkit-text-size-adjust: 100%;background-color: #ecf0f1;color: #000000">
  <!--[if IE]><div class="ie-container"><![endif]-->
  <!--[if mso]><div class="mso-container"><![endif]-->
  <table style="border-collapse: collapse;table-layout: fixed;border-spacing: 0;mso-table-lspace: 0pt;mso-table-rspace: 0pt;vertical-align: top;min-width: 320px;Margin: 0 auto;background-color: #ecf0f1;width:100%" cellpadding="0" cellspacing="0">
  <tbody>
  <tr style="vertical-align: top">
    <td style="word-break: break-word;border-collapse: collapse !important;vertical-align: top">
    <!--[if (mso)|(IE)]><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td align="center" style="background-color: #ecf0f1;"><![endif]-->
    
  
  
    <!--[if gte mso 9]>
      <table cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;min-width: 320px;max-width: 600px;">
        <tr>
          <td background="https://cdn.templates.unlayer.com/assets/1668754983570-header.png" valign="top" width="100%">
      <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width: 600px;">
        <v:fill type="frame" src="https://cdn.templates.unlayer.com/assets/1668754983570-header.png" /><v:textbox style="mso-fit-shape-to-text:true" inset="0,0,0,0">
      <![endif]-->
  
<div class="u-row-container" style="padding: 0px;background-repeat: no-repeat;background-position: center top;background-color: #111828">
  <div class="u-row" style="margin: 0 auto;min-width: 320px;max-width: 600px;overflow-wrap: break-word;word-wrap: break-word;word-break: break-word;background-color: #111828;">
    <div style="border-collapse: collapse;display: table;width: 100%;height: 100%;background-color: #111828;">
      <!--[if (mso)|(IE)]><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding: 0px;background-repeat: no-repeat;background-position: center top;background-color: #111828;" align="center"><table cellpadding="0" cellspacing="0" border="0" style="width:600px;"><tr style="background-color: #111828;"><![endif]-->
      
<!--[if (mso)|(IE)]><td align="center" width="600" style="width: 600px;padding: 0px;border-top: 0px solid #111828;border-left: 0px solid #111828;border-right: 0px solid #111828;border-bottom: 0px solid #111828;" valign="top"><![endif]-->
<div class="u-col u-col-100" style="max-width: 320px;min-width: 600px;display: table-cell;vertical-align: top;">
  <div style="height: 100%;width: 100% !important;">
  <!--[if (!mso)&(!IE)]><!--><div style="box-sizing: border-box; height: 100%; padding: 0px;border-top: 0px solid #111828;border-left: 0px solid #111828;border-right: 0px solid #111828;border-bottom: 0px solid #111828;"><!--<![endif]-->
  
<table id="u_content_heading_1" style="font-family:'Open Sans',sans-serif;" role="presentation" cellpadding="0" cellspacing="0" width="100%" border="0">
  <tbody>
    <tr>
      <td class="v-container-padding-padding" style="overflow-wrap:break-word;word-break:break-word;padding:105px 10px 5px;font-family:'Open Sans',sans-serif;" align="left">
        
  <!--[if mso]><table width="100%"><tr><td><![endif]-->
    <h1 class="v-text-align v-font-size" style="margin: 0px; color: #efb168; line-height: 100%; text-align: center; word-wrap: break-word; font-family: 'Playfair Display',serif; font-size: 50px; font-weight: 400;"><strong>WELCOME</strong></h1>
  <!--[if mso]></td></tr></table><![endif]-->

      </td>
    </tr>
  </tbody>
</table>

<table id="u_content_heading_3" style="font-family:'Open Sans',sans-serif;" role="presentation" cellpadding="0" cellspacing="0" width="100%" border="0">
  <tbody>
    <tr>
      <td class="v-container-padding-padding" style="overflow-wrap:break-word;word-break:break-word;padding:0px 10px;font-family:'Open Sans',sans-serif;" align="left">
        
  <!--[if mso]><table width="100%"><tr><td><![endif]-->
    <h1 class="v-text-align v-font-size" style="margin: 0px; color: #efb168; line-height: 100%; text-align: center; word-wrap: break-word; font-family: 'Playfair Display',serif; font-size: 65px; font-weight: 400;"><strong>To</strong></h1>
  <!--[if mso]></td></tr></table><![endif]-->

      </td>
    </tr>
  </tbody>
</table>

<table id="u_content_heading_2" style="font-family:'Open Sans',sans-serif;" role="presentation" cellpadding="0" cellspacing="0" width="100%" border="0">
  <tbody>
    <tr>
      <td class="v-container-padding-padding" style="overflow-wrap:break-word;word-break:break-word;padding:5px 10px 104px;font-family:'Open Sans',sans-serif;" align="left">
        
  <!--[if mso]><table width="100%"><tr><td><![endif]-->
    <h1 class="v-text-align v-font-size" style="margin: 0px; color: #efb168; line-height: 100%; text-align: center; word-wrap: break-word; font-family: 'Playfair Display',serif; font-size: 65px; font-weight: 400;"><strong>InQuiro AI</strong></h1>
  <!--[if mso]></td></tr></table><![endif]-->

      </td>
    </tr>
  </tbody>
</table>

  <!--[if (!mso)&(!IE)]><!--></div><!--<![endif]-->
  </div>
</div>
<!--[if (mso)|(IE)]></td><![endif]-->
      <!--[if (mso)|(IE)]></tr></table></td></tr></table><![endif]-->
    </div>
  </div>
  </div>
  
    <!--[if gte mso 9]>
      </v:textbox></v:rect>
    </td>
    </tr>
    </table>
    <![endif]-->
    


  
  
<div class="u-row-container" style="padding: 0px;background-color: #111828">
  <div class="u-row" style="margin: 0 auto;min-width: 320px;max-width: 600px;overflow-wrap: break-word;word-wrap: break-word;word-break: break-word;background-color: #111828;">
    <div style="border-collapse: collapse;display: table;width: 100%;height: 100%;background-color: #111828;">
      <!--[if (mso)|(IE)]><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding: 0px;background-color: #111828;" align="center"><table cellpadding="0" cellspacing="0" border="0" style="width:600px;"><tr style="background-color: #111828;"><![endif]-->
      
<!--[if (mso)|(IE)]><td align="center" width="600" style="background-color: #ffffff;width: 600px;padding: 0px;border-top: 0px solid #111828;border-left: 0px solid #111828;border-right: 0px solid #111828;border-bottom: 0px solid #111828;border-radius: 0px;-webkit-border-radius: 0px; -moz-border-radius: 0px;" valign="top"><![endif]-->
<div class="u-col u-col-100" style="max-width: 320px;min-width: 600px;display: table-cell;vertical-align: top;">
  <div style="background-color: #ffffff;height: 100%;width: 100% !important;border-radius: 0px;-webkit-border-radius: 0px; -moz-border-radius: 0px;">
  <!--[if (!mso)&(!IE)]><!--><div style="box-sizing: border-box; height: 100%; padding: 0px;border-top: 0px solid #111828;border-left: 0px solid #111828;border-right: 0px solid #111828;border-bottom: 0px solid #111828;border-radius: 0px;-webkit-border-radius: 0px; -moz-border-radius: 0px;"><!--<![endif]-->
  
<table id="u_content_text_1" style="font-family:'Open Sans',sans-serif;" role="presentation" cellpadding="0" cellspacing="0" width="100%" border="0">
  <tbody>
    <tr>
      <td class="v-container-padding-padding" style="overflow-wrap:break-word;word-break:break-word;padding:60px 30px;font-family:'Open Sans',sans-serif;" align="left">
        
  <div class="v-text-align v-font-size" style="font-size: 14px; line-height: 180%; text-align: justify; word-wrap: break-word;">
    <p style="font-size: 14px; line-height: 180%;"><strong>Hello from {name} email {email}</strong>,</p>
<p style="font-size: 14px; line-height: 180%;"> </p>
<p style="font-size: 14px; line-height: 180%;">{message}</p>
<p style="font-size: 14px; line-height: 180%;"> </p>
<p style="font-size: 14px; line-height: 180%;">Thanks.</p>
<p style="font-size: 14px; line-height: 180%;">have a good day.</p>
  </div>

      </td>
    </tr>
  </tbody>
</table>

  <!--[if (!mso)&(!IE)]><!--></div><!--<![endif]-->
  </div>
</div>
<!--[if (mso)|(IE)]></td><![endif]-->
      <!--[if (mso)|(IE)]></tr></table></td></tr></table><![endif]-->
    </div>
  </div>
  </div>
  


    <!--[if (mso)|(IE)]></td></tr></table><![endif]-->
    </td>
  </tr>
  </tbody>
  </table>
  <!--[if mso]></div><![endif]-->
  <!--[if IE]></div><![endif]-->
</body>

</html>
        """

        # Send email using Resend API
        response = resend.Emails.send({
            "from": "onboarding@resend.dev",  # Sender's email
            "to": "info.in.naturaleza@gmail.com",    # Recipient's email (where you want to receive the message)
            "subject": f"Contact Message from {name}",
            "html": html_template
        })

        # Return a success response
        if response:
            return jsonify({'message': 'Email sent successfully!'}), 200
        else:
            return jsonify({'error': 'Failed to send email'}), 500

    except Exception as e:
        # Handle errors
        return jsonify({'error': 'An error occurred', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)


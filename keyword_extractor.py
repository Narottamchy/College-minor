# keyword_extractor.py
import pickle
import logging
import os

# Configure logging to display error messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_model_and_functions():
    """Load the model and functions from the pickle file."""
    pickle_file_path = 'model_functions.pkl'  # Adjust this path if necessary

    # Check if the pickle file exists
    if not os.path.exists(pickle_file_path):
        logging.error(f"Pickle file '{pickle_file_path}' does not exist.")
        raise FileNotFoundError(f"Pickle file '{pickle_file_path}' not found.")

    try:
        try:
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
                logging.info("Model data loaded successfully.")
                return True, model_data  # Return success and model data
        except Exception as e:
            logging.error(f"An error occurred while loading the model: {e}")
            return False

        # Extract components
        cv = model_data['cv']
        tfidf_transformer = model_data['tfidf_transformer']
        preprocess_text = model_data['preprocess_text']
        get_keywords_from_text = model_data['get_keywords_from_text']
        get_keywords = model_data['get_keywords']

        return cv, tfidf_transformer, preprocess_text, get_keywords_from_text, get_keywords

    except FileNotFoundError as e:
        logging.error("The pickle file was not found. Please ensure that 'model_functions.pkl' exists.")
        raise e  # Re-raise the exception after logging
    except KeyError as e:
        logging.error(f"Missing key in the model data: {e}. Please check the contents of the pickle file.")
        raise e  # Re-raise the exception after logging
    except Exception as e:
        logging.error(f"An error occurred while loading the model and functions: {e}")
        raise e  # Re-raise the exception after logging

def extract_keywords(text, docs):
    """Preprocess the input text and extract keywords."""
    try:
        cv, tfidf_transformer, preprocess_text, get_keywords_from_text, get_keywords = load_model_and_functions()

        preprocessed_text = preprocess_text(text)
        keywords = get_keywords_from_text(preprocessed_text, docs)

        return keywords

    except Exception as e:
        logging.error(f"An error occurred while extracting keywords: {e}")
        return {"error": "Keyword extraction failed", "details": str(e)}  # Return a meaningful error response

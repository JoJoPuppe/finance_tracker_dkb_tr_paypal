import csv
import os
from datetime import datetime
import logging  # Using logging for better feedback
import argparse
import dotenv

dotenv.load_dotenv()  # Load environment variables from .env file


# --- Configuration ---
INPUT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
OUTPUT_DATE_FORMAT = "%d.%m.%Y"
IBAN_CONDITION_KEYWORDS = ["Einzahlung", "Marcus Loeper"]
OUTPUT_FILENAME_SUFFIX = "_converted"
LOG_LEVEL = logging.INFO  # Change to logging.DEBUG for more detail

# load env files
TRADEREPUBLIC_IBAN = os.getenv("TRADEREPUBLIC_IBAN")  # Example IBAN for metadata
MAIN_IBAN = os.getenv("MAIN_IBAN")  # Example IBAN for metadata

if not TRADEREPUBLIC_IBAN or not MAIN_IBAN:
    raise ValueError(
        "Environment variables TRADEREPUBLIC_IBAN and MAIN_IBAN must be set in .env file."
    )

# --- Setup Logging ---
logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s: %(message)s")

# --- Transformation Functions ---


def determine_umsatztyp(betrag_str: str) -> str | None:
    """
    Determines the transaction type ('Eingang' or 'Ausgang') based on the amount.
    Uses period as decimal separator for calculation, regardless of input format.
    """
    # [Function remains mostly the same, but ensures period for calculation]
    return "Eingang" if not betrag_str.startswith("-") else "Ausgang"


def format_buchungsdatum(date_str: str) -> str:
    """
    Formats a date string from INPUT_DATE_FORMAT to OUTPUT_DATE_FORMAT.
    """

    try:
        date_obj = datetime.strptime(date_str, INPUT_DATE_FORMAT)
        return date_obj.strftime(OUTPUT_DATE_FORMAT)
    except (ValueError, TypeError) as e:
        logging.warning(f"Could not parse date '{date_str}': {e}. Returning original.")
        return str(date_str)


def format_betrag_european(betrag_str: str) -> str:
    """
    Formats a number string to use a comma as the decimal separator.
    Replaces only the *last* period with a comma.

    Args:
        betrag_str: The amount string (e.g., '123.000.00', '2.0', '-50.99').

    Returns:
        The formatted string (e.g., '123.000,00', '2,0', '-50,99') or the
        original string if no period is found or input is invalid.
    """
    if not isinstance(betrag_str, str):
        logging.warning(
            f"Invalid input type for Betrag formatting: {type(betrag_str)}. Returning as is."
        )
        return str(betrag_str)  # Attempt to return string representation

    betrag_str = betrag_str.strip()  # Clean whitespace

    # Find the last occurrence of a period
    last_dot_index = betrag_str.rfind(".")

    # If no period exists, return the original string
    if last_dot_index == -1:
        return betrag_str

    # If a period is found, replace only the last one with a comma
    # Reconstruct the string: part before last dot + comma + part after last dot
    before_last_dot = betrag_str[:last_dot_index]
    after_last_dot = betrag_str[last_dot_index + 1 :]
    return f"{before_last_dot},{after_last_dot}"


def append_umsatztyp_to_verwendungszweck(verwendungszweck: str, umsatztyp: str) -> str:
    """
    Appends the (original) Umsatztyp to the Verwendungszweck.

    Args:
        verwendungszweck: The original purpose string.
        umsatztyp: The original transaction type string.

    Returns:
        The combined string.
    """
    # Ensure both parts are strings before joining
    vwz_str = str(verwendungszweck).strip() if verwendungszweck is not None else ""
    ut_str = str(umsatztyp).strip() if umsatztyp is not None else ""

    if not vwz_str:
        return ut_str
    if not ut_str:
        return vwz_str
    return f"{vwz_str} {ut_str}"


def determine_iban(verwendungszweck: str | None) -> str:
    """
    Determines the IBAN based on keywords in the Verwendungszweck.

    Args:
        verwendungszweck: The purpose string to check.

    Returns:
        TARGET_IBAN if any keyword is found, otherwise an empty string.
    """
    if MAIN_IBAN is None:
        return ""
    if verwendungszweck is None:
        return ""
    vwz_str = str(verwendungszweck)  # Ensure it's a string
    for keyword in IBAN_CONDITION_KEYWORDS:
        if keyword in vwz_str:
            return MAIN_IBAN
    return ""


# --- Core Processing Logic ---


def process_row(input_row: dict, row_number: int) -> dict | None:
    """
    Applies all transformation steps to a single row.

    Args:
        input_row: A dictionary representing the row read from the CSV.
        row_number: The original row number (for logging).

    Returns:
        A dictionary representing the processed row with the new structure,
        or None if a critical error occurs for this row.
    """
    try:
        # --- Essential Data Extraction (handle potential missing keys) ---
        original_buchungsdatum = input_row.get("Buchungsdatum", "")
        original_umsatztyp = input_row.get("Umsatztyp", "")
        original_betrag = input_row.get("Betrag (€)", "")
        original_verwendungszweck = input_row.get("Verwendungszweck", "")

        # --- Apply Transformations ---

        logging.debug(f"date_str: {original_buchungsdatum}")
        formatted_date = format_buchungsdatum(original_buchungsdatum)
        derived_umsatztyp = determine_umsatztyp(original_betrag)
        formatted_betrag = format_betrag_european(original_betrag)
        # appended_verwendungszweck = append_umsatztyp_to_verwendungszweck(
        #     original_verwendungszweck,
        #     original_umsatztyp,  # Use original Umsatztyp here
        # )
        iban = determine_iban(
            original_verwendungszweck
        )  # Use original Verwendungszweck

        # --- Construct Processed Row ---
        processed_row = {
            "Wertstellung": original_buchungsdatum,
            "Buchungsdatum": original_buchungsdatum,
            "Status": original_umsatztyp,
            "Umsatztyp": derived_umsatztyp
            if derived_umsatztyp is not None
            else original_umsatztyp,  # Fallback to original if Betrag was invalid
            "Betrag (€)": formatted_betrag,  # Keep original Betrag
            "Verwendungszweck": original_verwendungszweck,
            "IBAN": iban,
        }
        return processed_row

    except Exception as e:
        logging.error(
            f"Critical error processing row {row_number}: {input_row}. Error: {e}",
            exc_info=True,
        )
        return None  # Indicate row processing failed


def process_csv_file(input_filename: str):
    """
    Reads a CSV file, processes each row using modular functions,
    and writes the results to a new CSV file.

    Args:
        input_filename: The path to the input CSV file.
    """
    base, ext = os.path.splitext(input_filename)
    output_filename = f"{base}{OUTPUT_FILENAME_SUFFIX}{ext}"

    # Define the headers expected in the input and required for the output
    # Input headers are implicitly handled by DictReader
    output_headers = [
        "Buchungsdatum",
        "Wertstellung",
        "Status",
        "Umsatztyp",
        "Betrag (€)",
        "Verwendungszweck",
        "IBAN",
    ]

    logging.info(f"Starting processing for '{input_filename}'...")
    processed_count = 0
    error_count = 0

    try:
        with (
            open(input_filename, mode="r", newline="", encoding="utf-8") as infile,
            open(output_filename, mode="w", newline="", encoding="utf-8") as outfile,
        ):
            # Use DictReader for robust column access
            # Use restval='' to handle rows with fewer columns than headers gracefully
            reader = csv.DictReader(infile, restval="", delimiter=";")

            # Ensure all expected input headers are present (optional but good practice)
            expected_input_headers = [
                "Buchungsdatum",
                "Umsatztyp",
                "Betrag (€)",
                "Verwendungszweck",
            ]
            logging.debug(f"Input headers: {reader.fieldnames}")
            if not all(h in reader.fieldnames for h in expected_input_headers):
                missing = [
                    h for h in expected_input_headers if h not in reader.fieldnames
                ]
                logging.warning(
                    f"Input file missing expected headers: {missing}. Processing might be affected."
                )
                # Decide if this is critical: raise ValueError("Missing critical headers")

            writer = csv.DictWriter(outfile, fieldnames=output_headers, delimiter=";")
            writer.writeheader()

            for i, row in enumerate(
                reader, start=2
            ):  # Start counting from row 2 (after header)
                logging.debug(f"Processing row {i}: {row}")
                processed_data = process_row(row, i)
                if processed_data:
                    # Ensure only defined output headers are written
                    output_row = {
                        header: processed_data.get(header, "")
                        for header in output_headers
                    }
                    writer.writerow(output_row)
                    processed_count += 1
                else:
                    error_count += 1  # Row failed processing

        logging.info(f"Processing complete.")
        logging.info(f"Successfully processed {processed_count} rows.")
        if error_count > 0:
            logging.warning(f"{error_count} rows encountered errors during processing.")
        logging.info(f"Output saved as '{output_filename}'")

    except FileNotFoundError:
        logging.error(f"Input file '{input_filename}' not found.")
    except csv.Error as e:
        logging.error(f"CSV formatting error in '{input_filename}', {e}")
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during file processing: {e}", exc_info=True
        )

    add_metadata(output_filename)  # Add metadata to the output file


def add_metadata(csv_file):
    meta_data_list = [
        f"TagesgeldTR;{TRADEREPUBLIC_IBAN}\n",
        "-\n",
        "-\n",
        "-\n",
    ]
    output_filename = f"{os.path.splitext(csv_file)[0]}_metadata.csv"
    with (
        open(csv_file, mode="r", newline="", encoding="utf-8") as infile,
        open(output_filename, mode="w", newline="", encoding="utf-8") as outfile,
    ):
        csv_lines = infile.readlines()
        meta_data_list.extend(csv_lines)
        outfile.writelines(meta_data_list)


# --- Main Execution ---
if __name__ == "__main__":
    # Argument parsing for command line execution
    parser = argparse.ArgumentParser(
        description="Process a CSV file with banking data."
    )
    parser.add_argument("input_file", type=str, help="Path to the input CSV file")
    # Get the input filename from the user or set a default
    args = parser.parse_args()
    csv_file_to_process = args.input_file.strip() if args.input_file else ""

    if not csv_file_to_process:
        logging.warning("No filename entered. Exiting.")
    elif not os.path.exists(csv_file_to_process):
        logging.error(f"File not found: {csv_file_to_process}")
    else:
        process_csv_file(csv_file_to_process)

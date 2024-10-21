## -> Step 1: adjust paths ##

#Local path
path_script = "C:/Python/HV_PROJECTS"

#server_path
#path_script = "C:/Python/ft_projects"

#No changes needed
import pyodbc
from email.mime.text import MIMEText
import sys
sys.path.append(path_script)
import _AUTH
import _DEF 


## -> Step 2: Adjust script variables ##

# Variables for logging
script_name = "BC_bankledgder"
script_cat = "DWH_extract"


# Variables for the destination table
sql_table = "dbo.BC_bankledger"
entryno = "Entry_No"

columns_insert = [
    "[@odata.etag]"       
    ,"Entry_No"
      ,"Posting_Date"
      ,"Document_Type"
      ,"Document_No"
      ,"Bank_Account_No"
      ,"Description"
      ,"Global_Dimension_1_Code"
      ,"Global_Dimension_2_Code"
      ,"Our_Contact_Code"
      ,"Currency_Code"
      ,"Amount"
      ,"Debit_Amount"
      ,"Credit_Amount"
      ,"RunningBalance"
      ,"Amount_LCY"
      ,"Debit_Amount_LCY"
      ,"Credit_Amount_LCY"
      ,"RunningBalanceLCY"
      ,"Remaining_Amount"
      ,"Bal_Account_Type"
      ,"Bal_Account_No"
      ,"[Open]"
      ,"User_ID"
      ,"Source_Code"
      ,"Reason_Code"
      ,"Reversed"
      ,"Reversed_by_Entry_No"
      ,"Reversed_Entry_No"
      ,"Dimension_Set_ID"
      ,"Shortcut_Dimension_3_Code"
      ,"Shortcut_Dimension_4_Code"
      ,"Shortcut_Dimension_5_Code"
      ,"Shortcut_Dimension_6_Code"
      ,"Shortcut_Dimension_7_Code"
      ,"Shortcut_Dimension_8_Code"
      ,"Entity"
]

# Variables for API request
api_table = "')/bankposten"
api_full = _AUTH.end_Odata_BC + "/" + "Company('"

def get_max_entry_no_per_entity(connection):
    query = f"""
        SELECT Entity, MAX({entryno}) as MaxEntryNo
        FROM {sql_table}
        GROUP BY Entity
    """
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Convert results to a dictionary for easy lookup
    return {row[0]: row[1] for row in results}
 
# No changes needed 
if __name__ == "__main__":
    print(f"Copying {script_name} to SQL/Staging ...")
    connection = pyodbc.connect(_AUTH.connection_string)
    threshold = 0

    start_time = _DEF.datetime.now()
    overall_status = "Success"
    total_inserted_rows = 0

    try:
        company_names = _DEF.get_company_names(connection)
        max_entry_nos = get_max_entry_no_per_entity(connection)
    
        for company_name in company_names:
            # Get the maximum Entry_No for the current company (entity)
            max_entry_no = max_entry_nos.get(company_name, 0)  # Default to 0 if not found

            # Filter API data to only retrieve records with Entry_No greater than the max_entry_no
            api = f"{api_full}{company_name}{api_table}?$filter=Entry_No gt {max_entry_no}"
            api_data_generator = _DEF.make_api_request(api, _AUTH.client_id, _AUTH.client_secret, _AUTH.token_url)

            data_to_insert = list(api_data_generator)
            row_count = len(data_to_insert)

            if row_count > threshold:
                _DEF.insert_data_into_sql(connection, data_to_insert, sql_table, company_name, columns_insert)
                inserted_rows = _DEF.count_rows(data_to_insert)  # Assuming all rows are successfully inserted
                total_inserted_rows += inserted_rows

                if inserted_rows != row_count:
                    overall_status = "Error"
                    error_details = f"Expected to insert {row_count} rows, but only {inserted_rows} were inserted."
                    _DEF.log_status(connection, "Error", script_cat, script_name, start_time, _DEF.datetime.now(), int((_DEF.datetime.now() - start_time).total_seconds() / 60), row_count - inserted_rows, error_details, company_name, api)

                    _DEF.send_email_mfa(f"ErrorLog -> {script_name} / {script_cat}", error_details,  _AUTH.email_sender,  _AUTH.email_recipient, _AUTH.guid_blink, _AUTH.email_client_id, _AUTH.email_client_secret)       

    except Exception as e:
        overall_status = "Error"
        error_details = str(e)
        print(f"An error occurred: {e}")
        _DEF.log_status(connection, "Error", script_cat, script_name, start_time, _DEF.datetime.now(), int((_DEF.datetime.now() - start_time).total_seconds() / 60), 0, error_details, "None", "N/A")

        _DEF.send_email_mfa(f"ErrorLog -> {script_name} / {script_cat}", error_details,  _AUTH.email_sender,  _AUTH.email_recipient, _AUTH.guid_blink, _AUTH.email_client_id, _AUTH.email_client_secret)    

    finally:
        if overall_status == "Success":
            success_message = f"Total rows inserted: {total_inserted_rows}."
            _DEF.log_status(connection, "Success", script_cat, script_name, start_time, _DEF.datetime.now(), int((_DEF.datetime.now() - start_time).total_seconds() / 60), total_inserted_rows, success_message, "All", "N/A")

        elif overall_status == "Error":
            # Additional logging for error scenario can be added here if needed
            pass
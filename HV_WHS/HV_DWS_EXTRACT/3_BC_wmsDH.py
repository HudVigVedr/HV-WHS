import requests
import pyodbc
import json
import smtplib
from email.mime.text import MIMEText
import time

import sys
sys.path.append('C:/Python/HV_PROJECTS')
import _AUTH
import _DEF 

script_name = "BC_wmsDH"
script_cat = "DWH"

# SQL Server connection settings
connection_string = f"DRIVER=ODBC Driver 17 for SQL Server;SERVER={_AUTH.server};DATABASE={_AUTH.database};UID={_AUTH.username};PWD={_AUTH.password}"

sql_table = "dbo.BC_wmsDH"
print("SQL Server connection string created")


# API endpoint URL (same as before) -> aanvullen
api_url = _AUTH.end_REST_BOLTRICS_BC
api_table = "wmsDocumentHeaders"
api_full = api_url + "/" + api_table + "?" + "$select=announcedDate,announcedTime,arrivedDate,arrivedTime,attribute01,attribute02,attribute03,attribute04,attribute05,attribute06,attribute07,attribute08,attribute09,attribute10,billToCustomerName,billToCustomerNo,createdDateTime,createdUserID,deliveryDate,departedDate,documentDate,documentType,estimatedDepartureDate,id,modifiedDateTime,modifiedUserID,movementType,no,portFromName,portToName,postingDate,sellToCustomerName,sellToCustomerNo,shortcutDimension2Code,statusCode,vesselNo,voyageNo&company="



# Delete function
def delete_sql_table(connection):
    print("Deleting SQL table")
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM {sql_table}")
    connection.commit()

# Function to insert data into SQL Server
def insert_data_into_sql(connection, data, sql_table, company_name):
    
    cursor = connection.cursor()

    sql_insert = f"""
        INSERT INTO {sql_table} (
            [ODataEtag]
            ,[Id]
            ,[DocumentType]
            ,[No]
            ,[SellToCustomerNo]
            ,[SellToCustomerName]
            ,[BillToCustomerNo]
            ,[BillToCustomerName]
            ,[VoyageNo]
            ,[MovementType]
            ,[DocumentDate]
            ,[PostingDate]
            ,[StatusCode]
            ,[CreatedDateTime]
            ,[CreatedUserID]
            ,[ModifiedDateTime]
            ,[ModifiedUserID]
            ,[AnnouncedDate]
            ,[AnnouncedTime]
            ,[ArrivedDate]
            ,[ArrivedTime]
            ,[DepartedDate]
            ,[DeliveryDate]
            ,[EstimatedDepartureDate]
            ,[VesselNo]
            ,[ShortcutDimension2Code]
            ,[Attribute01]
            ,[Attribute02]
            ,[Attribute03]
            ,[Attribute04]
            ,[Attribute05]
            ,[Attribute06]
            ,[Attribute07]
            ,[Attribute08]
            ,[Attribute09]
            ,[Attribute10]
            ,[PortFromName]
            ,[PortToName]
            ,[Entity]
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for item in data:
        values = list(item.values())
        values.append(company_name)  # add company name to the list of values
        cursor.execute(sql_insert, tuple(values))

    connection.commit()

   
if __name__ == "__main__":
    print("Copying BC_wmsDH...")
    connection = pyodbc.connect(connection_string)
    threshold = 0

    start_time = _DEF.datetime.now()
    overall_status = "Success"
    total_inserted_rows = 0

    try:
        company_names = _DEF.get_company_names(connection)

        delete_sql_table(connection)

        for company_name in company_names:
            api = f"{api_full}{company_name}"
            api_data_generator = _DEF.make_api_request(api, _AUTH.client_id, _AUTH.client_secret, _AUTH.token_url)

            data_to_insert = list(api_data_generator)
            row_count = len(data_to_insert)

            if row_count > threshold:
                insert_data_into_sql(connection, data_to_insert, sql_table, company_name)
                inserted_rows = _DEF.count_rows(data_to_insert)  # Assuming all rows are successfully inserted
                total_inserted_rows += inserted_rows

                if inserted_rows != row_count:
                    overall_status = "Error"
                    error_details = f"Expected to insert {row_count} rows, but only {inserted_rows} were inserted."
                    _DEF.log_status(connection, "Error", script_cat, script_name, start_time, _DEF.datetime.now(), int((_DEF.datetime.now() - start_time).total_seconds() / 60), row_count - inserted_rows, error_details, company_name, api)

                    _DEF.send_email(
                    f"ErrorLog -> {script_name} / {script_cat}",
                    error_details,
                    _AUTH.email_recipient,
                    _AUTH.email_sender,
                    _AUTH.smtp_server,
                    _AUTH.smtp_port,
                    _AUTH.email_username,
                    _AUTH.email_password
                    )    


    except Exception as e:
        overall_status = "Error"
        error_details = str(e)
        print(f"An error occurred: {e}")
        _DEF.log_status(connection, "Error", script_cat, script_name, start_time, _DEF.datetime.now(), int((_DEF.datetime.now() - start_time).total_seconds() / 60), 0, error_details, "None", "N/A")

        _DEF.send_email(
        f"ErrorLog -> {script_name} / {script_cat}",
        error_details,
        _AUTH.email_recipient,
        _AUTH.email_sender,
        _AUTH.smtp_server,
        _AUTH.smtp_port,
        _AUTH.email_username,
        _AUTH.email_password
        )    

    finally:
        if overall_status == "Success":
            success_message = f"Total rows inserted: {total_inserted_rows}."
            _DEF.log_status(connection, "Success", script_cat, script_name, start_time, _DEF.datetime.now(), int((_DEF.datetime.now() - start_time).total_seconds() / 60), total_inserted_rows, success_message, "All", "N/A")

        elif overall_status == "Error":
            # Additional logging for error scenario can be added here if needed
            pass
import psycopg2
import requests
import pickle

import config

postgres_host = config.configuration.get("postgres_host", "localhost")
postgres_port = config.configuration.get("postgres_port", "5432")
postgres_db = config.configuration.get("postgres_db", "gpt")
postgres_user = config.configuration.get("postgres_user", "postgres")
postgres_pass = config.configuration.get("postgres_pass", "eo1Mgtm6HI")


def get_all_user_issue_inferences(issue_id, limit, offset):
    db_params = get_postgres_db_params()
    conn = psycopg2.connect(**db_params)

    offset = offset if offset >= 0 else 0
    # Create a cursor
    cur = conn.cursor()

    try:
        # Construct the SQL query with pagination and a WHERE clause
        query = f"SELECT * FROM public.issue_inference_raw_data WHERE issue_id = %s LIMIT %s OFFSET %s;"
        cur.execute(query, (issue_id, limit, (offset) * limit))

        # Fetch the rows from the result set
        rows = cur.fetchall()

        # Print or process the rows as needed
        results = []
        for row in rows:
            queryString = pickle.loads(row[3])
            answerString = pickle.loads(row[4])

            results.append({
                'issueId': row[2],
                'query': queryString,
                'answer': answerString,
                'temerature': row[5],
                'gptModel': row[6],
                'embeddingModel': row[7],
                'userComments': row[8],
                'topK': row[9],
                'userScore': row[10]
            })

        return results

    except requests.exceptions.RequestException as e:
        print(f"Error occurred fetching user inferences for an {issue_id} with exception : {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def insert_user_issue_inference(issue_id, query, temperature, topK, vectorEmbeddingModel, gptModel, requestId, answer):
    db_params = get_postgres_db_params()

    data = {
        'request_id': requestId,
        'issue_id': issue_id,
        'query': query,
        'answer': answer,
        'temperature': temperature,
        'gptModel': gptModel,
        'embeddingModel': vectorEmbeddingModel,
        'topK': topK,
    }

    # Convert string data to bytea
    data['query_bytea'] = pickle.dumps(data['query'])
    data['answer_bytea'] = pickle.dumps(data['answer'])

    # SQL query for inserting data
    insert_query = """
        INSERT INTO public.issue_inference_raw_data 
        (request_id, issue_id, query, answer, temerature, gptModel, embeddingModel, topK)
        VALUES (%(request_id)s, %(issue_id)s, %(query_bytea)s, %(answer_bytea)s, %(temperature)s, %(gptModel)s, %(embeddingModel)s, %(topK)s);
    """
    # Establish a connection to the PostgreSQL database
    conn = psycopg2.connect(**db_params)
    # Create a cursor
    cur = conn.cursor()

    try:

        # Execute the insert query with the data
        cur.execute(insert_query, data)
        # Commit the transaction
        conn.commit()
        print("Data inserted successfully!")

    except requests.exceptions.RequestException as e:
        print(f"Error occurred While inserting user inference data to postgres : {e}")

    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def update_user_inference_feedback(requestId, feedback, score):
    db_params = get_postgres_db_params()

    # Data for the update
    update_data = {
        'request_id': requestId,
        'new_userComments': feedback,
        'new_userScore': score
    }

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_params)

    # Create a cursor
    cur = conn.cursor()

    # SQL query for updating userComments and userScore based on request_id
    update_query = """
        UPDATE public.issue_inference_raw_data
        SET userComments = %(new_userComments)s, userScore = %(new_userScore)s
        WHERE request_id = %(request_id)s;
    """
    try:

        # Execute the update query with the data
        cur.execute(update_query, update_data)

        # Commit the transaction
        conn.commit()

        print("Data updated successfully!")

    except psycopg2.Error as e:
        print(f"Error occurred While updating user inference feedback data to postgres : {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def check_issue_presence_in_db(issue_id):
    # Database connection parameters
    db_params = get_postgres_db_params()

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_params)

    # Create a cursor
    cur = conn.cursor()

    # SQL query to check for the existence of a record with the given issue_id
    check_query = """
        SELECT EXISTS (SELECT 1 FROM public.issue_inference_raw_data WHERE issue_id = %s);
    """

    try:
        # Execute the check query with the issue_id as a parameter
        cur.execute(check_query, (issue_id,))

        # Fetch the result (True if a record exists, False if not)
        result = cur.fetchone()[0]

        return result

    except psycopg2.Error as e:
        print(f"Error occurred While fetching issueid in postgres : {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


# def insert_issue_user_query_response(issue_id, incident_id, query, answer, is_rca, created_at):
#     print("")
#     db_params = get_postgres_db_params()
#
#     data = {
#         'issue_id': issue_id,
#         'incident_id': incident_id,
#         'query': query,
#         'answer': answer,
#         'is_rca': is_rca,
#         'created_at': created_at
#     }
#
#     # Convert string data to bytea
#     data['query_bytea'] = psycopg2.Binary(data['query'].encode('utf-8'))
#     data['answer_bytea'] = psycopg2.Binary(data['answer'].encode('utf-8'))
#
#     # SQL query for inserting data
#     insert_query = """
#         INSERT INTO public.issue_incident_conversation
#         (issue_id,incident_id, query, answer, is_rca, created_at)
#         VALUES (%(issue_id)s, %(incident_id)s, %(query_bytea)s, %(answer_bytea)s, %(is_rca)s, %(created_at)s);
#     """
#     # Establish a connection to the PostgreSQL database
#     conn = psycopg2.connect(**db_params)
#     # Create a cursor
#     cur = conn.cursor()
#     try:
#         # Execute the insert query with the data
#         cur.execute(insert_query, data)
#         # Commit the transaction
#         conn.commit()
#         print("Query Answer Data inserted successfully!")
#
#     except requests.exceptions.RequestException as e:
#         print(
#             f"Error occurred While inserting user inference query answer to postgres for issue {issue_id} and incident:{incident_id} as exception:{e}")
#     finally:
#         # Close the cursor and the database connection
#         if cur:
#             cur.close()
#         if conn:
#             conn.close()
#

# def insert_issue_incident_context(issue_id, incident_id, context):
#     print("")
#     db_params = get_postgres_db_params()
#
#     data = {
#         'issue_id': issue_id,
#         'incident_id': incident_id,
#         'context': context
#     }
#
#     # Convert string data to bytea
#     data['context_bytea'] = psycopg2.Binary(data['context'].encode('utf-8'))
#
#     # SQL query for inserting data
#     insert_query = """
#         INSERT INTO public.issue_incident_context
#         (issue_id, incident_id, context, created_at, updated_at)
#         VALUES (%(issue_id)s, %(incident_id)s, %(context_bytea)s, NOW(), NOW());
#     """
#     # Establish a connection to the PostgreSQL database
#     conn = psycopg2.connect(**db_params)
#     # Create a cursor
#     cur = conn.cursor()
#     try:
#         # Execute the insert query with the data
#         cur.execute(insert_query, data)
#         # Commit the transaction
#         conn.commit()
#         print("Query Answer Data inserted successfully!")
#
#     except requests.exceptions.RequestException as e:
#         print(
#             f"Error occurred While inserting user inference query answer to postgres for issue {issue_id} and incident:{incident_id} as exception:{e}")
#     finally:
#         # Close the cursor and the database connection
#         if cur:
#             cur.close()
#         if conn:
#             conn.close()


def upsert_issue_incident_context(issue_id, incident_id, context):
    db_params = get_postgres_db_params()
    # Establish a connection to the PostgresSQL database
    conn = psycopg2.connect(**db_params)
    # Create a cursor
    cur = conn.cursor()
    try:

        # Define the SQL query for upsert
        upsert_query = """
                INSERT INTO public.issue_incident_context (issue_id, incident_id, context, created_at, updated_at)
                VALUES (%s, %s, %s, NOW(), NOW())
                ON CONFLICT (issue_id, incident_id)
                DO UPDATE SET context = EXCLUDED.context, updated_at = NOW();
            """

        # Convert string data to bytea
        context_bytea = pickle.dumps(context)

        # Execute the upsert query
        cur.execute(upsert_query, (issue_id, incident_id, context_bytea))

        conn.commit()
        print("Query Answer Data inserted successfully!")

    except requests.exceptions.RequestException as e:
        print(
            f"Error occurred While inserting user inference query answer to postgres for issue {issue_id} and incident:{incident_id} as exception:{e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def fetch_issue_incident_context(issue_id, incident_id):
    # Database connection parameters
    db_params = get_postgres_db_params()
    # Connect to the PostgresSQL database
    conn = psycopg2.connect(**db_params)

    # Create a cursor
    cur = conn.cursor()

    # Define the SQL query to fetch the context
    query = """
            SELECT context FROM public.issue_incident_context
            WHERE issue_id = %s AND incident_id = %s;
        """

    try:
        # Execute the query with the provided issue_id and incident_id
        cur.execute(query, (issue_id, incident_id))

        # Fetch the result (True if a record exists, False if not)
        result = cur.fetchone()

        if result is not None:
            context = result
            return pickle.loads(context[0])
        else:
            return None
    except psycopg2.Error as e:
        print(f"Error occurred While fetching context for issue Id in postgres : {e}")
        raise Exception("Error occurred While fetching context in postgres : {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


# def check_if_rca_already_generated(issue_id, incident_id):
#     # Database connection parameters
#     db_params = get_postgres_db_params()
#     # Connect to the PostgresSQL database
#     conn = psycopg2.connect(**db_params)
#
#     # Create a cursor
#     cur = conn.cursor()
#
#     # SQL query to check for the existence of a record with the given issue_id
#     check_query = """SELECT is_rca, answer FROM public.issue_incident_conversation WHERE issue_id = %s AND incident_id = %s;"""
#
#     try:
#         # Execute the check query with the issue_id as a parameter
#         cur.execute(check_query, (issue_id, incident_id))
#
#         # Fetch the result (True if a record exists, False if not)
#         result = cur.fetchone()
#
#         if result is not None:
#             isRca_value, answer = result
#             return isRca_value, bytes(answer).decode('utf-8')
#         else:
#             return None, None
#     except psycopg2.Error as e:
#         print(f"Error occurred While fetching issueid in postgres : {e}")
#         raise Exception("Error occurred While fetching issueid in postgres : {e}")
#     finally:
#         # Close the cursor and the database connection
#         if cur:
#             cur.close()
#         if conn:
#             conn.close()


def check_if_inference_already_present(issue_id, incident_id):
    # Database connection parameters
    db_params = get_postgres_db_params()
    # Connect to the PostgresSQL database
    conn = psycopg2.connect(**db_params)

    # Create a cursor
    cur = conn.cursor()

    # SQL query to check for the existence of a record with the given issue_id
    query = """SELECT inference FROM public.issue_incident_inference WHERE issue_id = %s AND incident_id = %s """

    try:
        # Execute the check query with the issue_id as a parameter and rca = True
        cur.execute(query, (issue_id, incident_id))

        result = cur.fetchone()

        if result is not None and result[0] is not None:
            inference = pickle.loads(result[0])
            return inference
        elif result is not None and result[0] is None:
            return None
        else:
            return None

    except psycopg2.Error as e:
        print(f"Error occurred While fetching issueid in postgres : {e}")
        raise Exception("Error occurred While fetching issueid in postgres : {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def check_if_inference_already_present_for_issue(issue_id):
    # Database connection parameters
    db_params = get_postgres_db_params()
    # Connect to the PostgresSQL database
    conn = psycopg2.connect(**db_params)

    # Create a cursor
    cur = conn.cursor()

    # SQL query to check for the existence of a record with the given issue_id
    query = """
            SELECT inference , incident_id FROM public.issue_incident_inference 
            WHERE issue_id = %s ORDER BY created_at DESC LIMIT 1
        """

    try:
        # Execute the check query with the issue_id as a parameter and rca = True
        cur.execute(query, (issue_id,))

        result = cur.fetchone()

        if result is not None:
            inference, incident_id = result
            return pickle.loads(inference), incident_id
        else:
            return None, None

    except psycopg2.Error as e:
        print(f"Error occurred While fetching issueid in postgres : {e}")
        raise Exception("Error occurred While fetching issueid in postgres : {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def insert_or_update_inference_to_db(issue_id, incident_id, inference):
    # Validate that 'answer' is not None
    if inference is None:
        print(
            "Inference is None. Aborting database operation. for issue: {} incidentId:{}".format(issue_id, incident_id))
        return
    # Issue and Incident IDs and answer to update/insert
    # Database connection parameters
    db_params = get_postgres_db_params()
    try:
        # Connect to the PostgresSQL database
        conn = psycopg2.connect(**db_params)

        # Create a cursor
        cur = conn.cursor()

        new_inference = pickle.dumps(inference)  # Replace with your new answer bytes

        # SQL query to update or insert the answer
        upsert_query = """
            INSERT INTO public.issue_incident_inference (issue_id, incident_id, inference, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (issue_id, incident_id)
            DO UPDATE SET inference = EXCLUDED.inference, created_at = EXCLUDED.created_at
            RETURNING inference;
        """

        # Execute the upsert query with the specified parameters
        cur.execute(upsert_query, (issue_id, incident_id, new_inference))

        # Fetch the updated/inserted answer
        updated_inference = cur.fetchone()[0]

        # Commit the transaction
        conn.commit()

        # Print or use the updated/inserted answer as needed
        print(f"Updated/Inserted answer: {updated_inference}")

    except psycopg2.Error as e:
        print(f"Error occurred while updating/inserting inference: {e}")
        conn.rollback()
        raise Exception(f"Error occurred while updating/inserting inference: {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def insert_user_conversation_event(issue_id, incident_id, event_type, event_request, event_response):
    try:
        db_params = get_postgres_db_params()

        # Define the data for the insert
        data = {
            "issue_id": issue_id,
            "incident_id": incident_id,
            "event_type": event_type,  # Use the enum value
            "event_request": event_request,
            "event_response": event_response
        }

        # Convert string data to bytea
        data['event_request_bytea'] = pickle.dumps(data['event_request'])
        data['event_response_bytea'] = pickle.dumps(data['event_response'])

        # SQL query for inserting data
        insert_query = """
            INSERT INTO public.issue_user_conversation_events 
            (issue_id, incident_id, event_type, event_request, event_response, created_at)
            VALUES (%(issue_id)s, %(incident_id)s, %(event_type)s, %(event_request_bytea)s, %(event_response_bytea)s, NOW());
        """

        # Establish a connection to the PostgresSQL database
        conn = psycopg2.connect(**db_params)
        # Create a cursor
        cur = conn.cursor()

        # Execute the insert query with the data
        cur.execute(insert_query, data)
        # Commit the transaction
        conn.commit()
        print("Data inserted successfully!")

    except requests.exceptions.RequestException as e:
        print(f"Error occurred While inserting user inference data to postgres : {e}")

    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_user_conversation_events(issue_id, limit, offset):
    db_params = get_postgres_db_params()
    conn = psycopg2.connect(**db_params)

    offset = offset if offset >= 0 else 0
    # Create a cursor
    cur = conn.cursor()

    try:
        # Fetch the total count first
        count_query = """
                SELECT COUNT(*) FROM public.issue_user_conversation_events
                WHERE issue_id = %s
                """
        cur.execute(count_query, (issue_id,))
        total_count = cur.fetchone()[0]

        # Construct the SQL query with pagination and a WHERE clause
        query = """
        SELECT * FROM public.issue_user_conversation_events
        WHERE issue_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        cur.execute(query, (issue_id, limit, (offset) * limit))

        # Fetch the rows from the result set
        rows = cur.fetchall()

        results = []
        for row in rows:
            event_request = pickle.loads(row[4])
            event_response = pickle.loads(row[5])
            event = event_response
            results.append({
                'issueId': row[1],
                'incidentId': row[2],
                'event': event,
                'created_at': row[6]
            })

        reverse_results = results[::-1]
        return total_count, reverse_results

    except requests.exceptions.RequestException as e:
        print(f"Error occurred fetching user inferences for an {issue_id} with exception : {e}")
        return 0, None
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_postgres_db_params():
    db_params = {
        'database': postgres_db,
        'user': postgres_user,
        'password': postgres_pass,
        'host': postgres_host,
        'port': postgres_port
    }
    return db_params


def get_last_issue_inferenced_timestamp():
    return None


def get_issues_inferred_already_in_db(issues_list):
    db_params = get_postgres_db_params()
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    query = """
        SELECT issue_id, COUNT(*) AS row_count 
        FROM public.issue_incident_inference 
        WHERE issue_id IN ({}) GROUP BY issue_id;
    """.format(', '.join(["'{}'".format(issue) for issue in issues_list]))

    try:

        cur.execute(query)
        results = cur.fetchall()
        issues_inferred_already = []
        for row in results:
            if row[1] is not None:
                issues_inferred_already.append(row[0])
        return issues_inferred_already
    except Exception as e:
        print(f"Error occurred while fetching issue inferences : {e}")
        return []
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def check_if_reporting_already_present_for_issue(issue_id):
    # Database connection parameters
    db_params = get_postgres_db_params()
    # Connect to the PostgresSQL database
    conn = psycopg2.connect(**db_params)

    # Create a cursor
    cur = conn.cursor()

    # SQL query to check for the existence of a record with the given issue_id
    query = """
            SELECT issue_id,incident_id FROM public.slack_inference_report
            WHERE issue_id = %s ORDER BY created_at DESC LIMIT 1
        """

    try:
        # Execute the check query with the issue_id as a parameter and rca = True
        cur.execute(query, (issue_id,))

        result = cur.fetchone()

        if result is not None:
            issue_id, incident_id = result
            return issue_id, incident_id
        else:
            return None, None

    except psycopg2.Error as e:
        print(f"Error occurred While fetching issueid in postgres : {e}")
        raise Exception("Error occurred While fetching issueid in postgres : {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def insert_issue_inference_to_slack_reporting_db(issue_id, incident_id):
    try:
        db_params = get_postgres_db_params()

        # Define the data for the insert
        data = {
            "issue_id": issue_id,
            "incident_id": incident_id,
            "reporting_status": False
        }

        # SQL query for inserting data
        insert_query = """
            INSERT INTO public.slack_inference_report 
            (issue_id, incident_id, reporting_status, issue_timestamp, report_timestamp,created_at)
            VALUES (%(issue_id)s, %(incident_id)s, %(reporting_status), NOW(), NOW(),NOW());
        """

        # Establish a connection to the PostgresSQL database
        conn = psycopg2.connect(**db_params)
        # Create a cursor
        cur = conn.cursor()

        # Execute the insert query with the data
        cur.execute(insert_query, data)
        # Commit the transaction
        conn.commit()
        print("Data inserted successfully!")

    except requests.exceptions.RequestException as e:
        print(f"Error occurred While inserting user inference data to postgres : {e}")

    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()


def fetch_issues_to_be_reported_to_slack():
    db_params = get_postgres_db_params()
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    try:
        query = """
            SELECT issue_id, incident_id 
            FROM public.slack_inference_report
            WHERE reporting_status = false;
        """
        cur.execute(query)
        rows = cur.fetchall()
        issue_incident_dict = []
        for row in rows:
            issue_incident_dict.append({"issue_id": row[0], "incident_id": row[1]})
        return issue_incident_dict
    except (Exception, psycopg2.Error) as error:
        print("Error fetching data from PostgreSQL:", error)
        return []
    finally:
        # Close the cursor and connection
        if conn:
            cur.close()
            conn.close()


def update_slack_reporting_status(issue_id, incident_id,status):
    db_params = get_postgres_db_params()
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    try:
        query = """
            UPDATE public.slack_inference_report
            SET reporting_status = %s
            WHERE issue_id = %s AND incident_id = %s;
        """
        cur.execute(query)
        cur.execute(query, (status, issue_id, incident_id))
        conn.commit()
        print("Status updated successfully.")
    except (Exception, psycopg2.Error) as error:
        print("Error updating status in PostgreSQL:", error)
    finally:
        if conn:
            cur.close()
            conn.close()
import requests
import config
import json
import redis
import psycopg2


postgres_host  = config.configuration.get("postgres_host", "localhost")
postgres_port  = config.configuration.get("postgres_port", "5432")
postgres_db = config.configuration.get("postgres_db", "pl")
postgres_user = config.configuration.get("postgres_user", "postgres")
postgres_pass = config.configuration.get("postgres_pass", "eo1Mgtm6HI")



def getAllUserIssueInferences(issue_id,limit,offset):
    db_params = getPostgresDBParams()
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

            queryString = bytes(row[3]).decode('utf-8')
            answerString = bytes(row[4]).decode('utf-8')

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

        # Serialize the result as JSON
        # json_response = json.dumps(results)
        try:
            json_data = json.dumps({'data': results})
        except Exception as e:
            print(f"Serialization error: {e}")
            json_data = json.dumps({'error': 'Serialization error'})

        return results
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred fetching user inferences for an {issue_id} with exception : {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def insertUserIssueInference(issue_id, query,temperature,topK,vectorEmbeddingModel,gptModel,requestId,answer):
    db_params = getPostgresDBParams()
        
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
    data['query_bytea'] = psycopg2.Binary(data['query'].encode('utf-8'))
    data['answer_bytea'] = psycopg2.Binary(data['answer'].encode('utf-8'))

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

def updateUserInferenceFeedback(requestId, feedback, score):
    
    db_params = getPostgresDBParams()

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

def findIfIssueIsPresentInDb(issue_id):
    # Database connection parameters
    db_params = getPostgresDBParams()


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

def insertIssueUserQueryResponse(issue_id,incident_id,query,answer,is_rca,created_at):
    print("")
    db_params = getPostgresDBParams()
   
    data = {
        'issue_id': issue_id,
        'incident_id': incident_id,
        'query': query,
        'answer': answer,
        'is_rca': is_rca,
        'created_at': created_at
    }

    # Convert string data to bytea
    data['query_bytea'] = psycopg2.Binary(data['query'].encode('utf-8'))
    data['answer_bytea'] = psycopg2.Binary(data['answer'].encode('utf-8'))

    # SQL query for inserting data
    insert_query = """
        INSERT INTO public.issue_incident_conversation
        (issue_id,incident_id, query, answer, is_rca, created_at)
        VALUES (%(issue_id)s, %(incident_id)s, %(query_bytea)s, %(answer_bytea)s, %(is_rca)s, %(created_at)s);
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
        print("Query Answer Data inserted successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred While inserting user inference query answer to postgres for issue {issue_id} and incident:{incident_id} as exception:{e}")
    finally:
    # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def insertIssueIncidentContext(issue_id,incident_id,context,created_at,updated_at):
    print("")
    db_params = getPostgresDBParams()
   
    data = {
        'issue_id': issue_id,
        'incident_id': incident_id,
        'context': context,
        'created_at': created_at,
        'updated_at': updated_at
    }

    # Convert string data to bytea
    data['context_bytea'] = psycopg2.Binary(data['context'].encode('utf-8'))

    # SQL query for inserting data
    insert_query = """
        INSERT INTO public.issue_incident_context
        (issue_id, incident_id, context, created_at, updated_at)
        VALUES (%(issue_id)s, %(incident_id)s, %(context_bytea)s, %(created_at)s, %(updated_at)s);
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
        print("Query Answer Data inserted successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred While inserting user inference query answer to postgres for issue {issue_id} and incident:{incident_id} as exception:{e}")
    finally:
    # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def getIssueIncidentUserConversation(issue_id,incident_id,limit,offset):
    print("")
    db_params = getPostgresDBParams()
   
    data = {
        'issue_id': issue_id,
        'incident_id': incident_id,
        'context': context,
        'created_at': created_at,
        'updated_at': updated_at
    }

    # Convert string data to bytea
    data['context_bytea'] = psycopg2.Binary(data['context'].encode('utf-8'))

    # SQL query for inserting data
    insert_query = """
        INSERT INTO public.issue_incident_context
        (issue_id, incident_id, context, created_at, updated_at)
        VALUES (%(issue_id)s, %(incident_id)s, %(context_bytea)s, %(created_at)s, %(updated_at)s);
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
        print("Query Answer Data inserted successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred While inserting user inference query answer to postgres for issue {issue_id} and incident:{incident_id} as exception:{e}")
    finally:
    # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def getIssueIncidentContext(issue_id,incident_id):
   
    db_params = getPostgresDBParams()
   
    data = {
        'issue_id': issue_id,
        'incident_id': incident_id,
        'context': context,
        'created_at': created_at,
        'updated_at': updated_at
    }

    # Convert string data to bytea
    data['context_bytea'] = psycopg2.Binary(data['context'].encode('utf-8'))

    # SQL query for inserting data
    insert_query = """
        INSERT INTO public.issue_incident_context
        (issue_id, incident_id, context, created_at, updated_at)
        VALUES (%(issue_id)s, %(incident_id)s, %(context_bytea)s, %(created_at)s, %(updated_at)s);
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
        print("Query Answer Data inserted successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred While inserting user inference query answer to postgres for issue {issue_id} and incident:{incident_id} as exception:{e}")
    finally:
    # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def checkIfRcaAlreadyGenerated(issue_id,incident_id):
    # Database connection parameters
    db_params = getPostgresDBParams()
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_params)

    # Create a cursor
    cur = conn.cursor()

    # SQL query to check for the existence of a record with the given issue_id
    check_query = """SELECT is_rca, answer FROM public.issue_incident_conversation WHERE issue_id = %s AND incident_id = %s;"""

    try:
        # Execute the check query with the issue_id as a parameter
        cur.execute(check_query, (issue_id, incident_id))

        # Fetch the result (True if a record exists, False if not)
        result = cur.fetchone()

        if result is not None:
            isRca_value , answer = result
            return isRca_value, bytes(answer).decode('utf-8')
        else:
            return None,None
    except psycopg2.Error as e:
        print(f"Error occurred While fetching issueid in postgres : {e}")
        raise Exception("Error occurred While fetching issueid in postgres : {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def checkIfRcaAlreadyPresent(issue_id):
    # Database connection parameters
    db_params = getPostgresDBParams()
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_params)

    # Create a cursor
    cur = conn.cursor()

    # SQL query to check for the existence of a record with the given issue_id
    query = """SELECT answer FROM public.issue_incident_conversation WHERE issue_id = %s AND is_rca = %s ORDER BY created_at DESC LIMIT 1; """

    try:
        # Execute the check query with the issue_id as a parameter and rca = True
        cur.execute(query, (issue_id,True))

        result = cur.fetchone()

        if result is not None and result[0] is not None:
            answer = bytes(result[0]).decode('utf-8')
            return answer
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

def insertOrUpdateRcaToDB(issue_id, incident_id,answer):
    # Validate that 'answer' is not None
    if answer is None:
        print("Rca is None. Aborting database operation. for issue: {} incidentId:{}".format(issue_id,incident_id))
        return
    # Issue and Incident IDs and answer to update/insert
    # Database connection parameters
    db_params = getPostgresDBParams()
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        
        # Create a cursor
        cur = conn.cursor()

        new_answer = psycopg2.Binary(answer.encode('utf-8')) # Replace with your new answer bytes
        query = "generate RCA"
        new_query = psycopg2.Binary(query.encode('utf-8'))

        # SQL query to update or insert the answer
        upsert_query = """
            INSERT INTO public.issue_incident_conversation (issue_id, incident_id, query, answer, created_at, is_rca)
            VALUES (%s, %s, %s, %s, NOW(), %s)
            ON CONFLICT (issue_id, incident_id) WHERE is_rca = true
            DO UPDATE SET answer = EXCLUDED.answer, created_at = EXCLUDED.created_at
            RETURNING answer;
        """

        # Execute the upsert query with the specified parameters
        cur.execute(upsert_query, (issue_id, incident_id, new_query, new_answer, True))

        # Fetch the updated/inserted answer
        updated_answer = cur.fetchone()[0]
        
        # Commit the transaction
        conn.commit()

        # Print or use the updated/inserted answer as needed
        print(f"Updated/Inserted answer: {updated_answer}")

    except psycopg2.Error as e:
        print(f"Error occurred while updating/inserting answer: {e}")
        conn.rollback()
        raise Exception(f"Error occurred while updating/inserting answer: {e}")
    finally:
        # Close the cursor and the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def getPostgresDBParams(): 
    db_params = {
        'database': postgres_db,
        'user': postgres_user,
        'password': postgres_pass,
        'host': postgres_host,
        'port': postgres_port
    }
    return db_params




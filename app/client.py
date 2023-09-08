import requests
import config
import json
import redis
import psycopg2

axon_host = config.configuration.get("ZK_AXON_HOST", "localhost:8080")
redis_host = config.configuration.get("ZK_REDIS_HOST", "localhost")
redis_db = config.configuration.get("ZK_REDIS_DB", 6)
redis_pass = config.configuration.get("ZK_REDIS_PASSWORD", "")
postgres_host  = config.configuration.get("POSTGRES_HOST", "localhost")
postgres_port  = config.configuration.get("POSTGRES_PORT", "5432")
postgres_db = config.configuration.get("POSTGRES_DB", "pl")
postgres_user = config.configuration.get("POSTGRES_USER", "postgres")
postgres_pass = config.configuration.get("POSTGRES_PASSWORD", "eo1Mgtm6HI")


def getIssueSummary(issue_id):
    url = f"http://{axon_host}/v1/c/axon/issue/{issue_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        issueSummary = data['payload']['issue']
        return issueSummary
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")


def getScenario(scenario_id):
    try:
        # Connect to Redis
        r = redis.StrictRedis(host=redis_host, port=6379, db=redis_db)

        # Read the JSON object from the specified key
        json_data = r.get(scenario_id)

        # If the key is not found or the value is None, return None
        if json_data is None:
            return None

        # Decode the JSON data
        scenario = json.loads(json_data)

        return scenario
    except redis.exceptions.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
    except Exception as e:
        print(f"Error reading JSON from Redis: {e}")
        return None


def getScenarioStats(scenario_id):
    url = f"http://{axon_host}/v1/c/axon/scenario"
    params = {"scenario_id_list": scenario_id, "st": "-12h"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        scenarioDetail = data['payload']['scenarios']
        return scenarioDetail
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")


def getSpansMap(issue_id, incident_id):
    url = f"http://{axon_host}/v1/c/axon/issue/{issue_id}/incident/{incident_id}"
    params = {"limit": 10, "offset": 0}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        spansMap = data['payload']['spans']
        return spansMap
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")

def getIssueIncidents(issue_id):
    url = f"http://{axon_host}/v1/c/axon/issue/{issue_id}/incident"
    params = {"limit": 50, "offset": 0}

    try: 
        response = requests.get(url,params=params)
        response.raise_for_status # Raise an HTTPError exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        incidents = data['payload']['trace_id_list']
        return incidents
    except requests.exceptions.RequestException as e:
        print(f"Error while fetching incident Ids for a given issue : {e}")


def getSpanRawdata(issue_id, incident_id, span_id):
    url = f"http://{axon_host}/v1/c/axon/issue/{issue_id}/incident/{incident_id}/span/{span_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        spanRawdata = data['payload']['span_raw_data_details'][span_id]
        return spanRawdata
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")

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


def findIfIssueIncidentIsPresentInDb(issue_id,incident_id):
    # Database connection parameters
    db_params = getPostgresDBParams()

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_params)

    # Create a cursor
    cur = conn.cursor()

    # SQL query to check for the existence of a record with the given issue_id
    query = "SELECT * FROM public.issue_incident_inference_raw_data WHERE issue_id = %s AND incident_id = %s"

    try:        
        # Execute the check query with the issue_id as a parameter
        cur.execute(query, (issue_id, incident_id))

        # Fetch the result (True if a record exists, False if not)
        row = cur.fetchone()

        # Check if a row exists and return it, or return False if not
        if row:
            result = row
        else:
            result = False

            return result

    except psycopg2.Error as e:
        print(f"Error occurred While fetching issueid, incident pair in postgres : {e}")
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



## Readme

### Setup this project (without Docker)

1. Create Conda Environment:
`conda env create -f environment.yml`
2. Run postgress locally with fitting credentials, or adjust credential in the rag_postgres_llm.py script:

`POSTGRES_USER=postgres
POSTGRES_PASSWORD=start
POSTGRES_DB=postgres
POSTGRES_PORT=5432`

3. Run the rag-api:
`python rag_postgres_llm.py`
By Default, Fast-API runs on `http://0.0.0.0:8000`
4. Test Ingestion & Query
Once the API is running, run the test script:

'python test_ingest_query.py'
The scripts automatically work with the respective Fast-apis endpoints.
For other uses, the endpoints are /ingest and /query. 

Currently the Project is using lightweight LLMs and Dummy Files. One File contains a clear answer to the example query to demonstrate basic functionality. Different Queries can be chosen and alternative files added to the dummyfile folder. For better functionality, more prepocessing should be added and a bigger model should be chosen


### Setup this project using docker

The project contains a Dockerfile, compose.yml and the corresponding environment.yml that are needed to create a dockerfile. As of right now, the resulting image produces an error when trying to reach the database. It was not possible to debug or solve the issue because of the time constraint on the assignment. 

### My approach
PostgreSQL is used to store vector embeddings. The files are in txt. format
A Sentence Transformer is used to calculate embeddings for the documents to perform a similarity search using FAISS. These emebeddings are stored in the PostgreSQL DB.
The sentence transformer is also used to generate embeddings for the queries.
The resulting documents of the similarity search are then used as context and passed along with the query to generate a response using a LLM. For this demonstration, Flan-T5 was used.
A Fast-API was set up to ingest dand query endpoints. 
Currently, because of time contraints on this project, no explicit preprocessing has been implemented. This will reduce the quality of the results. The project could be further opimized by adding data cleaning, normalization and tokenization.
Furthermore, the text could be transformed to not include upper/lowercase, punctuation or stopwords. 


AI was used as coding assistance in this Project.


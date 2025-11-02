## Readme

### How to setup:
Clone this repository:

```bash
git clone https://github.com//patrickthomasius/Assignment-RAG.git
cd Assignment-RAG
```
### Setup this project with Docker (recommended)
to replicate the runtime, a Dockerfile and a docker-compose file were included in this project.

To build and run the container open a shell inside the folder and run

`docker build .` to setup the docker image

afterwards run

`docker-compose up ` to run the container. This starts the postgres service, runs the api, then waits a few seconds and then ingests a test query. The outputs are given in the terminal where these lines are executed (therefore, dont add a -d flag). 
The waiting time and set amount of retries should be enough to make sure that the api is running when queries are send. If the ingest script still fails, it can be worked around by restarting the service manually from bash or inside docker desktop. 


#### Ports
This project uses the following ports:

- **5432** – PostgreSQL database
- **8000** – Fast API

#### Cuda compatibility
the project is currently specified to use a cuda 12.1 runtime. 
You need a driver version ≥ 525.60.13 for Linux, and for Windows x86_64 you need ≥ 527.41 to guarantee compatibility with CUDA 12.x. 
If it is not possible to run with these drivers, the base image can be adjusted in the dockerfile. However this project was only tested with the specified Cuda Version and up-to-date drivers.


#### API
the api has /query and /ingest endpoints. However, to test new documents and queries, also the test_ingest_query.py script can be easily modified. New documents can simply be added as txt files in the "dummy_docs" folder.
If you wish to directly utilize the api, requests can be send in the following format

`curl -X POST http://localhost:8000/query
     -H "Content-Type: application/json"
     -d '{"query": "Where is the Eiffel Tower located?", "top_k": 2}'
`

`
curl -X POST http://localhost:8000/ingest
     -H "Content-Type: application/json"
     -d '{"documents": ["The Eiffel Tower is located in Paris.", "Berlin is the capital of Germany."]}'
`


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



### My approach
PostgreSQL is used to store vector embeddings. The files are in txt. format. The files were generated using chatGPT.
A Sentence Transformer all-MiniLM-L6-v2 is used to calculate embeddings. A FAISS index is calculated for these embeddings which is later used to perform a quick similarity search. The index is also stored in a Postgresql Database. 
The sentence transformer is also used to generate embeddings for the queries.Which then in turn are used as inputs for the similarity search. 
The resulting documents of the similarity search are then used as context and passed along with the query to generate a response using a LLM. For this demonstration, Flan-T5 was used.
A Fast-API was set up with ingest and query endpoints to store documents and run queries. 
Because this application uses both SentenceTransformer and an LLM for question answering, no pre-processing besides tokenization was performed. 
One File was created manually that contains the answer to the query ("The capitol of France is Paris") to test core functionality of the script. With more complex questions the retrieved documents are typically suitable, but the answer to the question is sometimes not exact. A possible explanation for this is that a bigger or more performant model could outpower Flan-T5, but for the demonstration Flan-T5 was chosen for efficiency. 


AI was used as coding assistance in this Project.


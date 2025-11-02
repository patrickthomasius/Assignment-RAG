FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime

WORKDIR /app

COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml && conda clean -a

SHELL ["conda", "run", "-n", "rag_env", "/bin/bash", "-c"]

COPY rag_postgres_llm.py /app/
COPY dummy_docs/ /app/dummy_docs/
COPY test_ingest_query.py /app/
COPY environment.yml /tmp/environment.yml

EXPOSE 8000



FROM docker.io/python:3.12

COPY vault_snapshot /vault_snapshot
COPY requirements.txt /vault_snapshot/

WORKDIR /vault_snapshot
RUN pip install -r requirements.txt

CMD ["./vault_snapshot.py"]

FROM alpine

ARG VAULT_VERSION=1.13.2

COPY vault-snapshot.sh /

RUN wget https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip && \
    unzip vault_${VAULT_VERSION}_linux_amd64.zip && \ 
    mv vault /usr/local/bin && rm  vault*zip  && \
    apk add s3cmd && chmod +x vault-snapshot.sh

CMD ["/vault-snapshot.sh"]

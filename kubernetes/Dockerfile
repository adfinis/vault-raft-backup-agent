FROM alpine

ARG BAO_VERSION=2.4.0

COPY bao-snapshot.sh /

RUN wget https://github.com/openbao/openbao/releases/download/v${BAO_VERSION}/bao_${BAO_VERSION}_Linux_x86_64.tar.gz && \
    tar xzf bao_${BAO_VERSION}_Linux_x86_64.tar.gz && \ 
    mv bao /usr/local/bin && rm  bao*tar.gz  && \
    apk add s3cmd && chmod +x bao-snapshot.sh

CMD ["/bao-snapshot.sh"]

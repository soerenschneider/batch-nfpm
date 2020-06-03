FROM golang:1.14

ENV PYTHONPATH /opt/
RUN useradd -m buildmeister
COPY requirements.txt /opt/batchnfpm/requirements.txt

RUN apt update && \
    apt -y install python3 python3-pip && \
    pip3 install --no-cache-dir -r /opt/batchnfpm/requirements.txt

COPY batchnfpm/*.py /opt/batchnfpm/

RUN apt -y install yarn

USER buildmeister
WORKDIR /home/buildmeister

# Install 3rd party dependencies for the tools I build
# Install nfpm
RUN go get github.com/goreleaser/nfpm && \
    cd /go/src/github.com/goreleaser/nfpm && \
    go install cmd/nfpm/main.go && \
    mv /go/bin/main /go/bin/nfpm

# Install go-bindata
RUN GO111MODULE=off go get -u github.com/containous/go-bindata/...

# Install promu
RUN go get github.com/prometheus/promu


CMD ["python3", "/opt/batchnfpm"]

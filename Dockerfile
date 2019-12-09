### Build BonnMotion in seperate container
FROM maciresearch/core_worker:0.5.1 as jdk_builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends\
    unzip \
    wget \ 
    openjdk-8-jdk-headless \
    && apt-get clean

WORKDIR /
RUN wget -nv http://sys.cs.uos.de/bonnmotion/src/bonnmotion-3.0.1.zip \
    && unzip bonnmotion-3.0.1.zip \
    && rm bonnmotion-3.0.1.zip \
    && cd /bonnmotion-3.0.1 \
    && ./install \
    && mv /bonnmotion-3.0.1/bin/bm /usr/local/bin/ \
    && rm -rf bin/ src/ doc/ javadoc/ validate/ lib/*.txt install install.bat GPL



### Build dtn7d dtn7cat
FROM golang:1.11 AS dtn7-builder

COPY dtn7-go /dtn7-go
WORKDIR /dtn7-go
RUN go build -o /dtn7cat ./cmd/dtncat \
&& go build -o /dtn7d ./cmd/dtnd



### Setup core worker container
FROM maciresearch/core_worker:0.5.1
LABEL maintainer="msommer@informatik.uni-marburg.de"
LABEL name="umrds/cadr-evaluation"
LABEL version="0.3"

# install dependencies 
RUN apt-get update \
    && apt-get install -y \
    python-pip \
    python3-pip \
    python3-requests \
    bwm-ng \
    sysstat \
    tcpdump \
    openjdk-8-jre-headless \
    && apt-get clean

# install core-dtn7 integration
COPY --from=dtn7-builder /dtn7cat /usr/local/sbin/dtn7cat
COPY --from=dtn7-builder /dtn7d /usr/local/sbin/dtn7d
COPY --from=dtn7-builder /dtn7-go/cmd/dtnclient.py /usr/local/sbin/dtnclient
COPY dotcore /root/.core/
RUN echo "custom_services_dir = /root/.core/myservices" >> /etc/core/core.conf


# install BonnMotion
COPY --from=jdk_builder /bonnmotion-3.0.1 /bonnmotion-3.0.1
COPY --from=jdk_builder /usr/local/bin/bm /usr/local/bin/bm
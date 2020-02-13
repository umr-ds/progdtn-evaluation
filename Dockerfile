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
FROM golang:1.13 AS dtn7-builder

COPY dtn7-go /dtn7-go
WORKDIR /dtn7-go
RUN go build -o /dtncat ./cmd/dtncat \
&& go build -o /dtnd ./cmd/dtnd



### Setup core worker container
FROM maciresearch/core_worker:0.5.1
LABEL maintainer="msommer@informatik.uni-marburg.de"
LABEL name="umrds/cadr-evaluation"
LABEL version="0.4"

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
COPY --from=dtn7-builder /dtncat /usr/local/sbin/dtncat
COPY --from=dtn7-builder /dtnd /usr/local/sbin/dtnd
COPY --from=dtn7-builder /dtn7-go/cmd/dtnd/context_data.js /root/context.js
COPY dotcore /root/.core/
RUN echo "custom_services_dir = /root/.core/myservices" >> /etc/core/core.conf

COPY --from=dtn7-builder /dtn7-go/helpers/cadrhelpers/dtnclient.py /usr/local/sbin/dtnclient
COPY --from=dtn7-builder /dtn7-go/helpers/cadrhelpers/context_generator.py /usr/local/sbin/context_generator

# install python package for dependencies
COPY --from=dtn7-builder /dtn7-go/helpers /root/helpers
RUN pip3 install /root/helpers

# install BonnMotion
COPY --from=jdk_builder /bonnmotion-3.0.1 /bonnmotion-3.0.1
COPY --from=jdk_builder /usr/local/bin/bm /usr/local/bin/bm
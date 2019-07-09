### Build dtn7d dtn7cat
FROM golang:1.11 AS dtn7-builder

COPY dtn7-go /dtn7-go
WORKDIR /dtn7-go
RUN go build -o /dtn7cat ./cmd/dtncat \
&& go build -o /dtn7d ./cmd/dtnd



### Build BonnMotion in seperate container
FROM maciresearch/core_worker:0.3 as jdk_builder

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



### Setup core worker container
FROM maciresearch/core_worker:0.3
LABEL maintainer="hoechst@mathematik.uni-marburg.de"
LABEL name="umrds/multi_mechanism_dtn_routing"
LABEL version="0.1"

# install dependencies 
RUN apt-get update \
    && apt-get install -y \
    python-pip \
    python3-pip \
    bwm-ng \
    sysstat \
    tcpdump \
    openjdk-8-jre-headless \
    python3-numpy \
    && apt-get clean

# install local pyserval
ADD pyserval /pyserval
RUN python -m pip install /pyserval \
    && python3 -m pip install /pyserval \
    && python -m pip install pynacl \
    && python3 -m pip install pynacl \
    && rm -rf /root/.cache/pip/*

# install core-serval integration
COPY --from=dtn7-builder /dtn7-go/dtncat  /usr/local/sbin/dtncat
COPY --from=dtn7-builder /dtn7-go/dtnd  /usr/local/sbin/dtnd
COPY dotcore /root/.core/
ENV BASH_ENV /root/.serval
RUN echo "custom_services_dir = /root/.core/myservices" >> /etc/core/core.conf \
    && echo 'export SERVALINSTANCE_PATH=$SESSION_DIR/`hostname`.conf' >> /root/.serval \
    && echo 'export SERVALINSTANCE_PATH=$SESSION_DIR/`hostname`.conf' >> /root/.bashrc


# install BonnMotion
COPY --from=jdk_builder /bonnmotion-3.0.1 /bonnmotion-3.0.1
COPY --from=jdk_builder /usr/local/bin/bm /usr/local/bin/bm
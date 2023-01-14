### Build dtnd & dtncat
FROM golang:1.16.6 AS dtn7-builder

COPY dtn7-go /dtn7-go
WORKDIR /dtn7-go
RUN go build ./cmd/dtn-tool
RUN go build ./cmd/dtnd

### Setup core worker container
FROM maciresearch/core_worker:0.5.1
LABEL maintainer="msommer@informatik.uni-marburg.de"
LABEL name="umrds/cadr-evaluation"
LABEL url="https://github.com/umr-ds/cadr-evaluation"
LABEL version="0.4.2"

# update system
RUN apt update && apt dist-upgrade -y && apt clean

# install dependencies 
RUN apt update \
    && apt install -y \
    python3-pip \
    python3-dev \
    gcc \
    g++ \
    python3-requests \
    python3-daemon \
    python3-toml \
    python3-wheel \
    bwm-ng \
    sysstat \
    tcpdump \
    htop \
    && apt clean

# install core-dtn7 integration
COPY --from=dtn7-builder /dtn7-go/dtn-tool /usr/local/sbin/dtn-tool
COPY --from=dtn7-builder /dtn7-go/dtnd /usr/local/sbin/dtnd
COPY dotcore /root/.core/
RUN echo "custom_services_dir = /root/.core/myservices" >> /etc/core/core.conf

# cadr scripts
COPY --from=dtn7-builder /dtn7-go/cmd/dtnd/cadr_sensors.js /root/cadr_sensors.js
COPY --from=dtn7-builder /dtn7-go/cmd/dtnd/cadr_responders.js /root/cadr_responders.js
COPY --from=dtn7-builder /dtn7-go/cmd/dtnd/cadr_epidemic.js /root/cadr_epidemic.js
COPY --from=dtn7-builder /dtn7-go/cmd/dtnd/cadr_spray.js /root/cadr_spray.js

COPY helpers/cadrhelpers/dtnclient.py /usr/local/sbin/dtnclient
COPY helpers/cadrhelpers/node_helper.py /usr/local/sbin/node_helper
COPY helpers/cadrhelpers/log_saver.py /usr/local/sbin/log_saver
COPY helpers/cadrhelpers/traffic_generator.py /usr/local/sbin/traffic_generator
COPY helpers/cadrhelpers/movement_context.py /usr/local/sbin/movement_context
COPY helpers/cadrhelpers/node_context.py /usr/local/sbin/node_context

# install python package for dependencies
COPY helpers /root/helpers

RUN pip3 install wheel
RUN pip3 install /root/helpers

COPY . /dtn_routing

RUN ln -s /usr/lib/python3.6/dist-packages/core /usr/lib/python3/dist-packages/core
RUN ln -s /usr/lib/python3.6/dist-packages/core-5.5.2-py3.6.egg-info /usr/lib/python3/dist-packages/core-5.5.2-py3.6.egg-info

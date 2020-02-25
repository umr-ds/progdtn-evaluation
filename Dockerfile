### Build dtnd & dtncat
FROM golang:1.13 AS dtn7-builder

COPY dtn7-go /dtn7-go
WORKDIR /dtn7-go
RUN go build -o /dtncat ./cmd/dtncat \
&& go build -o /dtnd ./cmd/dtnd

### Setup core worker container
FROM maciresearch/core_worker:6.1.0-1
LABEL maintainer="msommer@informatik.uni-marburg.de"
LABEL name="umrds/cadr-evaluation"
LABEL version="0.4"

# install dependencies 
RUN apt-get update \
    && apt-get install -y \
    python-pip \
    python3-pip \
    python3-requests \
    python3-daemon \
    python3-toml \
    bwm-ng \
    sysstat \
    tcpdump \
    && apt-get clean

# install core-dtn7 integration
COPY --from=dtn7-builder /dtncat /usr/local/sbin/dtncat
COPY --from=dtn7-builder /dtnd /usr/local/sbin/dtnd
COPY --from=dtn7-builder /dtn7-go/cmd/dtnd/context_data.js /root/context.js
COPY dotcore /root/.core/
RUN echo "custom_services_dir = /root/.core/myservices" >> /etc/core/core.conf

COPY helpers/cadrhelpers/dtnclient.py /usr/local/sbin/dtnclient
COPY helpers/cadrhelpers/helper_sensor.py /usr/local/sbin/helper_sensor

# install python package for dependencies
COPY helpers /root/helpers
RUN pip3 install /root/helpers

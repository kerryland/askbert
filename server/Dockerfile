
# LABEL io.hass.version="0.1" io.hass.type="addon" io.hass.arch="armhf|aarch64|i386|amd64"

# ARG BUILD_FROM
ARG BUILD_FROM=homeassistant/aarch64-base-debian:latest
FROM $BUILD_FROM

# pip install -U pip setuptools wheel
# pip install -U spacy
# python -m spacy download en_core_web_sm

# Copy data for add-on
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]


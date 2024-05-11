FROM python:3.12-slim-bookworm
LABEL org.opencontainers.image.authors="Magus Vaerde <magus@verde.arbler.com>"
LABEL version="1.0"
LABEL description="A tool to manage the minimum power level of a battery attached to a Sungrow Hybrid Inverter"

ARG IGNORE_TESTS=n

WORKDIR /optmybat

COPY . /optmybat/
RUN apt-get update \
    && apt-get install -y build-essential \
    && pip3 install --no-cache-dir --upgrade -r requirements.txt \
    && apt-get remove -y build-essential \
    && apt-get autoremove -y \
    && apt-get clean

# Run the tests.  Serves two purposes:
# 1) Populates __pycache__ for all tested files
# 2) Checks that config/config.yml is correct
# To ignore the test results, use `--build-arg=IGNORE_TESTS=y`
RUN pytest --ignore=scanner || test $IGNORE_TESTS

# Switch to a completely safe user
RUN chown -R nobody: .
USER nobody
CMD ["python3", "optmybat"]

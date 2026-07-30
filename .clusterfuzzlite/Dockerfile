FROM gcr.io/oss-fuzz-base/base-builder-python
RUN pip3 install atheris
COPY . $SRC/operations
COPY fuzzers $SRC/fuzzers
COPY build.sh $SRC/
WORKDIR $SRC/operations

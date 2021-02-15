# Basic ubuntu setup
FROM ubuntu:latest
ARG DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y python3 python3-pip

# Grab Briann's model builder and parflow for definition files
RUN git clone https://github.com/bnmajor/simput-model-builder.git
WORKDIR simput-model-builder
RUN pip3 install -e .
# Copy modified local version
COPY src/model_builder.py src/model_builder.py 
RUN chmod +x src/model_builder.py
RUN git clone https://github.com/parflow/parflow.git

# Sanity check
RUN python3 src/model_builder.py --help 

# Use sample data to make model
# RUN python3 src/model_builder.py -o . -d parflow/pf-keys/definitions/ -f sample_data/*.json
# CMD cat model.json

# Use washita data to make model
COPY ./LW_Test.pfidb ./LW_Test.pfidb
RUN python3 src/model_builder.py -o . -d parflow/pf-keys/definitions/ -f ./LW_Test.pfidb
CMD cat model.json

# Simput Model Builder

A basic script to produce a Simput data model from ParFlow definition files.

Clone the repository:

    git clone https://github.com/bnmajor/simput-model-builder.git
    cd simput-model-builder
    pip install -e .

The script can accept either a directory:

    model_builder && \
    -o path/to/output/directory && \
    path/to/directory/of/definitions
    

Or a list of files:

    python model_builder.py && \
    -o path/to/output/directory && \
    path/to/definition_1.yaml path/to/definition_2.yaml


The `-o` flag denotes the output location and is optional. Use the `--help` flag to get information on the keys:

    model_builder --help


    Usage: model_builder [OPTIONS]

    Accepts a single file, list of files, or directory name.

    Options:
        -o, --output DIRECTORY      The directory to output the model file to. If no
                                    output is provided the file will be created in
                                    the current directory.

        -d, --directory DIRECTORY  The directory of definition files.
        -f, --file FILE            A definition file to use.
        --help                     Show this message and exit.


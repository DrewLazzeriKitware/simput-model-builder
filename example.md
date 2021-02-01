To set up a local Simput instance and use the provided script to create the model follow the following steps:

1. Clone this repository and install the requirements if you have not already done so:

        git clone https://github.com/bnmajor/simput-model-builder.git
        cd simput-model-builder
        pip install -e . && cd ../

2. Clone the forked repository branch that contains the changes for the new PFTools type:

        git clone -b type-pftools https://github.com/bnmajor/simput.git
        cd simput && npm install && cd ../

3. Clone the ParFlow repository:

        git clone https://github.com/parflow/parflow.git

4. Run the script:

        cd simput-model-builder/src
        model_builder && \
        -o path/to/simput-repo/types/pftools/src && \
        -d path/to/parflow-repo/pf-keys/definitions

5. Start Simput:

        cd path/to/simput-repo
        npm run type:pftools
        npm run dev
    Open http://localhost:9999 in your browser.

    Click the `ParFlow` card to view the generated forms.

6. Populate the model:

        Drag and drop the default_richards_model.json file (found in the sample_data directory) anywhere in the form.

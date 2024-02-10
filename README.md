# bottle-tone-experiment
A single file python program where one can run an experiment with the sounds from a bottle.


## Setting Up the Bottle Tone Experiment Environment

To get started with the Bottle Tone Experiment, you'll need to set up your environment. Follow these steps carefully to ensure everything is correctly installed and configured.

### 1. Install Python

- **Download Python**: First, you need to download Python. Ensure you download the correct version for your needs. For this example, we're using Python 3.11.
- **Install Python**: During installation, choose the custom install option. It's recommended to install Python in a specific directory, such as `C:/python/python311` for Python 3.11. This approach makes it easier to manage multiple Python versions, as you can later add versions like `C:/python/python310` for other projects.

### 2. Add Python to the Path

- **Modify System Path**: Make sure to add Python to the system's PATH environment variable to easily run Python from the command line.

### 3. Install Poetry

Install Poetry by running the following command in your terminal:

```bash
pip install poetry
```

### 4. Install Git

- **Download and Install Git**: If you haven't already, download and install Git from [git-scm.com](https://git-scm.com/).

### 5. Clone the Project Repository

Navigate to the folder where you want to store this project and clone the Bottle Tone Experiment repository:

```bash
git clone https://github.com/svenviktorjonsson/bottle-tone-experiment bottle-tone-experiment
```

This command downloads the project into the `bottle-tone-experiment` folder.

### 6. Set Up the Project Environment

Go to the newly downloaded project folder and execute the following commands to set up the project environment:

```bash
poetry env use C:/python/python311
poetry config virtualenvs.in-project true
.venv\Scripts\activate
poetry install
```

After all the dependencies are installed, you are ready to experiment with your Bottle Tone Experiment.

### 7. Run the Experiment

To run the experiment, use the following command:

```bash
python .\bottle_tone_experiment\experiment.py
```

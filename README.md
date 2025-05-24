## Setup
1. Install packages listed in requirements.

2. Create a config file named `.env` which contains the following line:
    ```sh
    OPENAI_API_KEY=...
    OPENAI_ORGANIZATION=...
    ```
    (when using openAI models.)

## Extract game log from Mafia dataset
Run the following python code:
```sh
python extract_mafia_dataset.py
```

## Run Mafia game outcome prediction 
Run the following python code:
```sh
python run.py
```
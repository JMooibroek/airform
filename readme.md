# TODO
---
* get_webpage() is too confusing for smaller AI
* AI's tend to only use a tool only once.
* AI's try to use tools that don't exist
* Create scroll tool? Helps with limited context (e.g. Showing line 50-100)
    - Create goto(line) function
* Press key tool function
* Print page if content has been altered. Preferably only returning the updated part to the LLM
* Use the new [lmstudio-python library](https://github.com/lmstudio-ai/lmstudio-python). Maybe fixes loop problem
* Needs better element identifiers ...$0 -> var1 = ... ?

# Installation
```
pip install requirements.txt -r
python -m playwright install
```
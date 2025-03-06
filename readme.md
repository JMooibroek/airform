![airform](/readme/logo1.png)
**AI I.nternet R.eadable Form.at**

# About
Airform is a HTML to Flavored Markdown formatter, made for LLM.

# Installation
```
> pip install requirements.txt -r
> python -m playwright install
```

# Usage
```
> venv\Scripts\activate
> python openai_async_example.py
```

# TODO
* Create scroll tool? Helps with limited context (e.g. Showing line 50-100)
    - Create goto(line) function
* Press key tool function
* Print page if content has been altered. Preferably only returning the updated part
* Use the new [lmstudio-python library](https://github.com/lmstudio-ai/lmstudio-python). Maybe fixes loop problem
* Needs better element identifiers ...$0 -> var1 = ... ?
* other input types: checkbox, radio, upload files, date

# Future Feature
LM Studio is working on a python SDK. But it doesn't support async function calling yet.
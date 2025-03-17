![airform](/readme/logo1.png)  
**Ai Internet Readable FORMat**

# What is Airform?

Airform allows LLM's *browse* the web, instead of only *searching* the web. That means the LLM has full control over the browser, like you have now.

Airform converts webpages into a readable markdown-like format. This lets LLM do what they are made for, reading and writing. You don't need a fancy vision model to use Airform.

The example includes usage with LM Studio, which uses an openai like API.

# Why markdown?

Markdown has a low token-overhead. That means it uses less tokens than just giving the whole HTML page. For example, my [website's](https://jamaro.net) visible body HTML will fill the AI's context with ~1220 tokens. Airform only uses ~320 tokens.

# Installation
```
> pip install requirements.txt -r
> python -m playwright install
```

# Using the openai example

The api endpoint is by default set to LM Studio's local endpoint.
```
> venv\Scripts\activate
> python openai_sync_example.py
```
Entering: `You: Find out what kind of books Jamaro Mooibroek reads`

Will result (with qwen2.5-7b-instruct-1m) in  

# Known Errors
- Sometimes throws error: `playwright._impl._errors.Error: Page.title: Execution context was destroyed, most likely because of a navigation`
- Links that open in a new tab (target=_blank)

# TODO
- Don't end page parts in id's
- Press key tool function
- Escape existing markdown characters <https://www.markdownguide.org/basic-syntax/#escaping-characters>
    - (also in lists e.g. `- 1968\. A great year!`)
- email address as `<fake@example.com>`
- if styling `white-space: pre-wrap;` don't strip() data -> Or just fix spacing overall
- check aria 
- Optimize code for speed

# Future Feature
* Use the new [lmstudio-python library](https://github.com/lmstudio-ai/lmstudio-python).

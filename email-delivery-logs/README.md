## Deploy Steps
1. `cd venv/lib/python-X.X/site-packages`
2. `zip -r ../../../../out.zip`
3. `zip -g out.zip lambda_function.py`
4. Upload the files to AWS Lambda
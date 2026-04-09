
### Development command
``` 
$ fastapi dev app/main.py
```

### Production command
```
$ uvicorn app.main:app --reload
```

Here is a useful link: [link](https://www.reddit.com/r/FastAPI/comments/1aljf4h/free_fastapi_hosting/)



### Render Service
```
$ uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
where $PORT is a env variable in RENDER

### Useful articles

- [Project structure](https://dev.to/mohammad222pr/structuring-a-fastapi-project-best-practices-53l6)
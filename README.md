# Backend Startkit
Template to get my favourite SQL stack up and running


![diagram](https://github.com/mekanix/backend-startkit/raw/master/backend.png)

## Forking
The `name.py` is special! Although it ends with .py, it is read by shell scripts and CBSD/Reggae `Makefile` (if you're using it). Because it's not regular Python file, it has some limitations. It should consist of one line:

```
app_name="application"  # noqa: E225
```

There must be no space around `=` in the previous example, otherwise shell scripts won't work. The `noqa` part prevents `flake8` failing the test, because it normally requires spaces around `=`.

On fork, edit `name.py` and rename `application` directory acordingly.

[Backend Tutorial](https://github.com/freenit-framework/backend-tutorial)

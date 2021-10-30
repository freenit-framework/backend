# Freenit Backend

## Initialize the Project
```bash
python -m venv ~/.virtualenvs/myproject
source ~/.virtualenvs/myproject/bin/activate
pip install freenit[dev]
freenit.sh myproject
cd myproject
bin/devel.sh
```
It will create initial DB migration, apply it and start
[local development server](http://localhost:5000/api/v1) so you can check if
everything is OK.


## Model
Let's say you want to add the simplest model for blog post with only title and
contents. In your project's `models` directory you need to create `blog.py`:
```py
import ormar

from freenit.config import getConfig
from freenit.models.base import BaseModel
from freenit.models.metaclass import AllOptional

config = getConfig()


class Blog(BaseModel):
    class Meta(config.meta):
        pass

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=1024)
    content: str = ormar.Text()



class BlogOptional(Blog, metaclass=AllOptional):
    pass
```

Please note two things: `BaseModel` is Freenit class not Ormar and
`BlogOptional` is for PATCH method so all it's fields are the same as `Blog`
except they are optional. The reason for this is that Ormar models are not just
for DB operations, but for validating JSON input and parsing objects into JSON.


## Endpoint
In `api` directory of your project add `blog.py` with the following content:
```py
from typing import List

import ormar
from fastapi import HTTPException
from freenit.router import route

from ..models.blog import Blog, BlogOptional


@route('/blogs', tags=['blog'])
class BlogListAPI():
    @staticmethod
    async def get() -> List[Blog]:
        return await Blog.objects.all()

    @staticmethod
    async def post(blog: Blog) -> Blog:
        await blog.save()
        return blog


@route('/blogs/{id}', tags=['blog'])
class BlogDetailAPI():
    @staticmethod
    async def get(id: int) -> Blog:
        try:
            blog = await Blog.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such blog")
        return blog

    @staticmethod
    async def patch(id: int, blog_data: BlogOptional) -> Blog:
        try:
            blog = await Blog.objects.get(pk=id)
            await blog.patch(blog_data)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such blog")
        return blog

    @staticmethod
    async def delete(id: str) -> Blog:
        try:
            blog = await Blog.objects.get(pk=id)
        except ormar.exceptions.NoMatch:
            raise HTTPException(status_code=404, detail="No such blog")
        await blog.delete()
        return blog

```
What you have now is basic CRUD operations on your blog. Note that `@route` is
Freenit's decorator to make it easy to write class based endpoints. As FastAPI
itself has great support for function based endpoints, the idea was to make
it possible for developer to choose between functions and classes. With Freenit
you can write any style you want. Also note that class methods are static
(decorated with `@staticmethod`) because API classes will never create an object.
Or in other words, methods are going to be called on class, not object.  Also,
return value type hinting is important. It will tell Freenit what object is
returned from the method and how to convert it to JSON.


## DB Migration
To connect it all, you need to add the following to `api/__init__.py`:
```py
import myproject.api.blog
```

After that you need to create migration. To do that run the following command
from `myproject` directory:
```
alembic revision --autogenerate -m blog
```
It will create new migration file in `alembic/versions` and format it with
black. Next time you run `bin/devel.sh` that migration will be applied.

Now you should see Blog endpoint in [Swagger](http://localhost:5000/api/v1)

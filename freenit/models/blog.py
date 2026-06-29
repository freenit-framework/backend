from freenit.config import getConfig

config = getConfig()
blog = config.get_model("blog")

BlogPost = blog.BlogPost
BlogPostOptional = blog.BlogPostOptional
BlogPostTag = blog.BlogPostTag
Tag = blog.Tag
NotFoundError = blog.NotFoundError
IntegrityError = blog.IntegrityError

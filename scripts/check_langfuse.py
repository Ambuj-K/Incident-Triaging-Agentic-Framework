from langfuse import Langfuse
import os
from dotenv import load_dotenv

load_dotenv()

lf = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ["LANGFUSE_BASE_URL"],
)

print(lf.auth_check())
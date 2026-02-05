FROM python:3.13-slim


WORKDIR /app


RUN apt-get update && apt-get install -y wget libkrb5-3 libgssapi-krb5-2

#  Download MongoDB Database Tools
RUN wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian10-x86_64-100.9.4.tgz && \
    # Extract and move mongoexport to /usr/local/bin
    tar -zxvf mongodb-database-tools-debian10-x86_64-100.9.4.tgz && \
    mv mongodb-database-tools-debian10-x86_64-100.9.4/bin/mongoexport /usr/local/bin/mongoexport && \
    # Clean up
    rm -rf mongodb-database-tools-*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Start Command
CMD ["python", "main.py"] 

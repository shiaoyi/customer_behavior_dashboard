# FROM：基底映像檔
FROM python:3.7.2-stretch

# WORKDI：建立 working directory
WORKDIR /app

# ADD：將檔案加到 images 內
ADD . /app

# 安裝 selenium 以爬蟲
RUN pip3 install -U selenium

# 只有build 時使用，會執行此命令
RUN pip3 install -r requirements.txt

# run container 時要執行的命令
CMD python3 app.py
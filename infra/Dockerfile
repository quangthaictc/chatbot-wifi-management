# Use python:3.9 as base
FROM python:3.9

# Install dependencies for mininet wifi over debian which is the base OS for python:3.9 image
RUN apt update 
RUN apt install -y sudo git make help2man pyflakes3 python3-pycodestyle tcpdump wpan-tools inetutils-ping
RUN pip install six numpy matplotlib beautifulsoup4 pyyaml flask

# Create a work directory for mininetwifi project
WORKDIR /app

ENV PYTHONPATH="/app"

# Fix install script outdated dependencies names solved by this dockerfile.
RUN git clone https://github.com/intrig-unicamp/mininet-wifi \
  && cd mininet-wifi \
  && sed -i 's/pyflakes//g' util/install.sh \
  && sed -i 's/pep8//g' util/install.sh \
  && util/install.sh -Wlnfv6 

COPY . .

RUN mv entrypoint.sh /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]


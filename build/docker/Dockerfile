FROM ubuntu:noble
LABEL maintainer="bsalis76@gmail.com"
RUN apt update && apt -y upgrade
RUN apt -y install locales vmtouch lib32gcc-s1 software-properties-common
RUN rm -rf /var/lib/apt/lists/* && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG=en_US.utf8
RUN add-apt-repository multiverse
RUN dpkg --add-architecture i386
RUN apt update
RUN { echo steam steam/license note ''; \
      echo steam steam/question select "I AGREE"; \
    } | debconf-set-selections && apt -y install steamcmd
COPY ./sjgms.deb ./sjgms.deb
ARG SJGMS_USER="container"
RUN apt -y install ./sjgms.deb && rm ./sjgms.deb
RUN apt clean && apt autoclean && apt -y autoremove --purge
USER container
ENV USER=container
ENV HOME=/home/container
WORKDIR /home/container
COPY ./entrypoint.sh /entrypoint.sh
CMD [ "/bin/bash", "/entrypoint.sh" ]

FROM postgres:13.21-bookworm

RUN apt-get update \
  && apt-get install -y locales locales-all \
  && localedef -i pt_BR -c -f CP1252 -A /usr/share/locale/locale.alias pt_BR \
  && rm -rf /var/lib/apt/lists/*

ENV LANG=pt_BR
